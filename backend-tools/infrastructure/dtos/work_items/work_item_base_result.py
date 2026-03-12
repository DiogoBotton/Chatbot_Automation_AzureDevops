from pydantic import BaseModel, ConfigDict

class WorkItemBaseResult(BaseModel):
    error: str | None = None
    message: str | None = None
    
    model_config = ConfigDict(from_attributes=True)