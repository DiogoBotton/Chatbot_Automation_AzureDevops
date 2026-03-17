from infrastructure.services.azure.azure_client import AzureDevOpsClient


class AzureDevOpsService:
    def __init__(self):
        self.azure_client = AzureDevOpsClient()

    def list_projects(self) -> list[dict]:
        projects = self.azure_client.core_client.get_projects()
        return [
            {"id": project.id, "name": project.name, "state": project.state}
            for project in projects
        ]

    def get_project_by_id(self, project_id: str) -> str | None:
        """Retorna o nome do projeto dado seu ID. Retorna None se não encontrado."""
        project = self.azure_client.core_client.get_project(project_id)
        return project.name if project else None
