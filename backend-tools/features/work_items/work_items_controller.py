from fastapi import APIRouter, Body, Depends

from features.work_items.methods import create_epic, create_task, create_user_story, get_backlog_structure
from infrastructure.dtos.work_items.backlog_structure_result import BacklogStructureResult
from infrastructure.dtos.work_items.work_item_result import WorkItemResult

router = APIRouter(tags=["Work Items"], prefix="/work-items")

@router.post("/epic", response_model=WorkItemResult)
async def create_epic_endpoint(command: create_epic.Command = Body(...),
               handler: create_epic.Chatbot = Depends()):
    """
    Cria uma Epic no Azure DevOps.

    **Obrigatório**
    - `project_id`: ID (UUID) do projeto no Azure DevOps
    - `title`: título da Epic

    **Opcional**
    - `description`: descrição da Epic
    - `parent_id`: ID do pai para vinculação hierárquica

    **Dica para LLM**
    - Use `GET /projects` para obter o `project_id` correto antes de criar.
    - O `project_id` é um UUID imutável — não alucie o nome do projeto.
    """
    return handler.execute(command)


@router.post("/user-story", response_model=WorkItemResult)
async def create_user_story_endpoint(
    command: create_user_story.Command = Body(...),
    handler: create_user_story.Chatbot = Depends(),
):
    """\
    Cria uma User Story no Azure DevOps.

    **Obrigatório**
    - `project_id`: ID (UUID) do projeto no Azure DevOps
    - `title`: título da User Story
    - `original_estimate`: esforço original em horas (ex.: `1.5` = 1h30)

    **Opcional**
    - `parent_id`: ID do pai (para vincular a uma Epic/Feature)

    **Dica para LLM**
    - Use `GET /projects` para obter o `project_id` correto antes de criar.
    - O `project_id` é um UUID imutável — não alucie o nome do projeto.
    """
    return handler.execute(command)


@router.post("/task", response_model=WorkItemResult)
async def create_task_endpoint(
    command: create_task.Command = Body(...),
    handler: create_task.Chatbot = Depends(),
):
    """\
    Cria uma Task no Azure DevOps.

    **Obrigatório**
    - `project_id`: ID (UUID) do projeto no Azure DevOps
    - `title`: título da Task
    - `original_estimate`: esforço original em horas (ex.: `0.25` = 15min)

    **Opcional**
    - `parent_id`: ID da User Story pai (recomendado)

    **Dica para LLM**
    - Use `GET /projects` para obter o `project_id` correto antes de criar.
    - O `project_id` é um UUID imutável — não alucie o nome do projeto.
    """
    return handler.execute(command)


@router.post("/backlog-structure", response_model=BacklogStructureResult)
async def get_backlog_structure_endpoint(
    command: get_backlog_structure.Command = Body(...),
    handler: get_backlog_structure.Chatbot = Depends(),
):
    """\
    Retorna a estrutura do backlog no formato **Epic → User Story → Task**.

    Use quando você precisar:
    - Encontrar IDs pelo título para vincular como `parent_id`.
    - Entender hierarquia existente antes de criar novos itens.

    **Entrada**
    - `project_id`: ID (UUID) do projeto no Azure DevOps.

    **Dica para LLM**
    - Use `GET /projects` para obter o `project_id` correto antes de usar.
    """
    return handler.execute(command)