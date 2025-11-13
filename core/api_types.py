"""
API Types Definition
Defines the types of API calls used in the workflow system.
"""

from enum import Enum


class APIResponseType(str, Enum):
    """
    Types of API responses in the system.

    These correspond to the three main API endpoints:
    - Planning API: Returns stages/steps/behaviors
    - Generating API: Returns actions to execute
    - Reflecting API: Returns reflection/completion analysis
    """

    PLANNING = 'planning'
    """Planning API - Returns stages, steps, or behaviors"""

    GENERATING = 'generating'
    """Generating API - Returns actions to execute"""

    COMPLETE = 'reflecting'
    """Reflecting API - Returns reflection on completion"""

    FINISH = 'finish'
    """Finish - No more API calls needed"""

class PlanningResponseType(str, Enum):
    """
    Sub-types of planning API responses.
    """

    STAGES = 'stages'
    """Planning response containing stages list (START_WORKFLOW)"""

    STEPS = 'steps'
    """Planning response containing steps list (START_STEP)"""

    BEHAVIOR = 'behavior'
    """Planning response containing behavior definition (START_BEHAVIOR)"""


class GeneratingResponseType(str, Enum):
    """
    Sub-types of generating API responses.
    """

    ACTIONS = 'actions'
    """Generating response containing actions list"""


class ReflectingResponseType(str, Enum):
    """
    Sub-types of reflecting API responses.
    """

    REFLECTION = 'reflection'
    """Reflecting response with completion analysis"""
