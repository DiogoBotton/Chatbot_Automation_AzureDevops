import json
from typing import List
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, ToolMessage
from domains.enums.message_type import MessageType
from domains.conversation_history import ConversationHistory
from settings import Settings
from langchain_mcp_adapters.client import MultiServerMCPClient
from infrastructure.services.llm_utils import has_error

from infrastructure.constants.prompts import SYS_PROMPT_LLM_FINAL_RESPONSE, SYS_PROMPT_LLM_TOOLS

class ChatbotService:
    def __init__(self):
        self.client_mcp = None
        self.tools = []
        self.tool_map = {}

        self.llm = None
        self.llm_with_tools = None

    async def initialize(self):
        self.client_mcp = MultiServerMCPClient({
            "azure_devops_api": {
                "url": f"{Settings().API_TOOLS_URL}/mcp",
                "transport": "sse"
            }
        })
        
        self.tools = await self.client_mcp.get_tools()

        self.tool_map = {tool.name: tool for tool in self.tools}

        self.llm, self.llm_with_tools = self._model_openai()

    def _model_openai(self, model_name = "gpt-4o-mini", temperature = 0):
        """
        Acessa o modelo do Chat GPT pela API.
        Retorna o modelo normal e o modelo com as ferramentas acopladas (bind_tools).
            - O modelo normal é utilizado para responder perguntas simples, que não precisam de ferramentas.
            - O modelo com ferramentas acopladas é utilizado para identificar quando o modelo precisa chamar uma ferramenta e qual ferramenta chamar.
        """
        llm = ChatOpenAI(model = model_name, temperature = temperature)
        llm_with_tools = llm.bind_tools(self.tools)
        return llm, llm_with_tools

    def _build_messages(self, user_query: str, chat_history: List[BaseMessage]):
        """
        Gera a lista de mensagens para passar como contexto para o modelo. A lista é composta por:
        - SystemMessage: mensagem de sistema (prompt) para orientar o comportamento do modelo
        - BaseMessage: mensagens anteriores da conversa (chat_history)
        - HumanMessage: mensagem atual do usuário (user_query)
        """

        return chat_history + [HumanMessage(content=user_query)]
    
    def _add_sys_prompt(self, sys_prompt: str, chat_history: List[BaseMessage]):
        """
        Adiciona o prompt de sistema no início da lista de mensagens. O prompt de sistema é utilizado para orientar o comportamento do modelo.
        """
        if chat_history and isinstance(chat_history[0], SystemMessage):
            del chat_history[0]
            
        return [SystemMessage(content=sys_prompt)] + chat_history

    async def execute_llm_with_tools(self, messages: List[BaseMessage], new_messages: List[ConversationHistory]):
        for step in range(15):
            print(f"Step {step+1}/15 - Executando modelo com ferramentas...")
            # Identifica se o modelo precisa chamar uma ferramenta ou não
            response = await self.llm_with_tools.ainvoke(messages)
            
            if "FINAL_RESPONSE_READY" in response.content:
                break
            
            # Mensagem da resposta final do modelo, sem chamar a ferramenta
            if not response.tool_calls:
                print("Resposta final do modelo obtida.")
                return response, messages
            
            # Mensagem de chamada de ferramentas
            new_messages.append(ConversationHistory(
                role=MessageType.ASSISTANT,
                tool_calls=response.tool_calls))
            
            # Adiciona o response a lista de mensagens para o modelo saber que houve necessidade de chamar uma ferramenta
            messages.append(response)
            error = False
            # Caso o modelo precise chamar uma ferramenta
            for tool_call in response.tool_calls:
                print(f"Chamando ferramenta: {tool_call['name']}")
                # Busca a função do tool_map (dicionário) pelo nome da ferramenta
                tool_func = self.tool_map.get(tool_call["name"])
                if tool_func:
                    try:
                        # Caso achar a ferramenta, chama a função passando os parâmetros (args) necessários
                        tool_response = await tool_func.ainvoke(tool_call["args"])
                        
                        if has_error(tool_response):
                            error = True
                            tool_response = json.dumps(tool_response)
                    except Exception as e:
                        error = True
                        tool_response = {"error": str(e)}
                        
                    # Adiciona o resultado da ferramenta como um ToolMessage para o modelo usar como contexto para responder a pergunta
                    messages.append(ToolMessage(
                        content=str(tool_response),
                        tool_call_id=tool_call["id"])) # Necessário o tool_call_id para o modelo entender de qual chamada de ferramenta aquela resposta se refere
                    
                    # Mensagem de resultado da ferramenta
                    new_messages.append(ConversationHistory(
                        role=MessageType.TOOL,
                        content=str(tool_response),
                        tool_call_id=tool_call["id"]))
                    
                    if error:
                        break
            if error:
                break
            
        return None, messages
    
    async def _execute_streaming(self, messages: List[BaseMessage], new_messages: List[ConversationHistory]):
        chunks = []
        
        # Finalmente, chama o modelo novamente (sem tools) passando toda a conversa (requisição para ferramenta + resposta) para gerar a resposta final
        async for chunk in self.llm.astream(messages):
            if chunk.content:
                chunks.append(chunk.content)
                yield chunk.content
        
        full_content = "".join(chunks)
        
        # Salva mensagem final do modelo
        new_messages.append(ConversationHistory(
            role=MessageType.ASSISTANT,
            content=full_content))

    async def get_response_stream(self, user_query: str, chat_history: List[BaseMessage]) -> tuple[str, List[ConversationHistory]]:
        # A edição de new_messages ocorre com referência de memória
        new_messages = []
        messages = self._build_messages(user_query, chat_history)
        messages = self._add_sys_prompt(SYS_PROMPT_LLM_TOOLS, messages)

        response, messages = await self.execute_llm_with_tools(messages, new_messages)
        
        if response:
            async def generator():
                for char in response.content:
                    yield char
                                
            new_messages.append(ConversationHistory(
                role=MessageType.ASSISTANT,
                content=response.content))
            
            return generator(), new_messages
        
        messages = self._add_sys_prompt(SYS_PROMPT_LLM_FINAL_RESPONSE, messages)
        # Caso precise de chamar uma ferramenta, gera a resposta final com o contexto atualizado (mensagem do modelo + resposta da ferramenta)
        return self._execute_streaming(messages, new_messages), new_messages