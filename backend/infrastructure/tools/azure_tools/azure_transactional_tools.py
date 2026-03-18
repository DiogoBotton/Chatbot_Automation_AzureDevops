from datetime import datetime

from langchain.tools import tool

from infrastructure.dtos.inputs.azure.azure_inputs import (
    AssignWorkItemItem,
    EpicItem,
    FeatureItem,
    UserStoryItem,
    TaskItem,
)
from infrastructure.dtos.results.work_items.work_item_batch_result import WorkItemBatchResult
from infrastructure.dtos.results.work_items.work_item_result import WorkItemResult
from infrastructure.enums.work_item import WorkItemProps, WorkItemTypes
from infrastructure.services.azure.azure_query_service import AzureQueryService
from infrastructure.services.azure.azure_transactional_service import AzureTransactionalService

_query_service = AzureQueryService()
_transactional_service = AzureTransactionalService()


# ─── Helpers ───────────────────────────────────────────────────────────────────

def _build_batch(results: list[WorkItemResult]) -> dict:
    created = sum(1 for r in results if r.error is None)
    return WorkItemBatchResult(total=len(results), created=created, results=results).model_dump()


def _validate_emails(items: list) -> list[str]:
    """Retorna lista de e-mails inválidos (não encontrados no Azure DevOps)."""
    invalid = []
    seen = set()
    for item in items:
        email = getattr(item, "assigned_to", None) or getattr(item, "assignee_email", None)
        if email and email not in seen:
            seen.add(email)
            if _query_service.resolve_user_by_email(email) is None:
                invalid.append(email)
    return invalid


# ─── Tools ────────────────────────────────────────────────────────────────────

@tool
def create_epic_tool(project_id: str, items: list[EpicItem]) -> dict:
    """
    Cria uma ou mais Epics no Azure DevOps. Epic é o item de mais alto nível — sem pai obrigatório.
    Retorna o ID de cada Epic criada; use-os como parent_id de Features ou User Stories filhas.
    assigned_to é opcional — preencha apenas se o usuário mencionar explicitamente um e-mail.
    """
    print(f"create_epic_tool chamado com project_id={project_id} e {len(items)} itens")
    invalid = _validate_emails(items)
    if invalid:
        return {"error": "USER_NOT_FOUND", "message": f"E-mails não encontrados no Azure DevOps: {invalid}"}
    results = []
    for item in items:
        try:
            fields = {
                WorkItemProps.TITLE.value: item.title,
                WorkItemProps.DESCRIPTION.value: item.description or "",
                WorkItemProps.START_DATE.value: datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
                WorkItemProps.FINISH_DATE.value: datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
                WorkItemProps.VALUE_AREA.value: "Business",
            }
            if item.assigned_to:
                fields[WorkItemProps.ASSIGNED_TO.value] = item.assigned_to
            results.append(_transactional_service.create_work_item(
                project_id=project_id,
                work_item_type=WorkItemTypes.EPIC.value,
                fields=fields,
                parent_id=item.parent_id,
            ))
        except Exception as e:
            results.append(WorkItemResult(error="UNEXPECTED_ERROR", message=str(e)))
    return _build_batch(results)


@tool
def create_feature_tool(project_id: str, items: list[FeatureItem]) -> dict:
    """
    Cria uma ou mais Features no Azure DevOps.
    parent_id DEVE ser o ID de uma Epic. Retorna o ID de cada Feature criada; use-os como parent_id de User Stories.
    assigned_to é opcional — preencha apenas se o usuário mencionar explicitamente um e-mail.
    """
    print(f"create_feature_tool chamado com project_id={project_id} e {len(items)} itens")
    invalid = _validate_emails(items)
    if invalid:
        return {"error": "USER_NOT_FOUND", "message": f"E-mails não encontrados no Azure DevOps: {invalid}"}
    results = []
    for item in items:
        try:
            fields = {
                WorkItemProps.TITLE.value: item.title,
                WorkItemProps.DESCRIPTION.value: item.description or "",
                WorkItemProps.VALUE_AREA.value: "Business",
                WorkItemProps.EFFORT.value: item.planned_work_hours,
            }
            if item.assigned_to:
                fields[WorkItemProps.ASSIGNED_TO.value] = item.assigned_to
            results.append(_transactional_service.create_work_item(
                project_id=project_id,
                work_item_type=WorkItemTypes.FEATURE.value,
                fields=fields,
                parent_id=item.parent_id,
            ))
        except Exception as e:
            results.append(WorkItemResult(error="UNEXPECTED_ERROR", message=str(e)))
    return _build_batch(results)


@tool
def create_user_story_tool(project_id: str, items: list[UserStoryItem]) -> dict:
    """
    Cria uma ou mais User Stories no Azure DevOps.
    parent_id DEVE ser o ID de uma Epic ou Feature. Retorna o ID de cada User Story criada; use-os como parent_id de Tasks ou outros filhos.
    assigned_to é opcional — preencha apenas se o usuário mencionar explicitamente um e-mail.
    """
    print(f"create_user_story_tool chamado com project_id={project_id} e {len(items)} itens")
    invalid = _validate_emails(items)
    if invalid:
        return {"error": "USER_NOT_FOUND", "message": f"E-mails não encontrados no Azure DevOps: {invalid}"}
    results = []
    for item in items:
        try:
            fields = {
                WorkItemProps.TITLE.value: item.title,
                WorkItemProps.ORIGINAL_ESTIMATE.value: item.original_estimate,
                WorkItemProps.DEVELOPMENT_AREA.value: "Back-End",
                WorkItemProps.BLOCKED.value: "No",
                WorkItemProps.VALUE_AREA.value: "Business",
            }
            if item.assigned_to:
                fields[WorkItemProps.ASSIGNED_TO.value] = item.assigned_to
            results.append(_transactional_service.create_work_item(
                project_id=project_id,
                work_item_type=WorkItemTypes.USER_STORY.value,
                fields=fields,
                parent_id=item.parent_id,
            ))
        except Exception as e:
            results.append(WorkItemResult(error="UNEXPECTED_ERROR", message=str(e)))
    return _build_batch(results)


@tool
def create_task_tool(project_id: str, items: list[TaskItem]) -> dict:
    """
    Cria uma ou mais Tasks no Azure DevOps.
    parent_id DEVE ser o ID de uma User Story. NUNCA use o ID de uma Epic ou Feature como pai de uma Task.
    assigned_to é opcional — preencha apenas se o usuário mencionar explicitamente um e-mail.
    """
    print(f"create_task_tool chamado com project_id={project_id} e {len(items)} itens")
    invalid = _validate_emails(items)
    if invalid:
        return {"error": "USER_NOT_FOUND", "message": f"E-mails não encontrados no Azure DevOps: {invalid}"}
    results = []
    for item in items:
        try:
            fields = {
                WorkItemProps.TITLE.value: item.title,
                WorkItemProps.ORIGINAL_ESTIMATE.value: item.original_estimate,
                WorkItemProps.ACTIVITY.value: "Development",
                WorkItemProps.DEVELOPMENT_AREA.value: "Back-End",
                WorkItemProps.BLOCKED.value: "No",
            }
            if item.assigned_to:
                fields[WorkItemProps.ASSIGNED_TO.value] = item.assigned_to
            results.append(_transactional_service.create_work_item(
                project_id=project_id,
                work_item_type=WorkItemTypes.TASK.value,
                fields=fields,
                parent_id=item.parent_id,
            ))
        except Exception as e:
            results.append(WorkItemResult(error="UNEXPECTED_ERROR", message=str(e)))
    return _build_batch(results)


@tool
def assign_work_item_tool(project_id: str, items: list[AssignWorkItemItem]) -> dict:
    """
    Atribui usuários a work items já existentes pelo e-mail.
    Valida todos os e-mails antes de executar qualquer alteração.
    Use quando o usuário pedir para vincular um e-mail a uma work item já criada.
    """
    print(f"assign_work_item_tool chamado com project_id={project_id} e {len(items)} itens")
    invalid = _validate_emails(items)
    if invalid:
        return {"error": "USER_NOT_FOUND", "message": f"E-mails não encontrados no Azure DevOps: {invalid}"}
    results = []
    for item in items:
        try:
            results.append(_transactional_service.assign_work_item(
                project_id=project_id,
                work_item_id=item.work_item_id,
                assignee_email=item.assignee_email,
            ))
        except Exception as e:
            results.append(WorkItemResult(error="UNEXPECTED_ERROR", message=str(e)))
    return _build_batch(results)
