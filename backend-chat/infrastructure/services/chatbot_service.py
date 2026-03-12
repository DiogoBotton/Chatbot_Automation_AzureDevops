from typing import List
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, ToolMessage
from domains.enums.message_type import MessageType
from domains.conversation_history import ConversationHistory
from settings import Settings
import time
from langchain_mcp_adapters.client import MultiServerMCPClient

class ChatbotService:
    def __init__(self):
        self.sys_prompt = """
            Você é um Product Owner técnico especializado em Azure DevOps.

            Você pode agir exclusivamente através das ferramentas disponíveis.
            Nunca simule resultados manualmente.

            REGRAS FUNDAMENTAIS:

            1) Nunca invente os paramêtros (args) das funções, sempre use os dados fornecidos pelo usuário ou retorne erro de campos faltantes.

            2) Nunca execute uma ferramenta se houver qualquer campo obrigatório ausente.

            3) Se faltar informação:
            - Pergunte explicitamente apenas pelos campos faltantes.
            - Não faça suposições.
            - Não gere valores automaticamente.
            - Aguarde o usuário responder.
            - Só então execute a ferramenta.

            4) Hierarquia:
            Epic → User Story → Task
            Task não pode ter filhos.

            5) Se o pedido não for relacionado ao Azure DevOps, informe que você apenas gerencia backlog no Azure DevOps.

            COMPORTAMENTO:

            - Trabalhe de forma incremental.
            - Faça uma pergunta por vez se necessário.
            - Só execute ferramentas quando tiver 100% dos dados obrigatórios.
            - Seja objetivo e técnico.
            """
            
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

        self.llm, self.llm_with_tools = self.model_openai()

    def model_openai(self, model_name = "gpt-4o-mini", temperature = 0):
        """
        Acessa o modelo do Chat GPT pela API.
        Retorna o modelo normal e o modelo com as ferramentas acopladas (bind_tools).
            - O modelo normal é utilizado para responder perguntas simples, que não precisam de ferramentas.
            - O modelo com ferramentas acopladas é utilizado para identificar quando o modelo precisa chamar uma ferramenta e qual ferramenta chamar.
        """
        llm = ChatOpenAI(model = model_name, temperature = temperature)
        llm_with_tools = llm.bind_tools(self.tools)
        return llm, llm_with_tools

    def build_messages(self, user_query: str, chat_history: List[BaseMessage]):
        """
        Gera a lista de mensagens para passar como contexto para o modelo. A lista é composta por:
        - SystemMessage: mensagem de sistema (prompt) para orientar o comportamento do modelo
        - BaseMessage: mensagens anteriores da conversa (chat_history)
        - HumanMessage: mensagem atual do usuário (user_query)
        """
        system = SystemMessage(content=self.sys_prompt)

        return [system] + chat_history + [HumanMessage(content=user_query)]

    async def execute_llm_with_tools(self, messages: List[BaseMessage], new_messages: List[ConversationHistory]):
        # Identifica se o modelo precisa chamar uma ferramenta ou não
        response = await self.llm_with_tools.ainvoke(messages)
        
        # Mensagem da resposta final do modelo, sem chamar a ferramenta
        if not response.tool_calls:
            return response, messages
        
        # Mensagem de chamada de ferramentas
        new_messages.append(ConversationHistory(
            role=MessageType.ASSISTANT,
            tool_calls=response.tool_calls))
        
        # Adiciona o response a lista de mensagens para o modelo saber que houve necessidade de chamar uma ferramenta
        messages.append(response)
        
        # Caso o modelo precise chamar uma ferramenta
        for tool_call in response.tool_calls:
            
            # Busca a função do tool_map (dicionário) pelo nome da ferramenta
            tool_func = self.tool_map.get(tool_call["name"])
            if tool_func:
                try:
                    # Caso achar a ferramenta, chama a função passando os parâmetros (args) necessários
                    tool_response = await tool_func.ainvoke(tool_call["args"])
                except Exception as e:
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
        
        return None, messages
    
    def execute_streaming(self, messages: List[BaseMessage], new_messages: List[ConversationHistory]):
        full_content = ""
        
        # Finalmente, chama o modelo novamente (sem tools) passando toda a conversa (requisição para ferramenta + resposta) para gerar a resposta final
        for chunk in self.llm.stream(messages):
            if chunk.content:
                full_content += chunk.content
                yield chunk.content
        
        # Salva mensagem final do modelo
        new_messages.append(ConversationHistory(
            role=MessageType.ASSISTANT,
            content=full_content))

    async def get_response_stream(self, user_query: str, chat_history: List[BaseMessage]) -> tuple[str, List[ConversationHistory]]:
        # A edição de new_messages ocorre com referência de memória
        new_messages = []
        messages = self.build_messages(user_query, chat_history)

        response, messages = await self.execute_llm_with_tools(messages, new_messages)
        
        if response:
            def generator():
                for char in response.content:
                    time.sleep(0.005) # Simula delay de streaming
                    yield char
                                
            new_messages.append(ConversationHistory(
                role=MessageType.ASSISTANT,
                content=response.content))
            
            return generator(), new_messages
        
        # Caso precise de chamar uma ferramenta, gera a resposta final com o contexto atualizado (mensagem do modelo + resposta da ferramenta)
        return self.execute_streaming(messages, new_messages), new_messages