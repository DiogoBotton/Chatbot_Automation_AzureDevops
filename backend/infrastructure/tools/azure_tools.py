from datetime import datetime

from langchain.tools import tool
from constants.work_item import WorkItemProps, WorkItemTypes
from infrastructure.services.azure.azure_service import AzureDevOpsService

azure_service = AzureDevOpsService()

@tool
def create_epic_tool(
        project: str,
        title: str,
        description: str | None = None,
        parent_id: int | None = None
):
    """
    Cria uma Epic no Azure DevOps.
    
    Para criar uma Epic é necessário enviar:
    - Nome do projeto (project)
    - Título (title)
    
    Os campos opcionais são:
    - Descrição (description)
    - ID do pai para vinculação hierárquica, se aplicável (parent_id)
    """
    try:
        fields = {
            WorkItemProps.TITLE.value: title,
            WorkItemProps.DESCRIPTION.value: description or "",
            WorkItemProps.START_DATE.value: datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
            WorkItemProps.FINISH_DATE.value: datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
            WorkItemProps.VALUE_AREA.value: "Business"
        }
        
        result = azure_service.create_work_item(
            project=project,
            work_item_type=WorkItemTypes.EPIC.value,
            fields=fields,
            parent_id=parent_id
        )

        return result

    except Exception as e:
        return {
            "error": "UNEXPECTED_ERROR",
            "message": str(e)
        }
    
@tool
def create_user_story_tool(
    project: str,
    title: str,
    original_estimate: float,
    parent_id: int | None = None
):
    """
    Cria uma User Story no Azure DevOps.
    
    Obrigatório:
    - project
    - title
    - original_estimate
        - Os números válidos devem ser de 15 em 15 minutos (0.25, 0.5, 0.75, 1, 1.25, etc), mas aceite também números inteiros para facilitar ou horas/minutos convertendo para horas (ex: 90 minutos = 1.5 horas)
    
    Opcional:
    - parent_id (para vincular a uma Epic ou Feature existente)"""

    try:
        default_dev_area = "Back-End"

        fields = {
            WorkItemProps.TITLE.value: title,
            WorkItemProps.ORIGINAL_ESTIMATE.value: original_estimate,
            WorkItemProps.DEVELOPMENT_AREA.value: default_dev_area,
            WorkItemProps.BLOCKED.value: "No",
            WorkItemProps.VALUE_AREA.value: "Business"
        }

        result = azure_service.create_work_item(
            project=project,
            work_item_type=WorkItemTypes.USER_STORY.value,
            fields=fields,
            parent_id=parent_id
        )

        return result

    except Exception as e:
        return {
            "error": "UNEXPECTED_ERROR",
            "message": str(e)
        }
    
@tool
def create_task_tool(
    project: str,
    title: str,
    original_estimate: float,
    parent_id: int | None = None
):
    """
    Cria uma Task no Azure DevOps.

    Obrigatório:
    - project
    - title
    - original_estimate
        - Os números válidos devem ser de 15 em 15 minutos (0.25, 0.5, 0.75, 1, 1.25, etc), mas aceite também números inteiros para facilitar ou horas/minutos convertendo para horas (ex: 90 minutos = 1.5 horas)
    """

    try:
        # Defaults temporários
        default_activity = "Development"  # depois pode buscar dinamicamente
        default_dev_area = "Back-End"      # depois pode buscar dinamicamente

        fields = {
            WorkItemProps.TITLE.value: title,
            WorkItemProps.ORIGINAL_ESTIMATE.value: original_estimate,
            WorkItemProps.ACTIVITY.value: default_activity,
            WorkItemProps.DEVELOPMENT_AREA.value: default_dev_area,
            WorkItemProps.BLOCKED.value: "No"
        }

        result = azure_service.create_work_item(
            project=project,
            work_item_type=WorkItemTypes.TASK.value,
            fields=fields,
            parent_id=parent_id
        )

        return result

    except Exception as e:
        return {
            "error": "UNEXPECTED_ERROR",
            "message": str(e)
        }
        
@tool
def list_projects_tool() -> list:
    """
    Lista todos os projetos do Azure DevOps disponíveis.
    Quando for o caso, use essa tool para obter o nome exato do projeto para usar nas outras ferramentas.
    """
    return azure_service.list_projects()

@tool
def get_backlog_structure_tool(project: str) -> list:
    """
    Lista toda a estrutura Epic → User Story → Task do projeto.
    Quando for o caso, use essa tool quando precisar saber o ID de alguma Work Item pelo nome para vincular como pai.
    """
    return azure_service.get_backlog_structure(project)