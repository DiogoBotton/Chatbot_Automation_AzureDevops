from mcp.server.fastmcp import FastMCP

from tools.projects import register_project_tools
from tools.work_items import register_work_item_tools

# Servidor MCP puro — expõe ferramentas Azure DevOps via SSE (sem FastAPI/Swagger)
# Para debug/teste interativo local: uv run mcp dev main.py
# O MCP Inspector abrirá no browser (http://localhost:5173) para chamar as tools manualmente.
mcp = FastMCP("Azure DevOps Tools", host="0.0.0.0", port=5050)

register_project_tools(mcp)
register_work_item_tools(mcp)

if __name__ == "__main__":
    mcp.run(transport="sse")