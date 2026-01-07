"""
Webhook Server for receiving notification callbacks.

This module provides an HTTP server that receives callbacks from
notification platforms (Telegram, Slack, etc.) when users interact
with buttons, polls, and other interactive elements.
"""

import json
import threading
import logging
import os
import signal
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Optional, Dict, Any, Callable
from pathlib import Path
from datetime import datetime

from .actions import ActionRegistry, ActionContext, ActionResult, parse_callback_data

# State file location
STATE_DIR = Path.home() / ".redgit"
STATE_FILE = STATE_DIR / "webhook_state.json"

logger = logging.getLogger(__name__)


class WebhookHandler(BaseHTTPRequestHandler):
    """HTTP request handler for webhook callbacks."""

    # Class-level callback handlers
    _handlers: Dict[str, Callable] = {}
    _config: Dict[str, Any] = {}

    def log_message(self, format: str, *args) -> None:
        """Override to use logging instead of stderr."""
        logger.info("%s - %s", self.address_string(), format % args)

    def do_GET(self):
        """Handle GET requests (health check)."""
        if self.path == "/health":
            self._send_json({"status": "ok", "server": "redgit-webhook"})
        else:
            self._send_json({"error": "Not found"}, status=404)

    def do_POST(self):
        """Handle POST requests (webhook callbacks)."""
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode("utf-8")) if post_data else {}

            # Route to appropriate handler
            if "/telegram" in self.path:
                response = self._handle_telegram(data)
            elif "/slack" in self.path:
                response = self._handle_slack(data)
            elif "/discord" in self.path:
                response = self._handle_discord(data)
            elif "/action" in self.path:
                response = self._handle_direct_action(data)
            else:
                response = {"error": "Unknown webhook endpoint"}

            self._send_json(response)

        except json.JSONDecodeError:
            self._send_json({"error": "Invalid JSON"}, status=400)
        except Exception as e:
            logger.exception("Error handling webhook")
            self._send_json({"error": str(e)}, status=500)

    def _send_json(self, data: dict, status: int = 200):
        """Send JSON response."""
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def _handle_telegram(self, data: dict) -> dict:
        """Handle Telegram webhook callback."""
        if "callback_query" in data:
            callback = data["callback_query"]
            callback_data = callback.get("data", "")
            action_id, payload = parse_callback_data(callback_data)

            context = ActionContext(
                user_id=str(callback.get("from", {}).get("id", "")),
                message_id=str(callback.get("message", {}).get("message_id", "")),
                chat_id=str(callback.get("message", {}).get("chat", {}).get("id", "")),
                integration="telegram",
                timestamp=datetime.now().isoformat(),
                raw_data=data
            )

            result = ActionRegistry.execute(action_id, payload, context)

            # Answer callback query if we have bot token
            self._answer_telegram_callback(callback.get("id"), result)

            return {
                "action": action_id,
                "success": result.success,
                "message": result.message or result.error
            }

        elif "poll_answer" in data:
            # Handle poll answer
            poll_answer = data["poll_answer"]
            return {
                "poll_id": poll_answer.get("poll_id"),
                "user_id": poll_answer.get("user", {}).get("id"),
                "options": poll_answer.get("option_ids", [])
            }

        return {"status": "received"}

    def _answer_telegram_callback(self, callback_id: str, result: ActionResult):
        """Answer Telegram callback query."""
        bot_token = self._config.get("telegram", {}).get("bot_token")
        if not bot_token or not callback_id:
            return

        try:
            from urllib.request import Request, urlopen
            url = f"https://api.telegram.org/bot{bot_token}/answerCallbackQuery"
            payload = {
                "callback_query_id": callback_id,
                "text": result.message or ("Done!" if result.success else result.error),
                "show_alert": not result.success
            }
            req = Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            urlopen(req, timeout=5)
        except Exception:
            pass

    def _handle_slack(self, data: dict) -> dict:
        """Handle Slack webhook callback."""
        # Slack sends payload as form-urlencoded in 'payload' field
        if "payload" in data:
            try:
                payload = json.loads(data["payload"])
            except (json.JSONDecodeError, TypeError):
                payload = data
        else:
            payload = data

        if payload.get("type") == "block_actions":
            actions = payload.get("actions", [])
            for action in actions:
                action_id = action.get("action_id", "")
                value = action.get("value", "{}")

                try:
                    action_data = json.loads(value)
                except json.JSONDecodeError:
                    action_data = {"value": value}

                context = ActionContext(
                    user_id=payload.get("user", {}).get("id"),
                    message_id=payload.get("message", {}).get("ts"),
                    chat_id=payload.get("channel", {}).get("id"),
                    integration="slack",
                    timestamp=datetime.now().isoformat(),
                    raw_data=payload
                )

                result = ActionRegistry.execute(action_id, action_data, context)
                return {
                    "action": action_id,
                    "success": result.success,
                    "message": result.message or result.error
                }

        return {"status": "received"}

    def _handle_discord(self, data: dict) -> dict:
        """Handle Discord webhook callback."""
        if data.get("type") == 3:  # MESSAGE_COMPONENT interaction
            custom_id = data.get("data", {}).get("custom_id", "")
            action_id, payload = parse_callback_data(custom_id)

            context = ActionContext(
                user_id=data.get("member", {}).get("user", {}).get("id"),
                message_id=data.get("message", {}).get("id"),
                chat_id=data.get("channel_id"),
                integration="discord",
                timestamp=datetime.now().isoformat(),
                raw_data=data
            )

            result = ActionRegistry.execute(action_id, payload, context)
            return {
                "type": 4,  # CHANNEL_MESSAGE_WITH_SOURCE
                "data": {
                    "content": result.message or ("Done!" if result.success else result.error),
                    "flags": 64  # EPHEMERAL
                }
            }

        return {"type": 1}  # PONG

    def _handle_direct_action(self, data: dict) -> dict:
        """Handle direct action execution (for testing)."""
        action_id = data.get("action")
        payload = data.get("data", {})

        if not action_id:
            return {"error": "Missing 'action' field"}

        context = ActionContext(
            user_id=data.get("user_id"),
            integration="direct",
            timestamp=datetime.now().isoformat(),
            raw_data=data
        )

        result = ActionRegistry.execute(action_id, payload, context)
        return {
            "action": action_id,
            "success": result.success,
            "result": result.result,
            "message": result.message,
            "error": result.error
        }


class WebhookServer:
    """
    Webhook server for receiving notification callbacks.

    Usage:
        server = WebhookServer(port=8765)
        server.start()
        # ... server running ...
        server.stop()
    """

    def __init__(self, port: int = 8765, host: str = "0.0.0.0"):
        self.port = port
        self.host = host
        self.server: Optional[HTTPServer] = None
        self.thread: Optional[threading.Thread] = None
        self._running = False

    def start(self, config: dict = None) -> bool:
        """
        Start the webhook server.

        Args:
            config: Optional configuration dict with integration credentials

        Returns:
            True if server started successfully
        """
        if self._running:
            return True

        try:
            # Store config for handlers
            if config:
                WebhookHandler._config = config

            self.server = HTTPServer((self.host, self.port), WebhookHandler)
            self.thread = threading.Thread(target=self.server.serve_forever)
            self.thread.daemon = True
            self.thread.start()
            self._running = True

            logger.info(f"Webhook server started on {self.host}:{self.port}")
            return True

        except Exception as e:
            logger.error(f"Failed to start webhook server: {e}")
            return False

    def stop(self):
        """Stop the webhook server."""
        if self.server:
            self.server.shutdown()
            self._running = False
            logger.info("Webhook server stopped")

    @property
    def running(self) -> bool:
        """Check if server is running."""
        return self._running

    def get_url(self, integration: str = "") -> str:
        """Get the webhook URL for an integration."""
        base = f"http://{self.host}:{self.port}"
        if integration:
            return f"{base}/{integration}"
        return base


# =============================================================================
# STATE MANAGEMENT
# =============================================================================

def save_webhook_state(
    port: int,
    pid: int,
    public_url: str = None,
    ngrok_pid: int = None
) -> None:
    """Save webhook server state to file."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)

    state = {
        "running": True,
        "port": port,
        "pid": pid,
        "public_url": public_url,
        "ngrok_pid": ngrok_pid,
        "started_at": datetime.now().isoformat()
    }

    STATE_FILE.write_text(json.dumps(state, indent=2))


def load_webhook_state() -> Optional[dict]:
    """Load webhook server state from file."""
    if not STATE_FILE.exists():
        return None

    try:
        state = json.loads(STATE_FILE.read_text())

        # Verify process is still running
        if state.get("pid"):
            try:
                os.kill(state["pid"], 0)
            except OSError:
                state["running"] = False

        return state

    except (json.JSONDecodeError, IOError):
        return None


def clear_webhook_state() -> None:
    """Clear webhook server state."""
    if STATE_FILE.exists():
        STATE_FILE.unlink()


# =============================================================================
# DAEMON MANAGEMENT
# =============================================================================

def start_daemon(port: int, use_ngrok: bool = False, config: dict = None) -> int:
    """
    Start webhook server as a background daemon.

    Args:
        port: Port to listen on
        use_ngrok: Whether to start ngrok tunnel
        config: Optional configuration dict

    Returns:
        Daemon process ID
    """
    import subprocess

    # Build command
    cmd = [
        sys.executable, "-c",
        f"""
import sys
sys.path.insert(0, '{Path(__file__).parent.parent}')
from redgit.core.webhook import WebhookServer, save_webhook_state
import os, signal, time

def shutdown(sig, frame):
    server.stop()
    sys.exit(0)

signal.signal(signal.SIGTERM, shutdown)
signal.signal(signal.SIGINT, shutdown)

server = WebhookServer(port={port})
server.start({repr(config)})
save_webhook_state({port}, os.getpid())

while True:
    time.sleep(1)
"""
    ]

    # Start daemon process
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True
    )

    return process.pid


def stop_daemon() -> bool:
    """
    Stop the webhook daemon.

    Returns:
        True if daemon was stopped
    """
    state = load_webhook_state()
    if not state or not state.get("pid"):
        return False

    pid = state["pid"]
    ngrok_pid = state.get("ngrok_pid")

    try:
        # Stop main process
        os.kill(pid, signal.SIGTERM)

        # Stop ngrok if running
        if ngrok_pid:
            try:
                os.kill(ngrok_pid, signal.SIGTERM)
            except OSError:
                pass

        clear_webhook_state()
        return True

    except OSError:
        clear_webhook_state()
        return False
