"""
Central notification command for RedGit.

Sends notifications through the active notification integration (Slack, Discord, etc.)
Can be used by other integrations or directly from CLI.

Usage:
    rgt notify "Deployment complete!"
    rgt notify --event deploy --title "v1.2.3 Released" --message "Deployed to production"
    rgt notify --event alert --level error --title "Build Failed"
"""

import typer
from typing import Optional

from ..core.common.config import ConfigManager
from ..integrations.registry import get_notification, get_integrations_by_type, IntegrationType


notify_app = typer.Typer(help="Send notifications through active notification integration")


def _get_notifier():
    """Get the active notification integration."""
    config = ConfigManager().load()
    return get_notification(config)


def _check_notifier():
    """Check if notification integration is configured."""
    notifier = _get_notifier()
    if not notifier:
        available = get_integrations_by_type(IntegrationType.NOTIFICATION)
        typer.secho("❌ No notification integration configured.", fg=typer.colors.RED)
        typer.echo("")
        if available:
            typer.echo("   Available notification integrations:")
            for name in available:
                typer.echo(f"     • {name}")
            typer.echo("")
            typer.echo(f"   Install one: rgt install {available[0]}")
        else:
            typer.echo("   Install a notification integration:")
            typer.echo("     rgt install slack")
        typer.echo("")
        typer.echo("   Then set as active:")
        typer.echo("     rgt integration use <name>")
        raise typer.Exit(1)
    return notifier


@notify_app.command("send")
def send_cmd(
    message: str = typer.Argument(..., help="Message to send"),
    event: str = typer.Option("message", "--event", "-e", help="Event type (commit, branch, pr, deploy, alert, etc.)"),
    title: str = typer.Option(None, "--title", "-t", help="Notification title"),
    url: str = typer.Option(None, "--url", "-u", help="URL to include"),
    level: str = typer.Option("info", "--level", "-l", help="Level: info, success, warning, error"),
    channel: str = typer.Option(None, "--channel", "-c", help="Channel override"),
    field: list[str] = typer.Option(None, "--field", "-f", help="Key=Value fields (can repeat)")
):
    """
    Send a notification message.

    Examples:
        rgt notify send "Hello World!"
        rgt notify send "Build complete" --event deploy --level success
        rgt notify send "Error occurred" --event alert --level error --title "CI Failed"
        rgt notify send "PR merged" --field "PR=#123" --field "Author=dev"
    """
    notifier = _check_notifier()

    # Parse fields
    fields = {}
    if field:
        for f in field:
            if "=" in f:
                k, v = f.split("=", 1)
                fields[k] = v

    # Send notification
    success = notifier.notify(
        event_type=event,
        title=title or message[:50],
        message=message,
        url=url,
        fields=fields if fields else None,
        level=level,
        channel=channel
    )

    if success:
        typer.secho("✅ Notification sent!", fg=typer.colors.GREEN)
    else:
        typer.secho("❌ Failed to send notification.", fg=typer.colors.RED)
        raise typer.Exit(1)


@notify_app.command("commit")
def commit_cmd(
    message: str = typer.Argument(..., help="Commit message"),
    branch: str = typer.Option("main", "--branch", "-b", help="Branch name"),
    author: str = typer.Option(None, "--author", "-a", help="Author name"),
    files: int = typer.Option(0, "--files", "-f", help="Number of files changed"),
    url: str = typer.Option(None, "--url", "-u", help="Commit URL")
):
    """
    Send a commit notification.

    Example:
        rgt notify commit "feat: add login" --branch main --author "Developer" --files 5
    """
    notifier = _check_notifier()

    files_list = [f"file{i}.py" for i in range(files)] if files > 0 else None

    success = notifier.notify_commit(
        branch=branch,
        message=message,
        author=author,
        files=files_list,
        url=url
    )

    if success:
        typer.secho("✅ Commit notification sent!", fg=typer.colors.GREEN)
    else:
        typer.secho("❌ Failed to send.", fg=typer.colors.RED)
        raise typer.Exit(1)


@notify_app.command("branch")
def branch_cmd(
    branch_name: str = typer.Argument(..., help="Branch name"),
    issue: str = typer.Option(None, "--issue", "-i", help="Linked issue key")
):
    """
    Send a branch creation notification.

    Example:
        rgt notify branch feature/PROJ-123-login --issue PROJ-123
    """
    notifier = _check_notifier()

    success = notifier.notify_branch(branch_name=branch_name, issue_key=issue)

    if success:
        typer.secho("✅ Branch notification sent!", fg=typer.colors.GREEN)
    else:
        typer.secho("❌ Failed to send.", fg=typer.colors.RED)
        raise typer.Exit(1)


@notify_app.command("pr")
def pr_cmd(
    title: str = typer.Argument(..., help="PR title"),
    url: str = typer.Argument(..., help="PR URL"),
    head: str = typer.Option("feature", "--head", "-h", help="Source branch"),
    base: str = typer.Option("main", "--base", "-b", help="Target branch")
):
    """
    Send a PR creation notification.

    Example:
        rgt notify pr "Add user authentication" "https://github.com/..." --head feature/login
    """
    notifier = _check_notifier()

    success = notifier.notify_pr(title=title, url=url, head=head, base=base)

    if success:
        typer.secho("✅ PR notification sent!", fg=typer.colors.GREEN)
    else:
        typer.secho("❌ Failed to send.", fg=typer.colors.RED)
        raise typer.Exit(1)


@notify_app.command("task")
def task_cmd(
    action: str = typer.Argument(..., help="Action: created, started, completed, etc."),
    issue_key: str = typer.Argument(..., help="Issue key (e.g., PROJ-123)"),
    summary: str = typer.Argument(..., help="Issue summary"),
    url: str = typer.Option(None, "--url", "-u", help="Issue URL")
):
    """
    Send a task-related notification.

    Example:
        rgt notify task completed PROJ-123 "Add login feature" --url "https://jira..."
    """
    notifier = _check_notifier()

    success = notifier.notify_task(
        action=action,
        issue_key=issue_key,
        summary=summary,
        url=url
    )

    if success:
        typer.secho("✅ Task notification sent!", fg=typer.colors.GREEN)
    else:
        typer.secho("❌ Failed to send.", fg=typer.colors.RED)
        raise typer.Exit(1)


@notify_app.command("alert")
def alert_cmd(
    title: str = typer.Argument(..., help="Alert title"),
    message: str = typer.Argument("", help="Alert message"),
    level: str = typer.Option("warning", "--level", "-l", help="Level: info, warning, error")
):
    """
    Send an alert notification.

    Examples:
        rgt notify alert "Build Failed" "Tests are failing on main"
        rgt notify alert "Disk Space Low" --level warning
        rgt notify alert "Service Down" "API server not responding" --level error
    """
    notifier = _check_notifier()

    success = notifier.notify_alert(title=title, message=message, level=level)

    if success:
        typer.secho("✅ Alert sent!", fg=typer.colors.GREEN)
    else:
        typer.secho("❌ Failed to send.", fg=typer.colors.RED)
        raise typer.Exit(1)


@notify_app.command("status")
def status_cmd():
    """Show notification integration status."""
    config = ConfigManager().load()
    active_name = config.get("active", {}).get("notification")

    if not active_name:
        typer.echo("\n📣 Notification Status\n")
        typer.secho("   No active notification integration.", fg=typer.colors.YELLOW)

        available = get_integrations_by_type(IntegrationType.NOTIFICATION)
        if available:
            typer.echo(f"\n   Available: {', '.join(available)}")
            typer.echo(f"   Install: rgt install {available[0]}")
        else:
            typer.echo("\n   Install one: rgt install slack")
        return

    notifier = _get_notifier()

    typer.echo("\n📣 Notification Status\n")
    typer.echo(f"   Active: {active_name}")

    if notifier:
        typer.secho("   Status: Connected", fg=typer.colors.GREEN)

        # Show integration-specific info
        if hasattr(notifier, 'channel') and notifier.channel:
            typer.echo(f"   Channel: {notifier.channel}")
        if hasattr(notifier, 'username'):
            typer.echo(f"   Bot Name: {notifier.username}")
    else:
        typer.secho("   Status: Not configured properly", fg=typer.colors.RED)
        typer.echo(f"   Run: rgt integration install {active_name}")


# Quick send shortcut (used by main CLI)
def quick_send(message: str) -> bool:
    """Quick send a message notification. Returns True if sent."""
    notifier = _get_notifier()
    if notifier:
        return notifier.send_message(message)
    return False