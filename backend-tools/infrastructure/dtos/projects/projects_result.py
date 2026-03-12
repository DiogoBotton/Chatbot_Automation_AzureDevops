from pydantic import BaseModel
from infrastructure.dtos.base import BaseResult


class ProjectItem(BaseModel):
    id: str
    name: str
    state: str


class ProjectsResult(BaseResult):
    items: list[ProjectItem]
