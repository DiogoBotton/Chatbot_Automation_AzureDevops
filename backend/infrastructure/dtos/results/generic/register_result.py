from uuid import UUID

from infrastructure.dtos.results.base import BaseResult


class RegisterResult(BaseResult):
    id: UUID
