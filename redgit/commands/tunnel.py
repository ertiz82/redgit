"""
Tunnel CLI commands.

Commands for managing tunnel connections to expose local ports to the internet.
Supports integrations like ngrok, cloudflare-tunnel, localtunnel, etc.
"""

import typer
from typing import Optional
from rich.console import Console
from rich.table import Table

from ..core.config import ConfigManager

console = Console()
tunnel_app = typer.Typer(help="Manage tunnel connections")


def get_tunnel_integration(config: dict):
    """Get the configured tunnel integration."""
    from ..integrations.registry import get_tunnel_integration as _get_tunnel
    return _get_tunnel(config)


@tunnel_app.command("start")
def start_cmd(
    port: int = typer.Argument(..., help="Local port to expose"),
    region: str = typer.Option(None, "--region", "-r", help="Server region (if supported)")
):
    """Start a tunnel to expose a local port to the internet."""
    config_manager = ConfigManager()
    config = config_manager.load()

    tunnel = get_tunnel_integration(config)
    if not tunnel:
        console.print("[red]No tunnel integration configured[/red]")
        console.print("\nInstall one with:")
        console.print("  rg install ngrok")
        console.print("  rg install cloudflare-tunnel")
        console.print("  rg install localtunnel")
        raise typer.Exit(1)

    if not tunnel.enabled:
        console.print(f"[red]{tunnel.name} is not configured properly[/red]")
        console.print(f"\nReconfigure with: rg integration configure {tunnel.name}")
        raise typer.Exit(1)

    # Check if already running
    if tunnel.is_running():
        url = tunnel.get_public_url()
        console.print(f"[yellow]Tunnel already running[/yellow]")
        console.print(f"   URL: {url}")
        return

    console.print(f"[dim]Starting {tunnel.name} tunnel on port {port}...[/dim]")

    kwargs = {}
    if region:
        kwargs["region"] = region

    url = tunnel.start_tunnel(port, **kwargs)

    if url:
        console.print(f"[green]Tunnel started[/green]")
        console.print(f"   Public URL: {url}")
        console.print(f"   Local port: {port}")
        console.print(f"\nStop with: rg tunnel stop")
    else:
        console.print(f"[red]Failed to start tunnel[/red]")
        raise typer.Exit(1)


@tunnel_app.command("stop")
def stop_cmd():
    """Stop the active tunnel."""
    config_manager = ConfigManager()
    config = config_manager.load()

    tunnel = get_tunnel_integration(config)
    if not tunnel:
        console.print("[dim]No tunnel integration configured[/dim]")
        return

    if not tunnel.is_running():
        console.print("[dim]No tunnel is currently running[/dim]")
        return

    if tunnel.stop_tunnel():
        console.print("[green]Tunnel stopped[/green]")
    else:
        console.print("[yellow]Tunnel may not have stopped properly[/yellow]")


@tunnel_app.command("status")
def status_cmd():
    """Check tunnel status."""
    config_manager = ConfigManager()
    config = config_manager.load()

    tunnel = get_tunnel_integration(config)
    if not tunnel:
        console.print("[dim]No tunnel integration configured[/dim]")
        console.print("\nInstall one with: rg install ngrok")
        return

    status = tunnel.get_status()

    if status.get("running"):
        console.print("[green]Running[/green]")
        console.print(f"   Integration: {status.get('integration')}")
        console.print(f"   URL: {status.get('url')}")
        if status.get("port"):
            console.print(f"   Local port: {status.get('port')}")
        if status.get("pid"):
            console.print(f"   PID: {status.get('pid')}")
    else:
        console.print("[dim]Not running[/dim]")
        console.print(f"   Integration: {tunnel.name}")
        console.print("\nStart with: rg tunnel start <port>")


@tunnel_app.command("url")
def url_cmd():
    """Get the current public URL."""
    config_manager = ConfigManager()
    config = config_manager.load()

    tunnel = get_tunnel_integration(config)
    if not tunnel:
        console.print("[red]No tunnel integration configured[/red]")
        raise typer.Exit(1)

    url = tunnel.get_public_url()
    if url:
        console.print(url)
    else:
        console.print("[dim]No active tunnel[/dim]")
        raise typer.Exit(1)
