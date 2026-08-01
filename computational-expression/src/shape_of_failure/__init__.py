"""Executable companion to the essay *The Shape of Failure*."""

from .domain import (
    Action,
    ModelDecision,
    PolicyDocument,
    RefundRequest,
    WorkflowResult,
)
from .workflow import DecisionWeaver

__all__ = [
    "Action",
    "DecisionWeaver",
    "ModelDecision",
    "PolicyDocument",
    "RefundRequest",
    "WorkflowResult",
]
