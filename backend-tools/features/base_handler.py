from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import Generic, TypeVar

# Tipos genéricos para Request e Response
TRequest = TypeVar("TRequest", bound=BaseModel)
TResponse = TypeVar("TResponse")

class BaseHandler(ABC, Generic[TRequest, TResponse]):
    def __init__(self):
        pass

    @abstractmethod
    def execute(self, request: TRequest) -> TResponse:
        """Método principal que deve ser implementado pelas subclasses"""
        raise NotImplementedError("Handler não implementada.")