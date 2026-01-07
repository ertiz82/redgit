"""
Action Registry for webhook callbacks.

This module provides a registry for actions that can be triggered from
notification button clicks and other interactive elements.

Actions are functions that execute in response to user interactions
with notification messages (e.g., clicking "Approve PR" button).
"""

from typing import Dict, Any, Callable, Optional, List
from dataclasses import dataclass
from enum import Enum


class ActionStatus(Enum):
    """Status of an action execution."""
    SUCCESS = "success"
    FAILED = "failed"
    PENDING = "pending"
    UNAUTHORIZED = "unauthorized"


@dataclass
class ActionResult:
    """Result of an action execution."""
    success: bool
    result: Any = None
    error: str = None
    message: str = None  # Response message to send back


@dataclass
class ActionContext:
    """Context information for action execution."""
    user_id: str = None
    message_id: str = None
    chat_id: str = None
    integration: str = None
    timestamp: str = None
    raw_data: Dict[str, Any] = None

    @classmethod
    def from_dict(cls, data: dict) -> "ActionContext":
        return cls(
            user_id=data.get("user_id"),
            message_id=data.get("message_id"),
            chat_id=data.get("chat_id"),
            integration=data.get("integration"),
            timestamp=data.get("timestamp"),
            raw_data=data
        )


class ActionRegistry:
    """
    Registry for actions that can be triggered from notifications.

    Actions are registered with an ID and handler function. When a callback
    is received (e.g., button click), the appropriate action is executed.

    Example:
        # Register an action
        @ActionRegistry.action("approve_pr", description="Approve a pull request")
        def approve_pr(data: dict, context: ActionContext) -> ActionResult:
            pr_number = data.get("pr")
            # ... approve the PR ...
            return ActionResult(success=True, message="PR approved!")

        # Execute an action
        result = ActionRegistry.execute("approve_pr", {"pr": 42}, context)
    """
    _actions: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def register(
        cls,
        action_id: str,
        handler: Callable[[dict, ActionContext], ActionResult],
        description: str = "",
        category: str = "general"
    ) -> None:
        """
        Register an action handler.

        Args:
            action_id: Unique action identifier (e.g., "approve_pr")
            handler: Function that handles the action
            description: Human-readable description
            category: Action category (pr, issue, pipeline, general)
        """
        cls._actions[action_id] = {
            "handler": handler,
            "description": description,
            "category": category
        }

    @classmethod
    def action(
        cls,
        action_id: str,
        description: str = "",
        category: str = "general"
    ) -> Callable:
        """
        Decorator to register an action handler.

        Example:
            @ActionRegistry.action("approve_pr", description="Approve PR")
            def approve_pr(data, context):
                return ActionResult(success=True)
        """
        def decorator(func: Callable) -> Callable:
            cls.register(action_id, func, description, category)
            return func
        return decorator

    @classmethod
    def unregister(cls, action_id: str) -> None:
        """Remove an action from the registry."""
        cls._actions.pop(action_id, None)

    @classmethod
    def execute(
        cls,
        action_id: str,
        data: dict,
        context: ActionContext
    ) -> ActionResult:
        """
        Execute a registered action.

        Args:
            action_id: Action identifier
            data: Action payload data
            context: Execution context

        Returns:
            ActionResult with success status and optional message
        """
        if action_id not in cls._actions:
            return ActionResult(
                success=False,
                error=f"Unknown action: {action_id}"
            )

        try:
            handler = cls._actions[action_id]["handler"]
            result = handler(data, context)
            if not isinstance(result, ActionResult):
                result = ActionResult(success=True, result=result)
            return result
        except Exception as e:
            return ActionResult(
                success=False,
                error=str(e)
            )

    @classmethod
    def get(cls, action_id: str) -> Optional[Dict[str, Any]]:
        """Get action definition."""
        return cls._actions.get(action_id)

    @classmethod
    def get_all(cls) -> Dict[str, Dict[str, Any]]:
        """Get all registered actions."""
        return cls._actions.copy()

    @classmethod
    def get_by_category(cls, category: str) -> Dict[str, Dict[str, Any]]:
        """Get actions filtered by category."""
        return {
            k: v for k, v in cls._actions.items()
            if v.get("category") == category
        }

    @classmethod
    def list_actions(cls) -> List[str]:
        """Get list of registered action IDs."""
        return list(cls._actions.keys())


# =============================================================================
# BUILT-IN ACTIONS
# =============================================================================

def _not_implemented(name: str):
    """Create a placeholder handler for not-yet-implemented actions."""
    def handler(data: dict, context: ActionContext) -> ActionResult:
        return ActionResult(
            success=False,
            error=f"Action '{name}' not implemented. Configure the appropriate integration."
        )
    return handler


# PR Actions
ActionRegistry.register(
    "approve_pr",
    _not_implemented("approve_pr"),
    description="Approve a pull request",
    category="pr"
)

ActionRegistry.register(
    "reject_pr",
    _not_implemented("reject_pr"),
    description="Request changes on a pull request",
    category="pr"
)

ActionRegistry.register(
    "merge_pr",
    _not_implemented("merge_pr"),
    description="Merge a pull request",
    category="pr"
)

# Pipeline Actions
ActionRegistry.register(
    "retry_pipeline",
    _not_implemented("retry_pipeline"),
    description="Retry a failed pipeline",
    category="pipeline"
)

ActionRegistry.register(
    "cancel_pipeline",
    _not_implemented("cancel_pipeline"),
    description="Cancel a running pipeline",
    category="pipeline"
)

# Issue Actions
ActionRegistry.register(
    "transition_issue",
    _not_implemented("transition_issue"),
    description="Change issue status",
    category="issue"
)

ActionRegistry.register(
    "close_issue",
    _not_implemented("close_issue"),
    description="Close an issue",
    category="issue"
)

ActionRegistry.register(
    "assign_user",
    _not_implemented("assign_user"),
    description="Assign a user to an issue",
    category="issue"
)

ActionRegistry.register(
    "add_comment",
    _not_implemented("add_comment"),
    description="Add a comment to an issue",
    category="issue"
)


# =============================================================================
# CALLBACK PARSER
# =============================================================================

def parse_callback_data(callback_str: str) -> tuple:
    """
    Parse callback data string into action_id and payload.

    Callback format: "action_id:json_payload"

    Args:
        callback_str: Callback data string

    Returns:
        Tuple of (action_id, payload_dict)
    """
    import json

    if ":" not in callback_str:
        return callback_str, {}

    parts = callback_str.split(":", 1)
    action_id = parts[0]

    try:
        payload = json.loads(parts[1]) if len(parts) > 1 else {}
    except json.JSONDecodeError:
        payload = {"raw": parts[1]}

    return action_id, payload


def format_callback_data(action_id: str, data: dict = None) -> str:
    """
    Format action and data into callback string.

    Args:
        action_id: Action identifier
        data: Payload data (will be JSON encoded)

    Returns:
        Callback string in format "action_id:json_payload"
    """
    import json

    if not data:
        return action_id

    return f"{action_id}:{json.dumps(data, separators=(',', ':'))}"
