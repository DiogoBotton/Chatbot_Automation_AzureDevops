from datetime import datetime
from fastapi import Depends
from fastapi.encoders import jsonable_encoder
from infrastructure.dtos.work_items.work_item_result import WorkItemResult
from infrastructure.services.azure.azure_service import AzureDevOpsService
from infrastructure.enums.work_item import WorkItemProps, WorkItemTypes
from pydantic import BaseModel, Field
from . import BaseHandler

# Request
class Command(BaseModel):
    project: str = Field(description="Projeto do Epic")
    title: str = Field(description="Título do Epic")
    description: str | None = Field(default=None, description="Descrição do Epic")
    parent_id: int | None = Field(default=None, description="ID do Epic pai")

# Handle
class Chatbot(BaseHandler[Command, WorkItemResult]):
    def __init__(self, azureService: AzureDevOpsService = Depends()):
        self.azureService = azureService

    def execute(self, request: Command) -> WorkItemResult:
        try:
            fields = {
                WorkItemProps.TITLE.value: request.title,
                WorkItemProps.DESCRIPTION.value: request.description or "",
                WorkItemProps.START_DATE.value: datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
                WorkItemProps.FINISH_DATE.value: datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
                WorkItemProps.VALUE_AREA.value: "Business"
            }

            result = self.azureService.create_work_item(
                project=request.project,
                work_item_type=WorkItemTypes.EPIC.value,
                fields=fields,
                parent_id=request.parent_id
            )

            return WorkItemResult(response=jsonable_encoder(result))

        except Exception as e:
            return WorkItemResult(response={"error": "UNEXPECTED_ERROR", "message": str(e)})