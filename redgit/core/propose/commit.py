"""
Commit-related utilities for building messages and managing branches.

This module centralizes commit message building and branch creation logic,
reducing code duplication across the propose command.
"""

from dataclasses import dataclass
from typing import Optional, List

from ..common.constants import REDGIT_SIGNATURE
from ..common.gitops import GitOps


@dataclass
class CommitResult:
    """Result of a commit operation."""
    success: bool
    branch_name: str
    issue_key: Optional[str] = None
    files_committed: int = 0
    error: Optional[str] = None


def build_commit_message(
    title: str,
    body: str = "",
    issue_ref: Optional[str] = None
) -> str:
    """
    Build commit message with RedGit signature.

    Args:
        title: Commit title (first line)
        body: Commit body (details)
        issue_ref: Issue reference (e.g., "PROJ-123")

    Returns:
        Complete commit message with RedGit signature
    """
    msg = title
    if body:
        msg += f"\n\n{body}"
    if issue_ref:
        msg += f"\n\nRefs: {issue_ref}"
    msg += REDGIT_SIGNATURE
    return msg


def execute_commit_group(
    gitops: GitOps,
    files: List[str],
    branch_name: str,
    message: str,
    strategy: str = "local-merge",
    parent_branch: Optional[str] = None
) -> CommitResult:
    """
    Execute a commit for a group of files with consistent error handling.

    This function consolidates the repeated commit execution pattern found
    in _process_matched_groups, _process_unmatched_groups, _process_subtasks_mode,
    _process_related_groups_as_subtasks, and _process_other_task_matches.

    Args:
        gitops: GitOps instance for git operations
        files: List of file paths to commit
        branch_name: Target branch name
        message: Complete commit message
        strategy: Workflow strategy ("local-merge" or "merge-request")
        parent_branch: Parent branch for subtask mode (optional)

    Returns:
        CommitResult with success status and details
    """
    try:
        if parent_branch:
            # Subtask mode: use create_subtask_branch_and_commit
            success = gitops.create_subtask_branch_and_commit(
                subtask_branch=branch_name,
                parent_branch=parent_branch,
                files=files,
                message=message,
                strategy=strategy
            )
        else:
            # Standard mode: use create_branch_and_commit
            success = gitops.create_branch_and_commit(
                branch_name=branch_name,
                files=files,
                message=message,
                strategy=strategy
            )

        if success:
            return CommitResult(
                success=True,
                branch_name=branch_name,
                files_committed=len(files)
            )
        else:
            return CommitResult(
                success=False,
                branch_name=branch_name,
                error="No files to commit or commit failed"
            )

    except Exception as e:
        return CommitResult(
            success=False,
            branch_name=branch_name,
            error=str(e)
        )


def build_commit_from_group(
    group: dict,
    issue_key: Optional[str] = None
) -> str:
    """
    Build commit message from a group dictionary.

    Convenience wrapper around build_commit_message that extracts
    title and body from group dict.

    Args:
        group: Group dictionary with commit_title and commit_body
        issue_key: Issue reference to include

    Returns:
        Complete commit message
    """
    return build_commit_message(
        title=group.get('commit_title', 'Changes'),
        body=group.get('commit_body', ''),
        issue_ref=issue_key
    )


def generate_branch_name(
    issue_key: Optional[str],
    title: str,
    prefix: str = "feature",
    max_length: int = 50
) -> str:
    """
    Generate a branch name from issue key and title.

    Args:
        issue_key: Issue key (e.g., "PROJ-123")
        title: Title or summary for the branch
        prefix: Branch prefix (default: "feature")
        max_length: Maximum length for the title part

    Returns:
        Formatted branch name
    """
    if issue_key:
        # Clean title for branch name
        clean_title = title.lower()
        clean_title = "".join(c if c.isalnum() or c == " " else "" for c in clean_title)
        clean_title = clean_title.strip().replace(" ", "-")[:max_length]
        return f"{prefix}/{issue_key.lower()}-{clean_title}"
    else:
        # No issue key - use title only
        clean_title = title.lower()
        clean_title = "".join(c if c.isalnum() or c == " " else "" for c in clean_title)
        clean_title = clean_title.strip().replace(" ", "-")[:max_length]
        return f"{prefix}/{clean_title}"
