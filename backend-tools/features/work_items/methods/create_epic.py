from datetime import datetime
from infrastructure.dtos.work_items.work_item_result import WorkItemResult
from infrastructure.dtos.work_items.work_item_batch_result import WorkItemBatchResult
from infrastructure.services.azure.azure_service import AzureDevOpsService
from infrastructure.enums.work_item import WorkItemProps, WorkItemTypes
from pydantic import BaseModel, Field
from . import BaseHandler

from uuid import UUID


class EpicItem(BaseModel):
    title: str = Field(description="Título do Epic")
    description: str | None = Field(default=None, description="Descrição do Epic")
    parent_id: int | None = Field(default=None, description="ID do Epic pai")


# Request
class Command(BaseModel):
    project_id: UUID = Field(description="ID do projeto no Azure DevOps (UUID). Use GET /projects para obter.")
    items: list[EpicItem] = Field(
        description="Lista de Epics a serem criadas. Pode conter 1 ou mais itens.",
        min_length=1,
    )


# Handle
class Chatbot(BaseHandler[Command, WorkItemBatchResult]):
    def __init__(self):
        self.azureService = AzureDevOpsService()

    def execute(self, request: Command) -> WorkItemBatchResult:
        results: list[WorkItemResult] = []

        try:
            project_name = self.azureService.get_project_by_id(request.project_id)
        except ValueError as e:
            return WorkItemBatchResult(
                total=len(request.items),
                created=0,
                results=[WorkItemResult(error="PROJECT_NOT_FOUND", message=str(e))],
            )

        for item in request.items:
            try:
                fields = {
                    WorkItemProps.TITLE.value: item.title,
                    WorkItemProps.DESCRIPTION.value: item.description or "",
                    WorkItemProps.START_DATE.value: datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
                    WorkItemProps.FINISH_DATE.value: datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
                    WorkItemProps.VALUE_AREA.value: "Business"
                }

                result = self.azureService.create_work_item(
                    project_id=request.project_id,
                    project_name=project_name,
                    work_item_type=WorkItemTypes.EPIC.value,
                    fields=fields,
                    parent_id=item.parent_id,
                )
                results.append(result)

            except Exception as e:
                results.append(WorkItemResult(error="UNEXPECTED_ERROR", message=str(e)))

        created = sum(1 for r in results if r.error is None)
        return WorkItemBatchResult(total=len(request.items), created=created, results=results)