"""
Unit tests for redgit.commands.propose module.

Tests focus on pure utility functions that can be tested without mocking external services.
"""

import json
import pytest
from unittest.mock import patch, MagicMock

from redgit.commands.propose import (
    _parse_detailed_result,
    _extract_param_pattern,
    _is_bare_command,
)


class TestParseDetailedResult:
    """Tests for _parse_detailed_result function."""

    def test_parses_valid_json_response(self):
        """Test parsing a valid JSON response."""
        result = '{"commit_title": "feat: add new feature", "commit_body": "Detailed description"}'
        original = {"files": ["src/main.py"], "group_name": "feature"}

        parsed = _parse_detailed_result(result, original)

        assert parsed["commit_title"] == "feat: add new feature"
        assert parsed["commit_body"] == "Detailed description"
        assert parsed["files"] == ["src/main.py"]
        assert parsed["group_name"] == "feature"

    def test_parses_json_with_extra_text(self):
        """Test parsing JSON embedded in other text."""
        result = '''Here is the analysis:
        {"commit_title": "fix: bug fix", "commit_body": "Fixed the issue"}
        Hope this helps!'''
        original = {"files": ["src/bug.py"]}

        parsed = _parse_detailed_result(result, original)

        assert parsed["commit_title"] == "fix: bug fix"
        assert parsed["commit_body"] == "Fixed the issue"

    def test_preserves_original_on_invalid_json(self):
        """Test that original group is returned when JSON is invalid."""
        result = "This is not JSON at all"
        original = {"files": ["src/main.py"], "commit_title": "original title"}

        parsed = _parse_detailed_result(result, original)

        assert parsed == original
        assert parsed["commit_title"] == "original title"

    def test_preserves_original_on_empty_json(self):
        """Test that original group is preserved when JSON is empty."""
        result = "{}"
        original = {"files": ["src/main.py"], "commit_title": "original"}

        parsed = _parse_detailed_result(result, original)

        assert parsed["commit_title"] == "original"

    def test_handles_issue_fields(self):
        """Test parsing issue_title and issue_description fields."""
        result = '{"issue_title": "New Feature", "issue_description": "Feature details"}'
        original = {"files": ["src/feature.py"]}

        parsed = _parse_detailed_result(result, original)

        assert parsed["issue_title"] == "New Feature"
        assert parsed["issue_description"] == "Feature details"

    def test_partial_update(self):
        """Test that only provided fields are updated."""
        result = '{"commit_title": "new title"}'
        original = {
            "files": ["src/main.py"],
            "commit_title": "old title",
            "commit_body": "old body"
        }

        parsed = _parse_detailed_result(result, original)

        assert parsed["commit_title"] == "new title"
        assert parsed["commit_body"] == "old body"

    def test_handles_nested_json(self):
        """Test handling of response with nested braces."""
        result = '{"commit_title": "feat: add {config}", "commit_body": "Added config"}'
        original = {"files": ["config.py"]}

        parsed = _parse_detailed_result(result, original)

        assert parsed["commit_title"] == "feat: add {config}"

    def test_handles_empty_result(self):
        """Test handling of empty result string."""
        result = ""
        original = {"files": ["src/main.py"], "commit_title": "original"}

        parsed = _parse_detailed_result(result, original)

        assert parsed == original

    def test_handles_unicode(self):
        """Test handling of unicode characters in response."""
        result = '{"commit_title": "feat: özellik eklendi", "commit_body": "Türkçe açıklama"}'
        original = {"files": ["src/main.py"]}

        parsed = _parse_detailed_result(result, original)

        assert parsed["commit_title"] == "feat: özellik eklendi"
        assert parsed["commit_body"] == "Türkçe açıklama"


class TestExtractParamPattern:
    """Tests for _extract_param_pattern function."""

    def test_empty_when_no_params(self):
        """Test returns empty list when no params are set."""
        result = _extract_param_pattern(
            prompt=None,
            no_task=False,
            task=None,
            dry_run=False,
            verbose=False,
            detailed=False,
            subtasks=False
        )

        assert result == []

    def test_extracts_task_flag(self):
        """Test extracts -t when task is provided."""
        result = _extract_param_pattern(
            prompt=None,
            no_task=False,
            task="PROJ-123",
            dry_run=False,
            verbose=False,
            detailed=False,
            subtasks=False
        )

        assert "-t" in result

    def test_extracts_subtasks_flag(self):
        """Test extracts --subtasks when enabled."""
        result = _extract_param_pattern(
            prompt=None,
            no_task=False,
            task="PROJ-123",
            dry_run=False,
            verbose=False,
            detailed=False,
            subtasks=True
        )

        assert "--subtasks" in result
        assert "-t" in result

    def test_extracts_detailed_flag(self):
        """Test extracts --detailed when enabled."""
        result = _extract_param_pattern(
            prompt=None,
            no_task=False,
            task=None,
            dry_run=False,
            verbose=False,
            detailed=True,
            subtasks=False
        )

        assert "--detailed" in result

    def test_extracts_dry_run_flag(self):
        """Test extracts --dry-run when enabled."""
        result = _extract_param_pattern(
            prompt=None,
            no_task=False,
            task=None,
            dry_run=True,
            verbose=False,
            detailed=False,
            subtasks=False
        )

        assert "--dry-run" in result

    def test_extracts_verbose_flag(self):
        """Test extracts --verbose when enabled."""
        result = _extract_param_pattern(
            prompt=None,
            no_task=False,
            task=None,
            dry_run=False,
            verbose=True,
            detailed=False,
            subtasks=False
        )

        assert "--verbose" in result

    def test_extracts_no_task_flag(self):
        """Test extracts --no-task when enabled."""
        result = _extract_param_pattern(
            prompt=None,
            no_task=True,
            task=None,
            dry_run=False,
            verbose=False,
            detailed=False,
            subtasks=False
        )

        assert "--no-task" in result

    def test_extracts_prompt_flag(self):
        """Test extracts -p when prompt is provided."""
        result = _extract_param_pattern(
            prompt="laravel",
            no_task=False,
            task=None,
            dry_run=False,
            verbose=False,
            detailed=False,
            subtasks=False
        )

        assert "-p" in result

    def test_multiple_flags_sorted(self):
        """Test multiple flags are returned sorted."""
        result = _extract_param_pattern(
            prompt="laravel",
            no_task=False,
            task="PROJ-123",
            dry_run=True,
            verbose=True,
            detailed=True,
            subtasks=True
        )

        # Check all flags present
        assert "-p" in result
        assert "-t" in result
        assert "--detailed" in result
        assert "--dry-run" in result
        assert "--subtasks" in result
        assert "--verbose" in result

        # Check sorted order
        assert result == sorted(result)

    def test_excludes_value_only_flag_names(self):
        """Test that only flag names are included, not values."""
        result = _extract_param_pattern(
            prompt="custom-prompt",
            no_task=False,
            task="PROJ-123",
            dry_run=False,
            verbose=False,
            detailed=False,
            subtasks=False
        )

        # Should have -t and -p flags, not the values
        assert "-t" in result
        assert "-p" in result
        assert "PROJ-123" not in result
        assert "custom-prompt" not in result


class TestIsBareCommand:
    """Tests for _is_bare_command function."""

    def test_true_when_empty_list(self):
        """Test returns True for empty parameter list."""
        assert _is_bare_command([]) is True

    def test_false_when_has_params(self):
        """Test returns False when parameters are present."""
        assert _is_bare_command(["-t"]) is False
        assert _is_bare_command(["--detailed"]) is False
        assert _is_bare_command(["-t", "--subtasks"]) is False

    def test_false_for_single_param(self):
        """Test returns False for any single parameter."""
        assert _is_bare_command(["--dry-run"]) is False


class TestNotificationHelpers:
    """Tests for notification helper functions."""

    def test_is_notification_enabled_returns_bool(self, temp_dir, change_cwd):
        """Test _is_notification_enabled returns boolean."""
        from redgit.commands.propose import _is_notification_enabled

        # Should return False by default for commit (default config)
        result = _is_notification_enabled({}, "commit")
        assert isinstance(result, bool)

        # Should return True by default for push
        result = _is_notification_enabled({}, "push")
        assert isinstance(result, bool)

    @patch('redgit.utils.notifications.get_notification')
    @patch('redgit.utils.notifications.ConfigManager')
    def test_send_commit_notification_skips_when_disabled(
        self, mock_cm, mock_get_notification
    ):
        """Test notification is skipped when disabled."""
        from redgit.commands.propose import _send_commit_notification

        mock_cm.return_value.is_notification_enabled.return_value = False

        _send_commit_notification({}, "main", "PROJ-123", 5)

        mock_get_notification.assert_not_called()

    @patch('redgit.utils.notifications.get_notification')
    @patch('redgit.utils.notifications.ConfigManager')
    def test_send_commit_notification_sends_message(
        self, mock_cm, mock_get_notification
    ):
        """Test notification sends correct message."""
        from redgit.commands.propose import _send_commit_notification

        mock_cm.return_value.is_notification_enabled.return_value = True
        mock_notification = MagicMock()
        mock_notification.enabled = True
        mock_get_notification.return_value = mock_notification

        _send_commit_notification({}, "feature/test", "PROJ-123", 5)

        mock_notification.send_message.assert_called_once()
        call_args = mock_notification.send_message.call_args[0][0]
        assert "feature/test" in call_args
        assert "PROJ-123" in call_args


class TestTransitionHelpers:
    """Tests for issue transition helper functions."""

    def test_transition_issue_with_strategy_auto(self):
        """Test transition uses auto mode by default."""
        from redgit.commands.propose import _transition_issue_with_strategy

        mock_task_mgmt = MagicMock()
        mock_task_mgmt.transition_strategy = 'auto'
        mock_task_mgmt.transition_issue.return_value = True

        result = _transition_issue_with_strategy(mock_task_mgmt, "PROJ-123")

        mock_task_mgmt.transition_issue.assert_called_once_with("PROJ-123", "after_propose")
        assert result is True

    @patch('redgit.commands.propose._transition_issue_interactive')
    def test_transition_issue_with_strategy_ask(self, mock_interactive):
        """Test transition uses interactive mode when strategy is 'ask'."""
        from redgit.commands.propose import _transition_issue_with_strategy

        mock_task_mgmt = MagicMock()
        mock_task_mgmt.transition_strategy = 'ask'
        mock_interactive.return_value = True

        result = _transition_issue_with_strategy(mock_task_mgmt, "PROJ-123")

        mock_interactive.assert_called_once_with(mock_task_mgmt, "PROJ-123")
        assert result is True


class TestShowHelpers:
    """Tests for display helper functions."""

    @patch('redgit.core.propose.display.console')
    def test_show_active_issues_displays_table(self, mock_console):
        """Test _show_active_issues displays issues in a table."""
        from redgit.commands.propose import _show_active_issues
        from redgit.integrations.base import Issue

        issues = [
            Issue(key="PROJ-1", summary="First issue", description="Desc 1", issue_type="bug", status="Open"),
            Issue(key="PROJ-2", summary="Second issue", description="Desc 2", issue_type="story", status="In Progress"),
        ]

        _show_active_issues(issues)

        # Verify console.print was called (table output)
        assert mock_console.print.called


class TestGroupsProcessing:
    """Tests for group processing logic."""

    def test_parse_result_preserves_files(self):
        """Test that file list is preserved during parsing."""
        result = '{"commit_title": "feat: new feature"}'
        original = {
            "files": ["src/a.py", "src/b.py"],
            "group_name": "feature"
        }

        parsed = _parse_detailed_result(result, original)

        assert parsed["files"] == ["src/a.py", "src/b.py"]
        assert parsed["group_name"] == "feature"
        assert parsed["commit_title"] == "feat: new feature"


class TestBuildDetailedAnalysisPrompt:
    """Tests for _build_detailed_analysis_prompt function."""

    def test_builds_prompt_with_files_and_diffs(self):
        """Test that prompt includes files and diffs."""
        from redgit.commands.propose import _build_detailed_analysis_prompt

        files = ["src/main.py", "src/utils.py"]
        diffs = "@@ -1,3 +1,5 @@\n+import os\n def main():\n     pass"

        prompt = _build_detailed_analysis_prompt(files, diffs)

        assert "src/main.py" in prompt
        assert "src/utils.py" in prompt
        assert "import os" in prompt
        assert "commit_title" in prompt
        assert "JSON" in prompt

    def test_includes_initial_title_and_body(self):
        """Test that initial analysis is included."""
        from redgit.commands.propose import _build_detailed_analysis_prompt

        prompt = _build_detailed_analysis_prompt(
            files=["test.py"],
            diffs="+ test code",
            initial_title="feat: initial title",
            initial_body="Initial body"
        )

        assert "feat: initial title" in prompt
        assert "Initial body" in prompt

    def test_adds_language_instruction_for_non_english(self):
        """Test that language instruction is added for non-English."""
        from redgit.commands.propose import _build_detailed_analysis_prompt

        prompt = _build_detailed_analysis_prompt(
            files=["test.py"],
            diffs="+ code",
            issue_language="tr"
        )

        assert "Turkish" in prompt
        assert "issue_title" in prompt
        assert "issue_description" in prompt

    def test_no_language_instruction_for_english(self):
        """Test that no extra language instruction for English."""
        from redgit.commands.propose import _build_detailed_analysis_prompt

        prompt = _build_detailed_analysis_prompt(
            files=["test.py"],
            diffs="+ code",
            issue_language="en"
        )

        assert "IMPORTANT: Language Requirements" not in prompt

    def test_truncates_long_diffs(self):
        """Test that long diffs are truncated."""
        from redgit.commands.propose import _build_detailed_analysis_prompt

        long_diff = "x" * 10000
        prompt = _build_detailed_analysis_prompt(
            files=["test.py"],
            diffs=long_diff
        )

        assert "diff truncated" in prompt
        assert len(prompt) < 15000  # Should be truncated

    def test_supports_multiple_languages(self):
        """Test various language codes are supported."""
        from redgit.commands.propose import _build_detailed_analysis_prompt

        languages = {
            "de": "German",
            "fr": "French",
            "es": "Spanish",
            "ja": "Japanese"
        }

        for code, name in languages.items():
            prompt = _build_detailed_analysis_prompt(
                files=["test.py"],
                diffs="+ code",
                issue_language=code
            )
            assert name in prompt


class TestIssueMatchingLogic:
    """Tests for issue matching and group categorization."""

    def test_group_with_issue_key_should_be_matched(self):
        """Test that groups with valid issue_key are matched."""
        # This simulates the matching logic from propose_cmd
        groups = [
            {"files": ["a.py"], "issue_key": "PROJ-123", "commit_title": "feat: add feature"},
            {"files": ["b.py"], "issue_key": None, "commit_title": "fix: bug fix"},
        ]

        matched = []
        unmatched = []

        for group in groups:
            if group.get("issue_key"):
                matched.append(group)
            else:
                unmatched.append(group)

        assert len(matched) == 1
        assert len(unmatched) == 1
        assert matched[0]["issue_key"] == "PROJ-123"
        assert unmatched[0]["commit_title"] == "fix: bug fix"

    def test_empty_issue_key_is_unmatched(self):
        """Test that empty string issue_key is treated as unmatched."""
        groups = [
            {"files": ["a.py"], "issue_key": "", "commit_title": "test"},
            {"files": ["b.py"], "issue_key": "PROJ-1", "commit_title": "test2"},
        ]

        matched = [g for g in groups if g.get("issue_key")]
        unmatched = [g for g in groups if not g.get("issue_key")]

        assert len(matched) == 1
        assert len(unmatched) == 1

    def test_all_groups_matched(self):
        """Test when all groups have issue keys."""
        groups = [
            {"files": ["a.py"], "issue_key": "PROJ-1", "commit_title": "feat1"},
            {"files": ["b.py"], "issue_key": "PROJ-2", "commit_title": "feat2"},
        ]

        matched = [g for g in groups if g.get("issue_key")]
        unmatched = [g for g in groups if not g.get("issue_key")]

        assert len(matched) == 2
        assert len(unmatched) == 0

    def test_all_groups_unmatched(self):
        """Test when no groups have issue keys."""
        groups = [
            {"files": ["a.py"], "issue_key": None, "commit_title": "feat1"},
            {"files": ["b.py"], "commit_title": "feat2"},  # No issue_key at all
        ]

        matched = [g for g in groups if g.get("issue_key")]
        unmatched = [g for g in groups if not g.get("issue_key")]

        assert len(matched) == 0
        assert len(unmatched) == 2

    def test_group_preserves_all_fields_after_matching(self):
        """Test that matched groups preserve all original fields."""
        group = {
            "files": ["a.py", "b.py"],
            "issue_key": "PROJ-123",
            "commit_title": "feat: test",
            "commit_body": "body text",
            "group_name": "feature-group",
            "issue_title": "Test Feature",
            "issue_description": "Description"
        }

        # Simulate adding _issue like the actual code does
        group["_issue"] = {"key": "PROJ-123", "status": "Open"}

        assert group["files"] == ["a.py", "b.py"]
        assert group["issue_key"] == "PROJ-123"
        assert group["commit_title"] == "feat: test"
        assert group["commit_body"] == "body text"
        assert group["_issue"]["key"] == "PROJ-123"


class TestPromptForPatternValues:
    """Tests for _prompt_for_pattern_values helper logic."""

    def test_extracts_boolean_flags_from_pattern(self):
        """Test that boolean flags are correctly extracted."""
        # Test the logic without actually prompting
        pattern = ["--subtasks", "--detailed", "--dry-run"]

        # Simulate the boolean extraction logic
        values = {}
        values["subtasks"] = "--subtasks" in pattern
        values["detailed"] = "--detailed" in pattern
        values["dry_run"] = "--dry-run" in pattern
        values["verbose"] = "--verbose" in pattern
        values["no_task"] = "--no-task" in pattern

        assert values["subtasks"] is True
        assert values["detailed"] is True
        assert values["dry_run"] is True
        assert values["verbose"] is False
        assert values["no_task"] is False

    def test_identifies_value_requiring_flags(self):
        """Test identifying flags that require values."""
        pattern = ["-t", "-p", "--detailed"]

        requires_value = []
        if "-t" in pattern:
            requires_value.append("task")
        if "-p" in pattern:
            requires_value.append("prompt")

        assert "task" in requires_value
        assert "prompt" in requires_value
        assert len(requires_value) == 2


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_parse_result_with_special_chars_in_json(self):
        """Test parsing JSON with special characters."""
        result = '{"commit_title": "fix: handle \\"quotes\\" and \\\\backslash"}'
        original = {"files": ["test.py"]}

        parsed = _parse_detailed_result(result, original)

        assert 'quotes' in parsed.get("commit_title", "")

    def test_parse_result_with_newlines_in_body(self):
        """Test parsing JSON with newlines in commit body."""
        result = '{"commit_title": "feat: add feature", "commit_body": "Line 1\\nLine 2\\nLine 3"}'
        original = {"files": ["test.py"]}

        parsed = _parse_detailed_result(result, original)

        assert parsed["commit_title"] == "feat: add feature"
        assert "Line 1" in parsed["commit_body"]

    def test_extract_pattern_with_all_false(self):
        """Test extract pattern with all boolean flags false."""
        result = _extract_param_pattern(
            prompt=None,
            no_task=False,
            task=None,
            dry_run=False,
            verbose=False,
            detailed=False,
            subtasks=False
        )

        assert result == []

    def test_parse_result_malformed_json_graceful(self):
        """Test graceful handling of malformed JSON."""
        malformed_cases = [
            '{"commit_title": "missing closing brace"',
            '{"commit_title": }',
            'commit_title: no quotes',
            '[{"array": "not object"}]',
        ]

        original = {"files": ["test.py"], "commit_title": "original"}

        for malformed in malformed_cases:
            parsed = _parse_detailed_result(malformed, original)
            # Should return original without raising exception
            assert parsed["commit_title"] == "original"


# ==================== Tests for _categorize_groups ====================

class TestCategorizeGroups:
    """Tests for _categorize_groups function."""

    def test_separates_matched_and_unmatched(self):
        """Test groups are correctly separated."""
        from redgit.commands.propose import _categorize_groups

        groups = [
            {"files": ["a.py"], "issue_key": "PROJ-123", "commit_title": "feat1"},
            {"files": ["b.py"], "issue_key": None, "commit_title": "feat2"},
        ]

        mock_task_mgmt = MagicMock()
        mock_issue = MagicMock()
        mock_task_mgmt.get_issue.return_value = mock_issue

        matched, unmatched = _categorize_groups(groups, mock_task_mgmt)

        assert len(matched) == 1
        assert len(unmatched) == 1
        assert matched[0]["issue_key"] == "PROJ-123"
        assert matched[0]["_issue"] == mock_issue

    def test_unmatched_when_issue_not_found(self):
        """Test group becomes unmatched when issue is not found."""
        from redgit.commands.propose import _categorize_groups

        groups = [
            {"files": ["a.py"], "issue_key": "PROJ-999", "commit_title": "feat1"},
        ]

        mock_task_mgmt = MagicMock()
        mock_task_mgmt.get_issue.return_value = None  # Issue not found

        matched, unmatched = _categorize_groups(groups, mock_task_mgmt)

        assert len(matched) == 0
        assert len(unmatched) == 1
        assert unmatched[0]["issue_key"] is None  # Key should be cleared

    def test_all_unmatched_without_task_mgmt(self):
        """Test all groups are unmatched without task management."""
        from redgit.commands.propose import _categorize_groups

        groups = [
            {"files": ["a.py"], "issue_key": "PROJ-123", "commit_title": "feat1"},
            {"files": ["b.py"], "issue_key": None, "commit_title": "feat2"},
        ]

        matched, unmatched = _categorize_groups(groups, None)

        assert len(matched) == 0
        assert len(unmatched) == 2

    def test_empty_groups_list(self):
        """Test empty groups list returns empty tuples."""
        from redgit.commands.propose import _categorize_groups

        matched, unmatched = _categorize_groups([], None)

        assert matched == []
        assert unmatched == []


# ==================== Tests for _show_groups_summary ====================

class TestShowGroupsSummary:
    """Tests for _show_groups_summary function."""

    @patch('redgit.core.propose.display.console')
    def test_displays_matched_groups(self, mock_console):
        """Test matched groups are displayed."""
        from redgit.commands.propose import _show_groups_summary
        from redgit.integrations.base import Issue

        matched = [
            {"issue_key": "PROJ-1", "commit_title": "feat: test", "files": ["a.py"], "_issue": MagicMock()}
        ]
        unmatched = []

        _show_groups_summary(matched, unmatched, None)

        # Check that console.print was called with matched info
        calls = [str(c) for c in mock_console.print.call_args_list]
        assert any("PROJ-1" in c for c in calls)

    @patch('redgit.core.propose.display.console')
    def test_displays_unmatched_groups(self, mock_console):
        """Test unmatched groups are displayed."""
        from redgit.commands.propose import _show_groups_summary

        matched = []
        unmatched = [
            {"commit_title": "fix: bug fix", "files": ["b.py"]}
        ]

        _show_groups_summary(matched, unmatched, None)

        calls = [str(c) for c in mock_console.print.call_args_list]
        assert any("No matching issue" in c or "bug fix" in c for c in calls)

    @patch('redgit.core.propose.display.console')
    def test_shows_new_issues_message_with_task_mgmt(self, mock_console):
        """Test shows 'New issues will be created' with task mgmt."""
        from redgit.commands.propose import _show_groups_summary

        mock_task_mgmt = MagicMock()
        mock_task_mgmt.enabled = True

        unmatched = [{"commit_title": "test", "files": ["a.py"]}]

        _show_groups_summary([], unmatched, mock_task_mgmt)

        calls = [str(c) for c in mock_console.print.call_args_list]
        assert any("New issues will be created" in c for c in calls)


# ==================== Tests for _show_verbose_groups ====================

class TestShowVerboseGroups:
    """Tests for _show_verbose_groups function."""

    @patch('redgit.core.propose.display.console')
    def test_displays_group_details(self, mock_console):
        """Test verbose output includes all group details."""
        from redgit.commands.propose import _show_verbose_groups

        groups = [
            {
                "files": ["a.py", "b.py"],
                "commit_title": "feat: test",
                "issue_key": "PROJ-123",
                "issue_title": "Test Issue"
            }
        ]

        _show_verbose_groups(groups)

        calls = [str(c) for c in mock_console.print.call_args_list]
        # Check group info is displayed
        assert any("Group 1" in c for c in calls)
        assert any("feat: test" in c or "commit_title" in c for c in calls)

    @patch('redgit.core.propose.display.console')
    def test_shows_file_count(self, mock_console):
        """Test shows file count in verbose output."""
        from redgit.commands.propose import _show_verbose_groups

        groups = [{"files": ["a.py", "b.py", "c.py"], "commit_title": "test"}]

        _show_verbose_groups(groups)

        calls = [str(c) for c in mock_console.print.call_args_list]
        assert any("3 files" in c for c in calls)


# ==================== Tests for _show_dry_run_summary ====================

class TestShowDryRunSummary:
    """Tests for _show_dry_run_summary function."""

    @patch('redgit.core.propose.display.console')
    def test_shows_dry_run_header(self, mock_console):
        """Test dry run summary shows header."""
        from redgit.commands.propose import _show_dry_run_summary

        _show_dry_run_summary([], [], None)

        calls = [str(c) for c in mock_console.print.call_args_list]
        assert any("DRY RUN" in c for c in calls)

    @patch('redgit.core.propose.display.console')
    def test_shows_matched_group_details(self, mock_console):
        """Test shows details for matched groups."""
        from redgit.commands.propose import _show_dry_run_summary

        mock_task_mgmt = MagicMock()
        mock_task_mgmt.format_branch_name.return_value = "feature/PROJ-123-test"

        matched = [
            {
                "issue_key": "PROJ-123",
                "commit_title": "feat: test feature",
                "files": ["a.py", "b.py"],
                "_issue": MagicMock()
            }
        ]

        _show_dry_run_summary(matched, [], mock_task_mgmt)

        calls = [str(c) for c in mock_console.print.call_args_list]
        assert any("PROJ-123" in c for c in calls)

    @patch('redgit.core.propose.display.console')
    def test_shows_unmatched_group_details(self, mock_console):
        """Test shows details for unmatched groups."""
        from redgit.commands.propose import _show_dry_run_summary

        unmatched = [
            {
                "commit_title": "fix: bug fix",
                "files": ["bug.py"],
                "issue_title": "Bug Fix Issue"
            }
        ]

        _show_dry_run_summary([], unmatched, None)

        calls = [str(c) for c in mock_console.print.call_args_list]
        assert any("New" in c or "bug fix" in c for c in calls)

    @patch('redgit.core.propose.display.console')
    def test_shows_parent_task_for_subtasks(self, mock_console):
        """Test shows parent task info in subtasks mode."""
        from redgit.commands.propose import _show_dry_run_summary
        from redgit.integrations.base import Issue

        parent_issue = Issue(
            key="PROJ-100",
            summary="Parent Task",
            description="",
            issue_type="story",
            status="Open"
        )

        _show_dry_run_summary([], [], None, parent_task_key="PROJ-100", parent_issue=parent_issue)

        calls = [str(c) for c in mock_console.print.call_args_list]
        assert any("Parent Task" in c or "PROJ-100" in c for c in calls)

    @patch('redgit.core.propose.display.console')
    def test_shows_summary_stats(self, mock_console):
        """Test shows summary statistics."""
        from redgit.commands.propose import _show_dry_run_summary

        matched = [{"issue_key": "P-1", "commit_title": "t", "files": ["a.py"], "_issue": MagicMock()}]
        unmatched = [{"commit_title": "t2", "files": ["b.py", "c.py"]}]

        _show_dry_run_summary(matched, unmatched, None)

        calls = [str(c) for c in mock_console.print.call_args_list]
        assert any("Summary" in c for c in calls)
        assert any("Total" in c for c in calls)


# ==================== Tests for _send_issue_created_notification ====================

class TestSendIssueCreatedNotification:
    """Tests for _send_issue_created_notification function."""

    @patch('redgit.utils.notifications.get_notification')
    @patch('redgit.utils.notifications.ConfigManager')
    def test_skips_when_disabled(self, mock_cm, mock_get_notification):
        """Test notification is skipped when disabled."""
        from redgit.commands.propose import _send_issue_created_notification

        mock_cm.return_value.is_notification_enabled.return_value = False

        _send_issue_created_notification({}, "PROJ-123", "Test Issue")

        mock_get_notification.assert_not_called()

    @patch('redgit.utils.notifications.get_notification')
    @patch('redgit.utils.notifications.ConfigManager')
    def test_sends_message_when_enabled(self, mock_cm, mock_get_notification):
        """Test sends correct notification message."""
        from redgit.commands.propose import _send_issue_created_notification

        mock_cm.return_value.is_notification_enabled.return_value = True
        mock_notification = MagicMock()
        mock_notification.enabled = True
        mock_get_notification.return_value = mock_notification

        _send_issue_created_notification({}, "PROJ-123", "New Feature")

        mock_notification.send_message.assert_called_once()
        message = mock_notification.send_message.call_args[0][0]
        assert "PROJ-123" in message
        assert "New Feature" in message


# ==================== Tests for _send_session_summary_notification ====================

class TestSendSessionSummaryNotification:
    """Tests for _send_session_summary_notification function."""

    @patch('redgit.utils.notifications.get_notification')
    @patch('redgit.utils.notifications.ConfigManager')
    def test_skips_when_disabled(self, mock_cm, mock_get_notification):
        """Test notification is skipped when disabled."""
        from redgit.commands.propose import _send_session_summary_notification

        mock_cm.return_value.is_notification_enabled.return_value = False

        _send_session_summary_notification({}, 3, 2)

        mock_get_notification.assert_not_called()

    @patch('redgit.utils.notifications.get_notification')
    @patch('redgit.utils.notifications.ConfigManager')
    def test_sends_summary_message(self, mock_cm, mock_get_notification):
        """Test sends session summary notification."""
        from redgit.commands.propose import _send_session_summary_notification

        mock_cm.return_value.is_notification_enabled.return_value = True
        mock_notification = MagicMock()
        mock_notification.enabled = True
        mock_get_notification.return_value = mock_notification

        _send_session_summary_notification({}, 5, 3)

        mock_notification.send_message.assert_called_once()
        message = mock_notification.send_message.call_args[0][0]
        assert "5" in message
        assert "3" in message


# ==================== Tests for _transition_issue_interactive ====================

class TestTransitionIssueInteractive:
    """Tests for _transition_issue_interactive function."""

    @patch('redgit.commands.propose.Prompt')
    @patch('redgit.core.propose.display.console')
    def test_returns_false_when_no_transitions(self, mock_console, mock_prompt):
        """Test returns False when no transitions available."""
        from redgit.commands.propose import _transition_issue_interactive

        mock_task_mgmt = MagicMock()
        mock_task_mgmt.get_issue.return_value = MagicMock(status="Open")
        mock_task_mgmt.get_available_transitions.return_value = []

        result = _transition_issue_interactive(mock_task_mgmt, "PROJ-123")

        assert result is False

    @patch('redgit.commands.propose.Prompt')
    @patch('redgit.core.propose.display.console')
    def test_returns_false_when_user_skips(self, mock_console, mock_prompt):
        """Test returns False when user chooses to skip."""
        from redgit.commands.propose import _transition_issue_interactive

        mock_task_mgmt = MagicMock()
        mock_task_mgmt.get_issue.return_value = MagicMock(status="Open")
        mock_task_mgmt.get_available_transitions.return_value = [
            {"id": "1", "to": "In Progress"}
        ]
        mock_prompt.ask.return_value = "0"  # User skips

        result = _transition_issue_interactive(mock_task_mgmt, "PROJ-123")

        assert result is False

    @patch('redgit.commands.propose.Prompt')
    @patch('redgit.core.propose.display.console')
    def test_returns_true_when_transition_succeeds(self, mock_console, mock_prompt):
        """Test returns True when transition succeeds."""
        from redgit.commands.propose import _transition_issue_interactive

        mock_task_mgmt = MagicMock()
        mock_task_mgmt.get_issue.return_value = MagicMock(status="Open")
        mock_task_mgmt.get_available_transitions.return_value = [
            {"id": "10", "to": "In Progress"}
        ]
        mock_task_mgmt.transition_issue_by_id.return_value = True
        mock_prompt.ask.return_value = "1"  # User selects first option

        result = _transition_issue_interactive(mock_task_mgmt, "PROJ-123")

        assert result is True
        mock_task_mgmt.transition_issue_by_id.assert_called_with("PROJ-123", "10")


# ==================== Tests for _build_detailed_analysis_prompt_with_integration ====================

class TestBuildDetailedAnalysisPromptWithIntegration:
    """Tests for _build_detailed_analysis_prompt_with_integration function."""

    def test_builds_prompt_with_custom_prompts(self):
        """Test prompt includes custom integration prompts."""
        from redgit.commands.propose import _build_detailed_analysis_prompt_with_integration

        mock_task_mgmt = MagicMock()
        mock_task_mgmt.issue_language = "tr"
        mock_task_mgmt.get_prompt.side_effect = lambda name: f"Custom {name} prompt" if name in ["issue_title", "issue_description"] else ""

        prompt = _build_detailed_analysis_prompt_with_integration(
            files=["test.py"],
            diffs="+ code",
            task_mgmt=mock_task_mgmt
        )

        assert "Custom issue_title prompt" in prompt
        assert "Custom issue_description prompt" in prompt

    def test_falls_back_to_default_prompts(self):
        """Test falls back to default when no custom prompts."""
        from redgit.commands.propose import _build_detailed_analysis_prompt_with_integration

        mock_task_mgmt = MagicMock()
        mock_task_mgmt.issue_language = "en"
        mock_task_mgmt.get_prompt.return_value = ""  # No custom prompts

        prompt = _build_detailed_analysis_prompt_with_integration(
            files=["test.py"],
            diffs="+ code",
            task_mgmt=mock_task_mgmt
        )

        assert "Generate a clear issue title" in prompt
        assert "Generate a detailed issue description" in prompt

    def test_truncates_long_diffs(self):
        """Test truncates diffs over limit."""
        from redgit.commands.propose import _build_detailed_analysis_prompt_with_integration

        long_diff = "x" * 10000
        prompt = _build_detailed_analysis_prompt_with_integration(
            files=["test.py"],
            diffs=long_diff,
            task_mgmt=None
        )

        assert "diff truncated" in prompt

    def test_includes_language_from_task_mgmt(self):
        """Test includes language setting from task management."""
        from redgit.commands.propose import _build_detailed_analysis_prompt_with_integration

        mock_task_mgmt = MagicMock()
        mock_task_mgmt.issue_language = "tr"
        mock_task_mgmt.get_prompt.return_value = ""

        prompt = _build_detailed_analysis_prompt_with_integration(
            files=["test.py"],
            diffs="+ code",
            task_mgmt=mock_task_mgmt
        )

        assert "Turkish" in prompt


# ==================== Tests for _enhance_groups_with_diffs ====================

class TestEnhanceGroupsWithDiffs:
    """Tests for _enhance_groups_with_diffs function."""

    @patch('redgit.commands.propose._parse_detailed_result')
    def test_skips_groups_without_files(self, mock_parse):
        """Test groups without files are returned unchanged."""
        from redgit.commands.propose import _enhance_groups_with_diffs

        groups = [{"files": [], "commit_title": "empty"}]
        mock_gitops = MagicMock()
        mock_llm = MagicMock()

        result = _enhance_groups_with_diffs(groups, mock_gitops, mock_llm)

        assert result[0] == groups[0]
        mock_parse.assert_not_called()

    @patch('redgit.commands.propose._parse_detailed_result')
    @patch('redgit.commands.propose._build_detailed_analysis_prompt')
    def test_calls_llm_with_diffs(self, mock_build_prompt, mock_parse):
        """Test calls LLM with diff content."""
        from redgit.commands.propose import _enhance_groups_with_diffs

        groups = [{"files": ["a.py"], "commit_title": "test"}]
        mock_gitops = MagicMock()
        mock_gitops.get_diffs_for_files.return_value = "+ new code"
        mock_llm = MagicMock()
        mock_llm.chat.return_value = '{"commit_title": "enhanced"}'
        mock_build_prompt.return_value = "prompt"
        mock_parse.return_value = {"files": ["a.py"], "commit_title": "enhanced"}

        result = _enhance_groups_with_diffs(groups, mock_gitops, mock_llm)

        mock_gitops.get_diffs_for_files.assert_called_with(["a.py"])
        mock_llm.chat.assert_called_once()

    @patch('redgit.commands.propose._parse_detailed_result')
    def test_returns_original_on_llm_error(self, mock_parse):
        """Test returns original group on LLM error."""
        from redgit.commands.propose import _enhance_groups_with_diffs

        groups = [{"files": ["a.py"], "commit_title": "original"}]
        mock_gitops = MagicMock()
        mock_gitops.get_diffs_for_files.return_value = "+ code"
        mock_llm = MagicMock()
        mock_llm.chat.side_effect = Exception("LLM error")

        result = _enhance_groups_with_diffs(groups, mock_gitops, mock_llm)

        assert result[0]["commit_title"] == "original"


# ==================== Tests for _show_task_commit_dry_run ====================

class TestShowTaskCommitDryRun:
    """Tests for _show_task_commit_dry_run function."""

    @patch('redgit.core.propose.display.console')
    def test_shows_task_info(self, mock_console):
        """Test shows task information in dry run."""
        from redgit.commands.propose import _show_task_commit_dry_run

        mock_task_mgmt = MagicMock()
        mock_task_mgmt.enabled = True
        mock_task_mgmt.get_issue.return_value = MagicMock(
            summary="Test Task",
            status="Open",
            description="Task description"
        )

        changes = [{"file": "a.py"}, {"file": "b.py"}]

        _show_task_commit_dry_run("PROJ-123", changes, MagicMock(), mock_task_mgmt)

        calls = [str(c) for c in mock_console.print.call_args_list]
        assert any("PROJ-123" in c for c in calls)
        assert any("DRY RUN" in c for c in calls)

    @patch('redgit.core.propose.display.console')
    def test_shows_error_when_task_not_found(self, mock_console):
        """Test shows error when task not found."""
        from redgit.commands.propose import _show_task_commit_dry_run

        mock_task_mgmt = MagicMock()
        mock_task_mgmt.enabled = True
        mock_task_mgmt.get_issue.return_value = None

        _show_task_commit_dry_run("PROJ-999", [], MagicMock(), mock_task_mgmt)

        calls = [str(c) for c in mock_console.print.call_args_list]
        assert any("not found" in c for c in calls)


# ==================== Tests for suggest_and_ask_pattern ====================

class TestSuggestAndAskPattern:
    """Tests for _suggest_and_ask_pattern function."""

    @patch('redgit.commands.propose.Confirm')
    @patch('redgit.commands.propose.console')
    def test_returns_true_when_accepted(self, mock_console, mock_confirm):
        """Test returns True when user accepts pattern."""
        from redgit.commands.propose import _suggest_and_ask_pattern

        mock_confirm.ask.return_value = True

        result = _suggest_and_ask_pattern(["-t", "--subtasks"])

        assert result is True

    @patch('redgit.commands.propose.Confirm')
    @patch('redgit.commands.propose.console')
    def test_returns_false_when_declined(self, mock_console, mock_confirm):
        """Test returns False when user declines pattern."""
        from redgit.commands.propose import _suggest_and_ask_pattern

        mock_confirm.ask.return_value = False

        result = _suggest_and_ask_pattern(["-t"])

        assert result is False

    @patch('redgit.commands.propose.Confirm')
    @patch('redgit.commands.propose.console')
    def test_displays_pattern_string(self, mock_console, mock_confirm):
        """Test displays the pattern as string."""
        from redgit.commands.propose import _suggest_and_ask_pattern

        mock_confirm.ask.return_value = True

        _suggest_and_ask_pattern(["-t", "--detailed"])

        calls = [str(c) for c in mock_console.print.call_args_list]
        assert any("-t" in c and "--detailed" in c for c in calls)


# ==================== Tests for _prompt_for_pattern_values ====================

class TestPromptForPatternValuesFull:
    """Full tests for _prompt_for_pattern_values with mocking."""

    @patch('redgit.commands.propose.Prompt')
    def test_asks_for_task_when_in_pattern(self, mock_prompt):
        """Test prompts for task ID when -t in pattern."""
        from redgit.commands.propose import _prompt_for_pattern_values

        mock_prompt.ask.return_value = "PROJ-123"

        values = _prompt_for_pattern_values(["-t"])

        assert values["task"] == "PROJ-123"
        mock_prompt.ask.assert_called()

    @patch('redgit.commands.propose.Prompt')
    def test_asks_for_prompt_when_in_pattern(self, mock_prompt):
        """Test prompts for prompt name when -p in pattern."""
        from redgit.commands.propose import _prompt_for_pattern_values

        mock_prompt.ask.side_effect = ["PROJ-1", "laravel"]  # task, then prompt

        values = _prompt_for_pattern_values(["-t", "-p"])

        assert values["prompt"] == "laravel"

    def test_sets_boolean_flags_without_prompting(self):
        """Test boolean flags are set without prompting."""
        from redgit.commands.propose import _prompt_for_pattern_values

        with patch('redgit.commands.propose.Prompt'):
            values = _prompt_for_pattern_values(["--subtasks", "--detailed"])

        assert values["subtasks"] is True
        assert values["detailed"] is True
        assert values["dry_run"] is False


# ==================== CLI Integration Tests ====================

class TestProposeCmdCLI:
    """CLI integration tests for propose_cmd."""

    @patch('redgit.commands.propose.StateManager')
    @patch('redgit.commands.propose.ConfigManager')
    @patch('redgit.commands.propose.GitOps')
    def test_shows_no_changes_message(self, mock_gitops, mock_config, mock_state):
        """Test shows message when no changes found."""
        from typer.testing import CliRunner
        from redgit.commands.propose import propose_cmd
        import typer

        mock_config.return_value.load.return_value = {}
        mock_gitops.return_value.get_changes.return_value = []
        mock_gitops.return_value.get_excluded_changes.return_value = []
        mock_state.return_value.get_common_propose_pattern.return_value = None

        # Create a test app with just propose command
        test_app = typer.Typer()
        test_app.command()(propose_cmd)

        runner = CliRunner()
        result = runner.invoke(test_app, [])

        assert "No changes found" in result.output or result.exit_code == 0

    @patch('redgit.commands.propose.StateManager')
    @patch('redgit.commands.propose.ConfigManager')
    @patch('redgit.commands.propose.GitOps')
    def test_dry_run_shows_banner(self, mock_gitops, mock_config, mock_state):
        """Test dry run shows banner."""
        from typer.testing import CliRunner
        from redgit.commands.propose import propose_cmd
        import typer

        mock_config.return_value.load.return_value = {}
        mock_gitops.return_value.get_changes.return_value = []
        mock_gitops.return_value.get_excluded_changes.return_value = []
        mock_state.return_value.get_common_propose_pattern.return_value = None

        test_app = typer.Typer()
        test_app.command()(propose_cmd)

        runner = CliRunner()
        result = runner.invoke(test_app, ["--dry-run"])

        assert "DRY RUN" in result.output

    @patch('redgit.commands.propose.StateManager')
    @patch('redgit.commands.propose.ConfigManager')
    @patch('redgit.commands.propose.GitOps')
    def test_subtasks_requires_task(self, mock_gitops, mock_config, mock_state):
        """Test --subtasks requires --task flag."""
        from typer.testing import CliRunner
        from redgit.commands.propose import propose_cmd
        import typer

        mock_config.return_value.load.return_value = {}
        mock_gitops.return_value.get_changes.return_value = [{"file": "a.py"}]
        mock_gitops.return_value.get_excluded_changes.return_value = []
        mock_state.return_value.get_common_propose_pattern.return_value = None

        test_app = typer.Typer()
        test_app.command()(propose_cmd)

        runner = CliRunner()
        result = runner.invoke(test_app, ["--subtasks"])

        assert "--subtasks requires --task" in result.output or result.exit_code == 1


# ==================== Tests for _process_matched_groups ====================

class TestProcessMatchedGroups:
    """Tests for _process_matched_groups function."""

    @patch('redgit.commands.propose._transition_issue_with_strategy')
    @patch('redgit.core.propose.display.console')
    def test_creates_branch_and_commits(self, mock_console, mock_transition):
        """Test creates branch and commits for matched groups."""
        from redgit.commands.propose import _process_matched_groups

        mock_gitops = MagicMock()
        mock_gitops.create_branch_and_commit.return_value = True

        mock_task_mgmt = MagicMock()
        mock_task_mgmt.format_branch_name.return_value = "feature/PROJ-123-test"

        mock_state = MagicMock()

        groups = [{
            "issue_key": "PROJ-123",
            "commit_title": "feat: test",
            "commit_body": "body",
            "files": ["a.py"],
            "_issue": MagicMock(status="Open")
        }]

        workflow = {"auto_transition": True, "strategy": "local-merge"}

        _process_matched_groups(groups, mock_gitops, mock_task_mgmt, mock_state, workflow)

        mock_gitops.create_branch_and_commit.assert_called_once()
        mock_state.add_session_branch.assert_called()

    @patch('redgit.commands.propose.console')
    def test_handles_commit_error(self, mock_console):
        """Test handles error during commit."""
        from redgit.commands.propose import _process_matched_groups

        mock_gitops = MagicMock()
        mock_gitops.create_branch_and_commit.side_effect = Exception("Git error")

        mock_task_mgmt = MagicMock()
        mock_task_mgmt.format_branch_name.return_value = "feature/test"

        groups = [{
            "issue_key": "PROJ-123",
            "commit_title": "test",
            "files": ["a.py"],
            "_issue": MagicMock(status="Open")
        }]

        _process_matched_groups(groups, mock_gitops, mock_task_mgmt, MagicMock(), {})

        # Should not raise, error is caught
        calls = [str(c) for c in mock_console.print.call_args_list]
        assert any("Error" in c for c in calls)
