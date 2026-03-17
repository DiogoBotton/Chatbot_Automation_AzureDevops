from infrastructure.dtos.work_items.work_item_result import WorkItemResult
from infrastructure.dtos.work_items.work_item_batch_result import WorkItemBatchResult
from infrastructure.enums.work_item import WorkItemProps, WorkItemTypes
from infrastructure.services.azure.azure_service import AzureDevOpsService
from pydantic import BaseModel, Field

from . import BaseHandler
from uuid import UUID


class UserStoryItem(BaseModel):
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
        description="ID numérico do pai (Epic/Feature). Obrigatório — use o ID retornado na criação do item pai.",
        examples=[1234],
    )


class Command(BaseModel):
    project_id: UUID = Field(description="ID do projeto no Azure DevOps (UUID). Use GET /projects para obter.")
    items: list[UserStoryItem] = Field(
        description="Lista de User Stories a serem criadas. Pode conter 1 ou mais itens.",
        min_length=1,
    )


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
                if item.parent_id is None:
                    results.append(WorkItemResult(
                        error="MISSING_PARENT_ID",
                        message=f"parent_id é obrigatório para User Story '{item.title}'. Use o ID retornado na criação da Epic ou Feature pai."
                    ))
                    continue

                fields = {
                    WorkItemProps.TITLE.value: item.title,
                    WorkItemProps.ORIGINAL_ESTIMATE.value: item.original_estimate,
                    WorkItemProps.DEVELOPMENT_AREA.value: "Back-End",
                    WorkItemProps.BLOCKED.value: "No",
                    WorkItemProps.VALUE_AREA.value: "Business",
                }

                result = self.azureService.create_work_item(
                    project_id=request.project_id,
                    project_name=project_name,
                    work_item_type=WorkItemTypes.USER_STORY.value,
                    fields=fields,
                    parent_id=item.parent_id,
                )
                results.append(result)

            except Exception as e:
                results.append(WorkItemResult(error="UNEXPECTED_ERROR", message=str(e)))

        created = sum(1 for r in results if r.error is None)
        return WorkItemBatchResult(total=len(request.items), created=created, results=results)
