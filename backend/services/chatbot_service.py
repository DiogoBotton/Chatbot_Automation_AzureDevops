from typing import List
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, ToolMessage
from tools.azure_tools import create_epic_tool, create_task_tool, create_user_story_tool, get_backlog_structure_tool, list_projects_tool

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

            4) Se uma tool retornar:
            {
              "error": "MISSING_REQUIRED_FIELDS",
              "missing_fields": [...]
            }

            Você deve:
            - Informar ao usuário quais campos estão faltando (nomes amigáveis).
            - Solicitar os valores.
            - Aguardar resposta.
            - Reexecutar a mesma tool incluindo TODOS os campos já informados + os novos.

            5) Hierarquia:
            Epic → User Story → Task
            Task não pode ter filhos.

            6) Se o pedido não for relacionado ao Azure DevOps, informe que você apenas gerencia backlog no Azure DevOps.

            COMPORTAMENTO:

            - Trabalhe de forma incremental.
            - Faça uma pergunta por vez se necessário.
            - Só execute ferramentas quando tiver 100% dos dados obrigatórios.
            - Seja objetivo e técnico.
            """
        self.llm, self.llm_with_tools = self.model_openai()

    def model_openai(self, model_name = "gpt-4o-mini", temperature = 0):
        """
        Acessa o modelo do Chat GPT pela API.
        Retorna o modelo normal e o modelo com as ferramentas acopladas (bind_tools).
            - O modelo normal é utilizado para responder perguntas simples, que não precisam de ferramentas.
            - O modelo com ferramentas acopladas é utilizado para identificar quando o modelo precisa chamar uma ferramenta e qual ferramenta chamar.
        """
        llm = ChatOpenAI(model = model_name, temperature = temperature)
        llm_with_tools = llm.bind_tools([create_epic_tool, create_task_tool, create_user_story_tool, get_backlog_structure_tool, list_projects_tool])
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

    def get_response(self, user_query: str, chat_history: List[BaseMessage]):
        messages = self.build_messages(user_query, chat_history)

        # Identifica se o modelo precisa chamar uma ferramenta ou não
        response = self.llm_with_tools.invoke(messages)

        # Caso o modelo precise chamar uma ferramenta
        if response.tool_calls:
            # Mapeia manualmente todas as ferramentas disponíveis para poder chamá-las dinamicamente depois
            tool_map = {
                "create_epic_tool": create_epic_tool,
                "create_task_tool": create_task_tool,
                "create_user_story_tool": create_user_story_tool,
                "get_backlog_structure_tool": get_backlog_structure_tool,
                "list_projects_tool": list_projects_tool
            }

            # Adiciona o response a lista de mensagens para o modelo saber que houve necessidade de chamar uma ferramenta
            messages.append(response)

            for tool_call in response.tool_calls:
                # Busca a função do tool_map (dicionário) pelo nome da ferramenta
                tool_func = tool_map.get(tool_call["name"])
                if tool_func:
                    try:
                        # Caso achar a ferramenta, chama a função passando os parâmetros (args) necessários
                        tool_response = tool_func.invoke(tool_call["args"])
                    except Exception as e:
                        tool_response = {"error": str(e)}

                    # Adiciona o resultado da ferramenta como um ToolMessage para o modelo usar como contexto para responder a pergunta
                    messages.append(ToolMessage(
                        content=str(tool_response),
                        tool_call_id=tool_call["id"])) # Necessário o tool_call_id para o modelo entender de qual chamada de ferramenta aquela resposta se refere

            # Finalmente, chama o modelo novamente (sem tools) passando toda a conversa (requisição para ferramenta + resposta) para gerar a resposta final
            final_response = self.llm.invoke(messages)

            # Retorna a resposta final
            return final_response.content

        # Caso o modelo não precise chamar uma ferramenta, retorna a resposta normalmente
        return response.content