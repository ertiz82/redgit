"""
Planning Poker WebSocket client.

Used by participants to connect to a poker session.
"""

import asyncio
import json
import logging
from typing import Dict, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum

try:
    import websockets
    import websockets.exceptions
    from websockets.client import connect
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    websockets = None

from .server import MessageType

logger = logging.getLogger(__name__)


class ClientState(Enum):
    """State of the poker client."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    JOINED = "joined"
    VOTING = "voting"
    REVEALED = "revealed"
    DISTRIBUTING = "distributing"  # Task distribution phase
    CLAIMING = "claiming"          # Waiting for claim decision
    FINISHED = "finished"


@dataclass
class ClientSession:
    """Local view of the poker session."""
    session_id: str = ""
    leader: str = ""
    participants: list = field(default_factory=list)
    state: str = "waiting"
    current_task: Optional[Dict] = None
    my_vote: Optional[int] = None
    voted_count: int = 0
    total_count: int = 0
    votes: Dict[str, Optional[int]] = field(default_factory=dict)
    statistics: Optional[Dict] = None
    fibonacci: list = field(default_factory=lambda: [1, 2, 3, 5, 8, 13, 21])
    allow_question_mark: bool = True
    # AI reasoning fields
    ai_reasoning: Optional[str] = None
    ai_confidence: Optional[str] = None
    ai_factors: list = field(default_factory=list)
    # Session summary (set when session ends)
    summary: Optional[Dict] = None
    # Distribution state
    current_offer: Optional[Dict] = None          # Current task being offered
    assignments: Dict[str, str] = field(default_factory=dict)  # task_key -> assigned_to
    distribution_summary: Optional[Dict] = None   # Final distribution summary


class PokerClient:
    """
    WebSocket client for Planning Poker sessions.

    Connects to a poker server and handles message exchange.
    """

    def __init__(self, url: str, name: str):
        if not WEBSOCKETS_AVAILABLE:
            raise ImportError(
                "websockets package is required. Install with: pip install websockets"
            )

        self.url = url
        self.name = name
        self.state = ClientState.DISCONNECTED
        self.session = ClientSession()
        self._websocket = None
        self._receive_task = None

        # Callbacks for events
        self.on_message: Optional[Callable[[str, Dict], None]] = None
        self.on_state_change: Optional[Callable[[ClientState], None]] = None
        self.on_error: Optional[Callable[[str], None]] = None
        self.on_session_ended: Optional[Callable[[Dict], None]] = None

    async def connect(self) -> bool:
        """Connect to the poker server."""
        self._set_state(ClientState.CONNECTING)

        try:
            # Configure ping/pong settings for long-running sessions
            # ping_interval=30: Send ping every 30 seconds
            # ping_timeout=60: Wait up to 60 seconds for pong response
            # close_timeout=10: Wait up to 10 seconds for close handshake
            self._websocket = await connect(
                self.url,
                ping_interval=30,
                ping_timeout=60,
                close_timeout=10
            )
            self._set_state(ClientState.CONNECTED)

            # Start receiving messages
            self._receive_task = asyncio.create_task(self._receive_loop())

            # Send join message
            await self._send({
                "type": MessageType.JOIN.value,
                "name": self.name
            })

            return True

        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            self._set_state(ClientState.DISCONNECTED)
            if self.on_error:
                self.on_error(f"Connection failed: {e}")
            return False

    async def disconnect(self):
        """Disconnect from the poker server."""
        if self._receive_task:
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass

        if self._websocket:
            await self._websocket.close()

        self._set_state(ClientState.DISCONNECTED)

    async def vote(self, points: Optional[int]) -> bool:
        """Submit a vote."""
        if self.state not in (ClientState.JOINED, ClientState.VOTING):
            return False

        self.session.my_vote = points
        await self._send({
            "type": MessageType.VOTE.value,
            "vote": points
        })
        return True

    async def _receive_loop(self):
        """Receive and process messages from the server."""
        try:
            async for message in self._websocket:
                try:
                    data = json.loads(message)
                    await self._handle_message(data)
                except json.JSONDecodeError:
                    logger.error("Received invalid JSON")
                except Exception as e:
                    logger.error(f"Error handling message: {e}")

        except asyncio.CancelledError:
            raise
        except Exception as e:
            # Check if it's a ConnectionClosed error
            error_name = type(e).__name__
            if "ConnectionClosed" in error_name:
                # Check if session ended normally (either already FINISHED or server sent close)
                if self.state == ClientState.FINISHED:
                    # Normal session end - not an error
                    logger.info("Session ended normally")
                    return
                # Check if it's a clean close (1000 = normal closure)
                close_code = getattr(e, 'code', None) if hasattr(e, 'code') else None
                if close_code == 1000:
                    # Server closed cleanly (session ended)
                    logger.info("Server closed connection normally")
                    self._set_state(ClientState.FINISHED)
                    return
                # Unexpected connection close
                logger.warning(f"Connection closed: {e}")
                self._set_state(ClientState.DISCONNECTED)
                if self.on_error:
                    self.on_error("Connection closed by server")
            else:
                logger.error(f"Receive loop error: {e}")
                self._set_state(ClientState.DISCONNECTED)
                if self.on_error:
                    self.on_error(f"Connection lost: {e}")

    async def _handle_message(self, data: Dict):
        """Handle a message from the server."""
        msg_type = data.get("type", "")

        handlers = {
            MessageType.WELCOME.value: self._handle_welcome,
            MessageType.PARTICIPANT_JOINED.value: self._handle_participant_joined,
            MessageType.PARTICIPANT_LEFT.value: self._handle_participant_left,
            MessageType.VOTING_STARTED.value: self._handle_voting_started,
            MessageType.VOTE_COUNT_UPDATE.value: self._handle_vote_count,
            MessageType.VOTING_REVEALED.value: self._handle_revealed,
            MessageType.POINTS_SET.value: self._handle_points_set,
            MessageType.TASK_CHANGED.value: self._handle_task_changed,
            MessageType.SESSION_ENDED.value: self._handle_session_ended,
            MessageType.ERROR.value: self._handle_error,
            # Distribution handlers
            MessageType.DISTRIBUTION_STARTED.value: self._handle_distribution_started,
            MessageType.TASK_OFFER.value: self._handle_task_offer,
            MessageType.TASK_CLAIMED.value: self._handle_task_claimed,
            MessageType.TASK_ASSIGNED.value: self._handle_task_assigned,
            MessageType.DISTRIBUTION_COMPLETE.value: self._handle_distribution_complete,
        }

        handler = handlers.get(msg_type)
        if handler:
            await handler(data)

        # Emit event to callback
        if self.on_message:
            self.on_message(msg_type, data)

    async def _handle_welcome(self, data: Dict):
        """Handle welcome message."""
        self.session.session_id = data.get("session_id", "")
        self.session.leader = data.get("leader", "")
        self.session.participants = data.get("participants", [])
        self.session.state = data.get("state", "waiting")
        self.session.current_task = data.get("current_task")

        self._set_state(ClientState.JOINED)

    async def _handle_participant_joined(self, data: Dict):
        """Handle participant joined."""
        self.session.participants = data.get("participants", [])
        self.session.total_count = data.get("count", 0)

    async def _handle_participant_left(self, data: Dict):
        """Handle participant left."""
        self.session.participants = data.get("participants", [])
        self.session.total_count = data.get("count", 0)

    async def _handle_voting_started(self, data: Dict):
        """Handle voting started."""
        self.session.current_task = data.get("task")
        self.session.fibonacci = data.get("fibonacci", [1, 2, 3, 5, 8, 13, 21])
        self.session.allow_question_mark = data.get("allow_question_mark", True)
        self.session.state = "voting"
        self.session.my_vote = None
        self.session.voted_count = 0
        self.session.votes = {}
        self.session.statistics = None

        self._set_state(ClientState.VOTING)

    async def _handle_vote_count(self, data: Dict):
        """Handle vote count update."""
        self.session.voted_count = data.get("voted", 0)
        self.session.total_count = data.get("total", 0)

    async def _handle_revealed(self, data: Dict):
        """Handle votes revealed."""
        self.session.votes = data.get("votes", {})
        self.session.statistics = data.get("statistics")
        self.session.state = "revealed"
        # AI reasoning fields
        self.session.ai_reasoning = data.get("ai_reasoning")
        self.session.ai_confidence = data.get("ai_confidence")
        self.session.ai_factors = data.get("ai_factors", [])

        self._set_state(ClientState.REVEALED)

    async def _handle_points_set(self, data: Dict):
        """Handle final points set."""
        self.session.state = "waiting"
        self._set_state(ClientState.JOINED)

    async def _handle_task_changed(self, data: Dict):
        """Handle task changed."""
        self.session.current_task = data.get("task")
        self.session.state = "waiting"
        self.session.my_vote = None
        self.session.votes = {}
        self.session.statistics = None

        self._set_state(ClientState.JOINED)

    async def _handle_session_ended(self, data: Dict):
        """Handle session ended."""
        self.session.state = "finished"
        self.session.summary = data.get("summary", {})  # Store for UI access
        self._set_state(ClientState.FINISHED)
        # Notify UI via callback with session summary
        if self.on_session_ended:
            self.on_session_ended(data.get("summary", {}))

    async def _handle_error(self, data: Dict):
        """Handle error message."""
        message = data.get("message", "Unknown error")
        logger.error(f"Server error: {message}")
        if self.on_error:
            self.on_error(message)

    # =========================================================================
    # DISTRIBUTION HANDLERS
    # =========================================================================

    async def _handle_distribution_started(self, data: Dict):
        """Handle distribution phase started."""
        self.session.state = "distributing"
        self.session.current_offer = None
        self.session.assignments = {}
        self._set_state(ClientState.DISTRIBUTING)

    async def _handle_task_offer(self, data: Dict):
        """Handle task being offered for claiming."""
        self.session.current_offer = {
            "task_key": data.get("task_key"),
            "task_summary": data.get("task_summary"),
            "final_points": data.get("final_points"),
            "claimed_by": None
        }
        self._set_state(ClientState.CLAIMING)

    async def _handle_task_claimed(self, data: Dict):
        """Handle task claimed by someone."""
        task_key = data.get("task_key")
        claimed_by = data.get("claimed_by")

        # Update current offer if it matches
        if self.session.current_offer and self.session.current_offer.get("task_key") == task_key:
            self.session.current_offer["claimed_by"] = claimed_by

    async def _handle_task_assigned(self, data: Dict):
        """Handle task assignment confirmed by leader."""
        task_key = data.get("task_key")
        assigned_to = data.get("assigned_to")
        skipped = data.get("skipped", False)

        if not skipped and assigned_to:
            self.session.assignments[task_key] = assigned_to

        # Clear current offer and go back to distributing state
        self.session.current_offer = None
        self._set_state(ClientState.DISTRIBUTING)

    async def _handle_distribution_complete(self, data: Dict):
        """Handle distribution phase complete."""
        self.session.distribution_summary = {
            "assignments": data.get("assignments", []),
            "assigned_count": data.get("assigned_count", 0),
            "skipped_count": data.get("skipped_count", 0)
        }
        self.session.state = "finished"
        self._set_state(ClientState.FINISHED)

    async def claim_task(self, task_key: str, account_id: Optional[str] = None) -> bool:
        """Claim a task during distribution phase."""
        if self.state != ClientState.CLAIMING:
            return False

        await self._send({
            "type": MessageType.CLAIM_TASK.value,
            "task_key": task_key,
            "account_id": account_id
        })
        return True

    async def _send(self, data: Dict):
        """Send a message to the server."""
        if self._websocket:
            try:
                await self._websocket.send(json.dumps(data))
            except Exception as e:
                logger.error(f"Failed to send message: {e}")

    def _set_state(self, state: ClientState):
        """Set client state and notify callback."""
        self.state = state
        if self.on_state_change:
            self.on_state_change(state)

    def get_session(self) -> ClientSession:
        """Get the current session state."""
        return self.session


class LeaderClient(PokerClient):
    """
    Extended client for the session leader.

    Provides additional methods for controlling the session.
    """

    async def start_voting(self, task_index: Optional[int] = None) -> bool:
        """Start voting on a task."""
        await self._send({
            "type": MessageType.START_VOTING.value,
            "task_index": task_index
        })
        return True

    async def reveal(self) -> bool:
        """Reveal all votes."""
        await self._send({
            "type": MessageType.REVEAL.value
        })
        return True

    async def set_points(self, points: int) -> bool:
        """Set final story points."""
        await self._send({
            "type": MessageType.SET_POINTS.value,
            "points": points
        })
        return True

    async def next_task(self) -> bool:
        """Move to the next task."""
        await self._send({
            "type": MessageType.NEXT_TASK.value
        })
        return True

    async def select_task(self, task_index: int) -> bool:
        """Select a specific task."""
        await self._send({
            "type": MessageType.SELECT_TASK.value,
            "task_index": task_index
        })
        return True

    async def retry(self) -> bool:
        """Retry the current vote."""
        await self._send({
            "type": MessageType.RETRY.value
        })
        return True

    async def skip(self) -> bool:
        """Skip the current task."""
        await self._send({
            "type": MessageType.SKIP.value
        })
        return True

    async def end_session(self) -> bool:
        """End the session."""
        await self._send({
            "type": MessageType.END_SESSION.value
        })
        return True
