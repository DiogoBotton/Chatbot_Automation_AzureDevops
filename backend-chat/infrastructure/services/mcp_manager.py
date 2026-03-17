from langchain_mcp_adapters.client import MultiServerMCPClient
from settings import Settings
from infrastructure.tools.interaction_tools import ask_user, think


class MCPManager:
    """
    Gerencia o ciclo de vida da conexão MCP com o backend-tools.

    Inicializado uma vez no startup da aplicação (via FastAPI lifespan)
    e compartilhado entre todas as requests. Não depende de flags ou
    inicialização lazy — o ciclo é explícito: connect() → get_tools() → disconnect().
    """

    _client: MultiServerMCPClient | None = None
    _tools: list = []

    @classmethod
    async def connect(cls) -> None:
        """Estabelece a conexão SSE com o servidor MCP e descobre as tools remotas."""
        if cls._client is not None:
            return

        cls._client = MultiServerMCPClient({
            "azure_devops_api": {
                "url": f"{Settings().API_TOOLS_URL}/sse",
                "transport": "sse",
            }
        })

        remote_tools = await cls._client.get_tools()
        # Tools locais (think, ask_user) são adicionadas aqui para centralizar
        cls._tools = remote_tools + [think, ask_user]

    @classmethod
    async def disconnect(cls) -> None:
        """Libera a conexão MCP. Chamado no shutdown da aplicação."""
        cls._client = None
        cls._tools = []

    @classmethod
    def get_tools(cls) -> list:
        """Retorna as tools disponíveis (remotas + locais)."""
        if not cls._tools:
            raise RuntimeError("MCPManager não inicializado. Chame connect() no lifespan da aplicação.")
        return cls._tools
