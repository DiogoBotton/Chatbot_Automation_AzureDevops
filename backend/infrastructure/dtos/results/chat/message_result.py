from uuid import UUID

from infrastructure.dtos.results.base import BaseResult


class MessageResult(BaseResult):
    response: str
    conversation_id: UUID
