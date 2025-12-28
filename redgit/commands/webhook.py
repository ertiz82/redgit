"""
Webhook CLI commands.

Commands for managing the webhook server that receives
notification callbacks from Telegram, Slack, etc.
"""

import time
import typer
from typing import Optional
from rich.console import Console
from rich.table import Table

from ..core.config import ConfigManager
from ..core.webhook import (
    WebhookServer,
    load_webhook_state,
    save_webhook_state,
    clear_webhook_state,
    start_daemon,
    stop_daemon
)
from ..core.actions import ActionRegistry
from ..integrations.registry import get_notification, get_tunnel_integration

console = Console()
webhook_app = typer.Typer(help="Manage notification webhooks")


@webhook_app.command("start")
def start_cmd(
    port: int = typer.Option(8765, "--port", "-p", help="Port to listen on"),
    ngrok: bool = typer.Option(False, "--ngrok", "-n", help="Use ngrok for public URL"),
    daemon: bool = typer.Option(False, "--daemon", "-d", help="Run as background daemon"),
    region: str = typer.Option(None, "--region", "-r", help="Ngrok region (us, eu, ap, au)")
):
    """Start webhook server for receiving notification callbacks."""

    # Check if already running
    state = load_webhook_state()
    if state and state.get("running"):
        console.print(f"[yellow]Webhook server already running on port {state['port']}[/yellow]")
        if state.get("public_url"):
            console.print(f"   URL: {state['public_url']}")
        return

    # Load config
    config_manager = ConfigManager()
    config = config_manager.load()

    if daemon:
        # Background daemon mode
        console.print("[dim]Starting webhook daemon...[/dim]")

        try:
            pid = start_daemon(port, use_ngrok=ngrok, config=config)

            # Wait for daemon to start
            time.sleep(1)

            public_url = None
            if ngrok:
                tunnel = get_tunnel_integration(config)
                if tunnel and tunnel.enabled:
                    try:
                        public_url = tunnel.start_tunnel(port, region=region) if region else tunnel.start_tunnel(port)
                        if public_url:
                            save_webhook_state(port, pid, public_url, None)
                            # Auto-configure notification integration
                            _configure_webhook(config, public_url)
                        else:
                            console.print("[red]Failed to start tunnel[/red]")
                            save_webhook_state(port, pid)
                    except Exception as e:
                        console.print(f"[red]Tunnel error: {e}[/red]")
                        save_webhook_state(port, pid)
                else:
                    console.print("[yellow]No tunnel integration configured[/yellow]")
                    console.print("Install one with: rg install ngrok")
                    save_webhook_state(port, pid)
            else:
                save_webhook_state(port, pid)

            console.print(f"[green]Webhook daemon started (PID: {pid})[/green]")
            console.print(f"   Port: {port}")
            if public_url:
                console.print(f"   URL: {public_url}")
            console.print(f"   Stop with: rg webhook stop")

        except Exception as e:
            console.print(f"[red]Failed to start daemon: {e}[/red]")
            raise typer.Exit(1)

    else:
        # Foreground mode
        server = WebhookServer(port=port)

        if not server.start(config=config):
            console.print("[red]Failed to start webhook server[/red]")
            raise typer.Exit(1)

        public_url = None
        if ngrok:
            tunnel = get_tunnel_integration(config)
            if tunnel and tunnel.enabled:
                try:
                    public_url = tunnel.start_tunnel(port, region=region) if region else tunnel.start_tunnel(port)
                    if public_url:
                        console.print(f"[cyan]Public URL: {public_url}[/cyan]")
                        # Auto-configure notification integration
                        _configure_webhook(config, public_url)
                    else:
                        console.print("[yellow]Failed to start tunnel[/yellow]")
                except Exception as e:
                    console.print(f"[yellow]Tunnel warning: {e}[/yellow]")
            else:
                console.print("[yellow]No tunnel integration configured[/yellow]")
                console.print("Install one with: rg install ngrok")

        console.print(f"\n[bold]Webhook server running on port {port}[/bold]")
        if not public_url:
            console.print(f"   Local URL: http://localhost:{port}")
        console.print("Press Ctrl+C to stop\n")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            server.stop()
            if ngrok:
                tunnel = get_tunnel_integration(config)
                if tunnel:
                    tunnel.stop_tunnel()
            console.print("\n[yellow]Server stopped[/yellow]")


@webhook_app.command("stop")
def stop_cmd():
    """Stop webhook server daemon."""
    state = load_webhook_state()

    if not state or not state.get("running"):
        console.print("[dim]No running webhook server[/dim]")
        return

    if stop_daemon():
        console.print("[green]Webhook server stopped[/green]")
    else:
        console.print("[yellow]Webhook server was not running[/yellow]")
        clear_webhook_state()


@webhook_app.command("status")
def status_cmd():
    """Check webhook server status."""
    state = load_webhook_state()

    if state and state.get("running"):
        console.print("[green]Running[/green]")
        console.print(f"   PID: {state.get('pid')}")
        console.print(f"   Port: {state.get('port')}")
        if state.get("public_url"):
            console.print(f"   URL: {state.get('public_url')}")
        if state.get("started_at"):
            console.print(f"   Started: {state.get('started_at')}")
    else:
        console.print("[dim]Not running[/dim]")


@webhook_app.command("actions")
def actions_cmd(
    category: str = typer.Option(None, "--category", "-c", help="Filter by category")
):
    """List registered actions."""
    if category:
        actions = ActionRegistry.get_by_category(category)
    else:
        actions = ActionRegistry.get_all()

    if not actions:
        console.print("[dim]No actions registered[/dim]")
        return

    table = Table(title="Registered Actions")
    table.add_column("Action ID", style="cyan")
    table.add_column("Category", style="green")
    table.add_column("Description")

    for action_id, info in sorted(actions.items()):
        table.add_row(
            action_id,
            info.get("category", "general"),
            info.get("description", "")
        )

    console.print(table)


@webhook_app.command("test")
def test_cmd(
    action: str = typer.Argument(..., help="Action ID to test"),
    data: str = typer.Option("{}", "--data", "-d", help="JSON data payload")
):
    """Test an action execution."""
    import json

    try:
        payload = json.loads(data)
    except json.JSONDecodeError as e:
        console.print(f"[red]Invalid JSON: {e}[/red]")
        raise typer.Exit(1)

    from ..core.actions import ActionContext

    context = ActionContext(
        user_id="test",
        integration="cli",
        raw_data={"action": action, "data": payload}
    )

    console.print(f"[dim]Executing action: {action}[/dim]")
    result = ActionRegistry.execute(action, payload, context)

    if result.success:
        console.print(f"[green]Success[/green]")
        if result.message:
            console.print(f"   Message: {result.message}")
        if result.result:
            console.print(f"   Result: {result.result}")
    else:
        console.print(f"[red]Failed[/red]")
        console.print(f"   Error: {result.error}")


@webhook_app.command("url")
def url_cmd(
    integration: str = typer.Argument("telegram", help="Integration name")
):
    """Get webhook URL for an integration."""
    state = load_webhook_state()

    if not state or not state.get("running"):
        console.print("[yellow]Webhook server not running[/yellow]")
        console.print("Start with: rg webhook start --ngrok")
        return

    base_url = state.get("public_url") or f"http://localhost:{state.get('port')}"
    webhook_url = f"{base_url}/{integration}"

    console.print(f"[cyan]Webhook URL for {integration}:[/cyan]")
    console.print(f"   {webhook_url}")

    # Show integration-specific instructions
    if integration == "telegram":
        config_manager = ConfigManager()
        config = config_manager.load()
        bot_token = config.get("integrations", {}).get("telegram", {}).get("bot_token")

        if bot_token:
            console.print(f"\n[dim]To configure Telegram webhook:[/dim]")
            console.print(f"   curl -X POST 'https://api.telegram.org/bot{bot_token}/setWebhook' \\")
            console.print(f"        -d 'url={webhook_url}'")


def _configure_webhook(config: dict, public_url: str) -> bool:
    """Configure webhook URL for the active notification integration."""
    notification = get_notification(config)

    if not notification or not notification.enabled:
        return False

    if hasattr(notification, 'setup_webhook'):
        try:
            if notification.setup_webhook(public_url):
                console.print(f"[green]Webhook configured for {notification.name}[/green]")
                return True
        except Exception as e:
            console.print(f"[yellow]Failed to configure webhook: {e}[/yellow]")

    return False
