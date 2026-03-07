from azure.devops.connection import Connection
from msrest.authentication import BasicAuthentication
from azure.devops.v7_0.work_item_tracking.work_item_tracking_client import WorkItemTrackingClient
from azure.devops.v7_0.core.core_client import CoreClient
from settings import Settings

class AzureDevOpsClient:
    def __init__(self):
        settings = Settings()
        credentials = BasicAuthentication("", settings.AZURE_DEVOPS_PAT)
        self.connection = Connection(base_url=settings.AZURE_DEVOPS_ORGANIZATION_URL, creds=credentials)
        self.wit_client: WorkItemTrackingClient = self.connection.clients.get_work_item_tracking_client()
        self.core_client: CoreClient = self.connection.clients.get_core_client()