from pydantic import BaseModel
from infrastructure.services.azure.azure_query_service import AzureQueryService
from . import BaseHandler


class Query(BaseModel):
    pass


class ListProjects(BaseHandler[Query, list]):
    def __init__(self):
        self.azure_service = AzureQueryService()

    def execute(self, request: Query) -> list:
        return self.azure_service.list_projects()
