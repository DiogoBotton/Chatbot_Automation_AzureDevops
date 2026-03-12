from fastapi import Depends
from infrastructure.dtos.work_items.backlog_structure_result import BacklogStructureResult
from infrastructure.services.azure.azure_service import AzureDevOpsService
from pydantic import BaseModel, Field

from . import BaseHandler


class Command(BaseModel):
    project: str = Field(
        description="Nome exato do projeto no Azure DevOps",
        examples=["MeuProjeto"],
    )


class Chatbot(BaseHandler[Command, BacklogStructureResult]):
    def __init__(self, azureService: AzureDevOpsService = Depends()):
        self.azureService = azureService

    def execute(self, request: Command) -> BacklogStructureResult:
        try:
            return self.azureService.get_backlog_structure(request.project)
        except Exception as e:
            return BacklogStructureResult(error="UNEXPECTED_ERROR", message=str(e))
