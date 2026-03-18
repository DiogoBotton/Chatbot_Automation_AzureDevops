"""
Registro de ferramentas do chatbot Azure DevOps.

Para adicionar uma nova ferramenta:
  1. Crie-a em infrastructure/tools/<dominio>_tools.py.
  2. Importe-a aqui e adicione-a à lista retornada por get_chatbot_tools().
"""

from infrastructure.tools.azure_tools.azure_query_tools import (
    get_backlog_structure_tool,
    get_my_work_items_tool,
)
from infrastructure.tools.azure_tools.azure_transactional_tools import (
    create_epic_tool,
    create_feature_tool,
    create_user_story_tool,
    create_task_tool,
    assign_work_item_tool,
)
from infrastructure.tools.interaction_tools import think, ask_user, finish_task


def get_chatbot_tools() -> list:
    """
    Retorna todas as ferramentas disponíveis para o chatbot.
    A lista é construída dinamicamente para facilitar a adição de novos tools
    sem precisar alterar o ChatbotService.
    """
    return [
        create_epic_tool,
        create_feature_tool,
        create_user_story_tool,
        create_task_tool,
        assign_work_item_tool,
        get_backlog_structure_tool,
        get_my_work_items_tool,
    ]
