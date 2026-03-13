from datetime import datetime
from fastapi import Depends
from infrastructure.dtos.work_items.work_item_result import WorkItemResult
from infrastructure.services.azure.azure_service import AzureDevOpsService
from infrastructure.enums.work_item import WorkItemProps, WorkItemTypes
from pydantic import BaseModel, Field
from . import BaseHandler

from uuid import UUID

# Request
class Command(BaseModel):
    project_id: UUID = Field(description="ID do projeto no Azure DevOps (UUID). Use GET /projects para obter.")
    title: str = Field(description="Título do Epic")
    description: str | None = Field(default=None, description="Descrição do Epic")
    parent_id: int | None = Field(default=None, description="ID do Epic pai")

# Handle
class Chatbot(BaseHandler[Command, WorkItemResult]):
    def __init__(self, azureService: AzureDevOpsService = Depends()):
        self.azureService = azureService

    def execute(self, request: Command) -> WorkItemResult:
        try:
            project_name = self.azureService.get_project_by_id(request.project_id)

            fields = {
                WorkItemProps.TITLE.value: request.title,
                WorkItemProps.DESCRIPTION.value: request.description or "",
                WorkItemProps.START_DATE.value: datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
                WorkItemProps.FINISH_DATE.value: datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
                WorkItemProps.VALUE_AREA.value: "Business"
            }

            return self.azureService.create_work_item(
                project_id=request.project_id,
                project_name=project_name,
                work_item_type=WorkItemTypes.EPIC.value,
                fields=fields,
                parent_id=request.parent_id
            )

        except ValueError as e:
            return WorkItemResult(error="PROJECT_NOT_FOUND", message=str(e))
        except Exception as e:
            return WorkItemResult(error="UNEXPECTED_ERROR", message=str(e))