"""
Semgrep analyzer module for multi-language static analysis.

Provides integration with Semgrep for detecting:
- Security vulnerabilities
- Code quality issues
- Best practice violations
- Pattern-based analysis across 35+ languages
"""

import subprocess
import json
from typing import List, Dict, Optional, Any
from pathlib import Path

from .config import ConfigManager


# Severity mapping from Semgrep to RedGit
SEVERITY_MAP = {
    "ERROR": "critical",
    "WARNING": "high",
    "INFO": "medium",
}

# Issue type mapping based on rule categories
TYPE_MAP = {
    "security": "security",
    "correctness": "bug",
    "best-practice": "maintainability",
    "performance": "performance",
    "maintainability": "maintainability",
    "portability": "maintainability",
}


def is_semgrep_installed() -> bool:
    """Check if Semgrep is installed and available."""
    try:
        result = subprocess.run(
            ["semgrep", "--version"],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def get_semgrep_version() -> Optional[str]:
    """Get Semgrep version string."""
    try:
        result = subprocess.run(
            ["semgrep", "--version"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    except FileNotFoundError:
        return None


def run_semgrep(
    path: str = ".",
    configs: Optional[List[str]] = None,
    severity: Optional[List[str]] = None,
    exclude: Optional[List[str]] = None,
    timeout: int = 300,
    files: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Run Semgrep analysis on the specified path.

    Args:
        path: Directory or file to analyze
        configs: List of Semgrep configs (e.g., ["auto", "p/security-audit"])
        severity: List of severity levels to include (e.g., ["ERROR", "WARNING"])
        exclude: List of paths to exclude
        timeout: Timeout in seconds
        files: Specific files to analyze (optional)

    Returns:
        Dict with 'success', 'results', 'errors', and 'stats' keys
    """
    if not is_semgrep_installed():
        return {
            "success": False,
            "error": "Semgrep is not installed. Install with: pip install semgrep",
            "results": [],
            "stats": {}
        }

    # Build command
    cmd = ["semgrep", "--json"]

    # Add configs
    if configs:
        for config in configs:
            cmd.extend(["--config", config])
    else:
        cmd.extend(["--config", "auto"])

    # Add severity filter (semgrep accepts multiple --severity flags)
    if severity:
        for sev in severity:
            cmd.extend(["--severity", sev])

    # Add excludes
    if exclude:
        for exc in exclude:
            cmd.extend(["--exclude", exc])

    # Add timeout
    cmd.extend(["--timeout", str(timeout)])

    # Add specific files or path
    if files:
        cmd.extend(files)
    else:
        cmd.append(path)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout + 30  # Extra buffer for process overhead
        )

        # Parse JSON output
        if result.stdout:
            try:
                output = json.loads(result.stdout)
                return {
                    "success": True,
                    "results": output.get("results", []),
                    "errors": output.get("errors", []),
                    "stats": {
                        "total": len(output.get("results", [])),
                        "paths_scanned": output.get("paths", {}).get("scanned", []),
                    }
                }
            except json.JSONDecodeError as e:
                return {
                    "success": False,
                    "error": f"Failed to parse Semgrep output: {e}",
                    "results": [],
                    "stats": {}
                }
        else:
            # No output means no findings (success)
            return {
                "success": True,
                "results": [],
                "errors": [],
                "stats": {"total": 0}
            }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": f"Semgrep timed out after {timeout} seconds",
            "results": [],
            "stats": {}
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Semgrep error: {e}",
            "results": [],
            "stats": {}
        }


def analyze_files(files: List[str]) -> Dict[str, Any]:
    """
    Analyze specific files using Semgrep with config from settings.

    Args:
        files: List of file paths to analyze

    Returns:
        Dict with analysis results
    """
    config_manager = ConfigManager()
    semgrep_config = config_manager.get_semgrep_config()

    if not semgrep_config.get("enabled", False):
        return {
            "success": True,
            "enabled": False,
            "results": [],
            "message": "Semgrep is disabled"
        }

    return run_semgrep(
        configs=semgrep_config.get("configs", ["auto"]),
        severity=semgrep_config.get("severity", ["ERROR", "WARNING"]),
        exclude=semgrep_config.get("exclude", []),
        timeout=semgrep_config.get("timeout", 300),
        files=files
    )


def analyze_directory(path: str = ".") -> Dict[str, Any]:
    """
    Analyze a directory using Semgrep with config from settings.

    Args:
        path: Directory path to analyze

    Returns:
        Dict with analysis results
    """
    config_manager = ConfigManager()
    semgrep_config = config_manager.get_semgrep_config()

    if not semgrep_config.get("enabled", False):
        return {
            "success": True,
            "enabled": False,
            "results": [],
            "message": "Semgrep is disabled"
        }

    return run_semgrep(
        path=path,
        configs=semgrep_config.get("configs", ["auto"]),
        severity=semgrep_config.get("severity", ["ERROR", "WARNING"]),
        exclude=semgrep_config.get("exclude", []),
        timeout=semgrep_config.get("timeout", 300)
    )


def convert_to_quality_issues(semgrep_results: List[Dict]) -> List[Dict]:
    """
    Convert Semgrep results to RedGit quality issue format.

    Args:
        semgrep_results: List of Semgrep result objects

    Returns:
        List of quality issues in RedGit format
    """
    issues = []

    for result in semgrep_results:
        # Extract severity
        semgrep_severity = result.get("extra", {}).get("severity", "WARNING")
        severity = SEVERITY_MAP.get(semgrep_severity, "medium")

        # Extract issue type from metadata
        metadata = result.get("extra", {}).get("metadata", {})
        category = metadata.get("category", "maintainability")
        issue_type = TYPE_MAP.get(category, "maintainability")

        # Build issue
        issue = {
            "severity": severity,
            "type": issue_type,
            "file": result.get("path", "unknown"),
            "line": result.get("start", {}).get("line", 0),
            "end_line": result.get("end", {}).get("line", 0),
            "description": result.get("extra", {}).get("message", "No description"),
            "suggestion": _build_suggestion(result),
            "source": "semgrep",
            "rule_id": result.get("check_id", "unknown"),
            "rule_name": metadata.get("shortname", result.get("check_id", "")),
        }

        # Add fix if available
        fix = result.get("extra", {}).get("fix", None)
        if fix:
            issue["fix"] = fix

        # Add references
        references = metadata.get("references", [])
        if references:
            issue["references"] = references

        issues.append(issue)

    return issues


def _build_suggestion(result: Dict) -> str:
    """Build a suggestion string from Semgrep result."""
    extra = result.get("extra", {})
    metadata = extra.get("metadata", {})

    suggestion_parts = []

    # Add message as base
    message = extra.get("message", "")
    if message:
        suggestion_parts.append(message)

    # Add fix suggestion if available
    fix = extra.get("fix", "")
    if fix:
        suggestion_parts.append(f"Suggested fix: {fix}")

    # Add references
    references = metadata.get("references", [])
    if references and len(references) > 0:
        suggestion_parts.append(f"See: {references[0]}")

    return " | ".join(suggestion_parts) if suggestion_parts else "Review this code for potential issues"


def get_severity_counts(issues: List[Dict]) -> Dict[str, int]:
    """
    Count issues by severity level.

    Args:
        issues: List of quality issues

    Returns:
        Dict with counts per severity level
    """
    counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}

    for issue in issues:
        severity = issue.get("severity", "medium")
        if severity in counts:
            counts[severity] += 1

    return counts


def calculate_score_penalty(issues: List[Dict]) -> int:
    """
    Calculate score penalty based on Semgrep issues.

    Args:
        issues: List of quality issues

    Returns:
        Score penalty (0-100)
    """
    counts = get_severity_counts(issues)

    # Penalty weights
    penalty = (
        counts["critical"] * 25 +
        counts["high"] * 15 +
        counts["medium"] * 5 +
        counts["low"] * 1
    )

    # Cap at 50 points (same as linter issues)
    return min(penalty, 50)


def format_issue_report(issues: List[Dict], verbose: bool = False) -> str:
    """
    Format issues for console output.

    Args:
        issues: List of quality issues
        verbose: Include detailed information

    Returns:
        Formatted string report
    """
    if not issues:
        return "No Semgrep issues found."

    lines = []
    counts = get_severity_counts(issues)

    # Summary
    lines.append(f"Semgrep found {len(issues)} issues:")
    lines.append(f"  Critical: {counts['critical']}, High: {counts['high']}, "
                 f"Medium: {counts['medium']}, Low: {counts['low']}")
    lines.append("")

    # Group by file
    by_file: Dict[str, List[Dict]] = {}
    for issue in issues:
        file = issue.get("file", "unknown")
        if file not in by_file:
            by_file[file] = []
        by_file[file].append(issue)

    # Output per file
    for file, file_issues in by_file.items():
        lines.append(f"[{file}]")
        for issue in file_issues:
            severity = issue.get("severity", "medium").upper()
            line = issue.get("line", 0)
            desc = issue.get("description", "No description")

            lines.append(f"  L{line}: [{severity}] {desc}")

            if verbose:
                if issue.get("suggestion"):
                    lines.append(f"       Suggestion: {issue['suggestion']}")
                if issue.get("rule_id"):
                    lines.append(f"       Rule: {issue['rule_id']}")

        lines.append("")

    return "\n".join(lines)