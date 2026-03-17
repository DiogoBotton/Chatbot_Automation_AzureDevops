from mcp.server.fastmcp import FastMCP

from infrastructure.services.azure.azure_service import AzureDevOpsService


def register_project_tools(mcp: FastMCP) -> None:
    """Registra as ferramentas MCP relacionadas a projetos Azure DevOps."""

    # Instância única do serviço por processo — evita overhead de reconexão por chamada
    _service = AzureDevOpsService()

    @mcp.tool()
    def list_projects() -> list[dict]:
        """
        Lista todos os projetos Azure DevOps disponíveis.
        Retorna lista com id, name e state de cada projeto.
        Use para obter o project_id correto antes de criar work items.
        """
        return _service.list_projects()
