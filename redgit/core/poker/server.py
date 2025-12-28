"""
Planning Poker WebSocket server.

Handles real-time communication between leader and participants.
"""

import asyncio
import json
import logging
from enum import Enum
from typing import Dict, Optional, Any, Callable
from dataclasses import dataclass

try:
    import websockets
    from websockets.server import serve, WebSocketServerProtocol
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    WebSocketServerProtocol = Any

from .session import PokerSession, SessionState
from .ai_voter import AIVoter, AIEstimate

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """WebSocket message types."""
    # Server -> Client
    WELCOME = "welcome"
    PARTICIPANT_JOINED = "participant_joined"
    PARTICIPANT_LEFT = "participant_left"
    VOTING_STARTED = "voting_started"
    VOTE_COUNT_UPDATE = "vote_count_update"
    VOTING_REVEALED = "voting_revealed"
    POINTS_SET = "points_set"
    TASK_CHANGED = "task_changed"
    SESSION_ENDED = "session_ended"
    ERROR = "error"

    # Task Distribution (Server -> Client)
    DISTRIBUTION_STARTED = "distribution_started"
    TASK_OFFER = "task_offer"
    TASK_CLAIMED = "task_claimed"
    TASK_ASSIGNED = "task_assigned"
    DISTRIBUTION_COMPLETE = "distribution_complete"

    # Client -> Server
    JOIN = "join"
    VOTE = "vote"
    CLAIM_TASK = "claim_task"  # Participant claims a task

    # Leader only
    START_VOTING = "start_voting"
    REVEAL = "reveal"
    SET_POINTS = "set_points"
    NEXT_TASK = "next_task"
    SELECT_TASK = "select_task"
    RETRY = "retry"
    SKIP = "skip"
    END_SESSION = "end_session"


@dataclass
class ConnectedClient:
    """Represents a connected client."""
    client_id: str
    websocket: WebSocketServerProtocol
    name: Optional[str] = None
    is_leader: bool = False


class PokerServer:
    """
    WebSocket server for Planning Poker sessions.

    Manages client connections and routes messages between
    the leader and participants.
    """

    def __init__(self, session: PokerSession, port: int = 8765, config: dict = None):
        if not WEBSOCKETS_AVAILABLE:
            raise ImportError(
                "websockets package is required. Install with: pip install websockets"
            )

        self.session = session
        self.port = port
        self.clients: Dict[str, ConnectedClient] = {}
        self._server = None
        self._running = False

        # AI voter (optional)
        self.ai_voter: Optional[AIVoter] = None
        if session.settings.ai_enabled:
            try:
                self.ai_voter = AIVoter(config)
                self.ai_voter.set_fibonacci(session.settings.fibonacci)
            except Exception as e:
                logger.warning(f"AI voter disabled: {e}")

        # Callback for session events
        self.on_session_event: Optional[Callable[[str, Dict], None]] = None

    async def start(self):
        """Start the WebSocket server."""
        # Configure ping/pong settings for long-running sessions
        # ping_interval=30: Send ping every 30 seconds
        # ping_timeout=60: Wait up to 60 seconds for pong response
        self._server = await serve(
            self._handle_connection,
            "0.0.0.0",
            self.port,
            ping_interval=30,
            ping_timeout=60
        )
        self._running = True
        logger.info(f"Poker server started on port {self.port}")

    async def stop(self):
        """Stop the WebSocket server."""
        self._running = False

        # Gracefully close all client connections
        for client_id, client in list(self.clients.items()):
            try:
                await client.websocket.close(1000, "Server shutting down")
            except Exception:
                pass  # Ignore errors when closing

        # Clear clients
        self.clients.clear()

        # Stop the server
        if self._server:
            self._server.close()
            await self._server.wait_closed()
            logger.info("Poker server stopped")

    async def _handle_connection(self, websocket: WebSocketServerProtocol):
        """Handle a new WebSocket connection."""
        client_id = str(id(websocket))
        client = ConnectedClient(client_id=client_id, websocket=websocket)
        self.clients[client_id] = client

        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self._handle_message(client, data)
                except json.JSONDecodeError:
                    await self._send_error(websocket, "Invalid JSON")
                except Exception as e:
                    logger.error(f"Error handling message: {e}")
                    await self._send_error(websocket, str(e))
        finally:
            await self._handle_disconnect(client)

    async def _handle_message(self, client: ConnectedClient, data: Dict):
        """Route a message to the appropriate handler."""
        msg_type = data.get("type", "")

        handlers = {
            MessageType.JOIN.value: self._handle_join,
            MessageType.VOTE.value: self._handle_vote,
            MessageType.START_VOTING.value: self._handle_start_voting,
            MessageType.REVEAL.value: self._handle_reveal,
            MessageType.SET_POINTS.value: self._handle_set_points,
            MessageType.NEXT_TASK.value: self._handle_next_task,
            MessageType.SELECT_TASK.value: self._handle_select_task,
            MessageType.RETRY.value: self._handle_retry,
            MessageType.SKIP.value: self._handle_skip,
            MessageType.END_SESSION.value: self._handle_end_session,
            # Distribution handlers
            MessageType.CLAIM_TASK.value: self._handle_claim_task,
        }

        handler = handlers.get(msg_type)
        if handler:
            await handler(client, data)
        else:
            await self._send_error(client.websocket, f"Unknown message type: {msg_type}")

    async def _handle_join(self, client: ConnectedClient, data: Dict):
        """Handle participant joining."""
        name = data.get("name", "").strip()
        if not name:
            await self._send_error(client.websocket, "Name is required")
            return

        # Check if name already taken
        existing_names = self.session.get_participant_names()
        if name in existing_names:
            await self._send_error(client.websocket, "Name already taken")
            return

        # Add participant
        client.name = name
        self.session.add_participant(client.client_id, name)

        # Send welcome message
        await self._send(client.websocket, {
            "type": MessageType.WELCOME.value,
            "session_id": self.session.session_id,
            "leader": self.session.leader_name,
            "participants": self.session.get_participant_names(),
            "state": self.session.state.value,
            "current_task": self._serialize_current_task()
        })

        # Notify others
        await self._broadcast({
            "type": MessageType.PARTICIPANT_JOINED.value,
            "name": name,
            "participants": self.session.get_participant_names(),
            "count": self.session.get_participant_count()
        }, exclude=client.client_id)

        self._emit_event("participant_joined", {"name": name})

    async def _handle_vote(self, client: ConnectedClient, data: Dict):
        """Handle vote submission."""
        if not client.name:
            await self._send_error(client.websocket, "Not joined")
            return

        vote = data.get("vote")  # int or None for "?"

        if self.session.submit_vote(client.client_id, vote):
            progress = self.session.get_vote_progress()

            # Notify all about vote count (not values)
            await self._broadcast({
                "type": MessageType.VOTE_COUNT_UPDATE.value,
                "voted": progress["voted"],
                "total": progress["total"],
                "all_voted": progress["all_voted"]
            })

            self._emit_event("vote_submitted", {
                "participant": client.name,
                "progress": progress
            })
        else:
            await self._send_error(client.websocket, "Cannot vote now")

    async def _handle_start_voting(self, client: ConnectedClient, data: Dict):
        """Handle leader starting voting."""
        if not client.is_leader:
            await self._send_error(client.websocket, "Only leader can start voting")
            return

        task_index = data.get("task_index")

        if self.session.start_voting(task_index):
            task = self.session.get_current_task()

            # Start AI estimation in parallel
            if self.ai_voter and task:
                self.ai_voter.start_estimation(
                    task.key,
                    task.summary,
                    task.description,
                    task.current_points
                )

            await self._broadcast({
                "type": MessageType.VOTING_STARTED.value,
                "task": self._serialize_current_task(),
                "fibonacci": self.session.settings.fibonacci,
                "allow_question_mark": self.session.settings.allow_question_mark,
                "timeout": self.session.settings.vote_timeout
            })

            self._emit_event("voting_started", {"task_key": task.key if task else None})
        else:
            await self._send_error(client.websocket, "Cannot start voting")

    async def _handle_reveal(self, client: ConnectedClient, data: Dict):
        """Handle leader revealing votes."""
        if not client.is_leader:
            await self._send_error(client.websocket, "Only leader can reveal")
            return

        result = self.session.reveal_votes()
        if result:
            # Get AI vote and reasoning
            ai_vote = None
            ai_reasoning = None
            ai_confidence = None
            ai_factors = []

            if self.ai_voter:
                try:
                    estimate = await self.ai_voter.get_estimate()
                    if estimate:
                        ai_vote = estimate.points
                        ai_reasoning = estimate.reasoning
                        ai_confidence = estimate.confidence
                        ai_factors = estimate.factors
                        # Add AI vote to results
                        result["votes"][AIVoter.NAME] = ai_vote
                except Exception as e:
                    logger.warning(f"Failed to get AI estimate: {e}")

            await self._broadcast({
                "type": MessageType.VOTING_REVEALED.value,
                "votes": result["votes"],
                "statistics": result["statistics"],
                "is_divergent": result["is_divergent"],
                "divergence_threshold": self.session.settings.divergence_threshold,
                "ai_reasoning": ai_reasoning,
                "ai_confidence": ai_confidence,
                "ai_factors": ai_factors
            })

            self._emit_event("votes_revealed", result)
        else:
            await self._send_error(client.websocket, "Cannot reveal now")

    async def _handle_set_points(self, client: ConnectedClient, data: Dict):
        """Handle leader setting final points."""
        if not client.is_leader:
            await self._send_error(client.websocket, "Only leader can set points")
            return

        points = data.get("points")
        if points is None:
            await self._send_error(client.websocket, "Points required")
            return

        task = self.session.get_current_task()
        if self.session.set_final_points(int(points)):
            await self._broadcast({
                "type": MessageType.POINTS_SET.value,
                "task_key": task.key if task else None,
                "points": points,
                "remaining_tasks": len(self.session.get_unestimated_tasks())
            })

            self._emit_event("points_set", {
                "task_key": task.key if task else None,
                "points": points
            })
        else:
            await self._send_error(client.websocket, "Cannot set points now")

    async def _handle_next_task(self, client: ConnectedClient, data: Dict):
        """Handle leader moving to next task."""
        if not client.is_leader:
            await self._send_error(client.websocket, "Only leader can change task")
            return

        task = self.session.next_task()
        if task:
            await self._broadcast({
                "type": MessageType.TASK_CHANGED.value,
                "task": self._serialize_task(task),
                "index": self.session.current_task_index,
                "total": len(self.session.tasks)
            })

            self._emit_event("task_changed", {"task_key": task.key})
        else:
            # No more tasks
            await self._send(client.websocket, {
                "type": MessageType.TASK_CHANGED.value,
                "task": None,
                "no_more_tasks": True
            })

    async def _handle_select_task(self, client: ConnectedClient, data: Dict):
        """Handle leader selecting a specific task."""
        if not client.is_leader:
            await self._send_error(client.websocket, "Only leader can select task")
            return

        task_index = data.get("task_index")
        if task_index is None:
            await self._send_error(client.websocket, "Task index required")
            return

        task = self.session.select_task(int(task_index))
        if task:
            await self._broadcast({
                "type": MessageType.TASK_CHANGED.value,
                "task": self._serialize_task(task),
                "index": self.session.current_task_index,
                "total": len(self.session.tasks)
            })
        else:
            await self._send_error(client.websocket, "Invalid task index")

    async def _handle_retry(self, client: ConnectedClient, data: Dict):
        """Handle leader retrying current vote."""
        if not client.is_leader:
            await self._send_error(client.websocket, "Only leader can retry")
            return

        if self.session.retry_voting():
            task = self.session.get_current_task()

            await self._broadcast({
                "type": MessageType.VOTING_STARTED.value,
                "task": self._serialize_current_task(),
                "fibonacci": self.session.settings.fibonacci,
                "allow_question_mark": self.session.settings.allow_question_mark,
                "timeout": self.session.settings.vote_timeout,
                "is_retry": True
            })

            self._emit_event("voting_retried", {"task_key": task.key if task else None})
        else:
            await self._send_error(client.websocket, "Cannot retry now")

    async def _handle_skip(self, client: ConnectedClient, data: Dict):
        """Handle leader skipping current task."""
        if not client.is_leader:
            await self._send_error(client.websocket, "Only leader can skip")
            return

        task = self.session.get_current_task()
        self.session.skip_task()

        await self._broadcast({
            "type": MessageType.TASK_CHANGED.value,
            "task": None,
            "skipped_task": task.key if task else None
        })

        self._emit_event("task_skipped", {"task_key": task.key if task else None})

    async def _handle_end_session(self, client: ConnectedClient, data: Dict):
        """Handle leader ending the session."""
        if not client.is_leader:
            await self._send_error(client.websocket, "Only leader can end session")
            return

        summary = self.session.finish_session()

        await self._broadcast({
            "type": MessageType.SESSION_ENDED.value,
            "summary": summary
        })

        self._emit_event("session_ended", summary)

    async def _handle_disconnect(self, client: ConnectedClient):
        """Handle client disconnection."""
        # Check if client still exists (might be cleared by stop())
        if client.client_id not in self.clients:
            return

        if client.name:
            self.session.remove_participant(client.client_id)

            await self._broadcast({
                "type": MessageType.PARTICIPANT_LEFT.value,
                "name": client.name,
                "participants": self.session.get_participant_names(),
                "count": self.session.get_participant_count()
            })

            self._emit_event("participant_left", {"name": client.name})

        if client.client_id in self.clients:
            del self.clients[client.client_id]

    async def _send(self, websocket: WebSocketServerProtocol, data: Dict):
        """Send a message to a client."""
        if not self._running:
            return  # Don't try to send if server is stopping

        try:
            await websocket.send(json.dumps(data))
        except Exception as e:
            # Only log if it's not a connection closed error
            error_name = type(e).__name__
            if "ConnectionClosed" not in error_name:
                logger.error(f"Failed to send message: {e}")

    async def _send_error(self, websocket: WebSocketServerProtocol, message: str):
        """Send an error message to a client."""
        await self._send(websocket, {
            "type": MessageType.ERROR.value,
            "message": message
        })

    async def _broadcast(self, data: Dict, exclude: Optional[str] = None):
        """Broadcast a message to all clients."""
        for client_id, client in self.clients.items():
            if client_id != exclude:
                await self._send(client.websocket, data)

    def _serialize_current_task(self) -> Optional[Dict]:
        """Serialize the current task for transmission."""
        task = self.session.get_current_task()
        return self._serialize_task(task) if task else None

    def _serialize_task(self, task) -> Dict:
        """Serialize a task for transmission."""
        return {
            "key": task.key,
            "summary": task.summary,
            "description": task.description,
            "current_points": task.current_points,
            "url": task.url
        }

    def _emit_event(self, event: str, data: Dict):
        """Emit a session event."""
        if self.on_session_event:
            self.on_session_event(event, data)

    def register_leader(self, client_id: str):
        """Register a client as the leader."""
        if client_id in self.clients:
            self.clients[client_id].is_leader = True
            self.clients[client_id].name = self.session.leader_name

    # =========================================================================
    # TASK DISTRIBUTION HANDLERS
    # =========================================================================

    async def _handle_claim_task(self, client: ConnectedClient, data: Dict):
        """Handle participant claiming a task."""
        task_key = data.get("task_key")
        account_id = data.get("account_id")  # Participant's account ID if available

        if not client.name:
            await self._send_error(client.websocket, "Not joined")
            return

        if self.session.state != SessionState.DISTRIBUTING:
            await self._send_error(client.websocket, "Not in distribution phase")
            return

        if self.session.claim_task(task_key, client.name, account_id):
            # Broadcast claim to all participants
            await self._broadcast({
                "type": MessageType.TASK_CLAIMED.value,
                "task_key": task_key,
                "claimed_by": client.name
            })
            self._emit_event("task_claimed", {"task_key": task_key, "claimed_by": client.name})
        else:
            await self._send_error(client.websocket, "Task already claimed or not available")

    async def start_distribution(self):
        """Start the task distribution phase."""
        if not self.session.start_distribution():
            return False

        await self._broadcast({
            "type": MessageType.DISTRIBUTION_STARTED.value,
            "tasks_count": len(self.session.completed_rounds)
        })

        self._emit_event("distribution_started", {
            "tasks_count": len(self.session.completed_rounds)
        })
        return True

    async def offer_task(self, task_key: str, task_summary: str, final_points: int):
        """Offer a task to all participants for claiming."""
        await self._broadcast({
            "type": MessageType.TASK_OFFER.value,
            "task_key": task_key,
            "task_summary": task_summary,
            "final_points": final_points
        })

    async def broadcast_task_assigned(
        self,
        task_key: str,
        assigned_to: Optional[str],
        skipped: bool = False
    ):
        """Broadcast task assignment result to all participants."""
        await self._broadcast({
            "type": MessageType.TASK_ASSIGNED.value,
            "task_key": task_key,
            "assigned_to": assigned_to,
            "skipped": skipped
        })

    async def complete_distribution(self, summary: Dict):
        """Broadcast distribution completion to all participants."""
        await self._broadcast({
            "type": MessageType.DISTRIBUTION_COMPLETE.value,
            "assignments": summary.get("assignments", []),
            "assigned_count": summary.get("assigned_count", 0),
            "skipped_count": summary.get("skipped_count", 0)
        })

        self._emit_event("distribution_complete", summary)
