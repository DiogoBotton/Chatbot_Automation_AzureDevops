from pydantic import BaseModel
from infrastructure.dtos.work_items.work_item_base_result import WorkItemBaseResult


class CreatedWorkItemData(BaseModel):
    id: int
    title: str
    type: str
    assigned_to: str | None = None
    url: str | None = None
    original_estimate: float | None = None


class WorkItemResult(WorkItemBaseResult):
    response: CreatedWorkItemData | None = None
