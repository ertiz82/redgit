"""
LLM command - Manage AI provider configuration.

Usage:
    rgt llm                 : Show current LLM provider
    rgt llm list            : List available providers
    rgt llm set <provider>  : Change LLM provider
    rgt llm status          : Show detailed provider info
"""

import typer
from typing import Optional
from rich.console import Console
from rich.table import Table
import json
from pathlib import Path

from ..core.common.config import ConfigManager

console = Console()
llm_app = typer.Typer(help="Manage AI provider configuration")

# Load provider definitions
PROVIDERS_FILE = Path(__file__).parent.parent / "core" / "common" / "llm_providers.json"


def _load_providers():
    """Load provider definitions from JSON."""
    try:
        with open(PROVIDERS_FILE, "r") as f:
            data = json.load(f)
            return data.get("providers", {})
    except Exception:
        return {}


@llm_app.callback(invoke_without_command=True)
def llm_cmd(ctx: typer.Context):
    """Show current LLM provider."""
    # If a subcommand was invoked, skip
    if ctx.invoked_subcommand is not None:
        return

    config_manager = ConfigManager()
    config = config_manager.load()

    current_provider = config.get("llm", {}).get("provider", "unknown")
    current_model = config.get("llm", {}).get("model", "unknown")

    console.print(f"\n[bold cyan]Current LLM Provider[/bold cyan]")
    console.print(f"  Provider: [green]{current_provider}[/green]")
    console.print(f"  Model:    [green]{current_model}[/green]")
    console.print("\n[dim]Use 'rgt llm list' to see available providers[/dim]")
    console.print("[dim]Use 'rgt llm set <provider>' to change[/dim]\n")


@llm_app.command("list")
def list_cmd():
    """List all available LLM providers."""
    providers = _load_providers()

    if not providers:
        console.print("[yellow]No providers found.[/yellow]")
        return

    config_manager = ConfigManager()
    config = config_manager.load()
    current_provider = config.get("llm", {}).get("provider", "")

    console.print("\n[bold cyan]Available LLM Providers[/bold cyan]\n")

    table = Table(show_header=True)
    table.add_column("Provider", style="cyan")
    table.add_column("Name")
    table.add_column("Type", style="dim")
    table.add_column("Models")

    for provider_id, provider_info in providers.items():
        name = provider_info.get("name", provider_id)
        provider_type = provider_info.get("type", "unknown")
        models = provider_info.get("models", [])
        model_str = ", ".join(models[:2])
        if len(models) > 2:
            model_str += f" (+{len(models) - 2})"

        # Mark current provider
        marker = " ✓" if provider_id == current_provider else ""
        table.add_row(
            f"{provider_id}{marker}",
            name,
            provider_type,
            model_str
        )

    console.print(table)
    console.print(f"\n[dim]Current: {current_provider or 'not set'}[/dim]")
    console.print("[dim]Use 'rgt llm set <provider>' to change[/dim]\n")


@llm_app.command("set")
def set_cmd(provider: str):
    """Change the LLM provider."""
    providers = _load_providers()

    if provider not in providers:
        console.print(f"[red]Unknown provider: {provider}[/red]")
        console.print("[yellow]Available providers:[/yellow]")
        for p_id, p_info in providers.items():
            console.print(f"  • {p_id:<15} {p_info.get('name', '')}")
        raise typer.Exit(1)

    provider_info = providers[provider]
    default_model = provider_info.get("default_model", "")

    config_manager = ConfigManager()
    config = config_manager.load()

    # Update LLM config
    if "llm" not in config:
        config["llm"] = {}

    config["llm"]["provider"] = provider
    config["llm"]["model"] = default_model

    # Save config
    config_manager.save(config)

    console.print(f"\n[green]✓ LLM provider changed to: {provider}[/green]")
    console.print(f"  Model: {default_model}")

    # Show installation instructions if needed
    if provider_info.get("type") == "api":
        env_key = provider_info.get("env_key")
        if env_key:
            console.print(f"\n[yellow]⚠️  Don't forget to set the API key:[/yellow]")
            console.print(f"  export {env_key}=<your-api-key>")
    elif provider_info.get("type") == "cli":
        install_cmd = provider_info.get("install", "")
        if install_cmd:
            console.print(f"\n[yellow]⚠️  Make sure {provider} is installed:[/yellow]")
            console.print(f"  {install_cmd}")

    console.print()


@llm_app.command("status")
def status_cmd():
    """Show detailed LLM provider information."""
    providers = _load_providers()
    config_manager = ConfigManager()
    config = config_manager.load()

    current_provider = config.get("llm", {}).get("provider", "unknown")
    current_model = config.get("llm", {}).get("model", "unknown")

    console.print(f"\n[bold cyan]LLM Configuration[/bold cyan]\n")
    console.print(f"Current Provider: [green]{current_provider}[/green]")
    console.print(f"Current Model:    [green]{current_model}[/green]")

    if current_provider in providers:
        provider_info = providers[current_provider]

        console.print(f"\n[bold]Provider Details:[/bold]")
        console.print(f"  Name:       {provider_info.get('name', 'N/A')}")
        console.print(f"  Type:       {provider_info.get('type', 'N/A')}")

        models = provider_info.get("models", [])
        if models:
            console.print(f"  Models:     {', '.join(models)}")

        if provider_info.get("type") == "api":
            env_key = provider_info.get("env_key")
            if env_key:
                console.print(f"  API Key:    ${env_key}")
                # Check if env var is set
                import os
                is_set = env_key in os.environ
                status = "[green]✓ Set[/green]" if is_set else "[yellow]⚠️  Not set[/yellow]"
                console.print(f"    Status: {status}")

        install_cmd = provider_info.get("install")
        if install_cmd:
            console.print(f"  Install:    {install_cmd}")

    console.print()
