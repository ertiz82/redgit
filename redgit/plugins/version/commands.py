"""
Version plugin CLI commands.
"""

import re
import typer
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel

from . import VersionPlugin, VersionInfo
from ...core.config import ConfigManager
from ...core.gitops import GitOps

console = Console()
version_app = typer.Typer(help="Version management commands")


def get_plugin() -> VersionPlugin:
    return VersionPlugin()


@version_app.command("init")
def version_init():
    """Initialize versioning for this project."""
    plugin = get_plugin()
    config_manager = ConfigManager()

    console.print("\n[bold cyan]Version Plugin Setup[/bold cyan]\n")

    # Check if already initialized
    current = plugin.get_current_version()
    if current:
        console.print(f"[yellow]Version already configured: {current}[/yellow]")
        if not Confirm.ask("Reinitialize?", default=False):
            return

    # Detect existing version from files
    detected = None
    file_info = plugin.detect_version_file()
    if file_info:
        filename, pattern = file_info
        try:
            from pathlib import Path
            content = Path(filename).read_text()
            match = re.search(pattern, content, re.MULTILINE)
            if match:
                detected = match.group(1)
                console.print(f"[green]Detected version {detected} from {filename}[/green]")
        except Exception:
            pass

    # Ask for starting version
    default_version = detected or "0.1.0"
    version_str = Prompt.ask(
        "Starting version (x.x.x format)",
        default=default_version
    )

    # Validate
    try:
        version = VersionInfo.parse(version_str)
    except ValueError:
        console.print("[red]Invalid version format. Use x.x.x (e.g., 1.0.0)[/red]")
        raise typer.Exit(1)

    # Ask for tag prefix
    tag_prefix = Prompt.ask("Git tag prefix", default="v")

    # Save to config
    config = config_manager.load()
    if "plugins" not in config:
        config["plugins"] = {}

    config["plugins"]["version"] = {
        "enabled": True,
        "current": str(version),
        "tag_prefix": tag_prefix,
        "auto_tag": True,
        "auto_commit": True,
    }

    config_manager.save(config)

    console.print(f"\n[green]✓ Version plugin initialized at {version}[/green]")
    console.print(f"[dim]Tag prefix: {tag_prefix}[/dim]")


@version_app.command("show")
def version_show():
    """Show current version."""
    plugin = get_plugin()
    current = plugin.get_current_version()

    if not current:
        console.print("[yellow]No version configured. Run 'rg version init' first.[/yellow]")
        raise typer.Exit(1)

    console.print(f"\n[bold]Current version:[/bold] [cyan]{current}[/cyan]")

    # Show version files
    files = plugin.get_version_files()
    if files:
        console.print("\n[dim]Version files:[/dim]")
        for filepath, _ in files:
            console.print(f"  [dim]- {filepath}[/dim]")


@version_app.command("release")
def version_release(
    level: str = typer.Argument(..., help="Release level: patch, minor, or major"),
    dry_run: bool = typer.Option(False, "--dry-run", "-n", help="Show what would happen"),
    no_changelog: bool = typer.Option(False, "--no-changelog", help="Skip changelog generation"),
):
    """
    Release a new version.

    Examples:
        rg version release patch   # 0.1.0 -> 0.1.1
        rg version release minor   # 0.1.1 -> 0.2.0
        rg version release major   # 0.2.0 -> 1.0.0
    """
    if level not in ["patch", "minor", "major"]:
        console.print(f"[red]Invalid level: {level}. Use patch, minor, or major.[/red]")
        raise typer.Exit(1)

    plugin = get_plugin()
    current = plugin.get_current_version()

    if not current:
        console.print("[yellow]No version configured. Run 'rg version init' first.[/yellow]")
        raise typer.Exit(1)

    # Calculate new version
    new_version = current.bump(level)
    tag_prefix = plugin.get_tag_prefix()
    tag_name = f"{tag_prefix}{new_version}"

    console.print(f"\n[bold]Release {level}:[/bold] {current} → [cyan]{new_version}[/cyan]")

    if dry_run:
        console.print("\n[yellow]Dry run - no changes made[/yellow]")

        # Show what would be updated
        files = plugin.get_version_files()
        console.print("\n[dim]Would update:[/dim]")
        for filepath, _ in files:
            console.print(f"  - {filepath}")

        console.print(f"\n[dim]Would create tag: {tag_name}[/dim]")

        if level == "major" and plugin.is_changelog_enabled() and not no_changelog:
            console.print(f"[dim]Would generate changelog for {new_version}[/dim]")

        return

    # Confirm
    if not Confirm.ask(f"Release {tag_name}?", default=True):
        return

    # Update all version files
    console.print("\n[yellow]Updating version files...[/yellow]")
    updated_files = plugin.update_all_versions(current, new_version)

    for f in updated_files:
        console.print(f"  [green]✓[/green] {f}")

    if not updated_files:
        console.print("  [yellow]No files updated[/yellow]")

    # Save to config
    plugin.save_version_to_config(new_version)
    console.print(f"  [green]✓[/green] .redgit/config.yaml")

    # Generate changelog for major releases
    if level == "major" and plugin.is_changelog_enabled() and not no_changelog:
        console.print("\n[yellow]Generating changelog...[/yellow]")
        try:
            from ..changelog.commands import generate_changelog
            generate_changelog(str(new_version), plugin.get_previous_major_version(new_version))
        except Exception as e:
            console.print(f"[yellow]Changelog generation failed: {e}[/yellow]")

    # Git operations
    try:
        gitops = GitOps()

        # Stage updated files
        files_to_stage = updated_files + [".redgit/config.yaml"]

        # Check if changelog was created
        from pathlib import Path
        changelog_file = Path(f"changelogs/v{new_version}.md")
        if changelog_file.exists():
            files_to_stage.append(str(changelog_file))
        main_changelog = Path("CHANGELOG.md")
        if main_changelog.exists():
            files_to_stage.append("CHANGELOG.md")

        console.print("\n[yellow]Creating release commit...[/yellow]")
        gitops.repo.index.add(files_to_stage)
        gitops.repo.index.commit(f"chore(release): {tag_name}")
        console.print(f"  [green]✓[/green] Committed: chore(release): {tag_name}")

        # Create tag
        console.print("\n[yellow]Creating git tag...[/yellow]")
        gitops.repo.create_tag(tag_name, message=f"Release {new_version}")
        console.print(f"  [green]✓[/green] Tag created: {tag_name}")

    except Exception as e:
        console.print(f"[red]Git error: {e}[/red]")
        raise typer.Exit(1)

    # Summary
    console.print(Panel(
        f"[bold green]Released {tag_name}[/bold green]\n\n"
        f"Run [cyan]rg push[/cyan] to push the release and tags to remote.",
        title="Release Complete",
        border_style="green"
    ))


# Shortcut command for main CLI
def release_shortcut(
    level: str = typer.Argument(..., help="Release level: patch, minor, or major"),
    dry_run: bool = typer.Option(False, "--dry-run", "-n", help="Show what would happen"),
    no_changelog: bool = typer.Option(False, "--no-changelog", help="Skip changelog generation"),
):
    """
    Shortcut for 'rg version release'.

    Examples:
        rg release patch   # 0.1.0 -> 0.1.1
        rg release minor   # 0.1.1 -> 0.2.0
        rg release major   # 0.2.0 -> 1.0.0
    """
    version_release(level, dry_run, no_changelog)