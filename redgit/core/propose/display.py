"""
Display utilities for propose command output.

This module centralizes all UI/display functions for the propose command,
providing consistent formatting and reducing code duplication.
"""

from typing import List, Dict, Optional, Any
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


# =============================================================================
# UTILITY DISPLAY FUNCTIONS
# =============================================================================

def display_file_list(files: List[str], max_display: int = 5, indent: str = "") -> None:
    """
    Display a truncated list of files with consistent formatting.

    Args:
        files: List of file paths to display
        max_display: Maximum number of files to show before truncating
        indent: Indentation string to prefix each line
    """
    for f in files[:max_display]:
        console.print(f"{indent}[dim]• {f}[/dim]")
    if len(files) > max_display:
        console.print(f"{indent}[dim]... +{len(files) - max_display} more[/dim]")


def display_commit_result(
    branch: str,
    issue_key: Optional[str],
    strategy: str,
    success: bool,
    error: Optional[str] = None
) -> None:
    """
    Display the result of a commit operation.

    Args:
        branch: Branch name where commit was made
        issue_key: Associated issue key (if any)
        strategy: Workflow strategy (local-merge or merge-request)
        success: Whether the commit succeeded
        error: Error message if failed
    """
    if success:
        if strategy == "local-merge":
            console.print(f"[green]   ✓ Committed and merged {branch}[/green]")
        else:
            console.print(f"[green]   ✓ Committed to {branch}[/green]")
    else:
        if error:
            console.print(f"[red]   ✗ Failed: {error}[/red]")
        else:
            console.print(f"[yellow]   ⚠️  No files to commit[/yellow]")


def display_group_details(
    group: Dict,
    index: int,
    show_files: bool = True,
    max_files: int = 3,
    indent: str = "  "
) -> None:
    """
    Display details of a single commit group.

    Args:
        group: Group dictionary with commit info
        index: Group number for display
        show_files: Whether to show file list
        max_files: Maximum files to show
        indent: Indentation string
    """
    issue_key = group.get('issue_key')
    commit_title = group.get('commit_title', 'N/A')
    files = group.get('files', [])

    if issue_key:
        console.print(f"{indent}[bold cyan]#{index}[/bold cyan] [bold]{issue_key}[/bold]")
    else:
        console.print(f"{indent}[bold cyan]#{index}[/bold cyan] [yellow]New Issue[/yellow]")

    console.print(f"{indent}    [dim]Commit:[/dim]  {commit_title[:60]}")
    console.print(f"{indent}    [dim]Files:[/dim]   {len(files)}")

    if show_files and files:
        display_file_list(files, max_display=max_files, indent=f"{indent}           ")


# =============================================================================
# PROMPT AND SOURCE DISPLAY
# =============================================================================

def show_prompt_sources(
    prompt_name: Optional[str],
    plugin_prompt: Optional[str],
    active_plugin: Optional[Any],
    issue_language: Optional[str]
) -> None:
    """Show which prompt sources are being used (for verbose mode)."""
    from ..core.config import RETGIT_DIR
    from ..core.prompt import PROMPT_CATEGORIES

    console.print(f"[dim]Prompt name (CLI): {prompt_name or 'auto'}[/dim]")
    console.print(f"[dim]Active plugin: {active_plugin.name if active_plugin else 'none'}[/dim]")
    console.print(f"[dim]Plugin prompt: {'yes' if plugin_prompt else 'no'}[/dim]")
    console.print(f"[dim]Issue language: {issue_language or 'en (default)'}[/dim]")

    # Check where the commit prompt comes from (same logic as _load_by_name)
    category = "commit"
    name = prompt_name or "default"

    # 1. User override path: .redgit/prompts/commit/default.md
    user_path = RETGIT_DIR / "prompts" / category / f"{name}.md"
    if user_path.exists():
        console.print(f"\n[green]✓ Using USER prompt:[/green] {user_path}")
    else:
        # 2. Legacy user path: .redgit/prompts/default.md
        user_legacy = RETGIT_DIR / "prompts" / f"{name}.md"
        if user_legacy.exists():
            console.print(f"\n[green]✓ Using USER prompt (legacy path):[/green] {user_legacy}")
        else:
            # 3. Builtin path
            builtin_dir = PROMPT_CATEGORIES.get(category)
            if builtin_dir:
                builtin_path = builtin_dir / f"{name}.md"
                if builtin_path.exists():
                    console.print(f"\n[cyan]Using BUILTIN prompt:[/cyan] {builtin_path}")
                else:
                    console.print(f"\n[yellow]Prompt not found:[/yellow] {name}")

    # Show all user overrides in prompts folder
    user_prompts_dir = RETGIT_DIR / "prompts"
    if user_prompts_dir.exists():
        user_files = list(user_prompts_dir.rglob("*.md"))
        if user_files:
            console.print(f"\n[dim]User prompt overrides ({len(user_files)}):[/dim]")
            for f in user_files[:10]:
                rel_path = f.relative_to(user_prompts_dir)
                console.print(f"  [dim]• {rel_path}[/dim]")
            if len(user_files) > 10:
                console.print(f"  [dim]... and {len(user_files) - 10} more[/dim]")


# =============================================================================
# ISSUE AND GROUP DISPLAY
# =============================================================================

def show_active_issues(issues: List) -> None:
    """Display active issues in a compact format."""
    table = Table(show_header=False, box=None, padding=(0, 1))
    for issue in issues[:5]:
        status_color = "green" if "progress" in issue.status.lower() else "yellow"
        table.add_row(
            f"[bold]{issue.key}[/bold]",
            f"[{status_color}]{issue.status}[/{status_color}]",
            issue.summary[:50] + ("..." if len(issue.summary) > 50 else "")
        )
    console.print(table)
    if len(issues) > 5:
        console.print(f"[dim]   ... and {len(issues) - 5} more[/dim]")


def show_groups_summary(
    matched: List[Dict],
    unmatched: List[Dict],
    task_mgmt: Optional[Any]
) -> None:
    """Show summary of groups."""

    if matched:
        console.print("\n[bold green]✓ Matched with existing issues:[/bold green]")
        for g in matched:
            console.print(f"  [green]• {g.get('issue_key')}[/green] - {g.get('commit_title', '')[:50]}")
            console.print(f"    [dim]{len(g.get('files', []))} files[/dim]")

    if unmatched:
        console.print("\n[bold yellow]? No matching issue:[/bold yellow]")
        for g in unmatched:
            # Show issue_title (localized) if available, fallback to commit_title
            display_title = g.get('issue_title') or g.get('commit_title', '')
            console.print(f"  [yellow]• {display_title[:60]}[/yellow]")
            # Also show commit_title if different from issue_title
            if g.get('issue_title') and g.get('commit_title'):
                console.print(f"    [dim]commit: {g.get('commit_title', '')[:50]}[/dim]")
            console.print(f"    [dim]{len(g.get('files', []))} files[/dim]")

        if task_mgmt and task_mgmt.enabled:
            console.print("\n[dim]New issues will be created for unmatched groups[/dim]")


def show_verbose_groups(groups: List[Dict]) -> None:
    """Display parsed groups in verbose mode."""
    console.print(f"\n[bold cyan]═══ Parsed Groups ({len(groups)}) ═══[/bold cyan]")
    for i, g in enumerate(groups, 1):
        console.print(f"\n[bold]Group {i}:[/bold]")
        console.print(f"  [dim]Files:[/dim] {len(g.get('files', []))} files")
        console.print(f"  [dim]commit_title:[/dim] {g.get('commit_title', 'N/A')}")
        console.print(f"  [dim]issue_key:[/dim] {g.get('issue_key', 'null')}")
        console.print(f"  [dim]issue_title:[/dim] {g.get('issue_title', 'null')}")
        if g.get('files'):
            console.print(f"  [dim]Files list:[/dim]")
            for f in g.get('files', [])[:5]:
                console.print(f"    - {f}")
            if len(g.get('files', [])) > 5:
                console.print(f"    ... and {len(g.get('files', [])) - 5} more")


# =============================================================================
# DRY RUN SUMMARIES
# =============================================================================

def show_dry_run_summary(
    matched_groups: List[Dict],
    unmatched_groups: List[Dict],
    task_mgmt: Optional[Any],
    parent_task_key: Optional[str] = None,
    parent_issue: Optional[Any] = None
) -> None:
    """Show detailed dry run summary of what would be done."""
    console.print(f"\n[bold yellow]═══ DRY RUN SUMMARY ═══[/bold yellow]")

    total_commits = len(matched_groups) + len(unmatched_groups)

    # Show parent task info for subtasks mode
    if parent_task_key and parent_issue:
        console.print(f"\n[bold cyan]📋 Parent Task:[/bold cyan]")
        console.print(f"   [bold]{parent_task_key}[/bold]: {parent_issue.summary}")
        console.print(f"   [dim]Status: {parent_issue.status}[/dim]")
        console.print(f"\n[cyan]Will create {total_commits} subtasks under this task:[/cyan]")
    else:
        console.print(f"\n[yellow]Would create {total_commits} commits:[/yellow]")

    # Matched groups (existing issues)
    if matched_groups:
        console.print(f"\n[bold green]✓ Matched with existing issues ({len(matched_groups)}):[/bold green]")
        for i, g in enumerate(matched_groups, 1):
            branch = task_mgmt.format_branch_name(g["issue_key"], g.get("commit_title", "")) if task_mgmt else f"feature/{g['issue_key']}"
            console.print(f"\n  [bold cyan]#{i}[/bold cyan] [bold]{g['issue_key']}[/bold]")
            console.print(f"      [dim]Commit:[/dim]  {g.get('commit_title', '')[:60]}")
            console.print(f"      [dim]Branch:[/dim]  {branch}")
            console.print(f"      [dim]Files:[/dim]   {len(g.get('files', []))}")
            display_file_list(g.get('files', []), max_display=3, indent="               ")

    # Unmatched groups (new issues/subtasks to create)
    if unmatched_groups:
        if parent_task_key:
            console.print(f"\n[bold yellow]📝 Subtasks to create ({len(unmatched_groups)}):[/bold yellow]")
        else:
            console.print(f"\n[bold yellow]📝 New issues to create ({len(unmatched_groups)}):[/bold yellow]")

        for i, g in enumerate(unmatched_groups, 1):
            # Calculate branch name
            commit_title = g.get("commit_title", "untitled")
            if task_mgmt:
                # For preview, use placeholder issue key
                preview_branch = f"feature/NEW-{i}-{commit_title[:20].lower().replace(' ', '-')}"
            else:
                clean_title = commit_title.lower()
                clean_title = "".join(c if c.isalnum() or c == " " else "" for c in clean_title)
                clean_title = clean_title.strip().replace(" ", "-")[:40]
                preview_branch = f"feature/{clean_title}"

            issue_title = g.get('issue_title') or g.get('commit_title', 'N/A')

            console.print(f"\n  [bold cyan]#{i}[/bold cyan] [yellow]New {'Subtask' if parent_task_key else 'Issue'}[/yellow]")
            console.print(f"      [dim]Title:[/dim]   {issue_title[:60]}")
            console.print(f"      [dim]Commit:[/dim]  {commit_title[:60]}")
            console.print(f"      [dim]Branch:[/dim]  {preview_branch}")
            console.print(f"      [dim]Files:[/dim]   {len(g.get('files', []))}")
            display_file_list(g.get('files', []), max_display=3, indent="               ")

            # Show issue description preview if available
            if g.get('issue_description'):
                desc_preview = g['issue_description'][:100].replace('\n', ' ')
                console.print(f"      [dim]Desc:[/dim]    {desc_preview}...")

    # Summary
    console.print(f"\n[bold]─────────────────────────────────────────[/bold]")
    console.print(f"[bold]Summary:[/bold]")
    console.print(f"   Total commits: {total_commits}")
    if matched_groups:
        console.print(f"   Existing issues: {len(matched_groups)}")
    if unmatched_groups:
        if parent_task_key:
            console.print(f"   New subtasks: {len(unmatched_groups)} (under {parent_task_key})")
        else:
            console.print(f"   New issues: {len(unmatched_groups)}")

    total_files = sum(len(g.get('files', [])) for g in matched_groups + unmatched_groups)
    console.print(f"   Total files: {total_files}")

    console.print(f"\n[dim]Run without --dry-run to apply changes[/dim]")


def show_task_commit_dry_run(
    task_id: str,
    changes: List[Dict],
    task_mgmt: Optional[Any]
) -> None:
    """Show dry-run summary for --task mode (single commit to specific task)."""

    console.print(f"\n[bold yellow]═══ DRY RUN SUMMARY ═══[/bold yellow]")

    # Resolve issue key
    issue_key = task_id
    issue = None

    if task_mgmt and task_mgmt.enabled:
        # If task_id is just a number, prepend project key
        if task_id.isdigit() and hasattr(task_mgmt, 'project_key') and task_mgmt.project_key:
            issue_key = f"{task_mgmt.project_key}-{task_id}"

        # Fetch issue details
        with console.status(f"Fetching task {issue_key}..."):
            issue = task_mgmt.get_issue(issue_key)

        if not issue:
            console.print(f"\n[red]❌ Task {issue_key} not found[/red]")
            return

    # Show task info
    console.print(f"\n[bold cyan]📋 Target Task:[/bold cyan]")
    if issue:
        console.print(f"   [bold]{issue_key}[/bold]: {issue.summary}")
        console.print(f"   [dim]Status: {issue.status}[/dim]")
        if issue.description:
            desc_preview = issue.description[:150].replace('\n', ' ')
            console.print(f"   [dim]Description: {desc_preview}...[/dim]")
    else:
        console.print(f"   [bold]{issue_key}[/bold] [dim](no task management)[/dim]")

    # Extract file paths
    file_paths = [c["file"] if isinstance(c, dict) else c for c in changes]

    # Generate commit info
    if issue:
        commit_title = f"{issue_key}: {issue.summary}"
    else:
        commit_title = f"Changes for {issue_key}"

    # Format branch name
    if task_mgmt and hasattr(task_mgmt, 'format_branch_name') and issue:
        branch_name = task_mgmt.format_branch_name(issue_key, issue.summary)
    else:
        branch_name = f"feature/{issue_key.lower()}"

    # Show commit details
    console.print(f"\n[bold green]📝 Commit to create:[/bold green]")
    console.print(f"   [dim]Title:[/dim]   {commit_title[:70]}{'...' if len(commit_title) > 70 else ''}")
    console.print(f"   [dim]Branch:[/dim]  {branch_name}")
    console.print(f"   [dim]Files:[/dim]   {len(file_paths)}")

    # Show file list
    display_file_list(file_paths, max_display=5, indent="            ")

    # Summary
    console.print(f"\n[bold]─────────────────────────────────────────[/bold]")
    console.print(f"[bold]Summary:[/bold]")
    console.print(f"   All {len(file_paths)} files will be committed to [bold]{issue_key}[/bold]")
    if issue:
        console.print(f"   Task: {issue.summary[:50]}{'...' if len(issue.summary) > 50 else ''}")

    console.print(f"\n[dim]Run without --dry-run to apply changes[/dim]")


# =============================================================================
# MULTI-TASK MODE DISPLAY
# =============================================================================

def show_multi_task_summary(result: dict, subtask_mode: bool = True) -> None:
    """
    Display multi-task analysis results.

    Shows how files are assigned to different parent tasks and what
    subtasks will be created under each.

    Args:
        result: Dict with task_assignments, unmatched_groups, and unmatched_files
        subtask_mode: If True, show subtask creation info; if False, show commit-only info
    """
    mode_label = "Subtask Mode" if subtask_mode else "Commit Mode"
    console.print(f"\n[bold cyan]═══ Multi-Task Analysis Results ({mode_label}) ═══[/bold cyan]\n")

    task_assignments = result.get("task_assignments", [])
    unmatched_groups = result.get("unmatched_groups", [])
    unmatched_files = result.get("unmatched_files", [])

    if not task_assignments and not unmatched_groups and not unmatched_files:
        console.print("[yellow]No assignments found. Check if files match any active tasks.[/yellow]")
        return

    # Show assignments for each parent task
    for assignment in task_assignments:
        task_key = assignment.get("task_key", "Unknown")
        subtask_groups = assignment.get("subtask_groups", [])
        file_count = sum(len(g.get("files", [])) for g in subtask_groups)

        console.print(f"[bold green]{task_key}[/bold green]")
        if subtask_mode:
            console.print(f"  └─ {file_count} files → {len(subtask_groups)} subtasks")
        else:
            console.print(f"  └─ {file_count} files → {len(subtask_groups)} commits")

        for i, group in enumerate(subtask_groups, 1):
            commit_title = group.get("commit_title", "N/A")[:50]
            files = group.get("files", [])
            console.print(f"     {i}. {commit_title}")
            console.print(f"        [dim]{len(files)} files[/dim]")

        console.print("")  # Empty line between tasks

    # Show unmatched groups (with suggested epic titles)
    if unmatched_groups:
        unmatched_file_count = sum(len(g.get("files", [])) for g in unmatched_groups)
        console.print(f"[bold yellow]📦 Suggested Epics ({unmatched_file_count} files → {len(unmatched_groups)} epics)[/bold yellow]")

        for i, group in enumerate(unmatched_groups, 1):
            issue_title = group.get("issue_title", "N/A")[:50]
            files = group.get("files", [])
            console.print(f"     {i}. {issue_title}")
            console.print(f"        [dim]{len(files)} files[/dim]")

        console.print("")

    # Show unmatched files (orphan files)
    if unmatched_files:
        console.print(f"[yellow]⚠️  Unmatched ({len(unmatched_files)} files):[/yellow]")
        for f in unmatched_files[:5]:
            console.print(f"  [dim]• {f}[/dim]")
        if len(unmatched_files) > 5:
            console.print(f"  [dim]... and {len(unmatched_files) - 5} more[/dim]")


def show_multi_task_dry_run(result: dict, task_mgmt: Optional[Any], subtask_mode: bool = True) -> None:
    """
    Show dry-run summary for multi-task mode.

    Args:
        result: Dict with task_assignments, unmatched_groups, and unmatched_files
        task_mgmt: Task management integration for branch formatting
        subtask_mode: If True, show subtask creation info; if False, show commit-only info
    """
    mode_label = "Subtask Mode" if subtask_mode else "Commit Mode"
    console.print(f"\n[bold yellow]═══ DRY RUN SUMMARY ({mode_label}) ═══[/bold yellow]")

    task_assignments = result.get("task_assignments", [])
    unmatched_groups = result.get("unmatched_groups", [])
    unmatched_files = result.get("unmatched_files", [])

    total_groups = sum(
        len(a.get("subtask_groups", []))
        for a in task_assignments
    )

    if subtask_mode:
        console.print(f"\n[yellow]Would create {total_groups} subtasks across {len(task_assignments)} parent tasks[/yellow]\n")
    else:
        console.print(f"\n[yellow]Would create {total_groups} commits for {len(task_assignments)} parent tasks[/yellow]\n")

    # Show detailed breakdown per parent task
    for assignment in task_assignments:
        task_key = assignment.get("task_key", "Unknown")
        subtask_groups = assignment.get("subtask_groups", [])

        console.print(f"[bold cyan]📋 Parent Task: {task_key}[/bold cyan]")

        for i, group in enumerate(subtask_groups, 1):
            files = group.get("files", [])
            commit_title = group.get("commit_title", "N/A")
            issue_title = group.get("issue_title", commit_title)

            if subtask_mode:
                console.print(f"\n  [bold]Subtask #{i}[/bold]")
                console.print(f"      [dim]Title:[/dim]   {issue_title[:60]}")
            else:
                console.print(f"\n  [bold]Commit #{i}[/bold]")
            console.print(f"      [dim]Commit:[/dim]  {commit_title[:60]}")
            console.print(f"      [dim]Files:[/dim]   {len(files)}")
            display_file_list(files, max_display=3, indent="               ")

        console.print("")  # Empty line between parent tasks

    # Show unmatched groups (suggested epics)
    if unmatched_groups:
        unmatched_group_files = sum(len(g.get("files", [])) for g in unmatched_groups)
        console.print(f"[bold yellow]📦 Suggested Epics ({unmatched_group_files} files → {len(unmatched_groups)} epics)[/bold yellow]")
        console.print("[dim]   These files don't match any active task. Suggested epic titles:[/dim]")

        for i, group in enumerate(unmatched_groups, 1):
            files = group.get("files", [])
            issue_title = group.get("issue_title", "N/A")
            issue_desc = group.get("issue_description", "")[:80]

            console.print(f"\n  [bold]Suggested Epic #{i}[/bold]")
            console.print(f"      [dim]Title:[/dim]   {issue_title[:60]}")
            if issue_desc:
                console.print(f"      [dim]Desc:[/dim]    {issue_desc}")
            console.print(f"      [dim]Files:[/dim]   {len(files)}")
            display_file_list(files, max_display=3, indent="               ")

        console.print("")

    # Show orphan unmatched files
    if unmatched_files:
        console.print(f"[yellow]⚠️  Unmatched files ({len(unmatched_files)}):[/yellow]")
        console.print("[dim]   These files did not match any active task:[/dim]")
        for f in unmatched_files[:10]:
            console.print(f"  [dim]• {f}[/dim]")
        if len(unmatched_files) > 10:
            console.print(f"  [dim]... and {len(unmatched_files) - 10} more[/dim]")

    # Summary
    console.print(f"\n[bold]─────────────────────────────────────────[/bold]")
    console.print(f"[bold]Summary:[/bold]")
    console.print(f"   Parent tasks: {len(task_assignments)}")
    if subtask_mode:
        console.print(f"   Total subtasks: {total_groups}")
    else:
        console.print(f"   Total commits: {total_groups}")

    total_files = sum(
        len(f)
        for a in task_assignments
        for g in a.get("subtask_groups", [])
        for f in [g.get("files", [])]
    )
    console.print(f"   Files assigned: {total_files}")

    if unmatched_groups:
        unmatched_group_files = sum(len(g.get("files", [])) for g in unmatched_groups)
        console.print(f"   Suggested epics: {len(unmatched_groups)} ({unmatched_group_files} files)")

    if unmatched_files:
        console.print(f"   Unmatched files: {len(unmatched_files)}")

    console.print(f"\n[dim]Run without --dry-run to apply changes[/dim]")
