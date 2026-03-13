from fastapi import Depends
from infrastructure.dtos.work_items.backlog_structure_result import BacklogStructureResult
from infrastructure.services.azure.azure_service import AzureDevOpsService
from pydantic import BaseModel, Field

from . import BaseHandler
from uuid import UUID

class Command(BaseModel):
    project_id: UUID = Field(
        description="ID do projeto no Azure DevOps (UUID). Use GET /projects para obter.",
    )


class Chatbot(BaseHandler[Command, BacklogStructureResult]):
    def __init__(self, azureService: AzureDevOpsService = Depends()):
        self.azureService = azureService

    def execute(self, request: Command) -> BacklogStructureResult:
        try:
            return self.azureService.get_backlog_structure(str(request.project_id))
        except ValueError as e:
            return BacklogStructureResult(error="PROJECT_NOT_FOUND", message=str(e))
        except Exception as e:
            return BacklogStructureResult(error="UNEXPECTED_ERROR", message=str(e))
