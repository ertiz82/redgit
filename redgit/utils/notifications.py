"""
Centralized notification utilities for RedGit.

This module provides a unified interface for sending notifications,
eliminating duplicate notification code across command modules.
"""

from typing import List, Optional, Dict, Any
from ..core.config import ConfigManager
from ..integrations.registry import get_notification


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
