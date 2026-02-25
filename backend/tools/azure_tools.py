from langchain.tools import tool
from services.azure_devops import AzureDevOpsService

azure_service = AzureDevOpsService()

@tool
def list_projects_tool() -> list:
    """Lista todos os projetos do Azure DevOps disponíveis."""
    return azure_service.list_projects()

@tool
def create_work_item_tool(
        project: str,
        work_item_type: str,
        title: str,
        description: str | None = None,
        parent_id: int | None = None
):
    """
    Cria um Work Item no Azure DevOps.

    Tipos permitidos (work_item_type):
    - Epic
    - User Story
    - Task
    - Bug
    - Reunion
    - Test
    - Theme
    - Study
    - Feature
    - Scope Creep
    - Test Case
    
    Para criar um Work Item é necessário enviar:
    - Nome do projeto (project)
    - Título (title)
    - Tipo (work_item_type)
    
    Os campos opcionais são:
    - Descrição (description)
    - ID do pai para vinculação hierárquica, se aplicável (parent_id)
    """

    try:
        result = azure_service.create_work_item(
            project=project,
            work_item_type=work_item_type,
            title=title,
            description=description,
            parent_id=parent_id
        )

        return result

    except Exception as e:
        return {
            "error": "UNEXPECTED_ERROR",
            "message": str(e)
        }

# @tool
# def create_epic_tool(project: str, title: str, description: str = "") -> dict:
#     """Cria um Epic em um projeto Azure DevOps."""
#     wi = azure_service.create_epic(project, title, description)
#     return {"id": wi.id, "title": title}


# @tool
# def create_user_story_tool(
#     project: str,
#     title: str,
#     description: str = "",
#     parent_epic_id: int | None = None
# ) -> dict:
#     """
#     Cria uma User Story.
#     Pode opcionalmente vincular a um Epic existente.
#     """
#     wi = azure_service.create_user_story(
#         project,
#         title,
#         description,
#         parent_epic_id
#     )
#     return {"id": wi.id}


# @tool
# def create_task_tool(
#     project: str,
#     title: str,
#     parent_user_story_id: int | None = None
# ) -> dict:
#     """
#     Cria uma Task.
#     Pode opcionalmente vincular a uma User Story existente.
#     """
#     wi = azure_service.create_task(
#         project,
#         title,
#         parent_user_story_id
#     )
#     return {"id": wi.id}


@tool
def get_backlog_structure_tool(project: str) -> list:
    """Lista toda a estrutura Epic → User Story → Task do projeto."""
    return azure_service.get_backlog_structure(project)