from enum import Enum

class WorkItemProps(Enum):
    TITLE = "System.Title" # Título
    DESCRIPTION = "System.Description" # Descrição
    START_DATE = "Microsoft.VSTS.Scheduling.StartDate" # Data de início
    FINISH_DATE = "Microsoft.VSTS.Scheduling.FinishDate" # Data de término
    AREA_PATH = "System.AreaPath" # Caminho de área (Area Path)
    ITERATION_PATH = "System.IterationPath" # Iteração (Sprint)
    STATE = "System.State" # Estado da Work Item (Ex: New, Active, Closed)
    PRIORITY = "Microsoft.VSTS.Common.Priority" # Prioridade
    VALUE_AREA = "Microsoft.VSTS.Common.ValueArea" # Área de valor

    # Obrigatórios para User Story e Task
    ORIGINAL_ESTIMATE = "Microsoft.VSTS.Scheduling.OriginalEstimate" # Esforço original estimado (em horas)
    ACTIVITY = "Microsoft.VSTS.Common.Activity" # Atividade (Ex: Desenvolvimento, Teste, Análise)
    DEVELOPMENT_AREA = "Custom.DevelopmentArea" # Área de desenvolvimento (Ex: Frontend, Backend, Mobile)
    BLOCKED = "Microsoft.VSTS.CMMI.Blocked" # Indicador se a Work Item está bloqueada (True/False)
    
class WorkItemTypes(Enum):
    EPIC = "Epic"
    FEATURE = "Feature"
    USER_STORY = "User Story"
    TASK = "Task"
    BUG = "Bug"
    REUNION = "Reunion"
    TEST = "Test"
    THEME = "Theme"
    STUDY = "Study"
    SCOPE_CREEP = "Scope Creep"
    TEST_CASE = "Test Case"
    