from langchain.tools import tool

from infrastructure.services.azure.azure_query_service import AzureQueryService

_query_service = AzureQueryService()


@tool
def list_projects_tool() -> list:
    """
    Lista todos os projetos Azure DevOps disponíveis. Retorna id, name e state de cada projeto.
    Chame esta ferramenta quando o projeto ativo não estiver definido no contexto.
    """
    print("list_projects_tool chamado")
    return _query_service.list_projects()


@tool
def get_backlog_structure_tool(project_id: str) -> dict:
    """
    Retorna a estrutura hierárquica completa do backlog (Epic → User Story → Task).
    Use para consultar o estado atual do backlog ou obter o ID de uma work item existente para usar como parent_id.
    """
    print(f"get_backlog_structure_tool chamado com project_id={project_id}")
    result = _query_service.get_backlog_structure(project_id)
    return result.model_dump()


@tool
def get_my_work_items_tool(project_id: str) -> list:
    """
    Retorna todas as work items atribuídas ao usuário autenticado pelo PAT (@Me).
    Use para responder perguntas como "quais work items estão atreladas a mim?".
    """
    print(f"get_my_work_items_tool chamado com project_id={project_id}")
    return _query_service.get_my_work_items(project_id)
