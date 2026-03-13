from fastapi import Depends
from infrastructure.dtos.work_items.work_item_result import WorkItemResult
from infrastructure.enums.work_item import WorkItemProps, WorkItemTypes
from infrastructure.services.azure.azure_service import AzureDevOpsService
from pydantic import BaseModel, Field

from . import BaseHandler
from uuid import UUID

class Command(BaseModel):
    project_id: UUID = Field(description="ID do projeto no Azure DevOps (UUID). Use GET /projects para obter.")
    title: str = Field(description="Título da User Story", examples=["Como usuário, quero ..."])
    original_estimate: float = Field(
        description=(
            "Esforço original estimado em horas. "
            "Sugestão: use múltiplos de 0.25 (15min). Ex.: 0.25, 0.5, 1, 1.5"
        ),
        examples=[1.5],
    )
    parent_id: int | None = Field(
        default=None,
        description="ID do pai (Epic/Feature) para criar vínculo hierárquico",
        examples=[1234],
    )


class Chatbot(BaseHandler[Command, WorkItemResult]):
    def __init__(self, azureService: AzureDevOpsService = Depends()):
        self.azureService = azureService

    def execute(self, request: Command) -> WorkItemResult:
        try:
            project_name = self.azureService.get_project_by_id(request.project_id)

            default_dev_area = "Back-End"

            fields = {
                WorkItemProps.TITLE.value: request.title,
                WorkItemProps.ORIGINAL_ESTIMATE.value: request.original_estimate,
                WorkItemProps.DEVELOPMENT_AREA.value: default_dev_area,
                WorkItemProps.BLOCKED.value: "No",
                WorkItemProps.VALUE_AREA.value: "Business",
            }

            return self.azureService.create_work_item(
                project_id=request.project_id,
                project_name=project_name,
                work_item_type=WorkItemTypes.USER_STORY.value,
                fields=fields,
                parent_id=request.parent_id,
            )

        except ValueError as e:
            return WorkItemResult(error="PROJECT_NOT_FOUND", message=str(e))
        except Exception as e:
            return WorkItemResult(error="UNEXPECTED_ERROR", message=str(e))
