"""
Propose command utilities.

This module provides commit building, display, and LLM analysis
functions for the propose command.
"""

from .commit import (
    CommitResult,
    build_commit_message,
    execute_commit_group,
    build_commit_from_group,
    generate_branch_name,
)
from .display import (
    display_file_list,
    display_commit_result,
    display_group_details,
    show_prompt_sources,
    show_active_issues,
    show_groups_summary,
    show_verbose_groups,
    show_dry_run_summary,
    show_task_commit_dry_run,
)
from .analysis import (
    setup_llm_and_generate_groups,
    enhance_groups_with_diffs,
    build_detailed_analysis_prompt,
    build_detailed_analysis_prompt_with_integration,
    parse_detailed_result,
    get_language_name,
    LANGUAGE_NAMES,
)

__all__ = [
    # Commit
    "CommitResult",
    "build_commit_message",
    "execute_commit_group",
    "build_commit_from_group",
    "generate_branch_name",
    # Display
    "display_file_list",
    "display_commit_result",
    "display_group_details",
    "show_prompt_sources",
    "show_active_issues",
    "show_groups_summary",
    "show_verbose_groups",
    "show_dry_run_summary",
    "show_task_commit_dry_run",
    # Analysis
    "setup_llm_and_generate_groups",
    "enhance_groups_with_diffs",
    "build_detailed_analysis_prompt",
    "build_detailed_analysis_prompt_with_integration",
    "parse_detailed_result",
    "get_language_name",
    "LANGUAGE_NAMES",
]
