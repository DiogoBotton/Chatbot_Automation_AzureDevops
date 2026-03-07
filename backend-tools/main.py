from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from features.work_items import work_items_controller
from features.projects import projects_controller

app = FastAPI(
    title="API Tools MCP",
    docs_url="/docs",  # URL para disponibilização do Swagger UI
)

# Libera o CORS da API para requisições via http
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*']
)

app.include_router(work_items_controller.router)
app.include_router(projects_controller.router)