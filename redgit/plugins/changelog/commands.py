"""
Changelog plugin CLI commands.
"""

import typer
from rich.console import Console
from rich.prompt import Confirm
from rich.panel import Panel
from pathlib import Path
from typing import Optional

from . import ChangelogPlugin
from ...core.config import ConfigManager

console = Console()
changelog_app = typer.Typer(help="Changelog management commands")


def get_plugin() -> ChangelogPlugin:
    return ChangelogPlugin()


@changelog_app.command("init")
def changelog_init():
    """Initialize changelog plugin."""
    plugin = get_plugin()

    console.print("\n[bold cyan]Changelog Plugin Setup[/bold cyan]\n")

    # Enable plugin
    plugin.enable_plugin()

    # Create changelogs directory
    output_dir = Path("changelogs")
    output_dir.mkdir(exist_ok=True)

    console.print("[green]✓ Changelog plugin enabled[/green]")
    console.print(f"[dim]Changelogs will be saved to: {output_dir}/[/dim]")


@changelog_app.command("generate")
def changelog_generate(
    version: Optional[str] = typer.Argument(None, help="Version for changelog (e.g., 1.0.0)"),
    from_ref: Optional[str] = typer.Option(None, "--from", "-f", help="Starting git ref (tag or commit)"),
    to_ref: str = typer.Option("HEAD", "--to", "-t", help="Ending git ref"),
):
    """
    Generate changelog from git commits.

    Examples:
        rg changelog generate              # Auto-detect version, all commits
        rg changelog generate 1.0.0        # Specify version
        rg changelog generate --from v0.9.0  # From specific tag
    """
    plugin = get_plugin()

    # Get version if not specified
    if not version:
        # Try to get from version plugin
        try:
            from ..version import VersionPlugin
            version_plugin = VersionPlugin()
            current = version_plugin.get_current_version()
            if current:
                version = str(current)
        except Exception:
            pass

    if not version:
        version = "unreleased"

    console.print(f"\n[bold]Generating changelog for {version}[/bold]\n")

    # Get commits
    console.print("[yellow]Fetching commits...[/yellow]")
    commits = plugin.get_commits_between(from_ref, to_ref)

    if not commits:
        console.print("[yellow]No commits found in range.[/yellow]")
        return

    console.print(f"[green]Found {len(commits)} commits[/green]")

    # Group and show summary
    grouped = plugin.group_commits_by_type(commits)
    console.print("\n[dim]Commit breakdown:[/dim]")
    for commit_type, type_commits in grouped.items():
        display_name, emoji = plugin.TYPE_DISPLAY.get(commit_type, (commit_type, "📝"))
        console.print(f"  {emoji} {display_name}: {len(type_commits)}")

    # Generate markdown
    content = plugin.generate_markdown(version, commits, from_ref)

    # Save version-specific file
    version_file = plugin.save_version_changelog(version, content)
    console.print(f"\n[green]✓ Created {version_file}[/green]")

    # Update main CHANGELOG.md
    main_file = plugin.update_main_changelog(version, content)
    console.print(f"[green]✓ Updated {main_file}[/green]")

    console.print(Panel(
        f"Changelog for [cyan]{version}[/cyan] generated successfully.\n\n"
        f"Files:\n"
        f"  • {version_file}\n"
        f"  • {main_file}",
        title="Changelog Generated",
        border_style="green"
    ))


@changelog_app.command("show")
def changelog_show(
    version: Optional[str] = typer.Argument(None, help="Version to show (e.g., v1.0.0)"),
):
    """Show changelog content."""
    if version:
        # Show specific version
        version_name = version if version.startswith("v") else f"v{version}"
        filepath = Path("changelogs") / f"{version_name}.md"

        if not filepath.exists():
            console.print(f"[red]Changelog not found: {filepath}[/red]")
            raise typer.Exit(1)

        console.print(filepath.read_text())
    else:
        # Show main CHANGELOG.md
        filepath = Path("CHANGELOG.md")

        if not filepath.exists():
            console.print("[yellow]No CHANGELOG.md found. Run 'rg changelog generate' first.[/yellow]")
            raise typer.Exit(1)

        console.print(filepath.read_text())


# Helper function called by version plugin
def generate_changelog(version: str, from_version: Optional[str] = None):
    """Generate changelog - called by version plugin during major release."""
    plugin = get_plugin()

    commits = plugin.get_commits_between(from_version, "HEAD")
    if not commits:
        return

    content = plugin.generate_markdown(version, commits, from_version)

    # Save files
    plugin.save_version_changelog(version, content)
    plugin.update_main_changelog(version, content)