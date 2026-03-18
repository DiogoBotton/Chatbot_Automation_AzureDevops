from enum import Enum


class WorkItemProps(Enum):
    TITLE = "System.Title"
    DESCRIPTION = "System.Description"
    START_DATE = "Microsoft.VSTS.Scheduling.StartDate"
    FINISH_DATE = "Microsoft.VSTS.Scheduling.FinishDate"
    AREA_PATH = "System.AreaPath"
    ITERATION_PATH = "System.IterationPath"
    STATE = "System.State"
    PRIORITY = "Microsoft.VSTS.Common.Priority"
    VALUE_AREA = "Microsoft.VSTS.Common.ValueArea"
    ORIGINAL_ESTIMATE = "Microsoft.VSTS.Scheduling.OriginalEstimate"
    EFFORT = "Microsoft.VSTS.Scheduling.Effort"  # "Horas de Trabalho Prevista" — usado em Features
    ACTIVITY = "Microsoft.VSTS.Common.Activity"
    DEVELOPMENT_AREA = "Custom.DevelopmentArea"
    BLOCKED = "Microsoft.VSTS.CMMI.Blocked"
    ASSIGNED_TO = "System.AssignedTo"
    WORK_ITEM_TYPE = "System.WorkItemType"


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
