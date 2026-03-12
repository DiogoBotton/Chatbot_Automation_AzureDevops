from __future__ import annotations
from typing import Any
from pydantic import BaseModel
from infrastructure.dtos.work_items.work_item_base_result import WorkItemBaseResult


class BacklogWorkItemNode(BaseModel):
    id: int
    title: str
    type: str
    assigned_to: str | None = None
    url: str | None = None
    original_estimate: float | None = None
    children: list[Any] = []  # list[BacklogWorkItemNode] evitada: causa $ref circular no OpenAPI que quebra o fastapi_mcp


class BacklogStructure(BaseModel):
    epics: list[BacklogWorkItemNode]
    orphan_user_stories: list[BacklogWorkItemNode]
    orphan_tasks: list[BacklogWorkItemNode]


class BacklogStructureResult(WorkItemBaseResult):
    items: BacklogStructure | None = None
