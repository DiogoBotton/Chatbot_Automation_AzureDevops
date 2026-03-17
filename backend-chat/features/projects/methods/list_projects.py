from pydantic import BaseModel
from infrastructure.services.azure.azure_service import AzureDevOpsService
from . import BaseHandler


class Query(BaseModel):
    pass


class ListProjects(BaseHandler[Query, list]):
    def __init__(self):
        self.azure_service = AzureDevOpsService()

    def execute(self, request: Query) -> list:
        return self.azure_service.list_projects()
