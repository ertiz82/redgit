"""
Task analysis and LLM integration for propose command.

This module centralizes LLM-based analysis functions for commit message
generation, detailed diff analysis, and task matching.
"""

import json
from typing import List, Dict, Optional, Tuple, Any

from rich.console import Console
from rich.panel import Panel

from ..common.llm import LLMClient
from ..common.prompt import PromptManager
from ..common.gitops import GitOps

console = Console()


# =============================================================================
# LANGUAGE UTILITIES
# =============================================================================

LANGUAGE_NAMES = {
    "tr": "Turkish",
    "de": "German",
    "fr": "French",
    "es": "Spanish",
    "pt": "Portuguese",
    "it": "Italian",
    "ru": "Russian",
    "zh": "Chinese",
    "ja": "Japanese",
    "ko": "Korean",
    "en": "English",
}


def get_language_name(code: Optional[str]) -> str:
    """Get full language name from code."""
    if not code:
        return "English"
    return LANGUAGE_NAMES.get(code, code)


# =============================================================================
# LLM SETUP AND GROUP GENERATION
# =============================================================================

def setup_llm_and_generate_groups(
    config: dict,
    changes: List[Dict],
    prompt_name: Optional[str],
    plugin_prompt: Optional[str],
    active_issues: List,
    issue_language: Optional[str],
    verbose: bool,
    detailed: bool,
    gitops: GitOps,
    task_mgmt: Optional[Any],
    show_prompt_sources_fn: Optional[callable] = None,
    show_verbose_groups_fn: Optional[callable] = None
) -> Tuple[Optional[List[Dict]], Optional[LLMClient]]:
    """
    Setup LLM, create prompt, and generate commit groups.

    Args:
        config: Configuration dictionary
        changes: List of file changes
        prompt_name: Custom prompt name
        plugin_prompt: Plugin-provided prompt
        active_issues: List of active issues
        issue_language: Language for issue content
        verbose: Enable verbose output
        detailed: Enable detailed mode
        gitops: GitOps instance
        task_mgmt: Task management integration
        show_prompt_sources_fn: Callback for showing prompt sources
        show_verbose_groups_fn: Callback for showing verbose groups

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

    if verbose and show_prompt_sources_fn:
        console.print(f"\n[bold cyan]=== Prompt Sources ===[/bold cyan]")
        show_prompt_sources_fn(prompt_name, plugin_prompt, None, issue_language)

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
        console.print(Panel(
            final_prompt[:3000] + ("..." if len(final_prompt) > 3000 else ""),
            title="Prompt",
            border_style="cyan"
        ))
        console.print(f"[dim]Total prompt length: {len(final_prompt)} characters[/dim]")

    # Generate groups with AI
    console.print("\n[yellow]AI analyzing changes...[/yellow]\n")
    try:
        if verbose:
            groups, raw_response = llm.generate_groups(final_prompt, return_raw=True) if hasattr(llm, 'generate_groups') else (llm.generate_groups(final_prompt), None)
            if raw_response:
                console.print(f"\n[bold cyan]=== Raw AI Response ===[/bold cyan]")
                console.print(Panel(
                    raw_response[:5000] + ("..." if len(raw_response) > 5000 else ""),
                    title="AI Response",
                    border_style="green"
                ))
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
        groups = enhance_groups_with_diffs(
            groups=groups,
            gitops=gitops,
            llm=llm,
            issue_language=issue_language,
            verbose=verbose,
            task_mgmt=task_mgmt
        )
        console.print("[green]Detailed analysis complete[/green]\n")

    if verbose and show_verbose_groups_fn:
        show_verbose_groups_fn(groups)

    return groups, llm


# =============================================================================
# DETAILED ANALYSIS
# =============================================================================

def enhance_groups_with_diffs(
    groups: List[Dict],
    gitops: GitOps,
    llm: LLMClient,
    issue_language: Optional[str] = None,
    verbose: bool = False,
    task_mgmt: Optional[Any] = None
) -> List[Dict]:
    """
    Enhance each group with detailed commit messages generated from file diffs.

    For each group:
    1. Get the diffs for all files in the group
    2. Send diffs to LLM with a specialized prompt
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
        console.print(f"\n[bold cyan]=== Detailed Mode Debug ===[/bold cyan]")
        console.print(f"[dim]task_mgmt: {task_mgmt}[/dim]")
        console.print(f"[dim]task_mgmt.name: {task_mgmt.name if task_mgmt else 'N/A'}[/dim]")
        console.print(f"[dim]issue_language param: {issue_language}[/dim]")
        if task_mgmt:
            console.print(f"[dim]task_mgmt.issue_language: {getattr(task_mgmt, 'issue_language', 'NOT_FOUND')}[/dim]")
            console.print(f"[dim]has_user_prompt method: {hasattr(task_mgmt, 'has_user_prompt')}[/dim]")

    # Check if user has EXPORTED custom prompts for this integration
    has_custom_prompts = False
    title_prompt_path = None
    desc_prompt_path = None

    if task_mgmt and hasattr(task_mgmt, 'has_user_prompt'):
        from ..common.config import RETGIT_DIR
        has_title = task_mgmt.has_user_prompt("issue_title")
        has_desc = task_mgmt.has_user_prompt("issue_description")
        if has_title or has_desc:
            has_custom_prompts = True
            if has_title:
                title_prompt_path = str(RETGIT_DIR / "prompts" / "integrations" / task_mgmt.name / "issue_title.md")
            if has_desc:
                desc_prompt_path = str(RETGIT_DIR / "prompts" / "integrations" / task_mgmt.name / "issue_description.md")
            if verbose:
                console.print(f"\n[bold cyan]=== Integration Prompts ===[/bold cyan]")
                console.print(f"[green]Using USER-EXPORTED prompts for issue generation[/green]")
                if title_prompt_path:
                    console.print(f"[dim]  issue_title: {title_prompt_path}[/dim]")
                if desc_prompt_path:
                    console.print(f"[dim]  issue_description: {desc_prompt_path}[/dim]")
        elif verbose:
            console.print(f"\n[bold cyan]=== Integration Prompts ===[/bold cyan]")
            console.print(f"[dim]Using RedGit default prompts (no user exports found)[/dim]")
            console.print(f"[dim]  issue_title: builtin default[/dim]")
            console.print(f"[dim]  issue_description: builtin default[/dim]")

    for i, group in enumerate(groups, 1):
        files = group.get("files", [])
        if not files:
            enhanced_groups.append(group)
            continue

        if verbose:
            console.print(f"\n[bold cyan]=== Detailed Analysis: Group {i}/{len(groups)} ===[/bold cyan]")
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
                console.print(f"[yellow]Could not get diffs: {e}[/yellow]")
            enhanced_groups.append(group)
            continue

        if not diffs:
            enhanced_groups.append(group)
            continue

        # Build prompt for detailed analysis
        if has_custom_prompts:
            prompt = build_detailed_analysis_prompt_with_integration(
                files=files,
                diffs=diffs,
                initial_title=group.get("commit_title", ""),
                initial_body=group.get("commit_body", ""),
                task_mgmt=task_mgmt
            )
            prompt_source = "integration prompts"
        else:
            prompt = build_detailed_analysis_prompt(
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
            console.print(Panel(
                prompt[:4000] + ("..." if len(prompt) > 4000 else ""),
                title=f"[cyan]LLM Prompt (Group {i})[/cyan]",
                border_style="cyan"
            ))

        # Get detailed analysis from LLM
        try:
            result = llm.chat(prompt)

            if verbose:
                console.print(Panel(
                    result[:3000] + ("..." if len(result) > 3000 else ""),
                    title=f"[green]LLM Raw Response (Group {i})[/green]",
                    border_style="green"
                ))

            enhanced = parse_detailed_result(result, group)

            if verbose:
                console.print(f"\n[bold]Parsed Result:[/bold]")
                console.print(f"[dim]  commit_title: {enhanced.get('commit_title', 'N/A')[:60]}[/dim]")
                console.print(f"[dim]  issue_title: {enhanced.get('issue_title', 'N/A')[:60]}[/dim]")
                console.print(f"[dim]  issue_description: {enhanced.get('issue_description', 'N/A')[:80]}...[/dim]")

            enhanced_groups.append(enhanced)
        except Exception as e:
            if verbose:
                console.print(f"[yellow]LLM error, using original: {e}[/yellow]")
            enhanced_groups.append(group)

    return enhanced_groups


# =============================================================================
# PROMPT BUILDING
# =============================================================================

def build_detailed_analysis_prompt(
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
        lang_name = get_language_name(issue_language)
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

    lang_name = get_language_name(issue_language) if issue_language and issue_language != 'en' else None

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
3. **issue_title**: A clear title for a Jira/task management issue{' in ' + lang_name if lang_name else ''}
4. **issue_description**: A detailed description of what this change does{' in ' + lang_name if lang_name else ''}

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


def build_detailed_analysis_prompt_with_integration(
    files: List[str],
    diffs: str,
    initial_title: str = "",
    initial_body: str = "",
    task_mgmt: Optional[Any] = None
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
        language = get_language_name(task_mgmt.issue_language)

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


# =============================================================================
# RESULT PARSING
# =============================================================================

def parse_detailed_result(result: str, original_group: Dict) -> Dict:
    """
    Parse the LLM response and merge with original group.

    Args:
        result: Raw LLM response string
        original_group: Original group dictionary

    Returns:
        Enhanced group dictionary with parsed fields
    """
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
