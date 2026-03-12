from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Alternativa para rodar localmente, caso não existir .env, considera variável de ambiente 
    model_config = SettingsConfigDict(
        env_file='.env', env_file_encoding='utf-8'
    )
    # Database
    DATABASE_URL: str
    
    # Azure DevOps
    AZURE_DEVOPS_PAT: str
    AZURE_DEVOPS_ORGANIZATION_URL: str
    
    # OpenAI (ChatGPT)
    OPENAI_API_KEY: str = ""
    
    # URL do serviço de ferramentas (FastAPI)
    API_TOOLS_URL: str = "http://localhost:5050"