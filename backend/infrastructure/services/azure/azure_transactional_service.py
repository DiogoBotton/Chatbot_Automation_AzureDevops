from azure.devops.v7_0.work_item_tracking.models import JsonPatchOperation

from infrastructure.dtos.results.work_items.work_item_result import WorkItemResult
from infrastructure.enums.work_item import WorkItemProps, WorkItemTypes
from infrastructure.services.azure.azure_client import AzureDevOpsClient


class AzureTransactionalService:
    def __init__(self):
        self.azure_client = AzureDevOpsClient()

    # ─── Helpers internos ─────────────────────────────────────────────────────

    def _web_url(self, project: str, work_item_id: int) -> str:
        base = self.azure_client.connection.base_url.rstrip("/")
        return f"{base}/{project}/_workitems/edit/{work_item_id}"

    def _get_project_name(self, project_id: str) -> str:
        """Resolve o nome do projeto a partir do seu ID. Levanta ValueError se não encontrado."""
        project = self.azure_client.core_client.get_project(project_id)
        if not project:
            raise ValueError(f"Projeto com ID '{project_id}' não encontrado.")
        return project.name

    def get_allowed_fields(self, project: str, work_item_type: str) -> set[str]:
        wit_type = self.azure_client.wit_client.get_work_item_type(project, work_item_type)
        return {field.reference_name for field in wit_type.fields}

    def get_required_fields(self, project: str, work_item_type: str) -> list[str]:
        wit_type = self.azure_client.wit_client.get_work_item_type(project, work_item_type)
        return [
            field.reference_name
            for field in wit_type.fields
            if field.always_required
        ]

    def set_default_fields(self, project_name: str, fields: dict) -> dict:
        defaults = {
            WorkItemProps.AREA_PATH.value: project_name,
            WorkItemProps.ITERATION_PATH.value: project_name,
            WorkItemProps.STATE.value: "New",
            WorkItemProps.PRIORITY.value: 2,
        }
        return {**defaults, **fields}

    def create_patch_document(self, fields: dict, parent_id: int | None = None) -> list:
        patch_document = [
            JsonPatchOperation(
                op="add",
                path=f"/fields/{field}",
                value=value,
            )
            for field, value in fields.items()
        ]
        if parent_id:
            patch_document.append(
                JsonPatchOperation(
                    op="add",
                    path="/relations/-",
                    value={
                        "rel": "System.LinkTypes.Hierarchy-Reverse",
                        "url": f"{self.azure_client.connection.base_url}/_apis/wit/workItems/{parent_id}",
                    },
                )
            )
        return patch_document

    # ─── Work Items ───────────────────────────────────────────────────────────

    def create_work_item(
        self,
        project_id: str,
        work_item_type: str,
        fields: dict,
        parent_id: int | None = None,
    ) -> WorkItemResult:
        """
        Cria uma work item no Azure DevOps.

        Resolve automaticamente o nome do projeto a partir do project_id,
        valida campos e retorna o resultado tipado.
        """
        if work_item_type not in [wt.value for wt in WorkItemTypes]:
            return WorkItemResult(error="INVALID_TYPE", message=f"Tipo '{work_item_type}' não é permitido.")

        try:
            project_name = self._get_project_name(project_id)
        except ValueError as e:
            return WorkItemResult(error="PROJECT_NOT_FOUND", message=str(e))

        fields = self.set_default_fields(project_name, fields)

        allowed_fields = self.get_allowed_fields(project_id, work_item_type)
        invalid_fields = [f for f in fields if f not in allowed_fields]
        if invalid_fields:
            return WorkItemResult(error="INVALID_FIELDS", message=str(invalid_fields))

        patch_document = self.create_patch_document(fields, parent_id)

        wi = self.azure_client.wit_client.create_work_item(
            document=patch_document,
            project=project_id,
            type=work_item_type,
        )

        assigned_to = wi.fields.get(WorkItemProps.ASSIGNED_TO.value)
        if isinstance(assigned_to, dict):
            assigned_to = assigned_to.get("displayName")

        return WorkItemResult(response={
            "id": wi.id,
            "title": wi.fields.get(WorkItemProps.TITLE.value),
            "type": wi.fields.get(WorkItemProps.WORK_ITEM_TYPE.value),
            "assigned_to": assigned_to,
            "url": self._web_url(project_id, wi.id),
            "original_estimate": wi.fields.get(WorkItemProps.ORIGINAL_ESTIMATE.value),
        })

    def assign_work_item(self, project_id: str, work_item_id: int, assignee_email: str) -> WorkItemResult:
        """Atribui um usuário a uma work item existente pelo e-mail."""
        patch = [
            JsonPatchOperation(
                op="add",
                path=f"/fields/{WorkItemProps.ASSIGNED_TO.value}",
                value=assignee_email,
            )
        ]
        wi = self.azure_client.wit_client.update_work_item(document=patch, id=work_item_id)
        assigned_to = wi.fields.get(WorkItemProps.ASSIGNED_TO.value)
        if isinstance(assigned_to, dict):
            assigned_to = assigned_to.get("displayName")
        return WorkItemResult(response={
            "id": wi.id,
            "title": wi.fields.get(WorkItemProps.TITLE.value),
            "type": wi.fields.get(WorkItemProps.WORK_ITEM_TYPE.value),
            "assigned_to": assigned_to,
            "url": self._web_url(project_id, wi.id),
            "original_estimate": wi.fields.get(WorkItemProps.ORIGINAL_ESTIMATE.value),
        })
