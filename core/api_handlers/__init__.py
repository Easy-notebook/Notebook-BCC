"""
API Handlers Module

Provides specialized handlers for different API types.
Each handler encapsulates the logic for calling a specific API endpoint.

Architecture:
- BaseAPIHandler: Abstract base class with common functionality
- PlanningAPIHandler: Handles Planning API calls (/planning)
- GeneratingAPIHandler: Handles Generating API calls (/generating)
- ReflectingAPIHandler: Handles Reflecting API calls (/reflecting)

This separation of concerns allows State classes to delegate API calling
to these specialized handlers, keeping State logic focused on transitions.
"""

from .base_api_handler import BaseAPIHandler
from .planning_api_handler import PlanningAPIHandler
from .generating_api_handler import GeneratingAPIHandler
from .reflecting_api_handler import ReflectingAPIHandler

__all__ = [
    'BaseAPIHandler',
    'PlanningAPIHandler',
    'GeneratingAPIHandler',
    'ReflectingAPIHandler',
]
