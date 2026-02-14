"""
Version upgrade check utilities.

Checks PyPI for newer versions and displays upgrade suggestions
with install-method-aware commands.
"""

import json
import shutil
import subprocess
import time
import urllib.request
from pathlib import Path
from typing import Optional

from redgit import __version__

CACHE_FILE = Path.home() / ".redgit" / "version_check.json"
CACHE_TTL = 86400  # 24 hours
PYPI_URL = "https://pypi.org/pypi/redgit/json"
PYPI_TIMEOUT = 5


def check_for_updates() -> Optional[str]:
    """Check for updates and return a Rich-formatted upgrade message, or None."""
    try:
        latest = None
        install_method = None

        if _is_cache_valid():
            data = json.loads(CACHE_FILE.read_text())
            latest = data.get("latest_version")
            install_method = data.get("install_method")
        else:
            latest = _get_latest_version()
            if latest is None:
                return None
            install_method = _detect_install_method()
            _write_cache(latest, install_method)

        if latest and _compare_versions(__version__, latest):
            upgrade_cmd = _get_upgrade_command(install_method or "pip")
            return (
                f"\n[bold yellow]╭─ Update Available ─────────────────────────────╮[/bold yellow]\n"
                f"[bold yellow]│[/bold yellow] redgit [dim]{__version__}[/dim] → [green]{latest}[/green]\n"
                f"[bold yellow]│[/bold yellow] Run: [cyan]{upgrade_cmd}[/cyan]\n"
                f"[bold yellow]╰────────────────────────────────────────────────╯[/bold yellow]"
            )
    except Exception:
        pass
    return None


def _get_latest_version() -> Optional[str]:
    """Fetch latest version from PyPI."""
    try:
        req = urllib.request.Request(PYPI_URL, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=PYPI_TIMEOUT) as resp:
            data = json.loads(resp.read().decode())
            return data.get("info", {}).get("version")
    except Exception:
        return None


def _detect_install_method() -> str:
    """Detect how redgit was installed: brew, pipx, or pip."""
    # Check brew
    if shutil.which("brew"):
        try:
            result = subprocess.run(
                ["brew", "list", "redgit"],
                capture_output=True, timeout=5
            )
            if result.returncode == 0:
                return "brew"
        except Exception:
            pass

    # Check pipx
    if shutil.which("pipx"):
        try:
            result = subprocess.run(
                ["pipx", "list"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0 and "redgit" in result.stdout:
                return "pipx"
        except Exception:
            pass

    return "pip"


def _is_cache_valid() -> bool:
    """Check if cache file exists and is less than 24 hours old."""
    try:
        if not CACHE_FILE.exists():
            return False
        age = time.time() - CACHE_FILE.stat().st_mtime
        return age < CACHE_TTL
    except Exception:
        return False


def _write_cache(latest_version: str, install_method: str) -> None:
    """Write version check result to cache file."""
    try:
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        CACHE_FILE.write_text(json.dumps({
            "checked_at": int(time.time()),
            "latest_version": latest_version,
            "install_method": install_method,
        }))
    except Exception:
        pass


def _compare_versions(current: str, latest: str) -> bool:
    """Return True if latest is newer than current."""
    try:
        def parse(v: str):
            return tuple(int(x) for x in v.strip().split("."))
        return parse(latest) > parse(current)
    except Exception:
        return False


def _get_upgrade_command(method: str) -> str:
    """Return the appropriate upgrade command for the install method."""
    if method == "brew":
        return "brew upgrade redgit"
    elif method == "pipx":
        return "pipx upgrade redgit"
    return "pip install --upgrade redgit"
