from fastapi import Depends
from infrastructure.dtos.projects.projects_result import ProjectsResult
from infrastructure.services.azure.azure_service import AzureDevOpsService
from pydantic import BaseModel

from . import BaseHandler


class Query(BaseModel):
    pass


class Chatbot(BaseHandler[Query, ProjectsResult]):
    def __init__(self, azureService: AzureDevOpsService = Depends()):
        self.azureService = azureService

    def execute(self, request: Query) -> ProjectsResult:
        try:
            result = self.azureService.list_projects()
            return ProjectsResult(response=result)
        except Exception as e:
            return ProjectsResult(response=[{"error": "UNEXPECTED_ERROR", "message": str(e)}])
