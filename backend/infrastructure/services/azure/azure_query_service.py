from azure.devops.v7_0.work_item_tracking.models import Wiql
from azure.devops.v7_0.work.models import TeamContext

from infrastructure.dtos.results.work_items.backlog_structure_result import (
    BacklogStructure,
    BacklogStructureResult,
)
from infrastructure.enums.work_item import WorkItemProps
from infrastructure.services.azure.azure_client import AzureDevOpsClient


class AzureQueryService:
    def __init__(self):
        self.azure_client = AzureDevOpsClient()

    # ─── Helpers internos ─────────────────────────────────────────────────────

    def _web_url(self, project: str, work_item_id: int) -> str:
        base = self.azure_client.connection.base_url.rstrip("/")
        return f"{base}/{project}/_workitems/edit/{work_item_id}"

    # ─── Projetos ─────────────────────────────────────────────────────────────

    def list_projects(self) -> list[dict]:
        projects = self.azure_client.core_client.get_projects()
        return [
            {"id": project.id, "name": project.name, "state": project.state}
            for project in projects
        ]

    def get_project_by_id(self, project_id: str) -> str:
        """Retorna o nome do projeto dado seu ID. Levanta ValueError se não encontrado."""
        project = self.azure_client.core_client.get_project(project_id)
        if not project:
            raise ValueError(f"Projeto com ID '{project_id}' não encontrado.")
        return project.name

    # ─── Consultas de Work Items ───────────────────────────────────────────────

    def query_work_items(self, project: str, wiql_query: str):
        wiql = Wiql(query=wiql_query)
        team_context = TeamContext(project=project)
        result = self.azure_client.wit_client.query_by_wiql(
            wiql=wiql,
            team_context=team_context,
        )
        ids = [item.id for item in result.work_items]
        if not ids:
            return []
        return self.azure_client.wit_client.get_work_items(ids, expand="relations")

    def get_backlog_structure(self, project_id: str) -> BacklogStructureResult:
        """Retorna a estrutura hierárquica completa do backlog (Epic → User Story → Task)."""
        wiql = """
        SELECT [System.Id]
        FROM WorkItems
        WHERE
            [System.TeamProject] = @project
            AND [System.WorkItemType] IN ('Epic','User Story','Task')
        ORDER BY [System.Id]
        """
        work_items = self.query_work_items(project_id, wiql)
        if not work_items:
            return BacklogStructureResult(items=BacklogStructure())

        items = {}
        epics = {}
        stories = {}
        tasks = {}

        for wi in work_items:
            assigned_to = wi.fields.get(WorkItemProps.ASSIGNED_TO.value)
            if isinstance(assigned_to, dict):
                assigned_to = assigned_to.get("displayName")

            item = {
                "id": wi.id,
                "title": wi.fields.get(WorkItemProps.TITLE.value),
                "type": wi.fields.get(WorkItemProps.WORK_ITEM_TYPE.value),
                "assigned_to": assigned_to,
                "url": self._web_url(project_id, wi.id),
                "original_estimate": wi.fields.get(WorkItemProps.ORIGINAL_ESTIMATE.value),
                "children": [],
            }
            items[wi.id] = item
            if item["type"] == "Epic":
                epics[wi.id] = item
            elif item["type"] == "User Story":
                stories[wi.id] = item
            elif item["type"] == "Task":
                tasks[wi.id] = item

        linked_stories = set()
        linked_tasks = set()

        for wi in work_items:
            if not wi.relations:
                continue
            for rel in wi.relations:
                if "Hierarchy-Reverse" in rel.rel:
                    parent_id = int(rel.url.split("/")[-1])
                    if wi.id in stories and parent_id in epics:
                        epics[parent_id]["children"].append(stories[wi.id])
                        linked_stories.add(wi.id)
                    if wi.id in tasks and parent_id in stories:
                        stories[parent_id]["children"].append(tasks[wi.id])
                        linked_tasks.add(wi.id)
                    if wi.id in tasks and parent_id in epics:
                        epics[parent_id]["children"].append(tasks[wi.id])
                        linked_tasks.add(wi.id)

        orphan_user_stories = [stories[sid] for sid in stories if sid not in linked_stories]
        orphan_tasks = [tasks[tid] for tid in tasks if tid not in linked_tasks]

        return BacklogStructureResult(
            items=BacklogStructure(
                epics=list(epics.values()),
                orphan_user_stories=orphan_user_stories,
                orphan_tasks=orphan_tasks,
            )
        )

    # ─── Usuários ──────────────────────────────────────────────────────────────

    def resolve_user_by_email(self, email: str) -> dict | None:
        """Valida e resolve um usuário pelo e-mail. Retorna None se não encontrado."""
        identities = self.azure_client.identity_client.read_identities(
            search_filter="MailAddress",
            filter_value=email,
        )
        if not identities:
            return None
        identity = identities[0]
        return {
            "display_name": identity.provider_display_name,
            "email": email,
        }

    def get_my_work_items(self, project_id: str) -> list[dict]:
        """Retorna todas as work items atribuídas ao usuário autenticado pelo PAT (@Me)."""
        wiql = """
        SELECT [System.Id]
        FROM WorkItems
        WHERE
            [System.TeamProject] = @project
            AND [System.AssignedTo] = @Me
        ORDER BY [System.WorkItemType], [System.Id]
        """
        work_items = self.query_work_items(project_id, wiql)
        result = []
        for wi in work_items:
            assigned_to = wi.fields.get(WorkItemProps.ASSIGNED_TO.value)
            if isinstance(assigned_to, dict):
                assigned_to = assigned_to.get("displayName")
            result.append({
                "id": wi.id,
                "title": wi.fields.get(WorkItemProps.TITLE.value),
                "type": wi.fields.get(WorkItemProps.WORK_ITEM_TYPE.value),
                "state": wi.fields.get(WorkItemProps.STATE.value),
                "assigned_to": assigned_to,
                "url": self._web_url(project_id, wi.id),
            })
        return result
