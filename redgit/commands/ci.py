"""
CI/CD command for RedGit.

Interacts with the active CI/CD integration (GitHub Actions, GitLab CI, Jenkins, etc.)

Usage:
    rg ci status              : Show CI/CD status overview
    rg ci pipelines           : List recent pipelines/builds
    rg ci trigger             : Trigger a new pipeline
    rg ci logs <pipeline_id>  : View pipeline logs
"""

import typer
from typing import Optional, List
from rich.console import Console
from rich.table import Table

from ..core.config import ConfigManager
from ..core.gitops import GitOps
from ..integrations.registry import get_cicd, get_integrations_by_type, IntegrationType

console = Console()
ci_app = typer.Typer(help="CI/CD pipeline management")


def _get_cicd():
    """Get the active CI/CD integration."""
    config = ConfigManager().load()
    return get_cicd(config)


def _check_cicd():
    """Check if CI/CD integration is configured."""
    cicd = _get_cicd()
    if not cicd:
        available = get_integrations_by_type(IntegrationType.CI_CD)
        console.print("[red]No CI/CD integration configured.[/red]")
        console.print("")
        if available:
            console.print("   Available CI/CD integrations:")
            for name in available:
                console.print(f"     [dim]- {name}[/dim]")
            console.print("")
            console.print(f"   Install one: [cyan]rg install {available[0]}[/cyan]")
        else:
            console.print("   Install a CI/CD integration:")
            console.print("     [cyan]rg install github-actions[/cyan]")
        console.print("")
        console.print("   Then set as active:")
        console.print("     [cyan]rg integration use <name>[/cyan]")
        raise typer.Exit(1)
    return cicd


def _status_icon(status: str) -> str:
    """Get icon for pipeline status."""
    icons = {
        "success": "[green]✓[/green]",
        "passed": "[green]✓[/green]",
        "completed": "[green]✓[/green]",
        "failed": "[red]✗[/red]",
        "failure": "[red]✗[/red]",
        "error": "[red]✗[/red]",
        "running": "[yellow]●[/yellow]",
        "in_progress": "[yellow]●[/yellow]",
        "pending": "[blue]○[/blue]",
        "queued": "[blue]○[/blue]",
        "waiting": "[blue]○[/blue]",
        "cancelled": "[dim]⊘[/dim]",
        "canceled": "[dim]⊘[/dim]",
        "skipped": "[dim]⊖[/dim]",
    }
    return icons.get(status.lower(), "[dim]?[/dim]")


@ci_app.command("status")
def status_cmd():
    """Show CI/CD status overview."""
    cicd = _check_cicd()

    console.print("\n[bold cyan]CI/CD Status[/bold cyan]\n")
    console.print(f"   Integration: {cicd.name}")
    console.print(f"   Status: [green]Connected[/green]")

    # Try to get current branch
    try:
        gitops = GitOps()
        branch = gitops.original_branch
        console.print(f"   Current branch: {branch}")
    except Exception:
        branch = None

    # Get recent pipelines
    pipelines = cicd.list_pipelines(branch=branch, limit=5)

    if not pipelines:
        console.print("\n   [yellow]No recent pipelines[/yellow]")
        return

    console.print("\n   [bold]Recent Pipelines:[/bold]")
    for p in pipelines:
        icon = _status_icon(p.status)
        branch_info = f" ({p.branch})" if p.branch else ""
        console.print(f"   {icon} {p.name}{branch_info} - {p.status}")


@ci_app.command("pipelines")
def list_pipelines(
    branch: Optional[str] = typer.Option(None, "--branch", "-b", help="Filter by branch"),
    status: Optional[str] = typer.Option(None, "--status", "-s", help="Filter by status"),
    limit: int = typer.Option(10, "--limit", "-n", help="Number of pipelines to show")
):
    """List recent pipelines/builds."""
    cicd = _check_cicd()

    title = "Pipelines"
    if branch:
        title += f" ({branch})"
    if status:
        title += f" [{status}]"

    console.print(f"\n[bold cyan]{title}[/bold cyan]\n")

    pipelines = cicd.list_pipelines(branch=branch, status=status, limit=limit)
    if not pipelines:
        console.print("[yellow]No pipelines found.[/yellow]")
        return

    table = Table(show_header=True)
    table.add_column("ID", style="dim", width=12)
    table.add_column("Status", width=10)
    table.add_column("Branch")
    table.add_column("Duration", style="dim")
    table.add_column("Trigger", style="dim")

    for p in pipelines:
        duration = f"{p.duration}s" if p.duration else "-"
        table.add_row(
            p.name,
            _status_icon(p.status),
            p.branch or "-",
            duration,
            p.trigger or "-"
        )

    console.print(table)


@ci_app.command("pipeline")
def show_pipeline(
    pipeline_id: str = typer.Argument(..., help="Pipeline ID/number")
):
    """Show details for a specific pipeline."""
    cicd = _check_cicd()

    console.print(f"\n[bold cyan]Pipeline {pipeline_id}[/bold cyan]\n")

    pipeline = cicd.get_pipeline_status(pipeline_id)
    if not pipeline:
        console.print("[red]Pipeline not found.[/red]")
        raise typer.Exit(1)

    console.print(f"   Status: {_status_icon(pipeline.status)} {pipeline.status}")
    console.print(f"   Branch: {pipeline.branch or '-'}")
    console.print(f"   Commit: {pipeline.commit_sha[:7] if pipeline.commit_sha else '-'}")
    console.print(f"   Duration: {pipeline.duration}s" if pipeline.duration else "   Duration: -")
    console.print(f"   Trigger: {pipeline.trigger or '-'}")
    if pipeline.url:
        console.print(f"\n   URL: {pipeline.url}")


@ci_app.command("jobs")
def list_jobs(
    pipeline_id: str = typer.Argument(..., help="Pipeline ID/number")
):
    """List jobs/stages for a pipeline."""
    cicd = _check_cicd()

    console.print(f"\n[bold cyan]Jobs for Pipeline {pipeline_id}[/bold cyan]\n")

    jobs = cicd.get_pipeline_jobs(pipeline_id)
    if not jobs:
        console.print("[yellow]No jobs found.[/yellow]")
        return

    table = Table(show_header=True)
    table.add_column("ID", style="dim", width=10)
    table.add_column("Status", width=10)
    table.add_column("Job")
    table.add_column("Duration", style="dim")

    for job in jobs:
        duration = f"{job.duration}s" if job.duration else "-"
        table.add_row(
            job.id,
            _status_icon(job.status),
            job.name,
            duration
        )

    console.print(table)


@ci_app.command("trigger")
def trigger_pipeline(
    branch: Optional[str] = typer.Option(None, "--branch", "-b", help="Branch to build"),
    workflow: Optional[str] = typer.Option(None, "--workflow", "-w", help="Workflow/pipeline name"),
    param: Optional[List[str]] = typer.Option(None, "--param", "-p", help="Parameter KEY=VALUE")
):
    """Trigger a new pipeline/build."""
    cicd = _check_cicd()

    console.print("\n[bold cyan]Triggering Pipeline[/bold cyan]\n")

    # Use current branch if not specified
    if not branch:
        try:
            gitops = GitOps()
            branch = gitops.original_branch
        except Exception:
            pass

    # Parse parameters
    params = {}
    if param:
        for p in param:
            if "=" in p:
                key, value = p.split("=", 1)
                params[key] = value

    if branch:
        console.print(f"   Branch: {branch}")
    if workflow:
        console.print(f"   Workflow: {workflow}")
    if params:
        console.print(f"   Parameters: {params}")

    pipeline = cicd.trigger_pipeline(
        branch=branch,
        workflow=workflow,
        inputs=params or None
    )

    if pipeline:
        console.print(f"\n[green]Pipeline triggered![/green]")
        console.print(f"   {pipeline.name}")
        if pipeline.url:
            console.print(f"   URL: {pipeline.url}")
    else:
        console.print("[red]Failed to trigger pipeline.[/red]")
        raise typer.Exit(1)


@ci_app.command("cancel")
def cancel_pipeline(
    pipeline_id: str = typer.Argument(..., help="Pipeline ID/number to cancel")
):
    """Cancel a running pipeline."""
    cicd = _check_cicd()

    if cicd.cancel_pipeline(pipeline_id):
        console.print(f"[green]Cancelled pipeline {pipeline_id}[/green]")
    else:
        console.print("[red]Failed to cancel pipeline.[/red]")
        raise typer.Exit(1)


@ci_app.command("retry")
def retry_pipeline(
    pipeline_id: str = typer.Argument(..., help="Pipeline ID/number to retry")
):
    """Retry a failed pipeline."""
    cicd = _check_cicd()

    pipeline = cicd.retry_pipeline(pipeline_id)
    if pipeline:
        console.print(f"[green]Pipeline retry started![/green]")
        console.print(f"   {pipeline.name}")
        if pipeline.url:
            console.print(f"   URL: {pipeline.url}")
    else:
        console.print("[red]Failed to retry pipeline.[/red]")
        raise typer.Exit(1)


@ci_app.command("logs")
def show_logs(
    pipeline_id: str = typer.Argument(..., help="Pipeline ID/number"),
    job: Optional[str] = typer.Option(None, "--job", "-j", help="Job ID"),
    tail: int = typer.Option(50, "--tail", "-n", help="Number of lines to show")
):
    """View pipeline/job logs."""
    cicd = _check_cicd()

    title = f"Logs for Pipeline {pipeline_id}"
    if job:
        title += f" (job {job})"
    console.print(f"\n[bold cyan]{title}[/bold cyan]\n")

    logs = cicd.get_build_logs(pipeline_id, job_id=job)
    if logs:
        lines = logs.strip().split("\n")
        if tail and len(lines) > tail:
            lines = lines[-tail:]
        for line in lines:
            console.print(line)
    else:
        console.print("[yellow]No logs available.[/yellow]")


@ci_app.command("watch")
def watch_pipeline(
    pipeline_id: Optional[str] = typer.Argument(None, help="Pipeline ID/number to watch"),
    interval: int = typer.Option(10, "--interval", "-i", help="Polling interval in seconds")
):
    """Watch a pipeline until it completes."""
    import time

    cicd = _check_cicd()

    # If no pipeline ID, get the most recent one
    if not pipeline_id:
        try:
            gitops = GitOps()
            branch = gitops.original_branch
        except Exception:
            branch = None

        pipelines = cicd.list_pipelines(branch=branch, limit=1)
        if not pipelines:
            console.print("[yellow]No pipelines found to watch.[/yellow]")
            raise typer.Exit(1)
        pipeline_id = pipelines[0].name
        console.print(f"[dim]Watching latest pipeline: {pipeline_id}[/dim]")

    console.print(f"\n[bold cyan]Watching Pipeline {pipeline_id}[/bold cyan]")
    console.print(f"[dim]Press Ctrl+C to stop[/dim]\n")

    try:
        while True:
            status = cicd.get_pipeline_status(pipeline_id)
            if not status:
                console.print("[yellow]Could not get pipeline status[/yellow]")
                break

            icon = _status_icon(status.status)
            duration = f" ({status.duration}s)" if status.duration else ""
            console.print(f"{icon} {status.status}{duration}", end="\r")

            if status.status.lower() in ("success", "passed", "completed"):
                console.print(f"\n\n[green]Pipeline completed successfully![/green]")
                break
            elif status.status.lower() in ("failed", "failure", "error"):
                console.print(f"\n\n[red]Pipeline failed![/red]")
                raise typer.Exit(1)
            elif status.status.lower() in ("cancelled", "canceled", "skipped"):
                console.print(f"\n\n[yellow]Pipeline {status.status}[/yellow]")
                break

            time.sleep(interval)

    except KeyboardInterrupt:
        console.print("\n\n[dim]Stopped watching.[/dim]")


@ci_app.command("artifacts")
def list_artifacts(
    pipeline_id: str = typer.Argument(..., help="Pipeline ID/number")
):
    """List artifacts from a pipeline."""
    cicd = _check_cicd()

    console.print(f"\n[bold cyan]Artifacts for Pipeline {pipeline_id}[/bold cyan]\n")

    # Check if the integration supports artifacts
    if not hasattr(cicd, 'list_artifacts'):
        console.print("[yellow]Artifact listing not supported for this integration.[/yellow]")
        return

    artifacts = cicd.list_artifacts(pipeline_id)
    if not artifacts:
        console.print("[yellow]No artifacts found.[/yellow]")
        return

    for artifact in artifacts:
        name = artifact.get('name', 'Unknown')
        size = artifact.get('size', 0)
        size_str = f" ({size / 1024:.1f} KB)" if size else ""
        console.print(f"   [dim]-[/dim] {name}{size_str}")