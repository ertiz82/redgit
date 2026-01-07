"""
Common utilities shared across all commands.

This module provides core infrastructure like configuration management,
git operations, LLM client, and prompt handling.
"""

from .config import (
    ConfigManager,
    StateManager,
    RETGIT_DIR,
    GLOBAL_REDGIT_DIR,
    GLOBAL_TAPS_DIR,
    GLOBAL_INTEGRATIONS_DIR,
    GLOBAL_PLUGINS_DIR,
    ensure_global_dirs,
)
from .gitops import GitOps
from .llm import LLMClient
from .prompt import PromptManager, PROMPT_CATEGORIES
from .constants import (
    REDGIT_SIGNATURE,
    MAX_DIFF_LENGTH,
    MAX_FILE_CONTENT_LENGTH,
    LLM_REQUEST_TIMEOUT,
    DEFAULT_QUALITY_THRESHOLD,
)

__all__ = [
    # Config
    "ConfigManager",
    "StateManager",
    "RETGIT_DIR",
    "GLOBAL_REDGIT_DIR",
    "GLOBAL_TAPS_DIR",
    "GLOBAL_INTEGRATIONS_DIR",
    "GLOBAL_PLUGINS_DIR",
    "ensure_global_dirs",
    # Git
    "GitOps",
    # LLM
    "LLMClient",
    # Prompt
    "PromptManager",
    "PROMPT_CATEGORIES",
    # Constants
    "REDGIT_SIGNATURE",
    "MAX_DIFF_LENGTH",
    "MAX_FILE_CONTENT_LENGTH",
    "LLM_REQUEST_TIMEOUT",
    "DEFAULT_QUALITY_THRESHOLD",
]
