from fastapi import Depends
from fastapi.encoders import jsonable_encoder
from infrastructure.dtos.work_items.work_item_result import WorkItemResult
from infrastructure.enums.work_item import WorkItemProps, WorkItemTypes
from infrastructure.services.azure.azure_service import AzureDevOpsService
from pydantic import BaseModel, Field

from . import BaseHandler


class Command(BaseModel):
    project: str = Field(description="Nome exato do projeto no Azure DevOps", examples=["MeuProjeto"])
    title: str = Field(description="Título da Task", examples=["Implementar endpoint X"])
    original_estimate: float = Field(
        description=(
            "Esforço original estimado em horas. "
            "Sugestão: use múltiplos de 0.25 (15min). Ex.: 0.25, 0.5, 1, 1.5"
        ),
        examples=[0.5],
    )
    parent_id: int | None = Field(
        default=None,
        description="ID do pai (normalmente uma User Story) para criar vínculo hierárquico",
        examples=[5678],
    )


class Chatbot(BaseHandler[Command, WorkItemResult]):
    def __init__(self, azureService: AzureDevOpsService = Depends()):
        self.azureService = azureService

    def execute(self, request: Command) -> WorkItemResult:
        try:
            default_activity = "Development"
            default_dev_area = "Back-End"

            fields = {
                WorkItemProps.TITLE.value: request.title,
                WorkItemProps.ORIGINAL_ESTIMATE.value: request.original_estimate,
                WorkItemProps.ACTIVITY.value: default_activity,
                WorkItemProps.DEVELOPMENT_AREA.value: default_dev_area,
                WorkItemProps.BLOCKED.value: "No",
            }

            result = self.azureService.create_work_item(
                project=request.project,
                work_item_type=WorkItemTypes.TASK.value,
                fields=fields,
                parent_id=request.parent_id,
            )

            return WorkItemResult(response=jsonable_encoder(result))

        except Exception as e:
            return WorkItemResult(response={"error": "UNEXPECTED_ERROR", "message": str(e)})
