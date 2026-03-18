# Backward-compatibility shim — use AzureQueryService or AzureTransactionalService directly.
from infrastructure.services.azure.azure_query_service import AzureQueryService
from infrastructure.services.azure.azure_transactional_service import AzureTransactionalService


class AzureDevOpsService(AzureQueryService, AzureTransactionalService):
    pass
