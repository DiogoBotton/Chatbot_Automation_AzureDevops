from datetime import datetime

from azure.devops.connection import Connection
from msrest.authentication import BasicAuthentication
from azure.devops.v7_0.work_item_tracking.models import JsonPatchOperation
from azure.devops.v7_0.work_item_tracking.work_item_tracking_client import WorkItemTrackingClient
from azure.devops.v7_0.core.core_client import CoreClient
from azure.devops.v7_0.work_item_tracking.models import Wiql
from azure.devops.v7_0.work.models import TeamContext
from settings import Settings
# TODO: Criar ferramentas para cada tipo de work item, pois para cada tipo é necessário enviar variáveis obrigatórias diferentes.
class AzureDevOpsService:
    def __init__(self):
        settings = Settings()
        credentials = BasicAuthentication("", settings.AZURE_DEVOPS_PAT)
        self.connection = Connection(base_url=settings.AZURE_DEVOPS_ORGANIZATION_URL, creds=credentials)
        self.wit_client: WorkItemTrackingClient = self.connection.clients.get_work_item_tracking_client()
        self.core_client: CoreClient = self.connection.clients.get_core_client()
        self.ALLOWED_WORK_ITEM_TYPES = {"Epic", "User Story", "Task"}
        
    def get_allowed_fields(self, project: str, work_item_type: str):
        wit_type = self.wit_client.get_work_item_type(project, work_item_type)
        return {field.reference_name for field in wit_type.fields}
    
    def get_required_fields(self, project: str, work_item_type: str):
        wit_type = self.wit_client.get_work_item_type(project, work_item_type)
        return [
            field.reference_name
            for field in wit_type.fields
            if field.always_required
        ]
    
    def get_default_area_path(self, project: str) -> str:
        areas = self.wit_client.get_classification_node(
            project=project,
            structure_group="areas",
            depth=1
        )

        # normalmente o root já é o default
        return areas.path.lstrip("\\")
        
    def set_default_fields(self, project: str, title: str) -> dict:
        defaults = {}
        
        defaults["System.Title"] = title
        defaults["Microsoft.VSTS.Scheduling.StartDate"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        defaults["Microsoft.VSTS.Scheduling.FinishDate"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")

        # 🔹 AreaPath
        defaults["System.AreaPath"] = project

        # 🔹 IterationPath
        defaults["System.IterationPath"] = project  # Exemplo simples, idealmente deveria verificar qual é a próxima Sprint ativa ou criar uma nova

        # 🔹 State (pode ser default do processo)
        defaults["System.State"] = "New"

        # 🔹 Priority
        defaults["Microsoft.VSTS.Common.Priority"] = 2

        # 🔹 ValueArea (Agile normalmente usa Business como default)
        defaults["Microsoft.VSTS.Common.ValueArea"] = "Business"

        return defaults
    
    def list_projects(self):
        projects = self.core_client.get_projects()

        return [
            {
                "id": project.id,
                "name": project.name,
                "state": project.state
            }
            for project in projects
        ]
    
    def create_patch_document(self, fields: dict, parent_id: int | None = None):
        patch_document = [
            JsonPatchOperation(
                op="add",
                path=f"/fields/{field}",
                value=value
            )
            for field, value in fields.items()
        ]

        # 7️⃣ adiciona parent se houver
        if parent_id:
            patch_document.append(
                JsonPatchOperation(
                    op="add",
                    path="/relations/-",
                    value={
                        "rel": "System.LinkTypes.Hierarchy-Reverse",
                        "url": f"{self.connection.base_url}/_apis/wit/workItems/{parent_id}"
                    }
                )
            )
            
        return patch_document
    
    # TODO: Mudar para Create Epic
    def create_work_item(
        self,
        project: str,
        work_item_type: str,
        title: str,
        description: str | None = None,
        parent_id: int | None = None
    ):
        # Valida tipo
        if work_item_type not in self.ALLOWED_WORK_ITEM_TYPES:
            return {"error": "INVALID_TYPE"}

        # Aplica defaults organizacionais
        fields = self.set_default_fields(project, title)
        if description:
            fields["System.Description"] = description

        # Valida campos permitidos
        allowed_fields = self.get_allowed_fields(project, work_item_type)
        invalid_fields = [f for f in fields if f not in allowed_fields]

        if invalid_fields:
            return {
                "error": "INVALID_FIELDS",
                "invalid_fields": invalid_fields
            }

        # Valida obrigatórios
        required_fields = self.get_required_fields(project, work_item_type)
        missing_fields = [f for f in required_fields if f not in fields]
        
        print("Campos faltantes:", missing_fields)  # DEBUG

        # if missing_fields:
        #     return {
        #         "error": "MISSING_REQUIRED_FIELDS",
        #         "missing_fields": missing_fields
        #     }

        # Cria patch document
        patch_document = self.create_patch_document(fields, parent_id)

        # Cria no Azure
        return self.wit_client.create_work_item(
            document=patch_document,
            project=project,
            type=work_item_type
        )

    # def create_epic(self, project: str, title: str, description: str = ""):
    #     document = [
    #         JsonPatchOperation(op="add", path="/fields/System.Title", value=title),
    #         JsonPatchOperation(op="add", path="/fields/System.Description", value=description),
    #         {
    #         "op": "add",
    #         "path": "/fields/Microsoft.VSTS.Scheduling.StartDate",
    #         "value": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    #     }
    #     ]

    #     return self.wit_client.create_work_item(
    #         document=document,
    #         project=project,
    #         type="Epic"
    #     )

    # def create_user_story(
    #     self,
    #     project: str,
    #     title: str,
    #     description: str = "",
    #     parent_epic_id: int | None = None
    # ):
    #     document = [
    #         JsonPatchOperation(op="add", path="/fields/System.Title", value=title),
    #         JsonPatchOperation(op="add", path="/fields/System.Description", value=description),
    #     ]

    #     if parent_epic_id:
    #         document.append(
    #             JsonPatchOperation(
    #                 op="add",
    #                 path="/relations/-",
    #                 value={
    #                     "rel": "System.LinkTypes.Hierarchy-Reverse",
    #                     "url": f"{self.connection.base_url}/_apis/wit/workItems/{parent_epic_id}"
    #                 }
    #             )
    #         )

    #     return self.wit_client.create_work_item(
    #         document=document,
    #         project=project,
    #         type="User Story"
    #     )

    # def create_task(
    #     self,
    #     project: str,
    #     title: str,
    #     parent_user_story_id: int | None = None
    # ):
    #     document = [
    #         JsonPatchOperation(op="add", path="/fields/System.Title", value=title),
    #     ]

    #     if parent_user_story_id:
    #         document.append(
    #             JsonPatchOperation(
    #                 op="add",
    #                 path="/relations/-",
    #                 value={
    #                     "rel": "System.LinkTypes.Hierarchy-Reverse",
    #                     "url": f"{self.connection.base_url}/_apis/wit/workItems/{parent_user_story_id}"
    #                 }
    #             )
    #         )

    #     return self.wit_client.create_work_item(
    #         document=document,
    #         project=project,
    #         type="Task"
    #     )

    # ---------- LISTAGEM DE BACKLOG ----------

    def query_work_items(self, project: str, wiql_query: str):
        wiql = Wiql(query=wiql_query)

        team_context = TeamContext(project=project)

        result = self.wit_client.query_by_wiql(
            wiql=wiql,
            team_context=team_context
        )

        ids = [item.id for item in result.work_items]

        if not ids:
            return []

        return self.wit_client.get_work_items(ids, expand="relations")

    def get_backlog_structure(self, project: str):
        """
        Retorna:
        - Epics com hierarquia completa
        - User Stories sem Epic
        - Tasks sem User Story
        """

        wiql = """
        SELECT [System.Id]
        FROM WorkItems
        WHERE 
            [System.TeamProject] = @project
            AND [System.WorkItemType] IN ('Epic','User Story','Task')
        ORDER BY [System.Id]
        """

        work_items = self.query_work_items(project, wiql)

        if not work_items:
            return {
                "epics": [],
                "orphan_user_stories": [],
                "orphan_tasks": []
            }

        # -------------------------
        # Indexação inicial
        # -------------------------

        items = {}
        epics = {}
        stories = {}
        tasks = {}

        for wi in work_items:
            item = {
                "id": wi.id,
                "title": wi.fields.get("System.Title"),
                "type": wi.fields.get("System.WorkItemType"),
                "children": []
            }

            items[wi.id] = item

            if item["type"] == "Epic":
                epics[wi.id] = item
            elif item["type"] == "User Story":
                stories[wi.id] = item
            elif item["type"] == "Task":
                tasks[wi.id] = item

        # -------------------------
        # Construção da hierarquia
        # -------------------------

        linked_stories = set()
        linked_tasks = set()

        for wi in work_items:
            if not wi.relations:
                continue

            for rel in wi.relations:
                if "Hierarchy-Reverse" in rel.rel:
                    parent_id = int(rel.url.split("/")[-1])

                    # Story → Epic
                    if wi.id in stories and parent_id in epics:
                        epics[parent_id]["children"].append(stories[wi.id])
                        linked_stories.add(wi.id)

                    # Task → Story
                    if wi.id in tasks and parent_id in stories:
                        stories[parent_id]["children"].append(tasks[wi.id])
                        linked_tasks.add(wi.id)

                    # Task direto no Epic (caso bagunçado)
                    if wi.id in tasks and parent_id in epics:
                        epics[parent_id]["children"].append(tasks[wi.id])
                        linked_tasks.add(wi.id)

        # -------------------------
        # Detectar órfãos
        # -------------------------

        orphan_user_stories = [
            stories[sid]
            for sid in stories
            if sid not in linked_stories
        ]

        orphan_tasks = [
            tasks[tid]
            for tid in tasks
            if tid not in linked_tasks
        ]

        return {
            "epics": list(epics.values()),
            "orphan_user_stories": orphan_user_stories,
            "orphan_tasks": orphan_tasks
        }