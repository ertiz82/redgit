"""
Centralized notification utilities for RedGit.

This module provides a unified interface for sending notifications,
eliminating duplicate notification code across command modules.

Features:
- EventRegistry: Extensible event type registration for integrations
- NotificationService: Centralized notification handling
- Interactive message support (buttons, polls)
"""

from typing import List, Optional, Dict, Any, Callable
from dataclasses import dataclass, field
from ..core.config import ConfigManager
from ..integrations.registry import get_notification


# =============================================================================
# EVENT REGISTRY
# =============================================================================

@dataclass
class EventConfig:
    """Configuration for a notification event type."""
    category: str = "general"
    priority: str = "normal"  # low, normal, high, urgent
    description: str = ""
    default_enabled: bool = True


class EventRegistry:
    """
    Registry for notification event types.

    Integrations can register their own event types with custom formatters.
    This allows task management, CI/CD, and other integrations to define
    custom notifications without modifying core code.

    Example:
        # Register a custom event
        EventRegistry.register(
            "sonar_analysis",
            category="quality",
            priority="normal",
            formatter=lambda project, bugs: f"📊 {project}: {bugs} bugs found"
        )

        # Format a message
        message = EventRegistry.format("sonar_analysis", project="MyApp", bugs=5)
    """
    _events: Dict[str, EventConfig] = {}
    _formatters: Dict[str, Callable] = {}

    @classmethod
    def register(
        cls,
        event_type: str,
        category: str = "general",
        priority: str = "normal",
        description: str = "",
        default_enabled: bool = True,
        formatter: Callable = None
    ) -> None:
        """
        Register a new event type.

        Args:
            event_type: Unique event identifier (e.g., "pr_created", "ci_failure")
            category: Event category (git, task, ci, quality, general)
            priority: Event priority (low, normal, high, urgent)
            description: Human-readable description
            default_enabled: Whether event is enabled by default
            formatter: Optional callable to format event messages
        """
        cls._events[event_type] = EventConfig(
            category=category,
            priority=priority,
            description=description,
            default_enabled=default_enabled
        )
        if formatter:
            cls._formatters[event_type] = formatter

    @classmethod
    def unregister(cls, event_type: str) -> None:
        """Remove an event type from the registry."""
        cls._events.pop(event_type, None)
        cls._formatters.pop(event_type, None)

    @classmethod
    def get(cls, event_type: str) -> Optional[EventConfig]:
        """Get event configuration."""
        return cls._events.get(event_type)

    @classmethod
    def get_all(cls) -> Dict[str, EventConfig]:
        """Get all registered events."""
        return cls._events.copy()

    @classmethod
    def get_by_category(cls, category: str) -> Dict[str, EventConfig]:
        """Get events filtered by category."""
        return {
            k: v for k, v in cls._events.items()
            if v.category == category
        }

    @classmethod
    def format(cls, event_type: str, **kwargs) -> str:
        """
        Format an event message using registered formatter.

        Args:
            event_type: Event type identifier
            **kwargs: Arguments to pass to formatter

        Returns:
            Formatted message string
        """
        if event_type in cls._formatters:
            try:
                return cls._formatters[event_type](**kwargs)
            except Exception:
                pass
        return cls._default_format(event_type, **kwargs)

    @classmethod
    def _default_format(cls, event_type: str, **kwargs) -> str:
        """Default message formatter."""
        parts = [f"[{event_type.upper()}]"]
        for key, value in kwargs.items():
            if value is not None:
                parts.append(f"{key}: {value}")
        return " | ".join(parts)

    @classmethod
    def has_formatter(cls, event_type: str) -> bool:
        """Check if event has a custom formatter."""
        return event_type in cls._formatters


# Register default events
EventRegistry.register("commit", category="git", priority="normal", description="Git commit created")
EventRegistry.register("push", category="git", priority="normal", description="Changes pushed to remote")
EventRegistry.register("pr_created", category="git", priority="high", description="Pull request created")
EventRegistry.register("pr_merged", category="git", priority="normal", description="Pull request merged")
EventRegistry.register("issue_created", category="task", priority="normal", description="Issue created")
EventRegistry.register("issue_completed", category="task", priority="normal", description="Issue completed")
EventRegistry.register("ci_success", category="ci", priority="normal", description="CI pipeline succeeded")
EventRegistry.register("ci_failure", category="ci", priority="high", description="CI pipeline failed")
EventRegistry.register("quality_failed", category="quality", priority="high", description="Quality check failed")
EventRegistry.register("session_complete", category="general", priority="normal", description="Work session completed")
EventRegistry.register("poker_session_started", category="poker", priority="high", description="Planning Poker session started")
EventRegistry.register("poker_session_ended", category="poker", priority="normal", description="Planning Poker session ended")
EventRegistry.register("poker_tasks_distributed", category="poker", priority="normal", description="Planning Poker tasks distributed")
EventRegistry.register("sprint_created", category="sprint", priority="normal", description="Sprint created from poker session")


class NotificationService:
    """
    Centralized service for handling notifications.

    This class provides a clean interface for sending various types
    of notifications while handling configuration checks and error handling.
    """

    def __init__(self, config: dict):
        """
        Initialize the notification service.

        Args:
            config: The application configuration dictionary
        """
        self.config = config
        self._config_manager = ConfigManager()
        self._notification = None
        self._initialized = False

    @property
    def notification(self):
        """Lazy-load the notification integration."""
        if not self._initialized:
            self._notification = get_notification(self.config)
            self._initialized = True
        return self._notification

    def is_enabled(self, event: str) -> bool:
        """
        Check if notification is enabled for a specific event.

        Args:
            event: Event name (e.g., 'push', 'pr_created', 'ci_success')

        Returns:
            True if notifications are enabled for this event
        """
        return self._config_manager.is_notification_enabled(event)

    def send(self, event: str, message: str) -> bool:
        """
        Send a notification if enabled.

        Args:
            event: Event name for configuration check
            message: Message to send

        Returns:
            True if notification was sent successfully
        """
        if not self.is_enabled(event):
            return False

        if not self.notification or not self.notification.enabled:
            return False

        try:
            self.notification.send_message(message)
            return True
        except Exception:
            # Notification failure shouldn't break the flow
            return False

    # =========================================================================
    # CONVENIENCE METHODS
    # =========================================================================

    def send_push(self, branch: str, issues: Optional[List[str]] = None) -> bool:
        """
        Send notification about successful push.

        Args:
            branch: Branch name that was pushed
            issues: Optional list of related issue keys
        """
        message = f"Pushed `{branch}` to remote"
        if issues:
            message += f"\nIssues: {', '.join(issues)}"
        return self.send("push", message)

    def send_pr_created(
        self,
        branch: str,
        pr_url: str,
        issue_key: Optional[str] = None
    ) -> bool:
        """
        Send notification about PR creation.

        Args:
            branch: Branch name for the PR
            pr_url: URL of the created PR
            issue_key: Optional related issue key
        """
        message = f"PR created for `{branch}`"
        if issue_key:
            message += f" ({issue_key})"
        message += f"\n{pr_url}"
        return self.send("pr_created", message)

    def send_ci_result(
        self,
        branch: str,
        status: str,
        url: Optional[str] = None
    ) -> bool:
        """
        Send notification about CI/CD pipeline result.

        Args:
            branch: Branch name
            status: Pipeline status ('success' or 'failure')
            url: Optional pipeline URL
        """
        event = "ci_success" if status == "success" else "ci_failure"

        if status == "success":
            message = f"Pipeline for `{branch}` completed successfully"
        else:
            message = f"Pipeline for `{branch}` failed"

        if url:
            message += f"\n{url}"

        return self.send(event, message)

    def send_issue_completed(self, issues: List[str]) -> bool:
        """
        Send notification about issues marked as done.

        Args:
            issues: List of issue keys that were completed
        """
        if not issues:
            return False

        if len(issues) == 1:
            message = f"Issue {issues[0]} marked as Done"
        else:
            message = f"{len(issues)} issues marked as Done: {', '.join(issues)}"

        return self.send("issue_completed", message)

    def send_issue_created(
        self,
        issue_key: str,
        summary: Optional[str] = None
    ) -> bool:
        """
        Send notification about issue creation.

        Args:
            issue_key: The created issue key
            summary: Optional issue summary
        """
        message = f"Issue created: {issue_key}"
        if summary:
            message += f"\n{summary[:100]}"

        return self.send("issue_created", message)

    def send_commit(
        self,
        branch: str,
        issue_key: Optional[str] = None,
        files_count: int = 0
    ) -> bool:
        """
        Send notification about commit creation.

        Args:
            branch: Branch name where commit was made
            issue_key: Optional related issue key
            files_count: Number of files in commit
        """
        message = f"Committed to `{branch}`"
        if issue_key:
            message += f" ({issue_key})"
        if files_count:
            message += f"\n{files_count} files"

        return self.send("commit", message)

    def send_session_complete(
        self,
        branches_count: int,
        issues_count: int
    ) -> bool:
        """
        Send notification about session completion.

        Args:
            branches_count: Number of branches in session
            issues_count: Number of issues in session
        """
        message = f"Session completed: {branches_count} branches, {issues_count} issues"
        return self.send("session_complete", message)

    def send_quality_failed(self, score: int, threshold: int) -> bool:
        """
        Send notification about quality check failure.

        Args:
            score: Actual quality score
            threshold: Required threshold score
        """
        message = f"Quality check failed: {score}% (threshold: {threshold}%)"
        return self.send("quality_failed", message)

    def send_poker_session_started(
        self,
        leader: str,
        session_id: str,
        project: Optional[str] = None,
        tasks_count: int = 0,
        participants: Optional[List[str]] = None
    ) -> bool:
        """
        Send notification about Planning Poker session start.

        Args:
            leader: Name of the session leader
            session_id: Session ID for joining
            project: Project key (e.g., Jira project)
            tasks_count: Number of tasks to estimate
            participants: Expected participants list
        """
        lines = ["🃏 <b>Planning Poker Session Started</b>"]
        lines.append(f"👤 Leader: {leader}")

        if project:
            lines.append(f"📁 Project: {project}")

        if tasks_count:
            lines.append(f"📋 Tasks: {tasks_count}")

        if participants:
            lines.append(f"👥 Expected: {', '.join(participants)}")

        lines.append("")
        lines.append(f"🆔 Session: <code>{session_id}</code>")
        lines.append(f"💻 Join: <code>rg poker join {session_id}</code>")

        message = "\n".join(lines)
        return self.send("poker_session_started", message)

    def send_poker_session_ended(
        self,
        leader: str,
        tasks_estimated: int = 0,
        total_points: int = 0,
        participants: Optional[List[str]] = None
    ) -> bool:
        """
        Send notification about Planning Poker session end.

        Args:
            leader: Name of the session leader
            tasks_estimated: Number of tasks estimated
            total_points: Total story points assigned
            participants: List of participants who joined
        """
        lines = ["🏁 *Planning Poker Session Ended*"]
        lines.append(f"👤 Leader: {leader}")

        if tasks_estimated:
            lines.append(f"✅ Tasks Estimated: {tasks_estimated}")

        if total_points:
            lines.append(f"📊 Total Points: {total_points}")

        if participants:
            lines.append(f"👥 Participants: {', '.join(participants)}")

        message = "\n".join(lines)
        return self.send("poker_session_ended", message)

    def send_poker_tasks_distributed(
        self,
        leader: str,
        assignments: List[Dict[str, Any]],
        assigned_in_task_mgmt: bool = False
    ) -> bool:
        """
        Send notification about task distribution completion.

        Args:
            leader: Session leader name
            assignments: List of task assignments
            assigned_in_task_mgmt: Whether tasks were assigned in task management
        """
        lines = ["📋 <b>Tasks Distributed</b>"]
        lines.append(f"👤 Leader: {leader}")

        # Filter assigned tasks
        assigned = [a for a in assignments if not a.get("skipped") and a.get("assigned_to")]
        if assigned:
            lines.append("\n📌 Assignments:")
            for a in assigned[:10]:  # Limit to 10
                points = a.get('final_points', '?')
                lines.append(f"  • {a['task_key']}: {a['assigned_to']} ({points} pts)")
            if len(assigned) > 10:
                lines.append(f"  ... and {len(assigned) - 10} more")

        if assigned_in_task_mgmt:
            lines.append("\n✅ Tasks assigned in task management")

        message = "\n".join(lines)
        return self.send("poker_tasks_distributed", message)

    def send_sprint_created(
        self,
        leader: str,
        sprint_name: str,
        tasks_count: int = 0,
        total_points: int = 0,
        started: bool = False
    ) -> bool:
        """
        Send notification about sprint creation.

        Args:
            leader: Session leader name
            sprint_name: Name of the created sprint
            tasks_count: Number of tasks in the sprint
            total_points: Total story points
            started: Whether the sprint was started
        """
        lines = ["🏃 <b>Sprint Created</b>"]
        lines.append(f"👤 Leader: {leader}")
        lines.append(f"📋 Sprint: {sprint_name}")

        if tasks_count:
            lines.append(f"📊 Tasks: {tasks_count}")

        if total_points:
            lines.append(f"🎯 Total Points: {total_points}")

        if started:
            lines.append("\n✅ Sprint started!")

        message = "\n".join(lines)
        return self.send("sprint_created", message)

    # =========================================================================
    # INTERACTIVE METHODS (v2)
    # =========================================================================

    def send_interactive(
        self,
        event: str,
        message: str,
        buttons: List[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Send an interactive message with buttons.

        Args:
            event: Event name for configuration check
            message: Message to send
            buttons: List of button definitions:
                - {"text": "Label", "action": "action_id", "data": {...}}
                - {"text": "Label", "url": "https://..."}

        Returns:
            Message ID if successful, None otherwise
        """
        if not self.is_enabled(event):
            return None

        if not self.notification or not self.notification.enabled:
            return None

        # Check if notification integration supports interactive messages
        if not hasattr(self.notification, 'send_interactive'):
            # Fall back to regular message
            self.send(event, message)
            return None

        try:
            return self.notification.send_interactive(message, buttons)
        except Exception:
            return None

    def send_poll(
        self,
        event: str,
        question: str,
        options: List[str]
    ) -> Optional[str]:
        """
        Send a poll for user voting.

        Args:
            event: Event name for configuration check
            question: Poll question
            options: List of poll options

        Returns:
            Poll ID if successful, None otherwise
        """
        if not self.is_enabled(event):
            return None

        if not self.notification or not self.notification.enabled:
            return None

        # Check if notification integration supports polls
        if not hasattr(self.notification, 'send_poll'):
            return None

        try:
            return self.notification.send_poll(question, options)
        except Exception:
            return None

    def get_capabilities(self) -> Dict[str, bool]:
        """
        Get capabilities of the active notification integration.

        Returns:
            Dict of capability flags (buttons, polls, threads, etc.)
        """
        if not self.notification or not self.notification.enabled:
            return {}

        if hasattr(self.notification, 'get_capabilities'):
            return self.notification.get_capabilities()

        return {
            "buttons": hasattr(self.notification, 'send_interactive'),
            "polls": hasattr(self.notification, 'send_poll'),
            "threads": False,
            "reactions": False,
            "webhooks": hasattr(self.notification, 'setup_webhook'),
        }


# =============================================================================
# HELPER FUNCTIONS (for backward compatibility)
# =============================================================================

def is_notification_enabled(config: dict, event: str) -> bool:
    """
    Check if notification is enabled for a specific event.

    This is a convenience function that wraps NotificationService.

    Args:
        config: Application configuration
        event: Event name

    Returns:
        True if notifications are enabled for this event
    """
    service = NotificationService(config)
    return service.is_enabled(event)


def send_notification(
    config: dict,
    event: str,
    message: str
) -> bool:
    """
    Send a notification if enabled.

    This is a convenience function that wraps NotificationService.

    Args:
        config: Application configuration
        event: Event name
        message: Message to send

    Returns:
        True if notification was sent successfully
    """
    service = NotificationService(config)
    return service.send(event, message)
