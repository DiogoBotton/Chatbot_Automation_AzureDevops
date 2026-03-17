from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from features.conversation import conversation_controller
from features.chat import chat_controller
from features.projects import projects_controller
from infrastructure.services.mcp_manager import MCPManager
from dotenv import load_dotenv
import os
load_dotenv()

os.environ['OPENAI_API_KEY'] = os.getenv("OPENAI_API_KEY")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ciclo de vida da aplicação: conecta MCP no startup, desconecta no shutdown."""
    await MCPManager.connect()
    yield
    await MCPManager.disconnect()


app = FastAPI(
    title="Chatbot Tool CallingAPI",
    docs_url="/docs",
    lifespan=lifespan,
)

# Libera o CORS da API para requisições via http
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*']
)

app.include_router(chat_controller.router)
app.include_router(conversation_controller.router)
app.include_router(projects_controller.router)