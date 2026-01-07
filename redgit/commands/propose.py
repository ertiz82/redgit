"""
Propose command - Analyze changes, match with tasks, and create commits.
"""

from typing import Optional, List, Dict, Any
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

import re

from ..core.common.config import ConfigManager, StateManager
from ..core.common.gitops import GitOps, NotAGitRepoError, init_git_repo
from ..core.common.llm import LLMClient
from ..core.common.prompt import PromptManager
from ..core.common.backup import BackupManager
from ..core.propose.commit import build_commit_message, execute_commit_group, build_commit_from_group, CommitResult
from ..core.propose.display import (
    display_file_list,
    display_commit_result,
    display_group_details,
    show_prompt_sources,
    show_active_issues,
    show_groups_summary,
    show_verbose_groups,
    show_dry_run_summary,
    show_task_commit_dry_run,
    show_multi_task_summary,
    show_multi_task_dry_run,
)
from ..core.propose.analysis import (
    setup_llm_and_generate_groups,
    enhance_groups_with_diffs,
    build_detailed_analysis_prompt,
    parse_detailed_result,
)
from ..integrations.registry import get_task_management, get_code_hosting, get_notification
from ..integrations.base import TaskManagementBase, Issue
from ..plugins.registry import load_plugins, get_active_plugin
from ..utils.security import filter_changes
from ..utils.logging import get_logger
from ..utils.notifications import NotificationService

console = Console()


def _show_recovery_info(backup_id: str, error: Exception):
    """Show detailed recovery information after failure."""
    console.print("\n[red bold]═══ HATA OLUŞTU ═══[/red bold]\n")
    console.print(f"[red]Hata: {error}[/red]\n")

    console.print("[yellow]Working tree yedeği alındı. Geri yüklemek için:[/yellow]")
    console.print(f"  [cyan]rg backup restore[/cyan]           # Son yedeği geri yükle")
    console.print(f"  [cyan]rg backup restore {backup_id}[/cyan]  # Bu yedeği geri yükle")
    console.print(f"  [cyan]rg backup list[/cyan]              # Tüm yedekleri listele")

    console.print("\n[yellow]Manuel düzeltme için:[/yellow]")
    console.print("  [dim]git status[/dim]                   # Mevcut durumu gör")
    console.print("  [dim]git stash list[/dim]               # Bekleyen stash'leri gör")
    console.print("  [dim]git checkout <branch>[/dim]        # Branch'e dön")


def _extract_issue_from_branch(branch_name: str, config: dict) -> Optional[str]:
    """
    Try to extract issue key from branch name.

    Looks for patterns like PROJ-123 in branch names like:
    - feature/PROJ-123-add-feature
    - bugfix/SCRUM-456-fix-login
    - PROJ-789-some-work

    Args:
        branch_name: Current git branch name
        config: Configuration dict with task management settings

    Returns:
        Issue key (e.g., "PROJ-123") or None if not found
    """
    # Get project key from task management config
    task_mgmt_name = config.get("active", {}).get("task_management")
    if not task_mgmt_name:
        return None

    integration_config = config.get("integrations", {}).get(task_mgmt_name, {})
    project_key = integration_config.get("project_key", "")

    if not project_key:
        return None

    # Look for pattern like PROJ-123 in branch name
    pattern = rf"({re.escape(project_key)}-\d+)"
    match = re.search(pattern, branch_name, re.IGNORECASE)
    if match:
        return match.group(1).upper()

    return None


# Note: _build_commit_message moved to core/commit.py as build_commit_message


# =============================================================================
# PROPOSE CONTEXT AND INITIALIZATION HELPERS
# =============================================================================

def _init_propose_context(
    prompt: Optional[str],
    no_task: bool,
    task: Optional[str],
    dry_run: bool,
    verbose: bool,
    detailed: bool,
    subtasks: bool
) -> tuple:
    """
    Initialize propose command context: load config and handle pattern suggestions.

    Returns:
        Tuple of (config_manager, state_manager, config, options_dict)
        options_dict may have updated values from pattern suggestion
    """
    config_manager = ConfigManager()
    state_manager = StateManager()
    config = config_manager.load()

    # Build options dict
    options = {
        "prompt": prompt,
        "no_task": no_task,
        "task": task,
        "dry_run": dry_run,
        "verbose": verbose,
        "detailed": detailed,
        "subtasks": subtasks,
    }

    # Check for usage pattern suggestion (only when no params provided)
    if not any([prompt, no_task, task, dry_run, verbose, detailed, subtasks]):
        common_pattern = state_manager.get_common_propose_pattern()
        if common_pattern and len(common_pattern) > 0:
            if _suggest_and_ask_pattern(common_pattern):
                values = _prompt_for_pattern_values(common_pattern)
                options.update(values)

    return config_manager, state_manager, config, options


def _init_gitops_with_fallback(dry_run: bool) -> Optional[GitOps]:
    """
    Initialize GitOps with fallback to git init if not a repo.

    Args:
        dry_run: If True, don't actually initialize git

    Returns:
        GitOps instance or None if user cancelled

    Raises:
        typer.Exit: If initialization fails
    """
    try:
        return GitOps()
    except NotAGitRepoError:
        console.print("[yellow]Warning: Not a git repository.[/yellow]")
        if dry_run:
            console.print("[yellow]Dry run: Would ask to initialize git repository[/yellow]")
            return None
        if Confirm.ask("Initialize git repository here?", default=True):
            remote_url = Prompt.ask("Remote URL (optional, press Enter to skip)", default="")
            remote_url = remote_url.strip() if remote_url else None
            try:
                init_git_repo(remote_url)
                console.print("[green]Git repository initialized[/green]")
                if remote_url:
                    console.print(f"[green]Remote 'origin' added: {remote_url}[/green]")
                return GitOps()
            except Exception as e:
                console.print(f"[red]Failed to initialize git: {e}[/red]")
                raise typer.Exit(1)
        else:
            raise typer.Exit(1)


def _fetch_and_validate_changes(
    gitops: GitOps,
    subtasks: bool,
    task: Optional[str],
    staged_only: bool = False
) -> Optional[List[Dict]]:
    """
    Fetch changes from git and perform validations.

    Args:
        gitops: Git operations helper
        subtasks: Whether subtask mode is enabled
        task: Task ID if specified
        staged_only: If True, only get staged files

    Returns:
        List of changes or None if no changes/validation fails
    """
    changes = gitops.get_changes(staged_only=staged_only)

    # Check for merge conflicts first
    conflict_files = [c for c in changes if c.get("status") == "C" or c.get("conflict")]
    if conflict_files:
        console.print("\n[red bold]⚠️  Merge conflict detected![/red bold]")
        console.print("[red]The following files have unresolved conflicts:[/red]")
        for cf in conflict_files:
            console.print(f"  [red]• {cf['file']}[/red]")
        console.print("\n[yellow]Please resolve conflicts first:[/yellow]")
        console.print("  [dim]git status                    # See conflict details[/dim]")
        console.print("  [dim]git checkout --theirs <file>  # Accept remote version[/dim]")
        console.print("  [dim]git checkout --ours <file>    # Accept local version[/dim]")
        console.print("  [dim]git add <file>                # Mark as resolved[/dim]")
        return None
    excluded_files = gitops.get_excluded_changes()

    if excluded_files:
        console.print(f"[dim]Locked: {len(excluded_files)} sensitive files excluded[/dim]")

    if staged_only:
        console.print("[dim]Mode: --staged (only staged files)[/dim]")

    if not changes:
        if staged_only:
            console.print("[yellow]Warning: No staged changes found. Use 'git add' to stage files.[/yellow]")
        else:
            console.print("[yellow]Warning: No changes found.[/yellow]")
        return None

    # Filter for sensitive files warning
    _, _, sensitive_files = filter_changes(changes, warn_sensitive=True)
    if sensitive_files:
        console.print(f"[yellow]Warning: {len(sensitive_files)} potentially sensitive files detected[/yellow]")
        for f in sensitive_files[:3]:
            console.print(f"[yellow]   - {f}[/yellow]")
        if len(sensitive_files) > 3:
            console.print(f"[yellow]   ... and {len(sensitive_files) - 3} more[/yellow]")
        console.print("")

    console.print(f"[cyan]Found {len(changes)} file changes.[/cyan]")

    # Note: --subtasks validation moved to propose_cmd() after auto-enable logic

    return changes


def _setup_llm_and_generate_groups(
    config: dict,
    changes: List[Dict],
    prompt_name: Optional[str],
    plugin_prompt: Optional[str],
    active_issues: List,
    issue_language: Optional[str],
    verbose: bool,
    detailed: bool,
    gitops: GitOps,
    task_mgmt: Optional[TaskManagementBase]
) -> tuple:
    """
    Setup LLM, create prompt, and generate commit groups.

    Returns:
        Tuple of (groups, llm) or (None, None) if error/no groups
    """
    # Create LLM client
    try:
        llm = LLMClient(config.get("llm", {}))
        console.print(f"[dim]Using LLM: {llm.provider}[/dim]")
    except FileNotFoundError as e:
        console.print(f"[red]LLM not found: {e}[/red]")
        return None, None
    except Exception as e:
        console.print(f"[red]LLM error: {e}[/red]")
        return None, None

    # Create prompt
    prompt_manager = PromptManager(config.get("llm", {}))

    if verbose:
        console.print(f"\n[bold cyan]=== Prompt Sources ===[/bold cyan]")
        show_prompt_sources(prompt_name, plugin_prompt, None, issue_language)

    try:
        final_prompt = prompt_manager.get_prompt(
            changes=changes,
            prompt_name=prompt_name,
            plugin_prompt=plugin_prompt,
            active_issues=active_issues,
            issue_language=issue_language
        )
    except FileNotFoundError as e:
        console.print(f"[red]Prompt not found: {e}[/red]")
        return None, None

    if verbose:
        console.print(f"\n[bold cyan]=== Full Prompt ===[/bold cyan]")
        console.print(Panel(final_prompt[:3000] + ("..." if len(final_prompt) > 3000 else ""), title="Prompt", border_style="cyan"))
        console.print(f"[dim]Total prompt length: {len(final_prompt)} characters[/dim]")

    # Generate groups with AI
    console.print("\n[yellow]AI analyzing changes...[/yellow]\n")
    try:
        if verbose:
            groups, raw_response = llm.generate_groups(final_prompt, return_raw=True) if hasattr(llm, 'generate_groups') else (llm.generate_groups(final_prompt), None)
            if raw_response:
                console.print(f"\n[bold cyan]=== Raw AI Response ===[/bold cyan]")
                console.print(Panel(raw_response[:5000] + ("..." if len(raw_response) > 5000 else ""), title="AI Response", border_style="green"))
        else:
            groups = llm.generate_groups(final_prompt)
    except Exception as e:
        console.print(f"[red]LLM error: {e}[/red]")
        return None, None

    if not groups:
        console.print("[yellow]Warning: No groups created.[/yellow]")
        return None, None

    # Detailed mode: enhance groups with diff-based analysis
    if detailed:
        console.print("\n[cyan]Analyzing diffs for detailed messages...[/cyan]")
        groups = _enhance_groups_with_diffs(
            groups=groups,
            gitops=gitops,
            llm=llm,
            issue_language=issue_language,
            verbose=verbose,
            task_mgmt=task_mgmt
        )
        console.print("[green]Detailed analysis complete[/green]\n")

    if verbose:
        show_verbose_groups(groups)

    return groups, llm


def _finalize_propose_session(
    state_manager: StateManager,
    workflow: dict,
    config: dict,
    prompt: Optional[str],
    no_task: bool,
    task: Optional[str],
    dry_run: bool,
    verbose: bool,
    detailed: bool,
    subtasks: bool
):
    """Finalize the propose session with summary and usage tracking."""
    session = state_manager.get_session()
    strategy = workflow.get("strategy", "local-merge")

    if session:
        branches = session.get("branches", [])
        issues = session.get("issues", [])
        console.print(f"\n[bold green]Created {len(branches)} commits for {len(issues)} issues[/bold green]")
        if strategy == "local-merge":
            console.print("[dim]All commits are merged to current branch.[/dim]")
            console.print("[dim]Run 'rg push' to push to remote and complete issues[/dim]")
        else:
            console.print("[dim]Branches ready for push and PR creation.[/dim]")
            console.print("[dim]Run 'rg push --pr' to push branches and create pull requests[/dim]")

        # Send session summary notification
        _send_session_summary_notification(config, len(branches), len(issues))

    # Track usage pattern for future suggestions
    current_params = _extract_param_pattern(
        prompt=prompt, no_task=no_task, task=task,
        dry_run=dry_run, verbose=verbose, detailed=detailed, subtasks=subtasks
    )
    state_manager.add_propose_usage(current_params)


# =============================================================================
# PROPOSE COMMAND
# =============================================================================

def propose_cmd(
    prompt: Optional[str] = typer.Option(
        None, "--prompt", "-p",
        help="Prompt template name (e.g., default, minimal, laravel)"
    ),
    no_task: bool = typer.Option(
        False, "--no-task",
        help="Skip task management integration"
    ),
    task: Optional[str] = typer.Option(
        None, "--task", "-t",
        help="Link all changes to a specific task/issue number (e.g., 123 or PROJ-123)"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", "-n",
        help="Analyze and show what would be done without making changes"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v",
        help="Show detailed information (prompts, AI request/response, etc.)"
    ),
    detailed: bool = typer.Option(
        False, "--detailed", "-d",
        help="Generate detailed commit messages using file diffs (slower but more accurate)"
    ),
    subtasks: bool = typer.Option(
        False, "--subtasks", "-s",
        help="Create subtasks under the specified task (requires --task)"
    ),
    force: bool = typer.Option(
        False, "--force", "-f",
        help="Skip LLM task relevance check, commit all files under the specified task (requires --task)"
    ),
    multi: bool = typer.Option(
        False, "--multi", "-m",
        help="Analyze changes for multiple parent tasks from active issues"
    ),
    ask: bool = typer.Option(
        False, "--ask", "-a",
        help="Interactive mode - select options step by step"
    ),
    staged: bool = typer.Option(
        False, "--staged", "--cached",
        help="Only analyze staged (git add) files, ignore unstaged changes"
    ),
    single_branch: bool = typer.Option(
        False, "--single-branch", "-sb",
        help="Commit all groups to current branch (no separate branches)"
    )
):
    """Analyze changes and propose commit groups with task matching."""
    logger = get_logger()
    logger.debug(f"propose_cmd called with: prompt={prompt}, task={task}, dry_run={dry_run}")

    # Dry run banner
    if dry_run:
        console.print(Panel("[bold yellow]DRY RUN MODE[/bold yellow] - No changes will be made", style="yellow"))

    config_manager = ConfigManager()
    state_manager = StateManager()
    config = config_manager.load()
    logger.debug("Config loaded successfully")

    # Check for usage pattern suggestion (only when no params provided)
    if not any([prompt, no_task, task, dry_run, verbose, detailed, subtasks]):
        common_pattern = state_manager.get_common_propose_pattern()
        if common_pattern and len(common_pattern) > 0:
            if _suggest_and_ask_pattern(common_pattern):
                values = _prompt_for_pattern_values(common_pattern)
                task = values.get("task")
                subtasks = values.get("subtasks", False)
                detailed = values.get("detailed", False)
                dry_run = values.get("dry_run", False)
                verbose = values.get("verbose", False)
                no_task = values.get("no_task", False)
                prompt = values.get("prompt")

    # Verbose: Show config paths
    if verbose:
        from ..core.common.config import RETGIT_DIR
        console.print(Panel("[bold cyan]VERBOSE MODE[/bold cyan]", style="cyan"))
        console.print(f"[dim]Config: {RETGIT_DIR / 'config.yaml'}[/dim]")

    # Initialize GitOps with fallback to git init
    gitops = _init_gitops_with_fallback(dry_run)
    if gitops is None:
        return

    workflow = config.get("workflow", {})

    # Get task management integration if available
    task_mgmt: Optional[TaskManagementBase] = None
    if not no_task:
        task_mgmt = get_task_management(config)

    # Verbose: Show task management config
    if verbose and task_mgmt:
        console.print(f"\n[bold cyan]═══ Task Management Config ═══[/bold cyan]")
        console.print(f"[dim]Integration: {task_mgmt.name}[/dim]")
        if hasattr(task_mgmt, 'issue_language'):
            console.print(f"[dim]Issue Language: {task_mgmt.issue_language or 'default (en)'}[/dim]")
        if hasattr(task_mgmt, 'project_key'):
            console.print(f"[dim]Project Key: {task_mgmt.project_key}[/dim]")

    # Load plugins
    plugins = load_plugins(config.get("plugins", {}))
    active_plugin = get_active_plugin(plugins)

    # Fetch and validate changes
    changes = _fetch_and_validate_changes(gitops, subtasks, task, staged_only=staged)
    if changes is None:
        return

    # Create backup before any git operations
    import sys
    backup_manager = BackupManager(gitops)
    backup_id = None
    try:
        command_args = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else ""
        command_str = f"rg propose {command_args}"
        backup_id = backup_manager.create_backup(command_str, changes)
        console.print(f"[dim]Backup: {backup_id}[/dim]")
    except Exception as backup_error:
        console.print(f"[yellow]Warning: Could not create backup: {backup_error}[/yellow]")

    # Handle --ask interactive mode first
    subtask_mode = subtasks  # Default from CLI flag
    if ask:
        options = _interactive_setup(config, task_mgmt)
        if options["mode"] == "multi":
            multi = True
        elif options["mode"] == "task":
            task = options.get("task")
        detailed = options.get("detailed", detailed)
        subtask_mode = options.get("subtask_mode", subtasks)
        # Note: create_policy is handled within the processing functions

    # Auto-enable multi mode when --staged + --subtasks used without --task
    # This matches staged files to active tasks and creates subtasks
    if staged and subtasks and not task and not multi:
        if task_mgmt and task_mgmt.enabled:
            console.print("[cyan]--staged + --subtasks: Staged dosyalar aktif tasklarla eşleştirilecek[/cyan]")
            multi = True
            subtask_mode = True

    # Validate --subtasks requires either --task or --multi (after auto-enable logic)
    if subtasks and not task and not multi:
        console.print("[red]Error: --subtasks requires --task flag (e.g., rg propose -t PROJ-123 --subtasks)[/red]")
        console.print("[dim]Tip: Use --staged -s for auto-matching with active tasks[/dim]")
        raise typer.Exit(1)

    # Handle --multi mode (before task-filtered mode)
    if multi:
        if not task_mgmt or not task_mgmt.enabled:
            console.print("[red]❌ Task management integration required for --multi flag[/red]")
            console.print("[dim]Configure Jira or another task management in .redgit/config.yaml[/dim]")
            raise typer.Exit(1)

        # task parameter can be comma-separated for multi mode
        task_filter = task  # None if not specified, otherwise comma-separated IDs

        try:
            _process_multi_task_mode(
                changes=changes,
                gitops=gitops,
                task_mgmt=task_mgmt,
                state_manager=state_manager,
                config=config,
                task_filter=task_filter,
                verbose=verbose,
                detailed=detailed,
                dry_run=dry_run,
                subtask_mode=subtask_mode
            )
            # Mark backup as completed on success
            if backup_id:
                backup_manager.mark_completed(backup_id)
                backup_manager.cleanup_old_backups(keep=5)
        except Exception as e:
            # Mark backup as failed and show recovery info
            if backup_id:
                backup_manager.mark_failed(backup_id, str(e))
                _show_recovery_info(backup_id, e)
            raise
        return

    # Auto-detect task from branch if on a task branch and -t not provided
    detected_task = None
    if task is None and task_mgmt and task_mgmt.enabled:
        detected_task = _extract_issue_from_branch(gitops.original_branch, config)
        if detected_task:
            console.print(f"[cyan]Branch'ten task tespit edildi: {detected_task}[/cyan]")
            if Confirm.ask(f"Task-filtered mode ile devam edilsin mi? ({detected_task})", default=True):
                task = detected_task
            else:
                console.print("[dim]Normal mode ile devam ediliyor...[/dim]")

    # Handle --task flag: smart task-filtered mode
    # This mode analyzes files for relevance to the parent task and creates subtasks
    if task:
        # Note: --subtasks flag is now implicit with -t
        if subtasks:
            console.print("[dim]Note: --subtasks is now implicit with -t flag[/dim]")

        # Check task management is available
        if not task_mgmt or not task_mgmt.enabled:
            console.print("[red]❌ Task management integration required for -t flag[/red]")
            console.print("[dim]Configure Jira or another task management in .redgit/config.yaml[/dim]")
            raise typer.Exit(1)

        if dry_run:
            _show_task_filtered_dry_run(task, changes, gitops, task_mgmt, config, verbose)
            return

        try:
            _process_task_filtered_mode(
                task_id=task,
                changes=changes,
                gitops=gitops,
                task_mgmt=task_mgmt,
                state_manager=state_manager,
                config=config,
                verbose=verbose,
                detailed=detailed,
                force=force
            )

            # Track usage pattern for future suggestions
            current_params = _extract_param_pattern(
                prompt=prompt, no_task=no_task, task=task,
                dry_run=dry_run, verbose=verbose, detailed=detailed, subtasks=subtasks
            )
            state_manager.add_propose_usage(current_params)

            # Mark backup as completed on success
            if backup_id:
                backup_manager.mark_completed(backup_id)
                backup_manager.cleanup_old_backups(keep=5)
        except Exception as e:
            # Mark backup as failed and show recovery info
            if backup_id:
                backup_manager.mark_failed(backup_id, str(e))
                _show_recovery_info(backup_id, e)
            raise
        return

    # Note: The old subtasks-only mode is now merged into task-filtered mode above
    parent_task_key = None
    parent_issue = None

    # Show active plugin
    if active_plugin:
        console.print(f"[magenta]🧩 Plugin: {active_plugin.name}[/magenta]")

    # Get active issues from task management
    active_issues: List[Issue] = []
    if task_mgmt and task_mgmt.enabled:
        console.print(f"[blue]📋 Task management: {task_mgmt.name}[/blue]")

        with console.status("Fetching active issues..."):
            active_issues = task_mgmt.get_my_active_issues()

        if active_issues:
            console.print(f"[green]   Found {len(active_issues)} active issues[/green]")
            show_active_issues(active_issues)
        else:
            console.print("[dim]   No active issues found[/dim]")

        # Show sprint info if available
        if task_mgmt.supports_sprints():
            sprint = task_mgmt.get_active_sprint()
            if sprint:
                console.print(f"[blue]   🏃 Sprint: {sprint.name}[/blue]")

    console.print("")

    # Get plugin prompt if available
    plugin_prompt = None
    if active_plugin and hasattr(active_plugin, "get_prompt"):
        plugin_prompt = active_plugin.get_prompt()

    # Get issue_language from Jira config if available
    issue_language = None
    if task_mgmt and hasattr(task_mgmt, 'issue_language'):
        issue_language = task_mgmt.issue_language

    # Setup LLM and generate commit groups
    groups, llm = _setup_llm_and_generate_groups(
        config=config,
        changes=changes,
        prompt_name=prompt,
        plugin_prompt=plugin_prompt,
        active_issues=active_issues,
        issue_language=issue_language,
        verbose=verbose,
        detailed=detailed,
        gitops=gitops,
        task_mgmt=task_mgmt
    )
    if groups is None:
        return

    # Separate matched and unmatched groups
    matched_groups, unmatched_groups = _categorize_groups(groups, task_mgmt)

    # Show results
    show_groups_summary(matched_groups, unmatched_groups, task_mgmt)

    # Dry run: Show what would be done and exit
    if dry_run:
        show_dry_run_summary(
            matched_groups=matched_groups,
            unmatched_groups=unmatched_groups,
            task_mgmt=task_mgmt,
            parent_task_key=parent_task_key,
            parent_issue=parent_issue
        )
        return

    # Confirm
    total_groups = len(matched_groups) + len(unmatched_groups)
    if not Confirm.ask(f"\nProceed with {total_groups} groups?"):
        return

    try:
        # Save base branch for session
        state_manager.set_base_branch(gitops.original_branch)

        # Check if using subtasks mode with hierarchical branching
        if subtasks and parent_task_key and parent_issue:
            # Subtasks mode: hierarchical branching strategy
            # - Create parent branch from original
            # - Each subtask branches from parent, merges back to parent
            # - Parent merges to original (or kept for PR)
            _process_subtasks_mode(
                matched_groups=matched_groups,
                unmatched_groups=unmatched_groups,
                gitops=gitops,
                task_mgmt=task_mgmt,
                state_manager=state_manager,
                workflow=workflow,
                config=config,
                llm=llm,
                parent_task_key=parent_task_key,
                parent_issue=parent_issue
            )
        else:
            # Standard mode: each group gets its own branch from original
            # Process matched groups
            if matched_groups:
                console.print("\n[bold cyan]Processing matched groups...[/bold cyan]")
                _process_matched_groups(
                    matched_groups, gitops, task_mgmt, state_manager, workflow,
                    single_branch=single_branch
                )

            # Process unmatched groups
            if unmatched_groups:
                console.print("\n[bold yellow]Processing unmatched groups...[/bold yellow]")
                _process_unmatched_groups(
                    unmatched_groups, gitops, task_mgmt, state_manager, workflow, config, llm,
                    parent_key=None,  # No hierarchical branching in standard mode
                    single_branch=single_branch
                )

        # Finalize session and track usage
        _finalize_propose_session(
            state_manager=state_manager,
            workflow=workflow,
            config=config,
            prompt=prompt,
            no_task=no_task,
            task=task,
            dry_run=dry_run,
            verbose=verbose,
            detailed=detailed,
            subtasks=subtasks
        )

        # Mark backup as completed on success
        if backup_id:
            backup_manager.mark_completed(backup_id)
            backup_manager.cleanup_old_backups(keep=5)
    except Exception as e:
        # Mark backup as failed and show recovery info
        if backup_id:
            backup_manager.mark_failed(backup_id, str(e))
            _show_recovery_info(backup_id, e)
        raise


# =============================================================================
# DEPRECATED WRAPPERS - Use functions from core.propose_display instead
# =============================================================================

def _show_prompt_sources(*args, **kwargs):
    """Deprecated: Use show_prompt_sources from core.propose_display instead."""
    return show_prompt_sources(*args, **kwargs)


def _show_active_issues(issues):
    """Deprecated: Use show_active_issues from core.propose_display instead."""
    return show_active_issues(issues)


def _show_groups_summary(matched, unmatched, task_mgmt):
    """Deprecated: Use show_groups_summary from core.propose_display instead."""
    return show_groups_summary(matched, unmatched, task_mgmt)


def _categorize_groups(
    groups: List[Dict],
    task_mgmt: Optional[TaskManagementBase]
) -> tuple:
    """
    Categorize groups into matched (existing issues) and unmatched (new issues).

    Args:
        groups: List of commit groups from AI analysis
        task_mgmt: Task management integration (optional)

    Returns:
        Tuple of (matched_groups, unmatched_groups)
    """
    matched_groups = []
    unmatched_groups = []

    for group in groups:
        issue_key = group.get("issue_key")
        if issue_key and task_mgmt:
            # Verify issue exists
            issue = task_mgmt.get_issue(issue_key)
            if issue:
                group["_issue"] = issue
                matched_groups.append(group)
            else:
                console.print(f"[yellow]⚠️  Issue {issue_key} not found, treating as unmatched[/yellow]")
                group["issue_key"] = None
                unmatched_groups.append(group)
        else:
            unmatched_groups.append(group)

    return matched_groups, unmatched_groups


def _show_verbose_groups(groups):
    """Deprecated: Use show_verbose_groups from core.propose_display instead."""
    return show_verbose_groups(groups)


def _show_dry_run_summary(matched_groups, unmatched_groups, task_mgmt, parent_task_key=None, parent_issue=None):
    """Deprecated: Use show_dry_run_summary from core.propose_display instead."""
    return show_dry_run_summary(matched_groups, unmatched_groups, task_mgmt, parent_task_key, parent_issue)


def _process_matched_groups(
    groups: List[Dict],
    gitops: GitOps,
    task_mgmt: TaskManagementBase,
    state_manager: StateManager,
    workflow: dict,
    single_branch: bool = False
):
    """Process groups that matched with existing issues.

    Args:
        single_branch: If True, commit directly to current branch (no separate branches)
    """

    auto_transition = workflow.get("auto_transition", True)
    strategy = workflow.get("strategy", "local-merge")

    for i, group in enumerate(groups, 1):
        issue_key = group["issue_key"]
        issue = group.get("_issue")

        console.print(f"\n[cyan]({i}/{len(groups)}) {issue_key}: {group.get('commit_title', '')[:40]}...[/cyan]")

        # Format branch name using task management
        branch_name = task_mgmt.format_branch_name(issue_key, group.get("commit_title", ""))
        group["branch"] = branch_name

        # Build commit message with issue reference
        msg = build_commit_message(
            title=group['commit_title'],
            body=group.get('commit_body', ''),
            issue_ref=issue_key
        )

        # Create branch and commit using new method
        try:
            files = group.get("files", [])

            if single_branch:
                # Single branch mode: commit directly to current branch
                staged_files, failed_files = gitops.stage_files(files)
                if staged_files:
                    gitops.commit(msg)
                    console.print(f"[green]   ✓ Committed: {group['commit_title'][:50]}[/green]")

                    # Add comment to issue
                    task_mgmt.on_commit(group, {"issue_key": issue_key})

                    # Transition to In Progress if configured
                    if auto_transition and issue and issue.status.lower() not in ["in progress", "in development"]:
                        _transition_issue_with_strategy(task_mgmt, issue_key, "after_propose")
                else:
                    console.print(f"[yellow]   ⚠️  No files to commit[/yellow]")
            else:
                # Normal mode: create branch and commit
                success = gitops.create_branch_and_commit(branch_name, files, msg, strategy=strategy)

                if success:
                    if strategy == "local-merge":
                        console.print(f"[green]   ✓ Committed and merged {branch_name}[/green]")
                    else:
                        console.print(f"[green]   ✓ Committed to {branch_name}[/green]")

                    # Add comment to issue
                    task_mgmt.on_commit(group, {"issue_key": issue_key})

                    # Transition to In Progress if configured
                    if auto_transition and issue.status.lower() not in ["in progress", "in development"]:
                        _transition_issue_with_strategy(task_mgmt, issue_key, "after_propose")

                    # Save to session
                    state_manager.add_session_branch(branch_name, issue_key)
                else:
                    console.print(f"[yellow]   ⚠️  No files to commit[/yellow]")

        except Exception as e:
            console.print(f"[red]   ❌ Error: {e}[/red]")


def _process_unmatched_groups(
    groups: List[Dict],
    gitops: GitOps,
    task_mgmt: Optional[TaskManagementBase],
    state_manager: StateManager,
    workflow: dict,
    config: dict,
    llm: LLMClient = None,
    parent_key: Optional[str] = None,
    single_branch: bool = False
):
    """Process groups that didn't match any existing issue.

    Args:
        parent_key: If provided, create subtasks under this parent issue (--subtasks mode)
        single_branch: If True, commit directly to current branch (no separate branches)
    """

    create_policy = workflow.get("create_missing_issues", "ask")
    # In subtasks mode, always create subtasks
    default_type = "subtask" if parent_key else workflow.get("default_issue_type", "task")
    auto_transition = workflow.get("auto_transition", True)
    strategy = workflow.get("strategy", "local-merge")

    for i, group in enumerate(groups, 1):
        # Show issue_title (localized) if available, fallback to commit_title
        display_title = group.get("issue_title") or group.get("commit_title", "Untitled")
        console.print(f"\n[yellow]({i}/{len(groups)}) {display_title[:50]}...[/yellow]")

        issue_key = None

        # Handle issue creation
        if task_mgmt and task_mgmt.enabled:
            should_create = False

            if create_policy == "auto":
                should_create = True
            elif create_policy == "ask":
                should_create = Confirm.ask(f"   Create new issue for this group?", default=True)
            # else: skip

            if should_create:
                # Use issue_title and commit_body from group (already generated if -d was used)
                default_summary = group.get("issue_title") or display_title[:100]
                description = group.get("issue_description") or group.get("commit_body", "")

                # In auto mode, don't prompt for title
                if create_policy == "auto":
                    summary = default_summary
                    console.print(f"[dim]   Issue: {summary[:60]}...[/dim]")
                else:
                    summary = Prompt.ask("   Issue title", default=default_summary)

                # Try to create issue, handle permission errors
                try:
                    issue_key = task_mgmt.create_issue(
                        summary=summary,
                        description=description,
                        issue_type=default_type,
                        parent_key=parent_key  # Pass parent_key for subtasks mode
                    )

                    if issue_key:
                        if parent_key:
                            console.print(f"[green]   ✓ Created subtask: {issue_key} (under {parent_key})[/green]")
                        else:
                            console.print(f"[green]   ✓ Created issue: {issue_key}[/green]")

                        # Send notification for issue creation
                        _send_issue_created_notification(config, issue_key, summary)

                        # Transition to In Progress
                        if auto_transition:
                            _transition_issue_with_strategy(task_mgmt, issue_key, "after_propose")
                    else:
                        # issue_key is None - creation failed silently
                        if parent_key:
                            console.print(f"[yellow]   ⚠️  Failed to create subtask under {parent_key}[/yellow]")
                            console.print(f"[dim]      Check if subtask type is enabled for your project[/dim]")
                        else:
                            console.print("[red]   ❌ Failed to create issue[/red]")

                except PermissionError as e:
                    # User doesn't have permission to create issues
                    console.print(f"[yellow]   ⚠️  No permission to create issues: {e}[/yellow]")
                    console.print("[dim]   You can create a subtask under an existing issue instead.[/dim]")

                    # Ask for parent issue key
                    parent_key = Prompt.ask(
                        "   Parent issue key (e.g., PROJ-123)",
                        default=""
                    )

                    if parent_key:
                        # Create subtask under parent
                        try:
                            issue_key = task_mgmt.create_issue(
                                summary=summary,
                                description=description,
                                issue_type="subtask",
                                parent_key=parent_key
                            )

                            if issue_key:
                                console.print(f"[green]   ✓ Created subtask: {issue_key} (under {parent_key})[/green]")
                                _send_issue_created_notification(config, issue_key, summary)

                                if auto_transition:
                                    _transition_issue_with_strategy(task_mgmt, issue_key, "after_propose")
                            else:
                                console.print("[red]   ❌ Failed to create subtask[/red]")
                        except Exception as sub_e:
                            console.print(f"[red]   ❌ Failed to create subtask: {sub_e}[/red]")
                    else:
                        console.print("[dim]   Skipping issue creation (no parent specified)[/dim]")

        # Determine branch name
        commit_title = group.get("commit_title", "untitled")
        if issue_key and task_mgmt:
            branch_name = task_mgmt.format_branch_name(issue_key, commit_title)
        else:
            # Generate branch name without issue
            clean_title = commit_title.lower()
            clean_title = "".join(c if c.isalnum() or c == " " else "" for c in clean_title)
            clean_title = clean_title.strip().replace(" ", "-")[:40]
            branch_name = f"feature/{clean_title}"

        group["branch"] = branch_name
        group["issue_key"] = issue_key

        # Build commit message
        msg = build_commit_message(
            title=group['commit_title'],
            body=group.get('commit_body', ''),
            issue_ref=issue_key if issue_key else None
        )

        # Create branch and commit using new method
        try:
            files = group.get("files", [])

            if single_branch:
                # Single branch mode: commit directly to current branch
                staged_files, failed_files = gitops.stage_files(files)
                if staged_files:
                    gitops.commit(msg)
                    console.print(f"[green]   ✓ Committed: {group['commit_title'][:50]}[/green]")

                    # Add comment if issue was created
                    if issue_key and task_mgmt:
                        task_mgmt.on_commit(group, {"issue_key": issue_key})
                else:
                    console.print(f"[yellow]   ⚠️  No files to commit[/yellow]")
            else:
                # Normal mode: create branch and commit
                success = gitops.create_branch_and_commit(branch_name, files, msg, strategy=strategy)

                if success:
                    if strategy == "local-merge":
                        console.print(f"[green]   ✓ Committed and merged {branch_name}[/green]")
                    else:
                        console.print(f"[green]   ✓ Committed to {branch_name}[/green]")

                    # Add comment if issue was created
                    if issue_key and task_mgmt:
                        task_mgmt.on_commit(group, {"issue_key": issue_key})

                    # Save to session
                    state_manager.add_session_branch(branch_name, issue_key)
                else:
                    console.print(f"[yellow]   ⚠️  No files to commit[/yellow]")

        except Exception as e:
            console.print(f"[red]   ❌ Error: {e}[/red]")


def _process_subtasks_mode(
    matched_groups: List[Dict],
    unmatched_groups: List[Dict],
    gitops: GitOps,
    task_mgmt: TaskManagementBase,
    state_manager: StateManager,
    workflow: dict,
    config: dict,
    llm: LLMClient,
    parent_task_key: str,
    parent_issue: Issue
):
    """
    Process all groups in subtask mode with hierarchical branching.

    In subtask mode:
    1. Create/checkout parent task branch from original branch
    2. For each group: create subtask, commit to subtask branch, merge to parent
    3. Final: merge parent to original (local-merge) OR keep for PR (merge-request)
    4. Ask user about deleting parent branch locally

    Args:
        matched_groups: Groups that matched existing issues
        unmatched_groups: Groups without matching issues
        gitops: Git operations instance
        task_mgmt: Task management integration
        state_manager: Session state manager
        workflow: Workflow configuration
        config: Full configuration
        llm: LLM client
        parent_task_key: Parent task key (e.g., SCRUM-858)
        parent_issue: Parent issue object
    """
    strategy = workflow.get("strategy", "local-merge")
    original_branch = gitops.original_branch
    create_policy = workflow.get("create_missing_issues", "ask")
    auto_transition = workflow.get("auto_transition", True)

    # Step 1: Create parent branch name
    parent_branch = task_mgmt.format_branch_name(parent_task_key, parent_issue.summary)

    console.print(f"\n[bold cyan]Setting up parent branch: {parent_branch}[/bold cyan]")

    # Step 2: Check if parent branch exists on remote
    if gitops.remote_branch_exists(parent_branch):
        console.print(f"[dim]Parent branch exists on remote, checking out and pulling...[/dim]")
        success, is_new, error = gitops.checkout_or_create_branch(
            parent_branch,
            from_branch=original_branch,
            pull_if_exists=True
        )
        if not success:
            console.print(f"[red]❌ Failed to checkout parent branch: {error}[/red]")
            raise typer.Exit(1)
        console.print(f"[green]✓ Checked out existing branch: {parent_branch}[/green]")
    else:
        # Create new parent branch
        success, is_new, error = gitops.checkout_or_create_branch(
            parent_branch,
            from_branch=original_branch,
            pull_if_exists=False
        )
        if not success:
            console.print(f"[red]❌ Failed to create parent branch: {error}[/red]")
            raise typer.Exit(1)
        console.print(f"[green]✓ Created new branch: {parent_branch}[/green]")

    # Track subtask branches for session
    created_subtasks = []

    # Step 3: Process all groups as subtasks
    all_groups = matched_groups + unmatched_groups
    for i, group in enumerate(all_groups, 1):
        display_title = group.get("issue_title") or group.get("commit_title", "Untitled")
        console.print(f"\n[cyan]({i}/{len(all_groups)}) Processing: {display_title[:50]}...[/cyan]")

        try:
            # Determine subtask key
            subtask_key = group.get("issue_key")

            # Create subtask if not matched to existing issue
            if not subtask_key:
                should_create = create_policy == "auto" or (
                    create_policy == "ask" and Confirm.ask("   Create subtask for this group?", default=True)
                )

                if should_create:
                    summary = group.get("issue_title") or display_title[:100]
                    description = group.get("issue_description") or group.get("commit_body", "")

                    try:
                        subtask_key = task_mgmt.create_issue(
                            summary=summary,
                            description=description,
                            issue_type="subtask",
                            parent_key=parent_task_key
                        )

                        if subtask_key:
                            console.print(f"[green]   ✓ Created subtask: {subtask_key}[/green]")
                            created_subtasks.append(subtask_key)
                            _send_issue_created_notification(config, subtask_key, summary)

                            if auto_transition:
                                _transition_issue_with_strategy(task_mgmt, subtask_key, "after_propose")
                        else:
                            console.print(f"[yellow]   ⚠️  Failed to create subtask[/yellow]")
                            continue

                    except Exception as e:
                        console.print(f"[red]   ❌ Failed to create subtask: {e}[/red]")
                        continue
                else:
                    console.print(f"[dim]   Skipping (no subtask created)[/dim]")
                    continue

            # Create subtask branch name
            commit_title = group.get("commit_title", "untitled")
            subtask_branch = task_mgmt.format_branch_name(subtask_key, commit_title)

            # Build commit message
            msg = build_commit_message(
                title=group['commit_title'],
                body=group.get('commit_body', ''),
                issue_ref=subtask_key
            )

            # Create subtask branch from parent, commit, and merge back to parent
            files = group.get("files", [])
            success = gitops.create_subtask_branch_and_commit(
                subtask_branch=subtask_branch,
                parent_branch=parent_branch,
                files=files,
                message=msg
            )

            if success:
                console.print(f"[green]   ✓ Committed and merged to parent: {subtask_branch}[/green]")

                # Add comment to subtask
                task_mgmt.on_commit(group, {"issue_key": subtask_key})

                # Track subtask issue for transition on push (but not branch - it's deleted)
                # Store in subtask_issues list so push knows to transition only these
                state = state_manager.load()
                if "session" not in state:
                    state["session"] = {"base_branch": None, "branches": [], "issues": []}

                # Add to subtask_issues (for transition) - separate from regular issues
                state["session"].setdefault("subtask_issues", []).append(subtask_key)
                state_manager.save(state)
            else:
                console.print(f"[yellow]   ⚠️  No files to commit[/yellow]")

        except Exception as e:
            console.print(f"[red]   ❌ Error processing subtask: {e}[/red]")

    # Step 4: Handle final merge/push based on strategy
    console.print(f"\n[bold cyan]Finalizing parent branch...[/bold cyan]")

    if strategy == "local-merge":
        # Merge parent branch back to original
        success, error = gitops.merge_branch(
            source_branch=parent_branch,
            target_branch=original_branch,
            delete_source=False  # Don't auto-delete, ask user
        )

        if success:
            console.print(f"[green]✓ Merged {parent_branch} into {original_branch}[/green]")

            # Ask user about deleting parent branch
            if Confirm.ask(f"Delete local parent branch '{parent_branch}'?", default=True):
                try:
                    gitops.repo.git.branch("-d", parent_branch)
                    console.print(f"[dim]Deleted {parent_branch}[/dim]")
                except Exception:
                    console.print(f"[yellow]Could not delete {parent_branch}[/yellow]")
        else:
            console.print(f"[red]❌ Failed to merge: {error}[/red]")
            console.print(f"[dim]Parent branch '{parent_branch}' preserved for manual resolution[/dim]")
    else:
        # merge-request strategy: keep parent branch for PR creation
        console.print(f"[dim]Parent branch '{parent_branch}' ready for push and PR creation[/dim]")
        state_manager.add_session_branch(parent_branch, parent_task_key)

        # Checkout back to original branch
        try:
            gitops.repo.git.checkout(original_branch)
        except Exception:
            pass

    # Summary
    console.print(f"\n[bold green]✅ Created {len(created_subtasks)} subtask(s) under {parent_task_key}[/bold green]")


def _show_task_commit_dry_run(task_id, changes, gitops, task_mgmt):
    """Deprecated: Use show_task_commit_dry_run from core.propose_display instead."""
    # Note: gitops parameter is ignored in the new implementation
    return show_task_commit_dry_run(task_id, changes, task_mgmt)


def _process_task_commit(
    task_id: str,
    changes: List[str],
    gitops: GitOps,
    task_mgmt: Optional[TaskManagementBase],
    state_manager: StateManager,
    config: dict
):
    """
    Process all changes as a single commit linked to a specific task.

    This is triggered when --task flag is used:
    rg propose --task 123
    rg propose --task PROJ-123
    """
    workflow = config.get("workflow", {})
    strategy = workflow.get("strategy", "local-merge")
    auto_transition = workflow.get("auto_transition", True)

    # Resolve issue key
    issue_key = task_id
    issue = None

    if task_mgmt and task_mgmt.enabled:
        console.print(f"[blue]📋 Task management: {task_mgmt.name}[/blue]")

        # If task_id is just a number, prepend project key
        if task_id.isdigit() and hasattr(task_mgmt, 'project_key') and task_mgmt.project_key:
            issue_key = f"{task_mgmt.project_key}-{task_id}"

        # Fetch issue details
        with console.status(f"Fetching issue {issue_key}..."):
            issue = task_mgmt.get_issue(issue_key)

        if not issue:
            console.print(f"[red]❌ Issue {issue_key} not found[/red]")
            raise typer.Exit(1)

        console.print(f"[green]✓ Found: {issue_key} - {issue.summary}[/green]")
        console.print(f"[dim]   Status: {issue.status}[/dim]")
    else:
        console.print(f"[yellow]⚠️  No task management configured, using {issue_key} as reference[/yellow]")

    # Extract file paths from changes (changes is list of dicts)
    file_paths = [c["file"] if isinstance(c, dict) else c for c in changes]

    # Show changes summary
    console.print(f"\n[cyan]📁 {len(file_paths)} files will be committed:[/cyan]")
    for f in file_paths[:10]:
        console.print(f"[dim]   • {f}[/dim]")
    if len(file_paths) > 10:
        console.print(f"[dim]   ... and {len(file_paths) - 10} more[/dim]")

    # Generate commit message
    if issue:
        commit_title = f"{issue_key}: {issue.summary}"
        commit_body = issue.description[:500] if issue.description else ""
    else:
        commit_title = f"Changes for {issue_key}"
        commit_body = ""

    # Format branch name
    if task_mgmt and hasattr(task_mgmt, 'format_branch_name'):
        branch_name = task_mgmt.format_branch_name(issue_key, issue.summary if issue else task_id)
    else:
        branch_name = f"feature/{issue_key.lower()}"

    console.print(f"\n[cyan]📝 Commit:[/cyan]")
    console.print(f"   Title: {commit_title[:60]}{'...' if len(commit_title) > 60 else ''}")
    console.print(f"   Branch: {branch_name}")
    console.print(f"   Files: {len(changes)}")

    # Confirm
    if not Confirm.ask("\nProceed?", default=True):
        console.print("[yellow]Cancelled.[/yellow]")
        return

    # Build full commit message
    msg = build_commit_message(
        title=commit_title,
        body=commit_body,
        issue_ref=issue_key
    )

    # Save base branch for session
    state_manager.set_base_branch(gitops.original_branch)

    # Create branch and commit (use file_paths, not changes dict)
    try:
        success = gitops.create_branch_and_commit(branch_name, file_paths, msg, strategy=strategy)

        if success:
            if strategy == "local-merge":
                console.print(f"[green]✓ Committed and merged {branch_name}[/green]")
            else:
                console.print(f"[green]✓ Committed to {branch_name}[/green]")

            # Add comment to issue
            if task_mgmt and issue:
                group = {
                    "commit_title": commit_title,
                    "branch": branch_name,
                    "files": file_paths
                }
                task_mgmt.on_commit(group, {"issue_key": issue_key})
                console.print(f"[blue]✓ Comment added to {issue_key}[/blue]")

            # Transition to In Progress if configured
            if task_mgmt and issue and auto_transition:
                if issue.status.lower() not in ["in progress", "in development"]:
                    _transition_issue_with_strategy(task_mgmt, issue_key, "after_propose")

            # Save to session
            state_manager.add_session_branch(branch_name, issue_key)

            # Send commit notification
            _send_commit_notification(config, branch_name, issue_key, len(file_paths))

            console.print(f"\n[bold green]✅ All changes committed to {issue_key}[/bold green]")
            console.print("[dim]Run 'rg push' to push to remote[/dim]")
        else:
            console.print("[yellow]⚠️  No files to commit[/yellow]")

    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        raise typer.Exit(1)


def _is_notification_enabled(config: dict, event: str) -> bool:
    """Check if notification is enabled for a specific event."""
    return NotificationService(config).is_enabled(event)


def _send_commit_notification(config: dict, branch: str, issue_key: str = None, files_count: int = 0):
    """Send notification about commit creation."""
    NotificationService(config).send_commit(branch, issue_key, files_count)


def _send_issue_created_notification(config: dict, issue_key: str, summary: str = None):
    """Send notification about issue creation."""
    NotificationService(config).send_issue_created(issue_key, summary)


def _send_session_summary_notification(config: dict, branches_count: int, issues_count: int):
    """Send notification about session summary."""
    NotificationService(config).send_session_complete(branches_count, issues_count)


def _transition_issue_with_strategy(task_mgmt, issue_key: str, target_status: str = "after_propose") -> bool:
    """Transition issue using the configured strategy (auto or ask).

    Args:
        task_mgmt: Task management integration
        issue_key: Issue key to transition
        target_status: Target status mapping key (default: after_propose)

    Returns:
        True if transitioned, False if skipped or failed
    """
    strategy = getattr(task_mgmt, 'transition_strategy', 'auto')

    if strategy == 'ask':
        return _transition_issue_interactive(task_mgmt, issue_key)
    else:
        # Auto mode - use status mapping
        return task_mgmt.transition_issue(issue_key, target_status)


def _transition_issue_interactive(task_mgmt, issue_key: str) -> bool:
    """Interactively ask user to select target status for an issue.

    Returns:
        True if transitioned, False if skipped
    """
    try:
        # Get current issue info
        issue = task_mgmt.get_issue(issue_key)
        old_status = issue.status if issue else "Unknown"

        # Get available transitions
        transitions = task_mgmt.get_available_transitions(issue_key)

        if not transitions:
            console.print(f"[dim]   No transitions available for {issue_key}[/dim]")
            return False

        # Show options
        console.print(f"[dim]   Current status: {old_status}[/dim]")
        console.print("   [bold]Move to:[/bold]")
        for i, t in enumerate(transitions, 1):
            console.print(f"     [{i}] {t['to']}")
        console.print(f"     [0] Skip (don't change)")

        # Get user choice
        while True:
            choice = Prompt.ask("   Select", default="1")

            if choice == "0":
                console.print(f"[dim]   - {issue_key}: Skipped[/dim]")
                return False

            elif choice.isdigit() and 1 <= int(choice) <= len(transitions):
                idx = int(choice) - 1
                target_status = transitions[idx]["to"]
                transition_id = transitions[idx]["id"]

                if task_mgmt.transition_issue_by_id(issue_key, transition_id):
                    console.print(f"[blue]   → {issue_key}: {old_status} → {target_status}[/blue]")
                    return True
                else:
                    console.print(f"[yellow]   ⚠️  Could not transition {issue_key}[/yellow]")
                    return False

            else:
                console.print("[red]   Invalid choice[/red]")

    except Exception as e:
        console.print(f"[red]   ❌ Transition error: {e}[/red]")
        return False


def _enhance_groups_with_diffs(
    groups: List[Dict],
    gitops: GitOps,
    llm: LLMClient,
    issue_language: Optional[str] = None,
    verbose: bool = False,
    task_mgmt: Optional[TaskManagementBase] = None
) -> List[Dict]:
    """
    Enhance each group with detailed commit messages generated from file diffs.

    For each group:
    1. Get the diffs for all files in the group
    2. Send diffs to LLM with a specialized prompt (or integration's prompts if available)
    3. Generate detailed commit_title, commit_body, issue_title, issue_description

    Args:
        groups: List of commit groups from initial analysis
        gitops: GitOps instance for getting diffs
        llm: LLM client for generating messages
        issue_language: Language for issue titles/descriptions
        verbose: Show detailed output
        task_mgmt: Task management integration (for custom prompts)

    Returns:
        Enhanced groups with better commit messages
    """
    enhanced_groups = []

    # Debug: Show what we received
    if verbose:
        console.print(f"\n[bold cyan]═══ Detailed Mode Debug ═══[/bold cyan]")
        console.print(f"[dim]task_mgmt: {task_mgmt}[/dim]")
        console.print(f"[dim]task_mgmt.name: {task_mgmt.name if task_mgmt else 'N/A'}[/dim]")
        console.print(f"[dim]issue_language param: {issue_language}[/dim]")
        if task_mgmt:
            console.print(f"[dim]task_mgmt.issue_language: {getattr(task_mgmt, 'issue_language', 'NOT_FOUND')}[/dim]")
            console.print(f"[dim]has_user_prompt method: {hasattr(task_mgmt, 'has_user_prompt')}[/dim]")

    # Check if user has EXPORTED custom prompts for this integration
    # (not just built-in defaults)
    has_custom_prompts = False
    title_prompt_path = None
    desc_prompt_path = None

    if task_mgmt and hasattr(task_mgmt, 'has_user_prompt'):
        from ..core.common.config import RETGIT_DIR
        has_title = task_mgmt.has_user_prompt("issue_title")
        has_desc = task_mgmt.has_user_prompt("issue_description")
        if has_title or has_desc:
            has_custom_prompts = True
            if has_title:
                title_prompt_path = str(RETGIT_DIR / "prompts" / "integrations" / task_mgmt.name / "issue_title.md")
            if has_desc:
                desc_prompt_path = str(RETGIT_DIR / "prompts" / "integrations" / task_mgmt.name / "issue_description.md")
            if verbose:
                console.print(f"\n[bold cyan]═══ Integration Prompts ═══[/bold cyan]")
                console.print(f"[green]✓ Using USER-EXPORTED prompts for issue generation[/green]")
                if title_prompt_path:
                    console.print(f"[dim]  issue_title: {title_prompt_path}[/dim]")
                if desc_prompt_path:
                    console.print(f"[dim]  issue_description: {desc_prompt_path}[/dim]")
        elif verbose:
            console.print(f"\n[bold cyan]═══ Integration Prompts ═══[/bold cyan]")
            console.print(f"[dim]Using RedGit default prompts (no user exports found)[/dim]")
            console.print(f"[dim]  issue_title: builtin default[/dim]")
            console.print(f"[dim]  issue_description: builtin default[/dim]")

    for i, group in enumerate(groups, 1):
        files = group.get("files", [])
        if not files:
            enhanced_groups.append(group)
            continue

        if verbose:
            console.print(f"\n[bold cyan]═══ Detailed Analysis: Group {i}/{len(groups)} ═══[/bold cyan]")
            console.print(f"[dim]Files: {len(files)}[/dim]")
            for f in files[:5]:
                console.print(f"[dim]  - {f}[/dim]")
            if len(files) > 5:
                console.print(f"[dim]  ... and {len(files) - 5} more[/dim]")
        else:
            console.print(f"[dim]   ({i}/{len(groups)}) Analyzing {len(files)} files...[/dim]")

        # Get diffs for files in this group
        try:
            diffs = gitops.get_diffs_for_files(files)
        except Exception as e:
            if verbose:
                console.print(f"[yellow]⚠️  Could not get diffs: {e}[/yellow]")
            enhanced_groups.append(group)
            continue

        if not diffs:
            enhanced_groups.append(group)
            continue

        # Build prompt for detailed analysis
        # Use integration's prompts if available
        if has_custom_prompts:
            prompt = _build_detailed_analysis_prompt_with_integration(
                files=files,
                diffs=diffs,
                initial_title=group.get("commit_title", ""),
                initial_body=group.get("commit_body", ""),
                task_mgmt=task_mgmt
            )
            prompt_source = "integration prompts"
        else:
            prompt = _build_detailed_analysis_prompt(
                files=files,
                diffs=diffs,
                initial_title=group.get("commit_title", ""),
                initial_body=group.get("commit_body", ""),
                issue_language=issue_language
            )
            prompt_source = f"builtin (issue_language={issue_language or 'en'})"

        if verbose:
            console.print(f"\n[bold]Prompt Source:[/bold] {prompt_source}")
            console.print(f"[dim]Prompt length: {len(prompt)} chars[/dim]")
            # Show full prompt in a panel
            console.print(Panel(
                prompt[:4000] + ("..." if len(prompt) > 4000 else ""),
                title=f"[cyan]LLM Prompt (Group {i})[/cyan]",
                border_style="cyan"
            ))

        # Get detailed analysis from LLM
        try:
            result = llm.chat(prompt)

            if verbose:
                # Show raw response
                console.print(Panel(
                    result[:3000] + ("..." if len(result) > 3000 else ""),
                    title=f"[green]LLM Raw Response (Group {i})[/green]",
                    border_style="green"
                ))

            enhanced = _parse_detailed_result(result, group)

            if verbose:
                console.print(f"\n[bold]Parsed Result:[/bold]")
                console.print(f"[dim]  commit_title: {enhanced.get('commit_title', 'N/A')[:60]}[/dim]")
                console.print(f"[dim]  issue_title: {enhanced.get('issue_title', 'N/A')[:60]}[/dim]")
                console.print(f"[dim]  issue_description: {enhanced.get('issue_description', 'N/A')[:80]}...[/dim]")

            enhanced_groups.append(enhanced)
        except Exception as e:
            if verbose:
                console.print(f"[yellow]⚠️  LLM error, using original: {e}[/yellow]")
            enhanced_groups.append(group)

    return enhanced_groups


def _build_detailed_analysis_prompt(
    files: List[str],
    diffs: str,
    initial_title: str = "",
    initial_body: str = "",
    issue_language: Optional[str] = None
) -> str:
    """Build a prompt for detailed commit message analysis from diffs."""

    # Language instruction
    lang_instruction = ""
    if issue_language and issue_language != "en":
        lang_names = {
            "tr": "Turkish",
            "de": "German",
            "fr": "French",
            "es": "Spanish",
            "pt": "Portuguese",
            "it": "Italian",
            "ru": "Russian",
            "zh": "Chinese",
            "ja": "Japanese",
            "ko": "Korean"
        }
        lang_name = lang_names.get(issue_language, issue_language)
        lang_instruction = f"""
## IMPORTANT: Language Requirements
- **issue_title**: MUST be written in {lang_name}
- **issue_description**: MUST be written in {lang_name}
- commit_title and commit_body: English
"""

    # Truncate diffs if too long (max ~8000 chars for diff content)
    max_diff_length = 8000
    if len(diffs) > max_diff_length:
        diffs = diffs[:max_diff_length] + "\n\n... (diff truncated)"

    prompt = f"""Analyze these code changes and generate a detailed commit message and issue description.

## Files Changed
{chr(10).join(f"- {f}" for f in files)}

## Code Diff
```diff
{diffs}
```

## Initial Analysis
- Title: {initial_title}
- Body: {initial_body}
{lang_instruction}
## Task
Based on the actual code changes (diff), generate:

1. **commit_title**: A concise conventional commit message (feat/fix/refactor/chore) in English
2. **commit_body**: Bullet points describing what changed in English
3. **issue_title**: A clear title for a Jira/task management issue{' in ' + lang_names.get(issue_language, issue_language) if issue_language and issue_language != 'en' else ''}
4. **issue_description**: A detailed description of what this change does{' in ' + lang_names.get(issue_language, issue_language) if issue_language and issue_language != 'en' else ''}

## Response Format (JSON only)
```json
{{
  "commit_title": "feat: add user authentication",
  "commit_body": "- Add login endpoint\\n- Add JWT token validation\\n- Add password hashing",
  "issue_title": "Add user authentication feature",
  "issue_description": "This change implements user authentication including login, JWT tokens, and secure password handling."
}}
```

Return ONLY the JSON object, no other text.
"""
    return prompt


def _build_detailed_analysis_prompt_with_integration(
    files: List[str],
    diffs: str,
    initial_title: str = "",
    initial_body: str = "",
    task_mgmt: Optional[TaskManagementBase] = None
) -> str:
    """Build a prompt using integration's custom prompts for issue generation."""

    # Truncate diffs if too long
    max_diff_length = 8000
    if len(diffs) > max_diff_length:
        diffs = diffs[:max_diff_length] + "\n\n... (diff truncated)"

    file_list = "\n".join(f"- {f}" for f in files[:20])
    if len(files) > 20:
        file_list += f"\n... and {len(files) - 20} more"

    # Get language info from task_mgmt
    language = "English"
    if task_mgmt and hasattr(task_mgmt, 'issue_language'):
        lang_names = {
            "tr": "Turkish",
            "de": "German",
            "fr": "French",
            "es": "Spanish",
            "en": "English",
        }
        language = lang_names.get(task_mgmt.issue_language, task_mgmt.issue_language or "English")

    # Get custom prompts from integration
    title_prompt = ""
    desc_prompt = ""
    if task_mgmt and hasattr(task_mgmt, 'get_prompt'):
        title_prompt = task_mgmt.get_prompt("issue_title") or ""
        desc_prompt = task_mgmt.get_prompt("issue_description") or ""

    # Build combined prompt
    prompt = f"""Analyze these code changes and generate commit message and issue content.

## Files Changed
{file_list}

## Code Diff
```diff
{diffs}
```

## Initial Analysis
- Title: {initial_title}
- Body: {initial_body}

## TASK 1: Generate Commit Message (in English)
Generate:
- **commit_title**: A concise conventional commit message (feat/fix/refactor/chore)
- **commit_body**: Bullet points describing what changed

## TASK 2: Generate Issue Title
{title_prompt if title_prompt else f'Generate a clear issue title in {language}.'}

## TASK 3: Generate Issue Description
{desc_prompt if desc_prompt else f'Generate a detailed issue description in {language}.'}

## Response Format (JSON only)
```json
{{
  "commit_title": "feat: add feature name",
  "commit_body": "- Change 1\\n- Change 2",
  "issue_title": "Issue title in {language}",
  "issue_description": "Detailed description in {language}"
}}
```

Return ONLY the JSON object, no other text.
"""
    return prompt


def _parse_detailed_result(result: str, original_group: Dict) -> Dict:
    """Parse the LLM response and merge with original group."""
    import json

    # Try to extract JSON from response
    try:
        # Find JSON block
        start = result.find("{")
        end = result.rfind("}") + 1
        if start != -1 and end > start:
            json_str = result[start:end]
            data = json.loads(json_str)

            # Merge with original group
            enhanced = original_group.copy()
            if data.get("commit_title"):
                enhanced["commit_title"] = data["commit_title"]
            if data.get("commit_body"):
                enhanced["commit_body"] = data["commit_body"]
            if data.get("issue_title"):
                enhanced["issue_title"] = data["issue_title"]
            if data.get("issue_description"):
                enhanced["issue_description"] = data["issue_description"]

            return enhanced
    except (json.JSONDecodeError, Exception):
        pass

    return original_group


# ─────────────────────────────────────────────────────────────────────────────
# Usage Pattern Tracking Functions
# ─────────────────────────────────────────────────────────────────────────────

def _extract_param_pattern(
    prompt: Optional[str],
    no_task: bool,
    task: Optional[str],
    dry_run: bool,
    verbose: bool,
    detailed: bool,
    subtasks: bool
) -> List[str]:
    """Extract parameter names that were explicitly set.

    Returns a sorted list of parameter flags that were used.
    Values are excluded - only the flag names are tracked.
    """
    params = []
    if task:
        params.append("-t")
    if subtasks:
        params.append("--subtasks")
    if detailed:
        params.append("--detailed")
    if dry_run:
        params.append("--dry-run")
    if verbose:
        params.append("--verbose")
    if no_task:
        params.append("--no-task")
    if prompt:
        params.append("-p")
    return sorted(params)


def _is_bare_command(params: List[str]) -> bool:
    """Check if command was run without any parameters."""
    return len(params) == 0


def _suggest_and_ask_pattern(pattern: List[str]) -> bool:
    """Show suggestion and ask user if they want to use the common pattern.

    Returns True if user accepts, False if declined.
    """
    pattern_str = " ".join(pattern)
    console.print(f"\n[cyan]💡 Sık kullandığınız: rg propose {pattern_str}[/cyan]")
    console.print("[dim]Son 5 kullanımınıza göre[/dim]\n")
    return Confirm.ask("Bu şekilde kullanmak ister misiniz?", default=True)


def _prompt_for_pattern_values(pattern: List[str]) -> Dict[str, Any]:
    """Ask user for required values for the pattern.

    Returns dict with parameter values ready to use.
    """
    values: Dict[str, Any] = {}

    # Ask for values for params that require input
    if "-t" in pattern:
        values["task"] = Prompt.ask("Task ID (örn: SCRUM-123)")

    if "-p" in pattern:
        values["prompt"] = Prompt.ask("Prompt şablonu", default="default")

    # Boolean flags don't need values - just set them
    values["subtasks"] = "--subtasks" in pattern
    values["detailed"] = "--detailed" in pattern
    values["dry_run"] = "--dry-run" in pattern
    values["verbose"] = "--verbose" in pattern
    values["no_task"] = "--no-task" in pattern

    return values


# =============================================================================
# TASK-FILTERED MODE FUNCTIONS
# =============================================================================

def _ask_and_push_parent_branch(
    parent_branch: str,
    parent_task_key: str,
    gitops: GitOps,
    task_mgmt: TaskManagementBase,
    config: dict,
    strategy: str
) -> bool:
    """
    Ask user if they want to push the parent branch after subtasks are processed.

    Args:
        parent_branch: Parent branch name
        parent_task_key: Parent task key
        gitops: GitOps instance
        task_mgmt: Task management integration
        config: Configuration dict
        strategy: Merge strategy (local-merge or merge-request)

    Returns:
        True if pushed, False otherwise
    """
    console.print(f"\n[green]✓ Tüm subtask'lar {parent_task_key} parent branch'ine merge edildi.[/green]")
    console.print(f"[dim]Parent branch: {parent_branch}[/dim]")
    console.print(f"[dim]Merge stratejisi: {strategy}[/dim]")

    if Confirm.ask(f"Parent branch'i ({parent_branch}) pushlamak istiyor musunuz?", default=False):
        try:
            # Push the parent branch
            gitops.push(parent_branch)
            console.print(f"[green]✓ {parent_branch} pushed[/green]")

            # For merge-request strategy, create PR and show URL
            if strategy == "merge-request":
                code_hosting = get_code_hosting(config)
                if code_hosting and code_hosting.enabled:
                    # Get base branch from config or default to main
                    base_branch = config.get("git", {}).get("base_branch", "main")

                    # Create PR title from parent task key
                    pr_title = f"{parent_task_key}: Parent task branch"
                    pr_body = f"Parent task branch for {parent_task_key}\n\nContains all subtask commits merged."

                    try:
                        pr_url = code_hosting.create_pull_request(
                            title=pr_title,
                            body=pr_body,
                            head_branch=parent_branch,
                            base_branch=base_branch
                        )
                        if pr_url:
                            console.print(f"[green]✓ PR created: {pr_url}[/green]")
                            # Send notification if configured
                            try:
                                NotificationService(config).send_pr_created(parent_branch, pr_url, parent_task_key)
                            except Exception:
                                pass
                        else:
                            console.print(f"[yellow]PR oluşturulamadı. Manuel oluşturmak için:[/yellow]")
                            console.print(f"[cyan]gh pr create --base {base_branch} --head {parent_branch}[/cyan]")
                    except Exception as e:
                        console.print(f"[yellow]PR oluşturulurken hata: {e}[/yellow]")
                        console.print(f"[cyan]Manuel PR: gh pr create --base {base_branch} --head {parent_branch}[/cyan]")
                else:
                    # No code hosting configured, show manual command
                    base_branch = config.get("git", {}).get("base_branch", "main")
                    console.print(f"[cyan]PR oluşturmak için: gh pr create --base {base_branch} --head {parent_branch}[/cyan]")

            return True
        except Exception as e:
            console.print(f"[red]❌ Push failed: {e}[/red]")
            console.print(f"[dim]Manuel push: git push -u origin {parent_branch}[/dim]")
            return False
    else:
        console.print(f"[yellow]Parent branch push atlandı. İş devam ediyorsa daha sonra pushleyebilirsiniz.[/yellow]")
        console.print(f"[dim]Manuel push: git push -u origin {parent_branch}[/dim]")
        return False


# =============================================================================
# INTERACTIVE SETUP
# =============================================================================

def _interactive_setup(
    config: dict,
    task_mgmt: Optional[TaskManagementBase]
) -> dict:
    """
    Run interactive wizard to select propose options.

    Behavior changes based on task_mgmt availability:
    - With task_mgmt: Full options (auto, task, multi modes)
    - Without task_mgmt: Only auto mode, no issue creation options

    Args:
        config: Configuration dict
        task_mgmt: Task management integration (may be None)

    Returns:
        Dict with selected options: mode, task, detailed, create_policy, subtask_mode
    """
    options = {}
    has_task_mgmt = task_mgmt and task_mgmt.enabled

    console.print("\n[bold cyan]🔧 RG Propose - Interactive Setup[/bold cyan]\n")

    # Show warning if no task management
    if not has_task_mgmt:
        console.print("[yellow]⚠️  Task management entegrasyonu bulunamadı[/yellow]")
        console.print("[dim]   Task-related özellikler devre dışı[/dim]\n")

    # 1. Analysis Mode - only show all options if task_mgmt available
    if has_task_mgmt:
        mode_choice = Prompt.ask(
            "Analiz modu",
            choices=["auto", "task", "multi"],
            default="auto"
        )
        options["mode"] = mode_choice

        # 2. If task mode, ask for task ID
        if mode_choice == "task":
            task_id = Prompt.ask("Task ID (e.g., SCRUM-123)")
            options["task"] = task_id

        # 3. Subtask mode - ask for all modes when task management is available
        # (auto mode can auto-detect task from branch, so subtask is still relevant)
        console.print("\n[dim]Subtask modu: Her dosya grubu için parent task altında subtask oluşturur[/dim]")
        if mode_choice == "auto":
            console.print("[dim]   (auto modda branch'ten task tespit edilirse subtask oluşturulur)[/dim]")
        options["subtask_mode"] = Confirm.ask("Subtask modu aktif olsun mu?", default=True)

        # 4. Issue creation policy (only relevant if not using subtask mode)
        if not options.get("subtask_mode"):
            create_policy = Prompt.ask(
                "Issue oluşturma politikası",
                choices=["auto", "ask", "skip"],
                default="ask"
            )
            options["create_policy"] = create_policy
        else:
            options["create_policy"] = "auto"  # Subtask mode always creates
    else:
        # No task management - only auto mode
        options["mode"] = "auto"
        options["create_policy"] = "skip"
        options["subtask_mode"] = False

    # 5. Detailed mode (always available)
    options["detailed"] = Confirm.ask("Detaylı analiz (diff içerikleri)?", default=False)

    # 6. Save preferences
    save = Confirm.ask("Bu tercihleri kaydet?", default=False)
    if save:
        _save_interactive_preferences(options, config)
        console.print("[green]✓ Tercihler kaydedildi[/green]")

    return options


def _save_interactive_preferences(options: dict, config: dict) -> None:
    """Save interactive mode preferences to config."""
    try:
        config_manager = ConfigManager()
        full_config = config_manager.load()

        # Save to propose section
        if "propose" not in full_config:
            full_config["propose"] = {}

        full_config["propose"]["default_mode"] = options.get("mode", "auto")
        full_config["propose"]["detailed"] = options.get("detailed", False)
        full_config["propose"]["create_policy"] = options.get("create_policy", "ask")

        config_manager.save(full_config)
    except Exception as e:
        console.print(f"[yellow]Tercihler kaydedilemedi: {e}[/yellow]")


# =============================================================================
# MULTI-TASK MODE
# =============================================================================

def _process_multi_task_mode(
    changes: List[Dict],
    gitops: GitOps,
    task_mgmt: TaskManagementBase,
    state_manager: StateManager,
    config: dict,
    task_filter: Optional[str] = None,
    verbose: bool = False,
    detailed: bool = False,
    dry_run: bool = False,
    subtask_mode: bool = True
) -> None:
    """
    Process changes for multiple parent tasks.

    This mode:
    1. Fetches active tasks (all or filtered by task_filter)
    2. Uses LLM to determine which files belong to which task
    3. If subtask_mode: Creates subtasks under each parent task
    4. If not subtask_mode: Just groups commits by parent task
    5. Reports unmatched files

    Args:
        changes: List of file changes
        gitops: Git operations helper
        task_mgmt: Task management integration
        state_manager: State manager
        config: Configuration dict
        task_filter: Optional comma-separated task IDs to filter
        verbose: Show verbose output
        detailed: Use detailed analysis with diffs
        dry_run: Only show what would be done
        subtask_mode: If True, create subtasks under parent tasks
    """
    original_branch = gitops.original_branch
    workflow_strategy = config.get("workflow", {}).get("strategy", "local-merge")

    # 1. Fetch tasks - either from filter or all active
    if task_filter:
        # Parse comma-separated task IDs
        task_ids = [t.strip() for t in task_filter.split(",")]
        console.print(f"\n[cyan]Fetching specified tasks: {', '.join(task_ids)}...[/cyan]")

        parent_tasks = []
        for task_id in task_ids:
            # Handle numeric IDs (e.g., "123" -> "SCRUM-123")
            if task_id.isdigit() and hasattr(task_mgmt, 'project_key') and task_mgmt.project_key:
                task_id = f"{task_mgmt.project_key}-{task_id}"
            issue = task_mgmt.get_issue(task_id)
            if issue:
                parent_tasks.append(issue)
            else:
                console.print(f"[yellow]⚠️ Task {task_id} not found[/yellow]")
    else:
        # Fetch ALL active issues assigned to user
        console.print("\n[cyan]Fetching all active tasks assigned to me...[/cyan]")
        parent_tasks = task_mgmt.get_my_active_issues()

    if not parent_tasks:
        console.print("[yellow]No active tasks found. Use standard mode instead.[/yellow]")
        return

    # Filter tasks by project (epic name or labels should contain project name)
    # Get project name from config first, fallback to git remote
    project_config = config.get("project", {})
    project_name = project_config.get("name") or gitops.get_project_name()

    # Initialize filtered_tasks at function scope for later use
    filtered_tasks = []

    if project_name:
        excluded_tasks = []

        import re

        def matches_project_name(text: str) -> bool:
            """Check if text contains project name as whole word (case-insensitive)."""
            if not text:
                return False
            # Word boundary ile tam kelime eşleşmesi
            pattern = re.compile(r'\b' + re.escape(project_name) + r'\b', re.IGNORECASE)
            return bool(pattern.search(text))

        def task_matches_project(task) -> bool:
            """Check if task matches project via epic summary OR labels."""
            # 1. Epic/parent summary kontrolü
            epic_summary = getattr(task, 'parent_summary', None) or ""
            if matches_project_name(epic_summary):
                return True

            # 2. Labels kontrolü
            labels = getattr(task, 'labels', None) or []
            for label in labels:
                if matches_project_name(label):
                    return True

            return False

        for t in parent_tasks:
            # Check if task matches project via epic summary OR labels
            if task_matches_project(t):
                filtered_tasks.append(t)
            else:
                excluded_tasks.append(t)

        if excluded_tasks:
            console.print(f"\n[yellow]⚠️ Filtered out {len(excluded_tasks)} tasks from other projects:[/yellow]")
            for t in excluded_tasks:
                epic_info = getattr(t, 'parent_summary', '') or getattr(t, 'parent_key', '')
                if epic_info:
                    console.print(f"  [dim]• {t.key}: {t.summary[:40]}... (Epic: {epic_info[:30]})[/dim]")
                else:
                    console.print(f"  [dim]• {t.key}: {t.summary[:50]}[/dim]")

        parent_tasks = filtered_tasks

    if not parent_tasks:
        console.print("[yellow]No matching tasks found for this project. Use standard mode instead.[/yellow]")
        return

    console.print(f"\n[green]Found {len(parent_tasks)} active tasks for project '{project_name}'[/green]")
    for t in parent_tasks:
        epic_info = getattr(t, 'parent_summary', '') or getattr(t, 'parent_key', '')
        if epic_info:
            console.print(f"  [dim]• {t.key}: {t.summary[:40]}... ({epic_info[:25]})[/dim]")
        else:
            console.print(f"  [dim]• {t.key}: {t.summary[:50]}[/dim]")

    # 2. Build and send prompt
    llm = LLMClient(config.get("llm", {}))
    prompt_manager = PromptManager(config.get("llm", {}))
    issue_language = getattr(task_mgmt, 'issue_language', None)

    prompt = prompt_manager.get_multi_task_prompt(
        changes=changes,
        parent_tasks=parent_tasks,
        issue_language=issue_language
    )

    if verbose:
        console.print(f"\n[dim]Prompt length: {len(prompt)} characters[/dim]")

    console.print("\n[yellow]AI analyzing changes for multiple tasks...[/yellow]")
    result, raw_output = llm.generate_multi_task_groups(prompt, return_raw=True)

    if verbose:
        console.print(f"\n[dim]Raw AI output:[/dim]")
        console.print(f"[dim]{raw_output[:1000]}...[/dim]")

    # 3. Handle dry run
    if dry_run:
        from ..core.propose.display import show_multi_task_dry_run
        show_multi_task_dry_run(result, task_mgmt, subtask_mode)
        return

    # 4. Display results
    from ..core.propose.display import show_multi_task_summary
    show_multi_task_summary(result, subtask_mode)

    # 5. Confirm and process each task
    confirm_msg = "\nProceed with subtask creation?" if subtask_mode else "\nProceed with commits?"
    if not Confirm.ask(confirm_msg):
        console.print("[yellow]Cancelled.[/yellow]")
        return

    # 6. Initialize session tracking
    state = state_manager.load()
    if "session" not in state:
        state["session"] = {}
    state["session"]["base_branch"] = original_branch
    state["session"]["branches"] = []
    state["session"]["issues"] = []
    state["session"]["subtask_issues"] = []

    # 7. Process each task assignment
    for assignment in result.get("task_assignments", []):
        parent_key = assignment.get("task_key")
        subtask_groups = assignment.get("subtask_groups", [])

        if not subtask_groups:
            continue

        parent_issue = task_mgmt.get_issue(parent_key)
        if not parent_issue:
            console.print(f"[yellow]⚠️ Task {parent_key} not found, skipping[/yellow]")
            continue

        console.print(f"\n[bold cyan]Processing {parent_key}: {parent_issue.summary[:40]}...[/bold cyan]")

        # Process subtasks for this parent
        for group in subtask_groups:
            files = group.get("files", [])
            commit_title = group.get("commit_title", "changes")
            issue_title = group.get("issue_title", commit_title)
            issue_description = group.get("issue_description", "")
            commit_body = group.get("commit_body", "")

            if not files:
                continue

            try:
                if subtask_mode:
                    # Create subtask under parent
                    console.print(f"\n  [cyan]Creating subtask: {issue_title[:50]}...[/cyan]")

                    subtask_key = task_mgmt.create_subtask(
                        parent_key=parent_key,
                        summary=issue_title,
                        description=issue_description or f"Files:\n" + "\n".join(f"- {f}" for f in files)
                    )

                    if subtask_key:
                        console.print(f"  [green]✓ Created {subtask_key}[/green]")

                        # Create branch and commit
                        branch_name = task_mgmt.format_branch_name(subtask_key, issue_title)

                        if workflow_strategy == "merge-request":
                            # Create separate branch for each subtask
                            gitops.checkout_or_create_branch(branch_name)
                            gitops.stage_files(files)
                            full_commit = build_commit_message(commit_title, commit_body)
                            gitops.commit(full_commit)
                            console.print(f"  [green]✓ Committed to {branch_name}[/green]")

                            # Track branch for push
                            state["session"]["branches"].append({
                                "branch": branch_name,
                                "issue_key": subtask_key,
                                "files": files
                            })
                        else:
                            # local-merge: commit directly to current branch
                            gitops.stage_files(files)
                            full_commit = build_commit_message(commit_title, commit_body)
                            gitops.commit(full_commit)
                            console.print(f"  [green]✓ Committed: {commit_title}[/green]")

                            # Track as merged branch
                            state["session"]["branches"].append({
                                "branch": original_branch,
                                "issue_key": subtask_key,
                                "files": files
                            })

                        # Track subtask for issue transition
                        state["session"]["subtask_issues"].append(subtask_key)

                        # Transition subtask if configured
                        if config.get("workflow", {}).get("auto_transition", False):
                            task_mgmt.transition_issue(subtask_key, "start")
                    else:
                        console.print(f"  [red]✗ Failed to create subtask[/red]")

                else:
                    # No subtask mode - just commit with parent task reference
                    console.print(f"\n  [cyan]Committing: {commit_title[:50]}...[/cyan]")

                    # Prefix commit with parent task key
                    prefixed_title = f"{parent_key}: {commit_title}"
                    full_commit = build_commit_message(prefixed_title, commit_body)

                    if workflow_strategy == "merge-request":
                        # Create branch for parent task
                        branch_name = task_mgmt.format_branch_name(parent_key, issue_title)

                        # Check if we're already on this branch
                        current = gitops.repo.active_branch.name
                        if current != branch_name:
                            try:
                                gitops.repo.git.checkout(branch_name)
                            except Exception:
                                gitops.checkout_or_create_branch(branch_name)

                        gitops.stage_files(files)
                        gitops.commit(full_commit)
                        console.print(f"  [green]✓ Committed to {branch_name}[/green]")

                        # Track branch (avoid duplicates)
                        existing_branches = [b["branch"] for b in state["session"]["branches"]]
                        if branch_name not in existing_branches:
                            state["session"]["branches"].append({
                                "branch": branch_name,
                                "issue_key": parent_key,
                                "files": files
                            })
                        else:
                            # Add files to existing branch entry
                            for b in state["session"]["branches"]:
                                if b["branch"] == branch_name:
                                    b["files"].extend(files)
                                    break
                    else:
                        # local-merge: commit to current branch
                        gitops.stage_files(files)
                        gitops.commit(full_commit)
                        console.print(f"  [green]✓ Committed: {prefixed_title[:60]}[/green]")

                        state["session"]["branches"].append({
                            "branch": original_branch,
                            "issue_key": parent_key,
                            "files": files
                        })

                    # Track parent issue for completion
                    if parent_key not in state["session"]["issues"]:
                        state["session"]["issues"].append(parent_key)

            except Exception as e:
                console.print(f"  [red]✗ Failed: {e}[/red]")
                if verbose:
                    import traceback
                    console.print(f"  [dim]{traceback.format_exc()}[/dim]")

    # 8. Save session
    state_manager.save(state)
    console.print(f"\n[green]✓ Session saved ({len(state['session']['branches'])} branches)[/green]")

    # 9. Report unmatched files
    unmatched = result.get("unmatched_files", [])
    if unmatched:
        console.print(f"\n[yellow]Unmatched files ({len(unmatched)}):[/yellow]")
        for f in unmatched[:10]:
            console.print(f"  [dim]• {f}[/dim]")
        if len(unmatched) > 10:
            console.print(f"  [dim]... and {len(unmatched) - 10} more[/dim]")

    # 10. Return to original branch
    try:
        gitops.checkout_branch(original_branch)
        console.print(f"\n[green]✓ Returned to {original_branch}[/green]")
    except Exception:
        pass

    # 11. Show next steps
    console.print("\n[bold cyan]Next steps:[/bold cyan]")
    if workflow_strategy == "merge-request":
        console.print("  [dim]• rg push --pr   - Push branches and create merge requests[/dim]")
    else:
        console.print("  [dim]• rg push        - Push commits to remote[/dim]")
    console.print("  [dim]• rg session     - View current session[/dim]")


def _process_task_filtered_mode(
    task_id: str,
    changes: List[Dict],
    gitops: GitOps,
    task_mgmt: TaskManagementBase,
    state_manager: StateManager,
    config: dict,
    verbose: bool = False,
    detailed: bool = False,
    force: bool = False
) -> None:
    """
    Process task-filtered mode: analyze files for relevance to parent task.

    This mode:
    1. Fetches parent task details
    2. Uses LLM to analyze which files relate to the parent task (unless force=True)
    3. Creates subtasks only for related files
    4. Matches unrelated files to user's other open tasks
    5. Reports truly unmatched files
    6. Asks to push parent branch
    7. ALWAYS returns to original branch at the end

    Args:
        task_id: Parent task ID (e.g., "123" or "PROJ-123")
        changes: List of file changes
        gitops: GitOps instance
        task_mgmt: Task management integration
        state_manager: State manager
        config: Configuration dict
        verbose: Enable verbose output
        detailed: Enable detailed mode
        force: Skip LLM relevance check, commit all files to parent task
    """
    # Save original branch to return to at the end
    original_branch = gitops.original_branch
    console.print(f"[dim]Başlangıç branch: {original_branch}[/dim]")

    # Initialize variables for finally block
    parent_branch = None
    parent_task_key = None

    try:
        # Resolve task key (handle numeric IDs)
        if task_id.isdigit() and hasattr(task_mgmt, 'project_key') and task_mgmt.project_key:
            parent_task_key = f"{task_mgmt.project_key}-{task_id}"
        else:
            parent_task_key = task_id

        # Fetch parent task
        console.print(f"\n[cyan]Fetching parent task {parent_task_key}...[/cyan]")
        parent_issue = task_mgmt.get_issue(parent_task_key)

        if not parent_issue:
            console.print(f"[red]❌ Parent task {parent_task_key} not found[/red]")
            raise typer.Exit(1)

        console.print(f"[green]✓ Parent task: {parent_task_key} - {parent_issue.summary}[/green]")
        if parent_issue.description:
            desc_preview = parent_issue.description[:200] + "..." if len(parent_issue.description) > 200 else parent_issue.description
            console.print(f"[dim]   {desc_preview}[/dim]")

        # Fetch user's other active tasks
        console.print("\n[cyan]Fetching other active tasks...[/cyan]")
        all_active_issues = task_mgmt.get_my_active_issues()
        other_tasks = [i for i in all_active_issues if i.key != parent_task_key]
        console.print(f"[dim]   Found {len(other_tasks)} other active tasks[/dim]")

        # Get issue language if configured
        issue_language = getattr(task_mgmt, 'issue_language', None)

        # Use LLM to analyze and group files
        console.print("\n[yellow]Analyzing file relevance to parent task...[/yellow]")
        llm = LLMClient(config.get("llm", {}))
        prompt_manager = PromptManager(config.get("llm", {}))

        prompt = prompt_manager.get_task_filtered_prompt(
            changes=changes,
            parent_task=parent_issue,
            other_tasks=other_tasks,
            issue_language=issue_language
        )

        if verbose:
            console.print(f"\n[bold cyan]=== Task-Filtered Prompt ===[/bold cyan]")
            console.print(Panel(prompt[:3000] + ("..." if len(prompt) > 3000 else ""), title="Prompt", border_style="cyan"))

        # Generate task-filtered groups
        result = llm.generate_task_filtered_groups(prompt)

        if verbose:
            console.print(f"\n[bold cyan]=== LLM Response ===[/bold cyan]")
            console.print(f"Related groups: {len(result['related_groups'])}")
            console.print(f"Other task matches: {len(result['other_task_matches'])}")
            console.print(f"Unmatched files: {len(result['unmatched_files'])}")

        # Force mode: move all groups to related_groups (skip task relevance filtering)
        if force:
            console.print("\n[yellow]Force mode: Tüm dosyalar parent task ile ilişkili kabul ediliyor[/yellow]")

            # Move other_task_matches to related_groups
            for match in result.get('other_task_matches', []):
                result['related_groups'].append({
                    'files': match.get('files', []),
                    'commit_title': match.get('commit_title', 'Changes'),
                    'commit_body': match.get('commit_body', ''),
                    'issue_title': match.get('issue_title', match.get('commit_title', 'Changes')),
                    'issue_description': match.get('issue_description', ''),
                    'relevance_reason': f"Force mode - originally matched {match.get('issue_key', 'other task')}"
                })

            # Move unmatched_files to a new related_group
            if result.get('unmatched_files'):
                result['related_groups'].append({
                    'files': result['unmatched_files'],
                    'commit_title': 'chore: miscellaneous changes',
                    'commit_body': '',
                    'issue_title': 'Diğer değişiklikler',
                    'issue_description': 'Force mode ile eklenen dosyalar',
                    'relevance_reason': 'Force mode - originally unmatched files'
                })

            # Clear other categories
            result['other_task_matches'] = []
            result['unmatched_files'] = []

            console.print(f"\n[bold]Force Mode:[/bold]")
            total_files = sum(len(g.get('files', [])) for g in result['related_groups'])
            console.print(f"  [green]✓ {total_files} dosya {len(result['related_groups'])} subtask olarak {parent_task_key} altına commit edilecek[/green]")
        else:
            # Normal mode: show summary with filtering
            console.print("\n[bold]Analysis Results:[/bold]")
            console.print(f"  [green]✓ {len(result['related_groups'])} subtask(s) for {parent_task_key}[/green]")
            if result['other_task_matches']:
                console.print(f"  [blue]→ {len(result['other_task_matches'])} group(s) match other tasks[/blue]")
            if result['unmatched_files']:
                console.print(f"  [yellow]○ {len(result['unmatched_files'])} file(s) unmatched[/yellow]")

        # Get workflow config
        workflow = config.get("workflow", {})
        strategy = workflow.get("strategy", "local-merge")

        # Determine parent branch
        parent_branch = task_mgmt.format_branch_name(parent_task_key, parent_issue.summary)

        # Check if we're already on the parent branch (or a matching task branch)
        is_already_on_parent = (
            original_branch == parent_branch or
            parent_task_key.lower() in original_branch.lower()
        )

        if is_already_on_parent:
            console.print(f"\n[dim]Zaten parent task branch'indesiniz: {original_branch}[/dim]")
            # Use original branch as parent branch since we're already there
            parent_branch = original_branch
        else:
            # Setup parent branch (create or checkout)
            console.print(f"\n[bold cyan]Setting up parent branch: {parent_branch}[/bold cyan]")

            # Check if parent branch exists on remote or locally
            if gitops.remote_branch_exists(parent_branch):
                console.print(f"[dim]Parent branch exists on remote, checking out and pulling...[/dim]")
                success, is_new, error = gitops.checkout_or_create_branch(
                    parent_branch,
                    from_branch=original_branch,
                    pull_if_exists=True
                )
                if not success:
                    console.print(f"[red]❌ Failed to checkout parent branch: {error}[/red]")
                    raise typer.Exit(1)
                console.print(f"[green]✓ Checked out existing branch: {parent_branch}[/green]")
            else:
                # Check if exists locally
                local_branches = [b.name for b in gitops.repo.branches]
                if parent_branch in local_branches:
                    console.print(f"[dim]Parent branch exists locally, checking out...[/dim]")
                    success, is_new, error = gitops.checkout_or_create_branch(
                        parent_branch,
                        from_branch=original_branch,
                        pull_if_exists=False
                    )
                    if not success:
                        console.print(f"[red]❌ Failed to checkout parent branch: {error}[/red]")
                        raise typer.Exit(1)
                    console.print(f"[green]✓ Checked out existing local branch: {parent_branch}[/green]")
                else:
                    # Create new parent branch from original
                    success, is_new, error = gitops.checkout_or_create_branch(
                        parent_branch,
                        from_branch=original_branch,
                        pull_if_exists=False
                    )
                    if not success:
                        console.print(f"[red]❌ Failed to create parent branch: {error}[/red]")
                        raise typer.Exit(1)
                    console.print(f"[green]✓ Created new branch: {parent_branch}[/green]")

        # 2. Process related groups as subtasks (from parent branch)
        if result['related_groups']:
            console.print(f"\n[bold cyan]Creating subtasks under {parent_task_key}...[/bold cyan]")
            _process_related_groups_as_subtasks(
                groups=result['related_groups'],
                parent_task_key=parent_task_key,
                parent_issue=parent_issue,
                parent_branch=parent_branch,
                gitops=gitops,
                task_mgmt=task_mgmt,
                state_manager=state_manager,
                config=config,
                strategy=strategy
            )

        # 3. Process other task matches
        if result['other_task_matches']:
            console.print(f"\n[bold blue]Processing matches with other tasks...[/bold blue]")
            _process_other_task_matches(
                matches=result['other_task_matches'],
                gitops=gitops,
                task_mgmt=task_mgmt,
                state_manager=state_manager,
                config=config,
                strategy=strategy
            )

        # 4. Handle unmatched files
        if result['unmatched_files']:
            console.print(f"\n[bold yellow]Handling unmatched files...[/bold yellow]")
            excluded_files = _handle_unmatched_files(
                files=result['unmatched_files'],
                gitops=gitops,
                task_mgmt=task_mgmt,
                state_manager=state_manager,
                config=config,
                strategy=strategy,
                filtered_tasks=filtered_tasks  # Proje ile eşleşen tasklar
            )
            if excluded_files:
                console.print(f"\n[yellow]⚠️  {len(excluded_files)} dosya commitlenmedi[/yellow]")

        # 5. Ask about pushing parent branch (only if subtasks were created)
        if result['related_groups']:
            _ask_and_push_parent_branch(
                parent_branch=parent_branch,
                parent_task_key=parent_task_key,
                gitops=gitops,
                task_mgmt=task_mgmt,
                config=config,
                strategy=strategy
            )

            # Track branch in session
            state_manager.add_session_branch(parent_branch, parent_task_key)

        # Show session summary
        session = state_manager.get_session()
        branches = session.get("branches", [])
        subtask_issues = session.get("subtask_issues", [])

        console.print(f"\n[bold green]✅ Session complete[/bold green]")
        if subtask_issues:
            console.print(f"[dim]   {len(subtask_issues)} subtask(s) created under {parent_task_key}[/dim]")
        if branches:
            console.print(f"[dim]   {len(branches)} branch(es) ready[/dim]")

    finally:
        # ALWAYS return to original branch
        try:
            current_branch = gitops.repo.active_branch.name
            if current_branch != original_branch:
                console.print(f"\n[cyan]Orijinal branch'e dönülüyor: {original_branch}[/cyan]")
                gitops.checkout(original_branch)
                console.print(f"[green]✓ {original_branch} branch'ine dönüldü[/green]")
        except Exception as e:
            console.print(f"[yellow]⚠ Orijinal branch'e dönülemedi: {e}[/yellow]")
            console.print(f"[dim]Manuel olarak dönmek için: git checkout {original_branch}[/dim]")


def _process_related_groups_as_subtasks(
    groups: List[Dict],
    parent_task_key: str,
    parent_issue: Issue,
    parent_branch: str,
    gitops: GitOps,
    task_mgmt: TaskManagementBase,
    state_manager: StateManager,
    config: dict,
    strategy: str = "local-merge"
) -> None:
    """
    Process related groups as subtasks under the parent task.

    Creates subtask issues in task management and commits files to subtask branches
    that are created FROM the parent branch and merged back to it.

    Args:
        groups: List of related file groups
        parent_task_key: Parent task key (e.g., SCRUM-858)
        parent_issue: Parent issue object
        parent_branch: Parent branch name to create subtasks from
        gitops: Git operations instance
        task_mgmt: Task management integration
        state_manager: Session state manager
        config: Configuration dict
        strategy: Merge strategy
    """
    for i, group in enumerate(groups, 1):
        files = group.get("files", [])
        if not files:
            continue

        commit_title = group.get("commit_title", f"Subtask {i}")
        commit_body = group.get("commit_body", "")
        issue_title = group.get("issue_title", commit_title)
        issue_description = group.get("issue_description", commit_body)
        relevance_reason = group.get("relevance_reason", "")

        console.print(f"\n[cyan]Subtask {i}: {issue_title}[/cyan]")
        console.print(f"[dim]   Files: {', '.join(files[:3])}{'...' if len(files) > 3 else ''}[/dim]")
        if relevance_reason:
            console.print(f"[dim]   Reason: {relevance_reason}[/dim]")

        # Create subtask issue
        subtask_key = None
        try:
            subtask_key = task_mgmt.create_issue(
                summary=issue_title,
                description=issue_description,
                issue_type="subtask",
                parent_key=parent_task_key
            )
            if subtask_key:
                console.print(f"[green]   ✓ Created subtask: {subtask_key}[/green]")
        except Exception as e:
            console.print(f"[yellow]   ⚠️ Could not create subtask: {e}[/yellow]")
            # Use parent task key as fallback
            subtask_key = parent_task_key

        # Create subtask branch FROM parent branch, commit, and merge back to parent
        subtask_branch = task_mgmt.format_branch_name(subtask_key or parent_task_key, commit_title)
        msg = build_commit_message(
            title=commit_title,
            body=commit_body,
            issue_ref=subtask_key if subtask_key else None
        )

        # Use create_subtask_branch_and_commit which creates branch FROM parent_branch
        success = gitops.create_subtask_branch_and_commit(
            subtask_branch=subtask_branch,
            parent_branch=parent_branch,
            files=files,
            message=msg
        )

        if success:
            console.print(f"[green]   ✓ Committed and merged to {parent_branch}[/green]")

            # Track subtask issue for transition on push
            state = state_manager.load()
            if "session" not in state:
                state["session"] = {"base_branch": None, "branches": [], "issues": []}
            state["session"].setdefault("subtask_issues", []).append(subtask_key or parent_task_key)
            state_manager.save(state)

            # Add comment to issue
            if subtask_key:
                task_mgmt.on_commit(group, {"issue_key": subtask_key})
        else:
            console.print(f"[red]   ❌ Failed to commit[/red]")


def _process_other_task_matches(
    matches: List[Dict],
    gitops: GitOps,
    task_mgmt: TaskManagementBase,
    state_manager: StateManager,
    config: dict,
    strategy: str = "local-merge"
) -> None:
    """
    Process files that match other active tasks.

    Shows matches to user and asks for confirmation before committing.
    """
    for match in matches:
        issue_key = match.get("issue_key")
        files = match.get("files", [])
        commit_title = match.get("commit_title", f"Changes for {issue_key}")
        reason = match.get("reason", "")

        if not files or not issue_key:
            continue

        # Verify issue exists
        issue = task_mgmt.get_issue(issue_key)
        if not issue:
            console.print(f"[yellow]⚠️ Issue {issue_key} not found, skipping[/yellow]")
            continue

        console.print(f"\n[blue]Match found: {issue_key} - {issue.summary}[/blue]")
        console.print(f"[dim]   Files: {', '.join(files[:5])}{'...' if len(files) > 5 else ''}[/dim]")
        if reason:
            console.print(f"[dim]   Reason: {reason}[/dim]")

        # Ask user for confirmation
        if Confirm.ask(f"   Commit these {len(files)} file(s) to {issue_key}?", default=True):
            branch_name = task_mgmt.format_branch_name(issue_key, commit_title)
            msg = build_commit_message(
                title=commit_title,
                body="",
                issue_ref=issue_key
            )

            success = gitops.create_branch_and_commit(branch_name, files, msg, strategy=strategy)
            if success:
                console.print(f"[green]   ✓ Committed to {branch_name}[/green]")
                state_manager.add_session_branch(branch_name, issue_key)
                task_mgmt.on_commit({"commit_title": commit_title, "files": files}, {"issue_key": issue_key})
            else:
                console.print(f"[red]   ❌ Failed to commit[/red]")
        else:
            console.print(f"[dim]   Skipped - files left in working directory[/dim]")


def _handle_unmatched_files(
    files: List[str],
    gitops: GitOps,
    task_mgmt: TaskManagementBase,
    state_manager: StateManager,
    config: dict,
    strategy: str = "local-merge",
    filtered_tasks: List = None
) -> List[str]:
    """
    Handle files that don't match any task.

    Uses create_branch_and_commit() for all commit options to respect
    the workflow strategy (local-merge vs merge-request).

    Options:
    1. Assign to existing filtered task
    2. Create new task for them
    3. Commit without task association (new branch)
    4. Leave in working directory (skip)

    Returns:
        List of files that were excluded (left in working directory)
    """
    if not files:
        return []

    excluded_files = []

    console.print(f"\n[yellow]⚠️  {len(files)} dosya hiçbir task ile eşleşmedi:[/yellow]")
    for f in files[:10]:
        console.print(f"  [dim]• {f}[/dim]")
    if len(files) > 10:
        console.print(f"  [dim]... ve {len(files) - 10} dosya daha[/dim]")

    # Toplu işlem seçenekleri
    console.print("\n[bold]Seçenekler:[/bold]")
    if filtered_tasks:
        console.print("  [1] Mevcut tasklerden birine ata")
    console.print("  [2] Yeni task oluştur")
    console.print("  [3] Tasksız commit at (yeni branch)")
    console.print("  [4] Working tree'de bırak")

    choices = ["1", "2", "3", "4"] if filtered_tasks else ["2", "3", "4"]
    choice = Prompt.ask("Seçim", choices=choices, default="4")

    if choice == "1" and filtered_tasks:
        # Mevcut tasklerden seç
        console.print("\n[bold]Mevcut taskler:[/bold]")
        for i, task in enumerate(filtered_tasks, 1):
            console.print(f"  [{i}] {task.key}: {task.summary[:50]}")

        task_choice = Prompt.ask("Task numarası seçin")
        try:
            idx = int(task_choice) - 1
            if 0 <= idx < len(filtered_tasks):
                selected_task = filtered_tasks[idx]
                branch_name = task_mgmt.format_branch_name(selected_task.key, selected_task.summary)
                msg = build_commit_message(
                    title=f"chore: add files to {selected_task.key}",
                    body="",
                    issue_ref=selected_task.key
                )
                # Strateji'ye göre branch oluştur ve commit et
                success = gitops.create_branch_and_commit(branch_name, files, msg, strategy=strategy)
                if success:
                    if strategy == "local-merge":
                        console.print(f"[green]✓ Committed and merged {branch_name}[/green]")
                    else:
                        console.print(f"[green]✓ Committed to {branch_name}[/green]")
                    state_manager.add_session_branch(branch_name, selected_task.key)
            else:
                console.print("[yellow]Geçersiz seçim, dosyalar working tree'de bırakıldı[/yellow]")
                excluded_files = files
        except ValueError:
            console.print("[yellow]Geçersiz giriş, dosyalar working tree'de bırakıldı[/yellow]")
            excluded_files = files

    elif choice == "2":
        # Yeni task oluştur
        summary = Prompt.ask("Yeni task başlığı")
        if Confirm.ask(f"'{summary}' taskını oluştur?"):
            issue_key = task_mgmt.create_issue(
                summary=summary,
                description="",
                issue_type="task"
            )
            if issue_key:
                console.print(f"[green]✓ Task oluşturuldu: {issue_key}[/green]")
                branch_name = task_mgmt.format_branch_name(issue_key, summary)
                msg = build_commit_message(title=summary, body="", issue_ref=issue_key)
                success = gitops.create_branch_and_commit(branch_name, files, msg, strategy=strategy)
                if success:
                    if strategy == "local-merge":
                        console.print(f"[green]✓ Committed and merged {branch_name}[/green]")
                    else:
                        console.print(f"[green]✓ Committed to {branch_name}[/green]")
                    state_manager.add_session_branch(branch_name, issue_key)
            else:
                console.print("[red]❌ Task oluşturulamadı[/red]")
                excluded_files = files
        else:
            console.print("[dim]Task oluşturulmadı, dosyalar working tree'de bırakıldı[/dim]")
            excluded_files = files

    elif choice == "3":
        # Tasksız commit - yine de yeni branch aç
        commit_title = Prompt.ask("Commit başlığı", default="chore: miscellaneous changes")
        # Branch adı oluştur (task ref olmadan)
        clean_title = commit_title.lower()
        clean_title = "".join(c if c.isalnum() or c == " " else "" for c in clean_title)
        clean_title = clean_title.strip().replace(" ", "-")[:40]
        branch_name = f"chore/{clean_title}"

        msg = commit_title  # Task ref yok
        success = gitops.create_branch_and_commit(branch_name, files, msg, strategy=strategy)
        if success:
            if strategy == "local-merge":
                console.print(f"[green]✓ Committed and merged {branch_name}[/green]")
            else:
                console.print(f"[green]✓ Committed to {branch_name}[/green]")
            state_manager.add_session_branch(branch_name, None)  # issue_key = None
        else:
            console.print("[red]❌ Commit başarısız[/red]")
            excluded_files = files

    else:  # choice == "4"
        console.print("[dim]Dosyalar working tree'de bırakıldı[/dim]")
        excluded_files = files

    return excluded_files


def _show_task_filtered_dry_run(
    task_id: str,
    changes: List[Dict],
    gitops: GitOps,
    task_mgmt: TaskManagementBase,
    config: dict,
    verbose: bool = False
) -> None:
    """
    Show dry-run preview for task-filtered mode.

    Analyzes files without making any changes.
    """
    console.print(Panel("[bold yellow]DRY RUN - Task Filtered Mode[/bold yellow]", style="yellow"))

    # Resolve task key
    if task_id.isdigit() and hasattr(task_mgmt, 'project_key') and task_mgmt.project_key:
        parent_task_key = f"{task_mgmt.project_key}-{task_id}"
    else:
        parent_task_key = task_id

    # Fetch parent task
    console.print(f"\n[cyan]Fetching parent task {parent_task_key}...[/cyan]")
    parent_issue = task_mgmt.get_issue(parent_task_key)

    if not parent_issue:
        console.print(f"[red]❌ Parent task {parent_task_key} not found[/red]")
        return

    console.print(f"[green]✓ Parent task: {parent_task_key} - {parent_issue.summary}[/green]")

    # Fetch other tasks
    all_active_issues = task_mgmt.get_my_active_issues()
    other_tasks = [i for i in all_active_issues if i.key != parent_task_key]

    # Get issue language if configured
    issue_language = getattr(task_mgmt, 'issue_language', None)

    # Create LLM and prompt
    console.print("\n[yellow]Analyzing file relevance...[/yellow]")
    llm = LLMClient(config.get("llm", {}))
    prompt_manager = PromptManager(config.get("llm", {}))

    prompt = prompt_manager.get_task_filtered_prompt(
        changes=changes,
        parent_task=parent_issue,
        other_tasks=other_tasks,
        issue_language=issue_language
    )

    if verbose:
        console.print(f"\n[bold cyan]=== Prompt ===[/bold cyan]")
        console.print(Panel(prompt[:2000] + ("..." if len(prompt) > 2000 else ""), border_style="cyan"))

    # Generate task-filtered groups
    result = llm.generate_task_filtered_groups(prompt)

    # Show results
    console.print("\n[bold]Preview Results:[/bold]")

    if result['related_groups']:
        console.print(f"\n[bold green]Related to {parent_task_key} ({len(result['related_groups'])} subtask(s)):[/bold green]")
        for i, group in enumerate(result['related_groups'], 1):
            title = group.get('issue_title', group.get('commit_title', f'Subtask {i}'))
            files = group.get('files', [])
            reason = group.get('relevance_reason', '')
            console.print(f"  [{i}] {title}")
            console.print(f"      [dim]Files: {', '.join(files[:3])}{'...' if len(files) > 3 else ''}[/dim]")
            if reason:
                console.print(f"      [dim]Reason: {reason}[/dim]")

    if result['other_task_matches']:
        console.print(f"\n[bold blue]Matches with other tasks ({len(result['other_task_matches'])}):[/bold blue]")
        for match in result['other_task_matches']:
            issue_key = match.get('issue_key', 'Unknown')
            files = match.get('files', [])
            reason = match.get('reason', '')
            console.print(f"  → {issue_key}: {len(files)} file(s)")
            if reason:
                console.print(f"    [dim]Reason: {reason}[/dim]")

    if result['unmatched_files']:
        console.print(f"\n[bold yellow]Unmatched files ({len(result['unmatched_files'])}):[/bold yellow]")
        for f in result['unmatched_files'][:10]:
            console.print(f"  - {f}")
        if len(result['unmatched_files']) > 10:
            console.print(f"  ... and {len(result['unmatched_files']) - 10} more")

    # Summary
    total_related = sum(len(g.get('files', [])) for g in result['related_groups'])
    total_other = sum(len(m.get('files', [])) for m in result['other_task_matches'])
    total_unmatched = len(result['unmatched_files'])

    console.print(f"\n[bold]Summary:[/bold]")
    console.print(f"  Total files: {len(changes)}")
    console.print(f"  Related to {parent_task_key}: {total_related}")
    console.print(f"  Match other tasks: {total_other}")
    console.print(f"  Unmatched: {total_unmatched}")

    console.print("\n[dim]Run without --dry-run to apply these changes[/dim]")