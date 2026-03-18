from pydantic import BaseModel, Field


class EpicItem(BaseModel):
    title: str = Field(..., description="Título da Epic.")
    description: str | None = Field(None, description="Descrição opcional da Epic.")
    assigned_to: str | None = Field(
        None,
        description="E-mail do responsável. OPCIONAL — preencha SOMENTE se o usuário mencionar explicitamente um e-mail.",
    )
    parent_id: int | None = Field(None, description="ID do pai (não obrigatório para Epics).")


class FeatureItem(BaseModel):
    title: str = Field(..., description="Título da Feature.")
    description: str | None = Field(None, description="Descrição opcional da Feature.")
    planned_work_hours: float = Field(
        0,
        description="Horas de trabalho previstas (Effort). Padrão 0; não pergunte ao usuário se não informado.",
    )
    assigned_to: str | None = Field(
        None,
        description="E-mail do responsável. OPCIONAL — preencha SOMENTE se o usuário mencionar explicitamente um e-mail.",
    )
    parent_id: int | None = Field(
        None,
        description="ID da Epic pai. Feature DEVE ser filha de uma Epic.",
    )


class UserStoryItem(BaseModel):
    title: str = Field(..., description="Título da User Story.")
    original_estimate: float = Field(
        0,
        description="Estimativa em horas. Padrão 0; não pergunte ao usuário se não informado.",
    )
    assigned_to: str | None = Field(
        None,
        description="E-mail do responsável. OPCIONAL — preencha SOMENTE se o usuário mencionar explicitamente um e-mail.",
    )
    parent_id: int | None = Field(
        None,
        description="ID da Epic ou Feature pai. User Story DEVE ser filha de uma Epic ou Feature.",
    )


class TaskItem(BaseModel):
    title: str = Field(..., description="Título da Task.")
    original_estimate: float = Field(
        0,
        description="Estimativa em horas. Padrão 0; não pergunte ao usuário se não informado.",
    )
    assigned_to: str | None = Field(
        None,
        description="E-mail do responsável. OPCIONAL — preencha SOMENTE se o usuário mencionar explicitamente um e-mail.",
    )
    parent_id: int | None = Field(
        None,
        description="ID da User Story pai. Task DEVE ser filha de uma User Story. NUNCA use o ID de uma Epic ou Feature.",
    )


class AssignWorkItemItem(BaseModel):
    work_item_id: int = Field(..., description="ID numérico da work item existente a ser atribuída.")
    assignee_email: str = Field(..., description="E-mail do usuário a ser vinculado à work item.")
