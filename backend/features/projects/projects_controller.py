from fastapi import APIRouter, Depends
from features.projects.methods import list_projects

router = APIRouter(tags=["Projects"], prefix="/projects")


@router.get("/", response_model=list)
def list_projects_endpoint(handler: list_projects.ListProjects = Depends()):
    """
    Lista todos os projetos Azure DevOps disponíveis.
    Utilizado pelo frontend para popular o seletor de projeto obrigatório antes do chat.
    """
    return handler.execute(list_projects.Query())
