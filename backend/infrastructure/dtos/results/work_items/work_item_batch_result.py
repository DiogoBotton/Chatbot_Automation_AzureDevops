from pydantic import BaseModel

from infrastructure.dtos.results.work_items.work_item_result import WorkItemResult


class WorkItemBatchResult(BaseModel):
    total: int
    created: int
    results: list[WorkItemResult]
