"""
Backup command for RedGit.

Provides CLI interface for managing working tree backups.
"""

import typer
from rich.console import Console
from rich.table import Table

from ..core.common.backup import BackupManager
from ..core.common.gitops import GitOps

app = typer.Typer(help="Manage working tree backups")
console = Console()


@app.command("list")
def list_cmd():
    """List all backups."""
    try:
        gitops = GitOps()
    except Exception:
        gitops = None

    backup_manager = BackupManager(gitops)
    backups = backup_manager.list_backups()

    if not backups:
        console.print("[yellow]No backups found.[/yellow]")
        return

    table = Table(title="RG Backups")
    table.add_column("ID", style="cyan")
    table.add_column("Date", style="dim")
    table.add_column("Branch")
    table.add_column("Files")
    table.add_column("Status", style="bold")

    for backup in backups:
        status = backup.get("status", "unknown")
        status_color = {
            "created": "yellow",
            "completed": "green",
            "failed": "red",
            "restored": "blue"
        }.get(status, "white")

        table.add_row(
            backup.get("id", "?"),
            backup.get("created_at", "")[:19],
            backup.get("base_branch", "?"),
            str(len(backup.get("files", []))),
            f"[{status_color}]{status}[/{status_color}]"
        )

    console.print(table)


@app.command("restore")
def restore_cmd(
    backup_id: str = typer.Argument("latest", help="Backup ID or 'latest'")
):
    """Restore working tree from backup."""
    try:
        gitops = GitOps()
    except Exception:
        gitops = None

    backup_manager = BackupManager(gitops)

    # Check if backup exists
    backup = backup_manager.get_backup(backup_id)
    if not backup:
        console.print(f"[red]Backup not found: {backup_id}[/red]")
        raise typer.Exit(1)

    console.print(f"[yellow]Restoring backup: {backup.get('id', backup_id)}...[/yellow]")
    console.print(f"  Branch: {backup.get('base_branch', '?')}")
    console.print(f"  Files:  {len(backup.get('files', []))}")

    try:
        manifest = backup_manager.restore_backup(backup_id)
        console.print("\n[green]✓ Backup restored successfully![/green]")
        console.print("\n[dim]Run 'git status' to see restored files.[/dim]")
    except Exception as e:
        console.print(f"\n[red]Error restoring backup: {e}[/red]")
        raise typer.Exit(1)


@app.command("show")
def show_cmd(
    backup_id: str = typer.Argument("latest", help="Backup ID or 'latest'")
):
    """Show backup details."""
    try:
        gitops = GitOps()
    except Exception:
        gitops = None

    backup_manager = BackupManager(gitops)
    manifest = backup_manager.get_backup(backup_id)

    if not manifest:
        console.print(f"[red]Backup not found: {backup_id}[/red]")
        raise typer.Exit(1)

    status = manifest.get("status", "unknown")
    status_color = {
        "created": "yellow",
        "completed": "green",
        "failed": "red",
        "restored": "blue"
    }.get(status, "white")

    console.print(f"\n[bold cyan]Backup: {manifest.get('id', '?')}[/bold cyan]\n")
    console.print(f"  Created: {manifest.get('created_at', '?')}")
    console.print(f"  Command: {manifest.get('command', '?')}")
    console.print(f"  Branch:  {manifest.get('base_branch', '?')}")
    console.print(f"  Commit:  {manifest.get('head_commit', '?')}")
    console.print(f"  Status:  [{status_color}]{status}[/{status_color}]")

    if manifest.get("error"):
        console.print(f"\n  [red]Error: {manifest['error']}[/red]")

    files = manifest.get("files", [])
    console.print(f"\n  Files ({len(files)}):")
    for f in files[:15]:
        staged = "[S]" if f.get("staged") else "   "
        status_char = f.get("status", "M")
        # Support both "file" and "path" keys
        file_path = f.get("file") or f.get("path", "?")
        console.print(f"    {staged} {status_char} {file_path}")

    if len(files) > 15:
        console.print(f"    ... and {len(files) - 15} more")


@app.command("cleanup")
def cleanup_cmd(
    keep: int = typer.Option(5, "--keep", "-k", help="Number of backups to keep")
):
    """Remove old backups, keep N most recent."""
    try:
        gitops = GitOps()
    except Exception:
        gitops = None

    backup_manager = BackupManager(gitops)

    before = len(backup_manager.list_backups())
    backup_manager.cleanup_old_backups(keep=keep)
    after = len(backup_manager.list_backups())

    removed = before - after
    if removed > 0:
        console.print(f"[green]✓ Removed {removed} old backup(s). Keeping {after}.[/green]")
    else:
        console.print(f"[dim]No backups to remove. Total: {after}[/dim]")


# Default command (when just 'rg backup' is called)
@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """Manage working tree backups."""
    if ctx.invoked_subcommand is None:
        # Default to list
        list_cmd()
