"""
Planning Poker UI components.

Rich console UI for the poker session interface.
"""

from typing import Dict, List, Optional, Any
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.columns import Columns
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, IntPrompt, Confirm


console = Console()


def render_task_panel(task: Dict) -> Panel:
    """
    Render a task panel showing task details.

    Args:
        task: Task dict with key, summary, description, current_points

    Returns:
        Rich Panel
    """
    content = Text()
    content.append(task.get("summary", ""), style="bold")

    description = task.get("description", "")
    if description:
        content.append("\n\n")
        # Truncate long descriptions
        if len(description) > 500:
            description = description[:500] + "..."
        content.append(description, style="dim")

    current = task.get("current_points")
    if current is not None:
        content.append(f"\n\nCurrent estimate: ", style="dim")
        content.append(f"{current} points", style="yellow")

    return Panel(
        content,
        title=f"[cyan]{task.get('key', 'Task')}[/cyan]",
        border_style="cyan"
    )


def render_voting_options(
    fibonacci: List[int],
    allow_question_mark: bool = True
) -> str:
    """
    Render voting options as a formatted string.

    Args:
        fibonacci: List of valid point values
        allow_question_mark: Whether to show ? option

    Returns:
        Formatted string of options
    """
    options = []
    for n in fibonacci:
        options.append(f"[bold cyan][{n}][/bold cyan]")

    if allow_question_mark:
        options.append("[bold yellow][?][/bold yellow]")

    return "  ".join(options)


def render_voting_buttons(
    fibonacci: List[int],
    allow_question_mark: bool = True,
    selected: Optional[int] = None
) -> Columns:
    """
    Render voting buttons as clickable-looking elements.

    Args:
        fibonacci: List of valid point values
        allow_question_mark: Whether to show ? option
        selected: Currently selected value

    Returns:
        Rich Columns
    """
    buttons = []

    for n in fibonacci:
        if selected == n:
            btn = Panel(
                f"[bold white]{n}[/bold white]",
                style="on green",
                width=6,
                padding=(0, 1)
            )
        else:
            btn = Panel(
                f"[cyan]{n}[/cyan]",
                style="dim",
                width=6,
                padding=(0, 1)
            )
        buttons.append(btn)

    if allow_question_mark:
        if selected is None:
            btn = Panel(
                "[bold white]?[/bold white]",
                style="on yellow",
                width=6,
                padding=(0, 1)
            )
        else:
            btn = Panel(
                "[yellow]?[/yellow]",
                style="dim",
                width=6,
                padding=(0, 1)
            )
        buttons.append(btn)

    return Columns(buttons, equal=True, expand=False)


def render_vote_progress(voted: int, total: int) -> str:
    """
    Render vote progress indicator.

    Args:
        voted: Number of votes submitted
        total: Total number of participants

    Returns:
        Formatted progress string
    """
    filled = voted
    empty = total - voted
    bar = "[green]" + "*" * filled + "[/green]" + "[dim]" + "*" * empty + "[/dim]"
    return f"{bar} ({voted}/{total})"


def render_results_table(votes: Dict[str, Optional[int]]) -> Table:
    """
    Render voting results as a table with visual bars.

    Args:
        votes: Dict of participant name -> vote value

    Returns:
        Rich Table
    """
    table = Table(title="Voting Results", show_header=True, header_style="bold")
    table.add_column("Participant", style="cyan")
    table.add_column("Points", justify="center")
    table.add_column("", width=20)

    # Get max vote for scaling bars
    numeric_votes = [v for v in votes.values() if v is not None]
    max_vote = max(numeric_votes) if numeric_votes else 1

    for name, vote in sorted(votes.items()):
        # Special styling for AI participant
        is_ai = name == "AI Assistant"

        if vote is None:
            vote_str = "[yellow]?[/yellow]"
            bar = "[yellow]???[/yellow]"
        else:
            vote_str = str(vote)
            bar_width = int((vote / max_vote) * 16) if max_vote > 0 else 0
            bar = "[green]" + "*" * bar_width + "[/green]"

        if is_ai:
            table.add_row(
                f"[magenta bold]{name}[/magenta bold]",
                f"[magenta]{vote_str}[/magenta]",
                bar
            )
        else:
            table.add_row(name, vote_str, bar)

    return table


def render_ai_reasoning(
    reasoning: str,
    confidence: Optional[str] = None,
    factors: Optional[List[str]] = None
) -> Panel:
    """
    Render AI reasoning panel.

    Args:
        reasoning: AI's explanation for the estimate
        confidence: Confidence level (low, medium, high)
        factors: List of factors considered

    Returns:
        Rich Panel
    """
    content = Text()

    # Reasoning
    content.append(reasoning, style="white")

    # Confidence indicator
    if confidence:
        content.append("\n\nConfidence: ", style="dim")
        if confidence == "high":
            content.append(confidence, style="bold green")
        elif confidence == "medium":
            content.append(confidence, style="yellow")
        else:
            content.append(confidence, style="red")

    # Factors
    if factors:
        content.append("\n\nFactors considered:", style="dim")
        for factor in factors:
            content.append(f"\n  - {factor}", style="cyan")

    return Panel(
        content,
        title="[magenta]AI Assistant Reasoning[/magenta]",
        border_style="magenta"
    )


def render_statistics(stats: Dict[str, Any]) -> Panel:
    """
    Render voting statistics panel.

    Args:
        stats: Statistics dict from VotingRound.get_statistics()

    Returns:
        Rich Panel
    """
    content = Text()

    if stats.get("average") is not None:
        content.append("Average: ", style="dim")
        content.append(f"{stats['average']}", style="bold cyan")
        content.append("\n")

    if stats.get("median") is not None:
        content.append("Median: ", style="dim")
        content.append(f"{stats['median']}", style="bold green")
        content.append("\n")

    if stats.get("min") is not None and stats.get("max") is not None:
        content.append("Range: ", style="dim")
        content.append(f"{stats['min']} - {stats['max']}", style="white")
        divergence = stats.get("divergence", 0)
        if divergence >= 8:
            content.append(f" (Divergence: {divergence})", style="bold red")
        elif divergence >= 5:
            content.append(f" (Divergence: {divergence})", style="yellow")
        content.append("\n")

    if stats.get("has_question_marks"):
        content.append("\n[yellow]Some participants voted '?'[/yellow]")

    return Panel(content, title="Statistics", border_style="blue")


def render_divergence_warning(
    votes: Dict[str, Optional[int]],
    threshold: int = 8
) -> Optional[Panel]:
    """
    Render a warning panel for divergent votes.

    Args:
        votes: Dict of participant name -> vote
        threshold: Divergence threshold

    Returns:
        Rich Panel or None if not divergent
    """
    numeric_votes = {k: v for k, v in votes.items() if v is not None}
    if len(numeric_votes) < 2:
        return None

    min_vote = min(numeric_votes.values())
    max_vote = max(numeric_votes.values())
    divergence = max_vote - min_vote

    if divergence < threshold:
        return None

    # Find who voted min and max
    min_voters = [k for k, v in numeric_votes.items() if v == min_vote]
    max_voters = [k for k, v in numeric_votes.items() if v == max_vote]

    content = Text()
    content.append("LARGE DIVERGENCE!\n\n", style="bold red")
    content.append(f"Lowest ({min_vote}): ", style="dim")
    content.append(", ".join(min_voters), style="cyan")
    content.append("\n")
    content.append(f"Highest ({max_vote}): ", style="dim")
    content.append(", ".join(max_voters), style="cyan")
    content.append("\n\n")
    content.append("Discussion recommended before final decision.", style="yellow")

    return Panel(content, title="Discussion Needed", border_style="red")


def render_session_summary(summary: Dict[str, Any]) -> Panel:
    """
    Render session summary panel.

    Args:
        summary: Summary dict from PokerSession.finish_session()

    Returns:
        Rich Panel
    """
    from rich.console import Group

    # Create table for estimated tasks
    table = Table(show_header=True, box=None)
    table.add_column("Task", style="dim")
    table.add_column("Points", justify="right", style="green")

    for round_info in summary.get("rounds", []):
        points = round_info.get("final_points")
        points_str = str(points) if points is not None else "-"
        task_summary = round_info.get('task_summary', '')
        if len(task_summary) > 40:
            task_summary = task_summary[:37] + "..."
        table.add_row(
            f"{round_info['task_key']}: {task_summary}",
            points_str
        )

    # Create footer text
    footer = Text()
    footer.append("\n")
    footer.append("Total: ", style="bold")
    footer.append(f"{summary.get('total_points', 0)} story points\n", style="bold green")
    footer.append("Tasks estimated: ", style="dim")
    footer.append(f"{summary.get('tasks_estimated', 0)}/{summary.get('tasks_total', 0)}\n", style="cyan")
    footer.append("Participants: ", style="dim")
    footer.append(", ".join(summary.get("participants", [])), style="cyan")

    # Combine table and footer
    content = Group(table, footer)

    return Panel(
        content,
        title="Planning Poker Session Summary",
        border_style="green"
    )


def render_task_list(
    tasks: List[Dict],
    completed_keys: List[str],
    current_index: int
) -> Table:
    """
    Render task list with completion status.

    Args:
        tasks: List of task dicts
        completed_keys: List of completed task keys
        current_index: Current task index

    Returns:
        Rich Table
    """
    table = Table(title="Tasks", show_header=True, header_style="bold")
    table.add_column("#", width=3, justify="right")
    table.add_column("Status", width=3, justify="center")
    table.add_column("Key", style="cyan")
    table.add_column("Summary")
    table.add_column("Points", justify="right")

    for i, task in enumerate(tasks):
        key = task.get("key", "")
        is_completed = key in completed_keys
        is_current = i == current_index

        if is_completed:
            status = "[green]v[/green]"
            style = "dim"
        elif is_current:
            status = "[yellow]>[/yellow]"
            style = "bold"
        else:
            status = " "
            style = ""

        points = task.get("current_points")
        points_str = str(int(points)) if points is not None else "-"

        table.add_row(
            str(i + 1),
            status,
            key,
            task.get("summary", "")[:50],
            points_str,
            style=style
        )

    return table


def render_participants_list(
    participants: List[str],
    leader: str,
    voted: Optional[List[str]] = None
) -> Panel:
    """
    Render participants list with voting status.

    Args:
        participants: List of participant names
        leader: Leader name
        voted: List of participants who have voted (optional)

    Returns:
        Rich Panel
    """
    content = Text()

    for name in sorted(participants):
        if name == leader:
            content.append("* ", style="yellow")
            content.append(name, style="bold yellow")
            content.append(" (Leader)\n")
        else:
            if voted and name in voted:
                content.append("[green]v[/green] ")
            else:
                content.append("  ")
            content.append(name, style="cyan")
            content.append("\n")

    return Panel(
        content,
        title=f"Participants ({len(participants)})",
        border_style="blue"
    )


def prompt_vote(fibonacci: List[int], allow_question_mark: bool = True) -> Optional[int]:
    """
    Prompt user for vote input.

    Args:
        fibonacci: Valid point values
        allow_question_mark: Whether ? is allowed

    Returns:
        Selected points or None for ?
    """
    options_str = ", ".join(str(n) for n in fibonacci)
    if allow_question_mark:
        options_str += ", ? (uncertain)"

    console.print(f"\n[dim]Options: {options_str}[/dim]")

    while True:
        choice = Prompt.ask("Your vote")

        if choice == "?" and allow_question_mark:
            return None

        try:
            points = int(choice)
            if points in fibonacci:
                return points
            console.print(f"[red]Invalid choice. Use: {options_str}[/red]")
        except ValueError:
            console.print(f"[red]Invalid input. Use: {options_str}[/red]")


def prompt_final_points(stats: Dict[str, Any], fibonacci: List[int]) -> int:
    """
    Prompt leader for final points decision.

    Args:
        stats: Voting statistics
        fibonacci: Valid point values

    Returns:
        Final points value
    """
    median = stats.get("median")
    average = stats.get("average")

    console.print("\n[bold]Choose final story points:[/bold]")

    options = []
    if median is not None:
        options.append(f"[M] Median: {int(median)}")
    if average is not None:
        avg_rounded = int(round(average))
        if avg_rounded != median:
            options.append(f"[A] Average: {avg_rounded}")

    options.append("[X] Custom value")
    options.append("[T] Re-vote")

    console.print("  " + "  |  ".join(options))

    while True:
        choice = Prompt.ask("Choice", default="M" if median else "X")

        if choice.upper() == "M" and median is not None:
            return int(median)
        elif choice.upper() == "A" and average is not None:
            return int(round(average))
        elif choice.upper() == "T":
            return -1  # Signal for re-vote
        elif choice.upper() == "X":
            return IntPrompt.ask("Enter points")
        else:
            try:
                points = int(choice)
                if points in fibonacci or points > 0:
                    return points
            except ValueError:
                pass

            console.print("[red]Invalid choice[/red]")


def prompt_session_settings() -> Dict[str, Any]:
    """
    Prompt for session settings.

    Returns:
        Settings dict
    """
    console.print("\n[bold cyan]Session Settings[/bold cyan]\n")

    # Jira update mode
    console.print("[dim]How to update Jira after voting?[/dim]")
    console.print("  [1] Ask for confirmation each time (default)")
    console.print("  [2] Auto-update with average")
    console.print("  [3] Only update at session end (batch)")

    jira_mode = Prompt.ask("Choice", default="1")
    auto_update = jira_mode == "2"
    confirm_each = jira_mode == "1"
    batch_update = jira_mode == "3"

    # Minimum participants
    min_parts = IntPrompt.ask(
        "Minimum participants",
        default=2
    )

    # Vote timeout
    timeout = IntPrompt.ask(
        "Vote timeout (seconds, 0=unlimited)",
        default=60
    )

    # Fibonacci sequence
    default_fib = "1, 2, 3, 5, 8, 13, 21"
    console.print(f"\n[dim]Fibonacci sequence (default: {default_fib})[/dim]")
    fib_str = Prompt.ask("Sequence", default=default_fib)

    try:
        fibonacci = [int(x.strip()) for x in fib_str.split(",")]
    except ValueError:
        fibonacci = [1, 2, 3, 5, 8, 13, 21]

    return {
        "auto_update_jira": auto_update,
        "confirm_each": confirm_each,
        "batch_update": batch_update,
        "min_participants": min_parts,
        "vote_timeout": timeout,
        "fibonacci": fibonacci,
        "allow_question_mark": True
    }


# =============================================================================
# TASK DISTRIBUTION UI
# =============================================================================

def render_task_offer(task: Dict) -> Panel:
    """
    Render task offer panel during distribution.

    Args:
        task: Task dict with task_key, task_summary, final_points

    Returns:
        Rich Panel
    """
    content = Text()
    content.append(f"{task.get('task_key', '')}\n", style="bold cyan")
    content.append(task.get("task_summary", ""), style="white")
    content.append(f"\n\nPoints: ", style="dim")
    content.append(f"{task.get('final_points', '?')}", style="bold green")

    claimed_by = task.get("claimed_by")
    if claimed_by:
        content.append(f"\n\n[yellow]Claimed by: {claimed_by}[/yellow]")

    return Panel(
        content,
        title="[yellow]Task Available[/yellow]",
        border_style="yellow"
    )


def prompt_claim_task() -> bool:
    """
    Prompt participant whether to claim the task.

    Returns:
        True if participant wants to claim
    """
    console.print("\n[bold yellow]Do you want to take this task?[/bold yellow]")
    return Confirm.ask("Claim task", default=False)


def render_distribution_summary(summary: Dict[str, Any]) -> Panel:
    """
    Render task distribution summary panel.

    Args:
        summary: Distribution summary dict

    Returns:
        Rich Panel
    """
    from rich.console import Group

    table = Table(show_header=True, box=None)
    table.add_column("Task", style="dim")
    table.add_column("Points", justify="right")
    table.add_column("Assigned To", style="cyan")

    for assignment in summary.get("assignments", []):
        task_key = assignment.get("task_key", "")
        points = assignment.get("final_points", "-")
        assigned_to = assignment.get("assigned_to")
        skipped = assignment.get("skipped", False)

        if skipped:
            status = "[dim]skipped[/dim]"
        elif assigned_to:
            status = assigned_to
        else:
            status = "[dim]-[/dim]"

        table.add_row(task_key, str(points), status)

    footer = Text()
    footer.append("\n")
    footer.append("Assigned: ", style="dim")
    footer.append(f"{summary.get('assigned_count', 0)}", style="bold green")
    footer.append("  |  Skipped: ", style="dim")
    footer.append(f"{summary.get('skipped_count', 0)}", style="yellow")

    content = Group(table, footer)

    return Panel(
        content,
        title="Task Distribution Summary",
        border_style="green"
    )


def prompt_select_participant(
    participants: List[str],
    prompt_text: str = "Select participant"
) -> Optional[str]:
    """
    Prompt leader to select a participant for assignment.

    Args:
        participants: List of participant names
        prompt_text: Prompt text to display

    Returns:
        Selected participant name or None
    """
    if not participants:
        console.print("[yellow]No participants available[/yellow]")
        return None

    console.print(f"\n[bold]{prompt_text}:[/bold]")
    for i, name in enumerate(participants, 1):
        console.print(f"  [{i}] {name}")

    choice = Prompt.ask("Choice")

    # Try number
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(participants):
            return participants[idx]
    except ValueError:
        pass

    # Try name match (partial)
    for name in participants:
        if choice.lower() in name.lower():
            return name

    console.print("[red]Invalid selection[/red]")
    return None


def render_distribution_task_for_leader(
    task_key: str,
    task_summary: str,
    final_points: Optional[int],
    claimed_by: Optional[str]
) -> Panel:
    """
    Render distribution task panel for leader view.

    Args:
        task_key: Task identifier
        task_summary: Task summary text
        final_points: Estimated story points
        claimed_by: Who claimed the task (if any)

    Returns:
        Rich Panel
    """
    content = Text()
    content.append(f"{task_key}\n", style="bold cyan")
    content.append(task_summary[:80], style="white")
    if len(task_summary) > 80:
        content.append("...", style="dim")
    content.append(f"\n\nPoints: ", style="dim")
    content.append(f"{final_points if final_points else '?'}", style="bold green")

    if claimed_by:
        content.append(f"\n\n[green]Claimed by: {claimed_by}[/green]")
    else:
        content.append("\n\n[yellow]No claims yet[/yellow]")

    return Panel(
        content,
        title="Task Distribution",
        border_style="cyan"
    )


# =============================================================================
# SPRINT CREATION UI
# =============================================================================

def prompt_sprint_settings(date_config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Prompt for sprint creation settings.

    Args:
        date_config: Date configuration from integration:
            - requires_dates: Whether dates are required
            - requires_start_date: Whether start date is required
            - requires_end_date: Whether end date is required
            - default_duration_days: Default sprint duration
            - date_format: Expected date format description

    Returns:
        Sprint settings dict or None if cancelled
    """
    from datetime import datetime, timedelta

    console.print("\n[bold cyan]Sprint Settings[/bold cyan]\n")

    # Sprint name
    default_name = f"Sprint {datetime.now().strftime('%Y-%m-%d')}"
    name = Prompt.ask("Sprint name", default=default_name)

    if not name.strip():
        return None

    result = {"name": name.strip()}

    # Dates based on integration requirements
    requires_start = date_config.get("requires_start_date", False) or date_config.get("requires_dates", False)
    requires_end = date_config.get("requires_end_date", False) or date_config.get("requires_dates", False)
    default_duration = date_config.get("default_duration_days", 14)
    date_format_hint = date_config.get("date_format", "YYYY-MM-DD")

    if requires_start or requires_end:
        console.print(f"[dim]Date format: {date_format_hint}[/dim]")

    # Start date
    if requires_start:
        today = datetime.now().strftime("%Y-%m-%d")
        start_date = Prompt.ask("Start date", default=today)
        if start_date.strip():
            result["start_date"] = start_date.strip()
    else:
        # Optional start date
        console.print("[dim]Start date (optional, press Enter to skip)[/dim]")
        start_date = Prompt.ask("Start date", default="")
        if start_date.strip():
            result["start_date"] = start_date.strip()

    # End date
    if requires_end:
        # Calculate default end date
        try:
            start = datetime.strptime(result.get("start_date", datetime.now().strftime("%Y-%m-%d")), "%Y-%m-%d")
            default_end = (start + timedelta(days=default_duration)).strftime("%Y-%m-%d")
        except ValueError:
            default_end = ""

        end_date = Prompt.ask("End date", default=default_end)
        if end_date.strip():
            result["end_date"] = end_date.strip()
    else:
        # Optional end date
        if result.get("start_date"):
            console.print(f"[dim]End date (optional, default: {default_duration} days from start)[/dim]")
            end_date = Prompt.ask("End date", default="")
            if end_date.strip():
                result["end_date"] = end_date.strip()

    # Optional goal
    console.print("[dim]Sprint goal (optional)[/dim]")
    goal = Prompt.ask("Goal", default="")
    if goal.strip():
        result["goal"] = goal.strip()

    return result


def render_sprint_created(
    sprint_name: str,
    tasks_count: int,
    total_points: int,
    started: bool = False
) -> Panel:
    """
    Render sprint creation confirmation panel.

    Args:
        sprint_name: Name of the created sprint
        tasks_count: Number of tasks in the sprint
        total_points: Total story points
        started: Whether the sprint was started

    Returns:
        Rich Panel
    """
    content = Text()
    content.append(f"{sprint_name}\n\n", style="bold green")
    content.append("Tasks: ", style="dim")
    content.append(f"{tasks_count}\n", style="cyan")
    content.append("Total Points: ", style="dim")
    content.append(f"{total_points}\n", style="green")

    if started:
        content.append("\n[green]Sprint started![/green]")

    return Panel(
        content,
        title="Sprint Created",
        border_style="green"
    )
