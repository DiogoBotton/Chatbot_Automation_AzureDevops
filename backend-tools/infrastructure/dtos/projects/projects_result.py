from infrastructure.dtos.base import BaseResult


class ProjectsResult(BaseResult):
    response: list[dict]
