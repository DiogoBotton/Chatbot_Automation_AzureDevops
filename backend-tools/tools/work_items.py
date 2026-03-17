from mcp.server.fastmcp import FastMCP

from features.work_items.methods.create_epic import Chatbot as EpicHandler
from features.work_items.methods.create_epic import Command as EpicCommand
from features.work_items.methods.create_epic import EpicItem
from features.work_items.methods.create_user_story import Chatbot as UserStoryHandler
from features.work_items.methods.create_user_story import Command as UserStoryCommand
from features.work_items.methods.create_user_story import UserStoryItem
from features.work_items.methods.create_task import Chatbot as TaskHandler
from features.work_items.methods.create_task import Command as TaskCommand
from features.work_items.methods.create_task import TaskItem
from features.work_items.methods.get_backlog_structure import Chatbot as BacklogHandler
from features.work_items.methods.get_backlog_structure import Command as BacklogCommand


def register_work_item_tools(mcp: FastMCP) -> None:
    """Registra as ferramentas MCP relacionadas a work items Azure DevOps."""

    @mcp.tool()
    def create_epic(project_id: str, items: list[EpicItem]) -> dict:
        """
        Cria uma ou mais Epics no Azure DevOps em batch.
        Pode enviar múltiplas Epics em uma única chamada usando a lista items.
        Retorna total criado e os detalhes de cada Epic — incluindo o id numérico
        que deve ser usado como parent_id ao criar User Stories.
        """
        result = EpicHandler().execute(EpicCommand(project_id=project_id, items=items))
        return result.model_dump()

    @mcp.tool()
    def create_user_story(project_id: str, items: list[UserStoryItem]) -> dict:
        """
        Cria uma ou mais User Stories no Azure DevOps em batch.
        parent_id é obrigatório: use o id numérico retornado por create_epic.
        Retorna total criado e os detalhes de cada User Story — incluindo o id numérico
        que deve ser usado como parent_id ao criar Tasks.
        """
        result = UserStoryHandler().execute(UserStoryCommand(project_id=project_id, items=items))
        return result.model_dump()

    @mcp.tool()
    def create_task(project_id: str, items: list[TaskItem]) -> dict:
        """
        Cria uma ou mais Tasks no Azure DevOps em batch.
        parent_id DEVE ser o id numérico de uma User Story — NUNCA de uma Epic.
        """
        result = TaskHandler().execute(TaskCommand(project_id=project_id, items=items))
        return result.model_dump()

    @mcp.tool()
    def get_backlog_structure(project_id: str) -> dict:
        """
        Retorna a estrutura hierárquica completa do backlog do projeto.
        Inclui Epics com User Stories e Tasks aninhadas, mais itens órfãos.
        Use para entender o estado atual do backlog antes de criar novos itens.
        """
        result = BacklogHandler().execute(BacklogCommand(project_id=project_id))
        return result.model_dump()
