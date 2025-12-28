"""
Planning Poker session state management.

Defines the data structures for poker sessions, settings, and voting rounds.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
import secrets
import statistics


class SessionState(Enum):
    """State of the poker session."""
    WAITING = "waiting"           # Waiting for participants
    VOTING = "voting"             # Voting in progress
    REVEALED = "revealed"         # Votes revealed
    DISTRIBUTING = "distributing" # Task distribution in progress
    FINISHED = "finished"         # Session ended


@dataclass
class SessionSettings:
    """Configuration for a poker session."""
    auto_update_jira: bool = False       # Auto-update Jira after each vote
    confirm_each: bool = True            # Ask for confirmation each time
    batch_update: bool = False           # Only update at session end
    min_participants: int = 2            # Minimum participants to start
    vote_timeout: int = 60               # Seconds, 0 = unlimited
    fibonacci: List[int] = field(default_factory=lambda: [1, 2, 3, 5, 8, 13, 21])
    allow_question_mark: bool = True     # Allow "?" vote for uncertain
    divergence_threshold: int = 8        # Points difference to trigger discussion
    expected_participants: List[str] = field(default_factory=list)  # Team members from integration
    ai_enabled: bool = True              # Enable AI voter participant


@dataclass
class VotingRound:
    """A single voting round for a task."""
    task_key: str
    task_summary: str
    task_description: str = ""
    current_points: Optional[float] = None
    votes: Dict[str, Optional[int]] = field(default_factory=dict)
    final_points: Optional[int] = None
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    retry_count: int = 0

    def add_vote(self, participant: str, vote: Optional[int]):
        """Add or update a vote."""
        self.votes[participant] = vote

    def get_statistics(self) -> Dict[str, Any]:
        """Calculate voting statistics."""
        # Filter out None/"?" votes
        numeric_votes = [v for v in self.votes.values() if v is not None]

        if not numeric_votes:
            return {
                "count": len(self.votes),
                "numeric_count": 0,
                "average": None,
                "median": None,
                "min": None,
                "max": None,
                "divergence": 0,
                "has_question_marks": any(v is None for v in self.votes.values())
            }

        return {
            "count": len(self.votes),
            "numeric_count": len(numeric_votes),
            "average": round(statistics.mean(numeric_votes), 1),
            "median": statistics.median(numeric_votes),
            "min": min(numeric_votes),
            "max": max(numeric_votes),
            "divergence": max(numeric_votes) - min(numeric_votes),
            "has_question_marks": any(v is None for v in self.votes.values())
        }

    def is_divergent(self, threshold: int = 8) -> bool:
        """Check if votes are too divergent."""
        stats = self.get_statistics()
        return stats["divergence"] >= threshold

    def all_voted(self, participant_count: int) -> bool:
        """Check if all participants have voted."""
        return len(self.votes) >= participant_count


@dataclass
class Task:
    """A task to be estimated."""
    key: str
    summary: str
    description: str = ""
    current_points: Optional[float] = None
    url: Optional[str] = None


@dataclass
class TaskAssignment:
    """Tracks task assignment during distribution phase."""
    task_key: str
    task_summary: str
    final_points: Optional[int] = None
    claimed_by: Optional[str] = None        # Participant name who claimed
    claimed_by_id: Optional[str] = None     # Account ID (for task management)
    confirmed: bool = False                  # Leader confirmed this assignment
    skipped: bool = False                    # Leader skipped distribution


class PokerSession:
    """
    Manages a Planning Poker session.

    Tracks participants, tasks, voting rounds, and session state.
    """

    def __init__(
        self,
        leader_name: str,
        tasks: List[Task],
        settings: Optional[SessionSettings] = None
    ):
        self.session_id = self._generate_session_id()
        self.leader_name = leader_name
        self.tasks = tasks
        self.settings = settings or SessionSettings()
        self.state = SessionState.WAITING
        self.created_at = datetime.now().isoformat()

        # Participants: {client_id: name}
        self.participants: Dict[str, str] = {}

        # Current task index
        self.current_task_index = 0

        # Current voting round
        self.current_round: Optional[VotingRound] = None

        # Completed rounds
        self.completed_rounds: List[VotingRound] = []

        # Distribution state
        self.distribution_assignments: Dict[str, TaskAssignment] = {}
        self.current_distribution_index: int = 0
        self.participant_user_ids: Dict[str, str] = {}  # participant_name -> account_id

    def _generate_session_id(self) -> str:
        """Generate a unique session ID."""
        return f"poker-{secrets.token_hex(4)}"

    def add_participant(self, client_id: str, name: str) -> bool:
        """Add a participant to the session."""
        if client_id in self.participants:
            return False
        self.participants[client_id] = name
        return True

    def remove_participant(self, client_id: str) -> Optional[str]:
        """Remove a participant from the session."""
        return self.participants.pop(client_id, None)

    def get_participant_name(self, client_id: str) -> Optional[str]:
        """Get participant name by client ID."""
        return self.participants.get(client_id)

    def get_participant_names(self) -> List[str]:
        """Get all participant names."""
        return list(self.participants.values())

    def get_participant_count(self) -> int:
        """Get number of participants."""
        return len(self.participants)

    def can_start(self) -> bool:
        """Check if session can start voting."""
        return (
            self.state == SessionState.WAITING and
            len(self.participants) >= self.settings.min_participants and
            len(self.tasks) > 0
        )

    def get_current_task(self) -> Optional[Task]:
        """Get the current task being voted on."""
        if 0 <= self.current_task_index < len(self.tasks):
            return self.tasks[self.current_task_index]
        return None

    def start_voting(self, task_index: Optional[int] = None) -> bool:
        """Start voting on a task."""
        if task_index is not None:
            if 0 <= task_index < len(self.tasks):
                self.current_task_index = task_index
            else:
                return False

        task = self.get_current_task()
        if not task:
            return False

        self.current_round = VotingRound(
            task_key=task.key,
            task_summary=task.summary,
            task_description=task.description,
            current_points=task.current_points,
            started_at=datetime.now().isoformat()
        )
        self.state = SessionState.VOTING
        return True

    def submit_vote(self, client_id: str, vote: Optional[int]) -> bool:
        """Submit a vote from a participant."""
        if self.state != SessionState.VOTING:
            return False
        if self.current_round is None:
            return False
        if client_id not in self.participants:
            return False

        name = self.participants[client_id]
        self.current_round.add_vote(name, vote)
        return True

    def get_vote_progress(self) -> Dict[str, Any]:
        """Get current voting progress."""
        if not self.current_round:
            return {"voted": 0, "total": len(self.participants)}

        return {
            "voted": len(self.current_round.votes),
            "total": len(self.participants),
            "all_voted": self.current_round.all_voted(len(self.participants))
        }

    def reveal_votes(self) -> Optional[Dict[str, Any]]:
        """Reveal all votes and calculate statistics."""
        if self.state != SessionState.VOTING:
            return None
        if not self.current_round:
            return None

        self.state = SessionState.REVEALED
        self.current_round.finished_at = datetime.now().isoformat()

        stats = self.current_round.get_statistics()
        return {
            "votes": self.current_round.votes.copy(),
            "statistics": stats,
            "is_divergent": self.current_round.is_divergent(
                self.settings.divergence_threshold
            )
        }

    def set_final_points(self, points: int) -> bool:
        """Set the final story points for the current task."""
        if not self.current_round:
            return False

        self.current_round.final_points = points

        # Update task
        task = self.get_current_task()
        if task:
            task.current_points = points

        # Move to completed
        self.completed_rounds.append(self.current_round)
        self.current_round = None
        self.state = SessionState.WAITING

        return True

    def retry_voting(self) -> bool:
        """Retry voting on the current task."""
        if not self.current_round:
            return False

        self.current_round.votes = {}
        self.current_round.retry_count += 1
        self.current_round.started_at = datetime.now().isoformat()
        self.current_round.finished_at = None
        self.state = SessionState.VOTING
        return True

    def skip_task(self) -> bool:
        """Skip the current task without setting points."""
        if self.current_round:
            self.current_round = None
        self.state = SessionState.WAITING
        return True

    def next_task(self) -> Optional[Task]:
        """Move to the next task."""
        self.current_task_index += 1
        return self.get_current_task()

    def select_task(self, task_index: int) -> Optional[Task]:
        """Select a specific task by index."""
        if 0 <= task_index < len(self.tasks):
            self.current_task_index = task_index
            return self.get_current_task()
        return None

    def get_unestimated_tasks(self) -> List[Task]:
        """Get tasks that haven't been estimated yet."""
        estimated_keys = {r.task_key for r in self.completed_rounds}
        return [t for t in self.tasks if t.key not in estimated_keys]

    def finish_session(self) -> Dict[str, Any]:
        """Finish the session and return summary."""
        self.state = SessionState.FINISHED

        total_points = sum(
            r.final_points or 0 for r in self.completed_rounds
        )

        return {
            "session_id": self.session_id,
            "leader": self.leader_name,
            "participants": self.get_participant_names(),
            "tasks_estimated": len(self.completed_rounds),
            "tasks_total": len(self.tasks),
            "total_points": total_points,
            "rounds": [
                {
                    "task_key": r.task_key,
                    "task_summary": r.task_summary,
                    "final_points": r.final_points
                }
                for r in self.completed_rounds
            ],
            "created_at": self.created_at,
            "finished_at": datetime.now().isoformat()
        }

    def to_dict(self) -> Dict[str, Any]:
        """Serialize session to dict."""
        return {
            "session_id": self.session_id,
            "leader_name": self.leader_name,
            "state": self.state.value,
            "participants": self.get_participant_names(),
            "current_task_index": self.current_task_index,
            "tasks_count": len(self.tasks),
            "completed_count": len(self.completed_rounds),
            "settings": {
                "min_participants": self.settings.min_participants,
                "vote_timeout": self.settings.vote_timeout,
                "fibonacci": self.settings.fibonacci,
                "allow_question_mark": self.settings.allow_question_mark
            }
        }

    # =========================================================================
    # TASK DISTRIBUTION METHODS
    # =========================================================================

    def start_distribution(self) -> bool:
        """Start task distribution phase."""
        if not self.completed_rounds:
            return False

        self.state = SessionState.DISTRIBUTING
        self.current_distribution_index = 0

        # Initialize assignments from completed rounds
        self.distribution_assignments = {
            r.task_key: TaskAssignment(
                task_key=r.task_key,
                task_summary=r.task_summary,
                final_points=r.final_points
            )
            for r in self.completed_rounds
        }

        return True

    def get_distributable_tasks(self) -> List[VotingRound]:
        """Get completed rounds that can be distributed."""
        return self.completed_rounds.copy()

    def claim_task(
        self,
        task_key: str,
        participant_name: str,
        account_id: Optional[str] = None
    ) -> bool:
        """
        Record a claim for a task.

        Returns True if claim was accepted (task not already claimed).
        """
        if self.state != SessionState.DISTRIBUTING:
            return False

        assignment = self.distribution_assignments.get(task_key)
        if not assignment:
            return False

        # Already claimed by someone else
        if assignment.claimed_by and assignment.claimed_by != participant_name:
            return False

        assignment.claimed_by = participant_name
        assignment.claimed_by_id = account_id
        return True

    def confirm_claim(self, task_key: str) -> bool:
        """Leader confirms a task claim."""
        assignment = self.distribution_assignments.get(task_key)
        if not assignment or not assignment.claimed_by:
            return False

        assignment.confirmed = True
        self.current_distribution_index += 1
        return True

    def reassign_task(
        self,
        task_key: str,
        participant_name: str,
        account_id: Optional[str] = None
    ) -> bool:
        """Leader assigns/reassigns a task to a participant."""
        assignment = self.distribution_assignments.get(task_key)
        if not assignment:
            return False

        assignment.claimed_by = participant_name
        assignment.claimed_by_id = account_id
        assignment.confirmed = True
        self.current_distribution_index += 1
        return True

    def skip_task_distribution(self, task_key: str) -> bool:
        """Skip distribution for a task (leave unassigned)."""
        assignment = self.distribution_assignments.get(task_key)
        if not assignment:
            return False

        assignment.skipped = True
        assignment.confirmed = True
        self.current_distribution_index += 1
        return True

    def get_current_distribution_task(self) -> Optional[TaskAssignment]:
        """Get the current task being distributed."""
        if self.state != SessionState.DISTRIBUTING:
            return None

        # Find next unconfirmed task
        for assignment in self.distribution_assignments.values():
            if not assignment.confirmed and not assignment.skipped:
                return assignment

        return None

    def get_next_undistributed_task(self) -> Optional[VotingRound]:
        """Get next completed round that hasn't been distributed yet."""
        for r in self.completed_rounds:
            assignment = self.distribution_assignments.get(r.task_key)
            if assignment and not assignment.confirmed and not assignment.skipped:
                return r
        return None

    def is_distribution_complete(self) -> bool:
        """Check if all tasks have been distributed or skipped."""
        if not self.distribution_assignments:
            return True

        return all(
            a.confirmed or a.skipped
            for a in self.distribution_assignments.values()
        )

    def get_distribution_summary(self) -> Dict[str, Any]:
        """Get summary of task assignments."""
        assignments = []
        assigned_count = 0
        skipped_count = 0

        for task_key, assignment in self.distribution_assignments.items():
            entry = {
                "task_key": assignment.task_key,
                "task_summary": assignment.task_summary,
                "final_points": assignment.final_points,
                "assigned_to": assignment.claimed_by,
                "account_id": assignment.claimed_by_id,
                "skipped": assignment.skipped
            }
            assignments.append(entry)

            if assignment.skipped:
                skipped_count += 1
            elif assignment.claimed_by:
                assigned_count += 1

        return {
            "assignments": assignments,
            "assigned_count": assigned_count,
            "skipped_count": skipped_count,
            "total_count": len(self.distribution_assignments)
        }
