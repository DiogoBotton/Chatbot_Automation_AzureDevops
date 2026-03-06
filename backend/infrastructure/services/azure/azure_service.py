from azure.devops.v7_0.work_item_tracking.models import JsonPatchOperation
from azure.devops.v7_0.work_item_tracking.models import Wiql
from azure.devops.v7_0.work.models import TeamContext
from constants.work_item import WorkItemProps, WorkItemTypes
from infrastructure.services.azure.azure_client import AzureDevOpsClient

class AzureDevOpsService:
    def __init__(self):
        self.azure_client = AzureDevOpsClient()
        
    def get_allowed_fields(self, project: str, work_item_type: str):
        wit_type = self.azure_client.wit_client.get_work_item_type(project, work_item_type)
        return {field.reference_name for field in wit_type.fields}
    
    def get_required_fields(self, project: str, work_item_type: str):
        wit_type = self.azure_client.wit_client.get_work_item_type(project, work_item_type)
        return [
            field.reference_name
            for field in wit_type.fields
            if field.always_required
        ]
    
    def get_default_area_path(self, project: str) -> str:
        areas = self.azure_client.wit_client.get_classification_node(
            project=project,
            structure_group="areas",
            depth=1
        )

        # normalmente o root já é o default
        return areas.path.lstrip("\\")
    
    def set_default_fields(self, project: str, fields: dict) -> dict:
        defaults = {
            WorkItemProps.AREA_PATH.value: project,
            WorkItemProps.ITERATION_PATH.value: project,
            WorkItemProps.STATE.value: "New",
            WorkItemProps.PRIORITY.value: 2
        }

        return {**defaults, **fields} # Os campos enviados sobrescrevem os defaults
    
    def list_projects(self):
        projects = self.azure_client.core_client.get_projects()

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

        # adiciona parent se houver
        if parent_id:
            patch_document.append(
                JsonPatchOperation(
                    op="add",
                    path="/relations/-",
                    value={
                        "rel": "System.LinkTypes.Hierarchy-Reverse",
                        "url": f"{self.azure_client.connection.base_url}/_apis/wit/workItems/{parent_id}"
                    }
                )
            )
            
        return patch_document
    
    def create_work_item(
        self,
        project: str,
        work_item_type: str,
        fields: dict,
        parent_id: int | None = None
    ):
        # Valida tipo
        if work_item_type not in [wt.value for wt in WorkItemTypes]:
            return {
                "error": "INVALID_TYPE", 
                "message": f"Tipo '{work_item_type}' não é permitido."
            }

        # Aplica defaults organizacionais
        fields = self.set_default_fields(project, fields)

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
        return self.azure_client.wit_client.create_work_item(
            document=patch_document,
            project=project,
            type=work_item_type
        )

    # ---------- LISTAGEM DE BACKLOG ----------

    def query_work_items(self, project: str, wiql_query: str):
        wiql = Wiql(query=wiql_query)

        team_context = TeamContext(project=project)

        result = self.azure_client.wit_client.query_by_wiql(
            wiql=wiql,
            team_context=team_context
        )

        ids = [item.id for item in result.work_items]

        if not ids:
            return []

        return self.azure_client.wit_client.get_work_items(ids, expand="relations")

    # TODO: Retornar tbm Assigned To
    def get_backlog_structure(self, project: str):
        """
        Retorna:
        - Epics com hierarquia completa
        - User Stories sem Epic
        - Tasks sem User Story
        """

        # 'Epic','User Story','Task', 'Feature', 'Bug', 'Reunion', 'Test', 'Theme', 'Study', 'Scope Creep', 'Test Case'
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