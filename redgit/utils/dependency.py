"""
Dependency installation utilities.

Provides helper functions to check and install optional dependencies
with proper error handling and user guidance.
"""

import subprocess
import shutil
import sys
from typing import Optional, Tuple
from rich.console import Console

console = Console()


def check_websockets_available() -> bool:
    """Check if websockets package is available."""
    try:
        import websockets
        return True
    except ImportError:
        return False


def install_package_pipx(package: str) -> Tuple[bool, str]:
    """
    Try to install a package using pipx inject.

    Returns:
        Tuple of (success, message)
    """
    if not shutil.which("pipx"):
        return False, "pipx not found"

    try:
        result = subprocess.run(
            ["pipx", "inject", "redgit", package],
            capture_output=True,
            text=True,
            timeout=120
        )
        if result.returncode == 0:
            return True, f"Successfully installed {package} via pipx"
        return False, result.stderr or result.stdout
    except subprocess.TimeoutExpired:
        return False, "Installation timed out"
    except Exception as e:
        return False, str(e)


def install_package_pip(package: str) -> Tuple[bool, str]:
    """
    Try to install a package using pip.

    Returns:
        Tuple of (success, message)
    """
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", package, "--quiet"],
            capture_output=True,
            text=True,
            timeout=120
        )
        if result.returncode == 0:
            return True, f"Successfully installed {package} via pip"
        return False, result.stderr or result.stdout
    except subprocess.TimeoutExpired:
        return False, "Installation timed out"
    except Exception as e:
        return False, str(e)


def ensure_websockets() -> bool:
    """
    Ensure websockets package is available.

    Installation priority:
    1. Check if already installed
    2. Try pipx inject
    3. Try pip install
    4. Show manual installation instructions

    Returns:
        True if websockets is available, False otherwise
    """
    # Check if already available
    if check_websockets_available():
        return True

    console.print("\n[yellow]websockets package is required for Planning Poker[/yellow]")
    console.print("[dim]Attempting automatic installation...[/dim]\n")

    # Try pipx first (preferred for pipx installations)
    pipx_path = shutil.which("pipx")
    if pipx_path:
        console.print("[dim]Trying pipx inject...[/dim]")
        success, message = install_package_pipx("websockets")
        if success:
            console.print(f"[green]{message}[/green]\n")
            # Verify installation
            if check_websockets_available():
                return True
            console.print("[yellow]Package installed but not loadable. Restart may be required.[/yellow]")
        else:
            console.print(f"[dim]pipx: {message}[/dim]")

    # Try pip
    console.print("[dim]Trying pip install...[/dim]")
    success, message = install_package_pip("websockets")
    if success:
        console.print(f"[green]{message}[/green]\n")
        # Verify installation
        if check_websockets_available():
            return True
        console.print("[yellow]Package installed but not loadable. Restart may be required.[/yellow]")
    else:
        console.print(f"[dim]pip: {message}[/dim]")

    # Manual installation instructions
    console.print("\n[red]Automatic installation failed.[/red]")
    console.print("\n[bold]Manual Installation Options:[/bold]")
    console.print()

    if pipx_path:
        console.print("  [cyan]Option 1 (Recommended for pipx installations):[/cyan]")
        console.print("    pipx inject redgit websockets")
        console.print()
        console.print("  [cyan]Option 2:[/cyan]")
    else:
        console.print("  [cyan]Option 1:[/cyan]")

    console.print("    pip install websockets")
    console.print()
    console.print("  [cyan]Or reinstall redgit with poker support:[/cyan]")
    console.print("    pip install 'redgit[poker]'")
    console.print()
    console.print("[dim]After installation, run the command again.[/dim]")

    return False


def show_websockets_install_help():
    """Show installation help for websockets package."""
    console.print("\n[bold red]websockets package is required for Planning Poker[/bold red]")
    console.print()

    pipx_path = shutil.which("pipx")

    if pipx_path:
        console.print("[bold]Install using one of these methods:[/bold]")
        console.print()
        console.print("  [cyan]1. pipx inject (recommended):[/cyan]")
        console.print("     pipx inject redgit websockets")
        console.print()
        console.print("  [cyan]2. pip install:[/cyan]")
        console.print("     pip install websockets")
    else:
        console.print("[bold]Install using pip:[/bold]")
        console.print()
        console.print("  pip install websockets")

    console.print()
    console.print("[dim]Then run this command again.[/dim]")
