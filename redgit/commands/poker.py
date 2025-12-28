"""
Planning Poker CLI commands.

Commands for running planning poker sessions for sprint estimation.
"""

import asyncio
import typer
from typing import Optional, List, Dict
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt, Confirm
from rich.table import Table

from ..core.config import ConfigManager
from ..utils.dependency import ensure_websockets, show_websockets_install_help
from ..integrations.registry import get_task_management, get_tunnel_integration


def get_current_user_name(config: dict) -> Optional[str]:
    """
    Get current user's name from active task management integration.

    Returns:
        User's display name or None if not available.
    """
    task_mgmt = get_task_management(config)
    if not task_mgmt:
        return None

    try:
        user = task_mgmt.get_current_user()
        return user.get("display_name") if user else None
    except Exception:
        return None


def get_team_members_from_integration(config: dict) -> List[Dict]:
    """
    Get team members from active task management integration.

    Returns:
        List of dicts with 'id' and 'name' for each active team member.
    """
    task_mgmt = get_task_management(config)
    if not task_mgmt:
        return []

    try:
        members = task_mgmt.get_team_members()
        return [
            {"id": m.get("id"), "name": m.get("display_name")}
            for m in members
            if m.get("active", True)  # Only active users
        ]
    except Exception:
        return []


def prompt_team_selection(team: List[Dict], leader_name: str, console: Console) -> List[str]:
    """
    Show team selection UI for leader.

    Args:
        team: List of team members from integration
        leader_name: Name of the session leader
        console: Rich console for output

    Returns:
        List of selected team member names.
    """
    if not team:
        console.print("[dim]Could not retrieve team info from integration[/dim]")
        return []

    console.print("\n[bold]Team Members:[/bold]")

    for i, member in enumerate(team, 1):
        marker = "[yellow]*[/yellow]" if member.get("name") == leader_name else " "
        console.print(f"  {marker} {i}. {member.get('name', 'Unknown')}")

    console.print("\n[dim]Press Enter to include all, or enter numbers to exclude (e.g., 2,4)[/dim]")

    exclude = Prompt.ask("Exclude", default="")
    if not exclude.strip():
        return [m.get("name") for m in team if m.get("name")]

    exclude_indices = {int(x.strip()) - 1 for x in exclude.split(",") if x.strip().isdigit()}
    return [m.get("name") for i, m in enumerate(team) if i not in exclude_indices and m.get("name")]

# Lazy imports for poker modules (require websockets)
PokerSession = None
SessionSettings = None
Task = None
SessionState = None
PokerServer = None
MessageType = None
PokerClient = None
LeaderClient = None
ClientState = None
poker_ui = None


def _load_poker_modules() -> bool:
    """
    Lazily load poker modules that require websockets.

    Returns:
        True if modules loaded successfully, False otherwise
    """
    global PokerSession, SessionSettings, Task, SessionState
    global PokerServer, MessageType, PokerClient, LeaderClient, ClientState
    global poker_ui

    if PokerSession is not None:
        return True  # Already loaded

    try:
        from ..core.poker.session import PokerSession as _PS, SessionSettings as _SS, Task as _T, SessionState as _State
        from ..core.poker.server import PokerServer as _Server, MessageType as _MT
        from ..core.poker.client import PokerClient as _Client, LeaderClient as _LC, ClientState as _CS
        from ..core.poker import ui as _ui

        PokerSession = _PS
        SessionSettings = _SS
        Task = _T
        SessionState = _State
        PokerServer = _Server
        MessageType = _MT
        PokerClient = _Client
        LeaderClient = _LC
        ClientState = _CS
        poker_ui = _ui
        return True
    except ImportError:
        return False

console = Console()
poker_app = typer.Typer(help="Planning Poker for sprint estimation")


def _get_tasks_from_jira(
    config: dict,
    sprint: Optional[str] = None,
    issues: Optional[str] = None
) -> List[Task]:
    """Get tasks from Jira for estimation."""
    jira = get_task_management(config)
    if not jira:
        return []

    tasks = []

    if issues:
        # Get specific issues
        issue_keys = [k.strip() for k in issues.split(",")]
        for key in issue_keys:
            issue = jira.get_issue(key)
            if issue:
                tasks.append(Task(
                    key=issue.key,
                    summary=issue.summary,
                    description=issue.description or "",
                    current_points=issue.story_points,
                    url=issue.url
                ))
    elif sprint:
        # Get sprint issues
        if sprint.lower() == "active":
            active_sprint = jira.get_active_sprint()
            if active_sprint:
                sprint_id = active_sprint.id
            else:
                return []
        else:
            sprint_id = sprint

        issues_list = jira.get_sprint_issues(sprint_id)
        for issue in issues_list:
            tasks.append(Task(
                key=issue.key,
                summary=issue.summary,
                description=issue.description or "",
                current_points=issue.story_points,
                url=issue.url
            ))
    else:
        # Get unestimated backlog items
        my_issues = jira.get_my_active_issues()
        for issue in my_issues:
            if issue.story_points is None:
                tasks.append(Task(
                    key=issue.key,
                    summary=issue.summary,
                    description=issue.description or "",
                    current_points=None,
                    url=issue.url
                ))

    return tasks


async def _run_leader_session(
    session: PokerSession,
    server: PokerServer,
    tunnel_url: Optional[str],
    config: dict
):
    """Run the leader session loop."""
    jira = get_task_management(config)

    console.print(f"\n[bold green]Session started![/bold green]")
    console.print(f"   Session ID: [cyan]{session.session_id}[/cyan]")

    if tunnel_url:
        console.print(f"   Public URL: [cyan]{tunnel_url}[/cyan]")
        console.print(f"\n[dim]Participants can join with:[/dim]")
        console.print(f"   rg poker join {session.session_id}")
        console.print(f"   rg poker join {tunnel_url}")
    else:
        console.print(f"   Local URL: ws://localhost:{server.port}")

    console.print(f"\n[dim]Waiting for participants ({session.settings.min_participants} minimum)...[/dim]")
    console.print("[dim]Press Ctrl+C to cancel[/dim]\n")

    # Wait for participants
    while session.get_participant_count() < session.settings.min_participants:
        await asyncio.sleep(1)

        # Show joined participants
        participants = session.get_participant_names()
        if participants:
            console.print(f"\r[green]Participants ({len(participants)}):[/green] {', '.join(participants)}    ", end="")

    console.print("\n")

    # Main session loop
    try:
        while session.state != SessionState.FINISHED:
            if session.state == SessionState.WAITING:
                # Show task list
                tasks_data = [
                    {"key": t.key, "summary": t.summary, "current_points": t.current_points}
                    for t in session.tasks
                ]
                completed_keys = [r.task_key for r in session.completed_rounds]

                console.print(poker_ui.render_task_list(
                    tasks_data,
                    completed_keys,
                    session.current_task_index
                ))

                # Check if all done
                unestimated = session.get_unestimated_tasks()
                if not unestimated:
                    if Confirm.ask("All tasks estimated. End session?"):
                        break
                    continue

                # Ask which task to vote on
                console.print("\n[bold]Actions:[/bold]")
                console.print("  [S] Start voting on current task")
                console.print("  [N] Next task")
                console.print("  [1-9] Select task by number")
                console.print("  [L] List participants")
                console.print("  [E] End session")
                console.print("  [D] Distribute tasks and end")

                action = Prompt.ask("\nAction", default="S").upper()

                if action == "S":
                    session.start_voting()

                    # Broadcast voting started
                    task = session.get_current_task()

                    # Start AI estimation in parallel
                    if server.ai_voter and task:
                        server.ai_voter.start_estimation(
                            task.key,
                            task.summary,
                            task.description,
                            task.current_points
                        )
                    await server._broadcast({
                        "type": MessageType.VOTING_STARTED.value,
                        "task": server._serialize_task(task) if task else None,
                        "fibonacci": session.settings.fibonacci,
                        "allow_question_mark": session.settings.allow_question_mark,
                        "timeout": session.settings.vote_timeout
                    })

                elif action == "N":
                    session.next_task()

                elif action == "L":
                    console.print(poker_ui.render_participants_list(
                        session.get_participant_names(),
                        session.leader_name
                    ))

                elif action == "E":
                    if Confirm.ask("End session?"):
                        break

                elif action == "D":
                    if not session.completed_rounds:
                        console.print("[yellow]No tasks have been estimated yet[/yellow]")
                    elif Confirm.ask("Start task distribution?"):
                        await _run_distribution_phase(session, server, config, console)
                        break

                elif action.isdigit():
                    idx = int(action) - 1
                    if 0 <= idx < len(session.tasks):
                        session.select_task(idx)

            elif session.state == SessionState.VOTING:
                # Show current task
                task = session.get_current_task()
                if task:
                    console.print(poker_ui.render_task_panel({
                        "key": task.key,
                        "summary": task.summary,
                        "description": task.description,
                        "current_points": task.current_points
                    }))

                console.print(f"\n[dim]Waiting for votes...[/dim]")
                console.print("[R] Reveal  [S] Skip  [E] End session\n")

                # Wait for votes or leader action
                while session.state == SessionState.VOTING:
                    progress = session.get_vote_progress()
                    console.print(
                        f"\r[cyan]Votes:[/cyan] {poker_ui.render_vote_progress(progress['voted'], progress['total'])}    ",
                        end=""
                    )

                    # Check if all voted
                    if progress["all_voted"]:
                        console.print("\n[green]All votes in![/green]")
                        if Confirm.ask("Reveal votes?", default=True):
                            result = session.reveal_votes()
                            if result:
                                # Get AI vote and include in broadcast
                                ai_reasoning = None
                                ai_confidence = None
                                ai_factors = []
                                if server.ai_voter:
                                    try:
                                        estimate = await server.ai_voter.get_estimate()
                                        if estimate:
                                            result["votes"]["AI Assistant"] = estimate.points
                                            # Also add to local session for display
                                            if session.current_round:
                                                session.current_round.votes["AI Assistant"] = estimate.points
                                            ai_reasoning = estimate.reasoning
                                            ai_confidence = estimate.confidence
                                            ai_factors = estimate.factors
                                    except Exception:
                                        pass

                                await server._broadcast({
                                    "type": MessageType.VOTING_REVEALED.value,
                                    "votes": result["votes"],
                                    "statistics": result["statistics"],
                                    "is_divergent": result["is_divergent"],
                                    "ai_reasoning": ai_reasoning,
                                    "ai_confidence": ai_confidence,
                                    "ai_factors": ai_factors
                                })
                        break

                    await asyncio.sleep(0.5)

            elif session.state == SessionState.REVEALED:
                # Show results
                if session.current_round:
                    # AI data was already fetched during reveal and stored
                    # in the variables from the VOTING block above

                    console.print(poker_ui.render_results_table(session.current_round.votes))
                    stats = session.current_round.get_statistics()
                    console.print(poker_ui.render_statistics(stats))

                    # Show AI reasoning if available (from the reveal block)
                    if ai_reasoning:
                        console.print(poker_ui.render_ai_reasoning(
                            ai_reasoning,
                            ai_confidence,
                            ai_factors
                        ))

                    # Check divergence
                    if session.current_round.is_divergent(session.settings.divergence_threshold):
                        warning = poker_ui.render_divergence_warning(
                            session.current_round.votes,
                            session.settings.divergence_threshold
                        )
                        if warning:
                            console.print(warning)

                    # Get final points
                    points = poker_ui.prompt_final_points(stats, session.settings.fibonacci)

                    if points == -1:
                        # Re-vote
                        session.retry_voting()
                        await server._broadcast({
                            "type": MessageType.VOTING_STARTED.value,
                            "task": server._serialize_current_task(),
                            "fibonacci": session.settings.fibonacci,
                            "allow_question_mark": session.settings.allow_question_mark,
                            "is_retry": True
                        })
                    else:
                        task = session.get_current_task()
                        session.set_final_points(points)

                        # Update Jira if configured
                        if jira and task:
                            should_update = False
                            if session.settings.auto_update_jira:
                                should_update = True
                            elif session.settings.confirm_each:
                                should_update = Confirm.ask(
                                    f"Update {task.key} in Jira with {points} points?"
                                )

                            if should_update:
                                try:
                                    if hasattr(jira, 'set_story_points'):
                                        jira.set_story_points(task.key, points)
                                        console.print(f"[green]Updated {task.key} in Jira[/green]")
                                except Exception as e:
                                    console.print(f"[red]Failed to update Jira: {e}[/red]")

                        await server._broadcast({
                            "type": MessageType.POINTS_SET.value,
                            "task_key": task.key if task else None,
                            "points": points
                        })

    except KeyboardInterrupt:
        console.print("\n[yellow]Session interrupted[/yellow]")

    # End session
    summary = session.finish_session()
    await server._broadcast({
        "type": MessageType.SESSION_ENDED.value,
        "summary": summary
    })

    console.print(poker_ui.render_session_summary(summary))

    # Offer sprint creation (if not already done via distribution)
    if session.state != SessionState.FINISHED:
        from ..utils.notifications import NotificationService
        notifier = NotificationService(config)
        await _offer_sprint_creation(session, jira, notifier, console)

    # Batch update Jira if configured
    if jira and session.settings.batch_update:
        if Confirm.ask("Update all tasks in Jira?"):
            for round_info in summary.get("rounds", []):
                if round_info.get("final_points"):
                    try:
                        if hasattr(jira, 'set_story_points'):
                            jira.set_story_points(
                                round_info["task_key"],
                                round_info["final_points"]
                            )
                            console.print(f"[green]Updated {round_info['task_key']}[/green]")
                    except Exception as e:
                        console.print(f"[red]Failed to update {round_info['task_key']}: {e}[/red]")


async def _run_participant_session(client: PokerClient):
    """Run the participant session loop."""

    # Wait for connection
    console.print("[dim]Connecting...[/dim]")

    while client.state == ClientState.CONNECTING:
        await asyncio.sleep(0.1)

    if client.state == ClientState.DISCONNECTED:
        console.print("[red]Failed to connect[/red]")
        return

    console.print(f"[green]Connected![/green]")
    console.print(f"   Session: {client.session.session_id}")
    console.print(f"   Leader: {client.session.leader}")
    console.print(f"   Participants: {', '.join(client.session.participants)}")

    console.print("\n[dim]Waiting for voting to start...[/dim]\n")

    try:
        while client.state not in (ClientState.FINISHED, ClientState.DISCONNECTED):
            if client.state == ClientState.VOTING:
                # Show task
                task = client.session.current_task
                if task:
                    console.print(poker_ui.render_task_panel(task))

                # Check if already voted
                if client.session.my_vote is not None:
                    console.print(f"\n[green]Your vote: {client.session.my_vote}[/green]")
                    console.print("[dim]Waiting for others...[/dim]")
                else:
                    # Get vote
                    vote = poker_ui.prompt_vote(
                        client.session.fibonacci,
                        client.session.allow_question_mark
                    )
                    await client.vote(vote)
                    console.print(f"[green]Vote submitted: {vote if vote else '?'}[/green]")

                # Wait for reveal
                while client.state == ClientState.VOTING:
                    progress_str = poker_ui.render_vote_progress(
                        client.session.voted_count,
                        client.session.total_count
                    )
                    console.print(f"\r[dim]Votes: {progress_str}[/dim]    ", end="")
                    await asyncio.sleep(0.5)

                console.print()

            elif client.state == ClientState.REVEALED:
                # Show results
                console.print(poker_ui.render_results_table(client.session.votes))

                if client.session.statistics:
                    console.print(poker_ui.render_statistics(client.session.statistics))

                # Show AI reasoning if available
                if client.session.ai_reasoning:
                    console.print(poker_ui.render_ai_reasoning(
                        client.session.ai_reasoning,
                        client.session.ai_confidence,
                        client.session.ai_factors
                    ))

                console.print("\n[dim]Waiting for leader decision...[/dim]")

                # Wait for next state
                while client.state == ClientState.REVEALED:
                    await asyncio.sleep(0.5)

            elif client.state == ClientState.JOINED:
                # Waiting for next vote
                console.print("[dim]Waiting for next task...[/dim]")
                while client.state == ClientState.JOINED:
                    await asyncio.sleep(0.5)

            elif client.state == ClientState.DISTRIBUTING:
                # Distribution phase started
                console.print("\n[bold cyan]Task Distribution[/bold cyan]")
                console.print("[dim]Tasks will be offered for claiming...[/dim]")
                while client.state == ClientState.DISTRIBUTING:
                    await asyncio.sleep(0.5)

            elif client.state == ClientState.CLAIMING:
                # Task offered for claiming
                offer = client.session.current_offer
                if offer:
                    console.print(poker_ui.render_task_offer(offer))

                    if poker_ui.prompt_claim_task():
                        # Get my account ID if possible
                        account_id = None
                        my_task_mgmt = get_task_management(config)
                        if my_task_mgmt:
                            try:
                                user = my_task_mgmt.get_current_user()
                                account_id = user.get("id") if user else None
                            except Exception:
                                pass

                        await client.claim_task(offer["task_key"], account_id)
                        console.print("[green]Claim sent![/green]")

                    # Wait for assignment result
                    console.print("[dim]Waiting for leader decision...[/dim]")
                    while client.state == ClientState.CLAIMING:
                        # Check if task was claimed by someone
                        if client.session.current_offer and client.session.current_offer.get("claimed_by"):
                            console.print(f"\r[dim]Claimed by: {client.session.current_offer['claimed_by']}[/dim]    ", end="")
                        await asyncio.sleep(0.5)

                    # Show assignment result
                    if offer:
                        task_key = offer.get("task_key")
                        assigned_to = client.session.assignments.get(task_key)
                        if assigned_to:
                            if assigned_to == client.name:
                                console.print(f"\n[bold green]Assigned to you![/bold green]")
                            else:
                                console.print(f"\n[dim]Assigned to: {assigned_to}[/dim]")
                        else:
                            console.print(f"\n[dim]Skipped[/dim]")

            else:
                await asyncio.sleep(0.5)

    except KeyboardInterrupt:
        console.print("\n[yellow]Disconnected[/yellow]")

    # Show session summary if available
    if client.state == ClientState.FINISHED and client.session.summary:
        console.print("\n[bold green]Session ended by leader[/bold green]")
        console.print(poker_ui.render_session_summary(client.session.summary))

    # Show distribution summary if available
    if client.state == ClientState.FINISHED and client.session.distribution_summary:
        console.print(poker_ui.render_distribution_summary(client.session.distribution_summary))

    await client.disconnect()


def _resolve_participant_ids(
    session: PokerSession,
    config: dict
) -> Dict[str, str]:
    """
    Resolve participant names to task management account IDs.

    Strategy:
    1. Get team members from active task management integration
    2. Match participant names to account IDs (case-insensitive)

    Returns:
        Dict mapping participant_name -> account_id
    """
    task_mgmt = get_task_management(config)
    if not task_mgmt:
        return {}

    participant_ids = {}

    # Get team members from integration
    try:
        team_members = task_mgmt.get_team_members()
    except Exception:
        team_members = []

    if not team_members:
        return {}

    # Create lookup by display name (case-insensitive)
    team_lookup = {
        m.get("display_name", "").lower(): m.get("id")
        for m in team_members
        if m.get("id") and m.get("display_name")
    }

    for participant_name in session.get_participant_names():
        # Try exact match first
        if participant_name.lower() in team_lookup:
            participant_ids[participant_name] = team_lookup[participant_name.lower()]
            continue

        # Try partial match (first name or last name)
        for team_name, account_id in team_lookup.items():
            if participant_name.lower() in team_name or team_name in participant_name.lower():
                participant_ids[participant_name] = account_id
                break

    return participant_ids


async def _offer_sprint_creation(
    session: PokerSession,
    task_mgmt,
    notifier,
    console: Console
):
    """
    Offer sprint creation after estimation/distribution.

    Args:
        session: The poker session with completed rounds
        task_mgmt: Task management integration (may be None)
        notifier: Notification service
        console: Rich console for output
    """
    # Check if we have a task management integration that supports sprints
    if not task_mgmt:
        return

    if not task_mgmt.supports_sprints():
        return

    # Check if we have estimated tasks
    if not session.completed_rounds:
        return

    # Ask leader
    console.print("\n[bold cyan]Sprint Creation[/bold cyan]")
    if not Confirm.ask("Create a new sprint with the estimated tasks?"):
        return

    # Get sprint settings from integration
    date_config = task_mgmt.get_sprint_date_config()

    # Prompt for sprint details
    sprint_settings = poker_ui.prompt_sprint_settings(date_config)
    if not sprint_settings:
        console.print("[dim]Sprint creation cancelled[/dim]")
        return

    # Create the sprint
    console.print("\n[dim]Creating sprint...[/dim]")
    try:
        sprint = task_mgmt.create_sprint(
            name=sprint_settings["name"],
            start_date=sprint_settings.get("start_date"),
            end_date=sprint_settings.get("end_date"),
            goal=sprint_settings.get("goal")
        )
    except Exception as e:
        console.print(f"[red]Failed to create sprint: {e}[/red]")
        return

    if not sprint:
        console.print("[red]Failed to create sprint[/red]")
        return

    console.print(f"[green]Sprint created: {sprint.name}[/green]")

    # Move tasks to sprint
    issue_keys = [r.task_key for r in session.completed_rounds]
    console.print(f"[dim]Moving {len(issue_keys)} tasks to sprint...[/dim]")

    try:
        results = task_mgmt.move_issues_to_sprint(sprint.id, issue_keys)
        success_count = sum(1 for v in results.values() if v)
        console.print(f"[green]Moved {success_count}/{len(issue_keys)} tasks to sprint[/green]")
    except Exception as e:
        console.print(f"[yellow]Failed to move some tasks: {e}[/yellow]")

    # Ask to start the sprint (if dates provided)
    sprint_started = False
    if sprint_settings.get("start_date"):
        if Confirm.ask("Start the sprint now?"):
            try:
                started = task_mgmt.start_sprint(
                    sprint.id,
                    start_date=sprint_settings.get("start_date"),
                    end_date=sprint_settings.get("end_date")
                )
                if started:
                    console.print("[green]Sprint started![/green]")
                    sprint_started = True
                else:
                    console.print("[yellow]Could not start sprint[/yellow]")
            except Exception as e:
                console.print(f"[yellow]Failed to start sprint: {e}[/yellow]")

    # Send notification
    notifier.send_sprint_created(
        leader=session.leader_name,
        sprint_name=sprint.name,
        tasks_count=len(issue_keys),
        total_points=sum(r.final_points or 0 for r in session.completed_rounds),
        started=sprint_started
    )


async def _run_distribution_phase(
    session: PokerSession,
    server: PokerServer,
    config: dict,
    console: Console
):
    """Run the task distribution phase."""
    from ..utils.notifications import NotificationService

    task_mgmt = get_task_management(config)
    notifier = NotificationService(config)

    # Resolve participant IDs
    console.print("\n[dim]Resolving participant IDs...[/dim]")
    participant_ids = _resolve_participant_ids(session, config)
    session.participant_user_ids = participant_ids

    # Report unresolved participants
    unresolved = [
        name for name in session.get_participant_names()
        if name not in participant_ids
    ]
    if unresolved:
        console.print(f"[yellow]Could not resolve IDs for: {', '.join(unresolved)}[/yellow]")
        console.print("[dim]These participants won't be auto-assigned[/dim]")

    # Start distribution
    await server.start_distribution()

    console.print("\n[bold cyan]Task Distribution[/bold cyan]")
    console.print("[dim]Tasks will be offered to participants for claiming[/dim]\n")

    participants = session.get_participant_names()

    # Distribute each task
    while not session.is_distribution_complete():
        current_round = session.get_next_undistributed_task()
        if not current_round:
            break

        task_key = current_round.task_key
        assignment = session.distribution_assignments.get(task_key)

        # Offer task to all participants
        await server.offer_task(
            task_key,
            current_round.task_summary,
            current_round.final_points
        )

        # Show task to leader
        console.print(poker_ui.render_distribution_task_for_leader(
            task_key,
            current_round.task_summary,
            current_round.final_points,
            assignment.claimed_by if assignment else None
        ))

        # Wait briefly for claims
        console.print("\n[dim]Waiting for claims...[/dim]")
        await asyncio.sleep(2)  # Give participants time to claim

        # Check if someone claimed
        assignment = session.distribution_assignments.get(task_key)
        if assignment and assignment.claimed_by:
            console.print(f"[green]Claimed by: {assignment.claimed_by}[/green]")
            console.print("\n[C] Confirm  [R] Reassign  [S] Skip")
            action = Prompt.ask("Action", default="C").upper()

            if action == "C":
                # Get account ID for claimer
                account_id = participant_ids.get(assignment.claimed_by)
                if account_id:
                    assignment.claimed_by_id = account_id
                session.confirm_claim(task_key)
                await server.broadcast_task_assigned(task_key, assignment.claimed_by, skipped=False)

            elif action == "R":
                selected = poker_ui.prompt_select_participant(participants, "Assign to")
                if selected:
                    account_id = participant_ids.get(selected)
                    session.reassign_task(task_key, selected, account_id)
                    await server.broadcast_task_assigned(task_key, selected, skipped=False)
                else:
                    # Skip if no selection
                    session.skip_task_distribution(task_key)
                    await server.broadcast_task_assigned(task_key, None, skipped=True)
            else:
                session.skip_task_distribution(task_key)
                await server.broadcast_task_assigned(task_key, None, skipped=True)
        else:
            # No claim - leader assigns
            console.print("[yellow]No claims received[/yellow]")
            console.print("\n[A] Assign to someone  [S] Skip")
            action = Prompt.ask("Action", default="A").upper()

            if action == "A":
                selected = poker_ui.prompt_select_participant(participants, "Assign to")
                if selected:
                    account_id = participant_ids.get(selected)
                    session.reassign_task(task_key, selected, account_id)
                    await server.broadcast_task_assigned(task_key, selected, skipped=False)
                else:
                    session.skip_task_distribution(task_key)
                    await server.broadcast_task_assigned(task_key, None, skipped=True)
            else:
                session.skip_task_distribution(task_key)
                await server.broadcast_task_assigned(task_key, None, skipped=True)

        console.print()  # Spacing

    # Distribution complete
    summary = session.get_distribution_summary()
    console.print(poker_ui.render_distribution_summary(summary))

    # Complete distribution for clients
    await server.complete_distribution(summary)

    # Ask about task management assignment
    assigned_in_task_mgmt = False
    if task_mgmt and summary.get("assigned_count", 0) > 0:
        if Confirm.ask("Assign tasks in task management?"):
            assignments = {
                a["task_key"]: a["account_id"]
                for a in summary.get("assignments", [])
                if a.get("account_id") and not a.get("skipped")
            }
            if assignments:
                try:
                    if hasattr(task_mgmt, 'bulk_assign_issues'):
                        results = task_mgmt.bulk_assign_issues(assignments)
                        success_count = sum(1 for v in results.values() if v)
                        console.print(f"[green]Assigned {success_count}/{len(assignments)} tasks[/green]")
                    else:
                        success_count = 0
                        for task_key, account_id in assignments.items():
                            if hasattr(task_mgmt, 'assign_issue'):
                                if task_mgmt.assign_issue(task_key, account_id):
                                    success_count += 1
                        console.print(f"[green]Assigned {success_count}/{len(assignments)} tasks[/green]")
                    assigned_in_task_mgmt = True
                except Exception as e:
                    console.print(f"[red]Failed to assign in task management: {e}[/red]")

    # Send notification
    notifier.send_poker_tasks_distributed(
        leader=session.leader_name,
        assignments=summary.get("assignments", []),
        assigned_in_task_mgmt=assigned_in_task_mgmt
    )

    # Ask about sprint creation
    await _offer_sprint_creation(session, task_mgmt, notifier, console)

    # End session properly
    session.state = SessionState.FINISHED


@poker_app.command("start")
def start_cmd(
    sprint: str = typer.Option(None, "--sprint", "-s", help="Sprint ID or 'active'"),
    issues: str = typer.Option(None, "--issues", "-i", help="Comma-separated issue keys"),
    port: int = typer.Option(8765, "--port", "-p", help="Server port"),
    name: str = typer.Option(None, "--name", "-n", help="Your name as leader")
):
    """Start a Planning Poker session as leader."""
    # Check websockets dependency
    if not ensure_websockets():
        raise typer.Exit(1)

    # Load poker modules
    if not _load_poker_modules():
        show_websockets_install_help()
        raise typer.Exit(1)

    config_manager = ConfigManager()
    config = config_manager.load()

    # Get leader name (auto-detect from task management integration)
    if not name:
        name = get_current_user_name(config)
        if name:
            console.print(f"[dim]Detected user: {name}[/dim]")
        else:
            name = Prompt.ask("Your name")

    # Get team members from integration and let leader select
    team = get_team_members_from_integration(config)
    expected_participants = []
    if team:
        expected_participants = prompt_team_selection(team, name, console)
        if expected_participants:
            console.print(f"[dim]Expected participants: {len(expected_participants)}[/dim]")

    # Get tasks
    console.print("[dim]Loading tasks...[/dim]")
    tasks = _get_tasks_from_jira(config, sprint, issues)

    if not tasks:
        console.print("[yellow]No tasks found[/yellow]")
        console.print("\nMake sure you have a task management integration configured")
        console.print("and there are unestimated tasks available.")
        raise typer.Exit(1)

    console.print(f"[green]Found {len(tasks)} tasks[/green]")

    # Get session settings
    settings_dict = poker_ui.prompt_session_settings()
    settings_dict["expected_participants"] = expected_participants
    settings = SessionSettings(**settings_dict)

    # Create session
    session = PokerSession(
        leader_name=name,
        tasks=tasks,
        settings=settings
    )

    # Create server (pass config for AI voter)
    server = PokerServer(session, port=port, config=config)

    # Start tunnel
    tunnel = get_tunnel_integration(config)
    tunnel_url = None

    if tunnel and tunnel.enabled:
        console.print("[dim]Starting tunnel...[/dim]")
        tunnel_url = tunnel.start_tunnel(port)
        if tunnel_url:
            console.print(f"[green]Tunnel started: {tunnel_url}[/green]")
        else:
            console.print("[yellow]Failed to start tunnel, using local only[/yellow]")

    # Send notification about session start
    from ..utils.notifications import NotificationService
    notifier = NotificationService(config)

    # Get project key from jira integration
    jira = get_task_management(config)
    project_key = getattr(jira, 'project_key', None) if jira else None

    notifier.send_poker_session_started(
        leader=name,
        session_id=session.session_id,
        project=project_key,
        tasks_count=len(tasks),
        participants=expected_participants if expected_participants else None
    )

    # Run session
    async def run():
        await server.start()
        try:
            await _run_leader_session(session, server, tunnel_url, config)
        finally:
            await server.stop()
            if tunnel:
                tunnel.stop_tunnel()

            # Send notification about session end
            # Calculate stats from completed rounds
            total_points = sum(
                r.final_points or 0
                for r in session.completed_rounds
            )
            notifier.send_poker_session_ended(
                leader=name,
                tasks_estimated=len(session.completed_rounds),
                total_points=total_points,
                participants=session.get_participant_names()
            )

    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        console.print("\n[yellow]Session cancelled[/yellow]")


@poker_app.command("join")
def join_cmd(
    session: str = typer.Argument(..., help="Session ID or URL"),
    name: str = typer.Option(None, "--name", "-n", help="Your name")
):
    """Join a Planning Poker session as participant."""
    # Check websockets dependency
    if not ensure_websockets():
        raise typer.Exit(1)

    # Load poker modules
    if not _load_poker_modules():
        show_websockets_install_help()
        raise typer.Exit(1)

    config_manager = ConfigManager()
    config = config_manager.load()

    # Parse session argument
    if session.startswith("http"):
        # It's a URL, convert to WebSocket
        url = session.replace("http://", "ws://").replace("https://", "wss://")
        if not url.endswith("/ws"):
            url = url.rstrip("/") + "/ws"
    elif session.startswith("ws"):
        url = session
    else:
        # Assume it's a session ID, ask for URL
        host = Prompt.ask("Server URL", default="ws://localhost:8765")
        url = host.rstrip("/") + f"/{session}"

    # Get name (auto-detect from task management integration)
    if not name:
        name = get_current_user_name(config)
        if name:
            console.print(f"[dim]Detected user: {name}[/dim]")
        else:
            name = Prompt.ask("Your name")

    # Create client
    client = PokerClient(url, name)

    # Run session
    async def run():
        connected = await client.connect()
        if connected:
            await _run_participant_session(client)

    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        console.print("\n[yellow]Disconnected[/yellow]")


@poker_app.command("status")
def status_cmd():
    """Check for active poker sessions."""
    console.print("[dim]No active local sessions[/dim]")
    console.print("\nTo start a session: rg poker start")
    console.print("To join a session: rg poker join <session-id-or-url>")
