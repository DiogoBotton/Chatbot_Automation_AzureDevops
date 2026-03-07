from infrastructure.dtos.base import BaseResult
    
class WorkItemResult(BaseResult):
    response: dict | None = None
