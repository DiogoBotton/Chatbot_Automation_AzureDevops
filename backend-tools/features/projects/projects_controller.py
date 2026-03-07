from fastapi import APIRouter, Depends

from features.projects.methods import list_projects
from infrastructure.dtos.projects.projects_result import ProjectsResult

router = APIRouter(tags=["Projects"], prefix="/projects")


@router.get("/", response_model=ProjectsResult)
async def list_projects_endpoint(
    handler: list_projects.Chatbot = Depends(),
):
    """\
    Lista todos os projetos do Azure DevOps disponíveis.

    **Quando usar**
    - Antes de criar Work Items, para obter o nome exato do projeto (`project`).

    **Saída**
    - Lista de projetos com `id`, `name` e `state`.
    """
    return handler.execute(list_projects.Query())
