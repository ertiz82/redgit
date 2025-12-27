"""
Tests for redgit/commands/daily.py and redgit/core/daily_state.py
"""

import pytest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock

from redgit.core.daily_state import DailyStateManager, DAILY_STATE_PATH
from redgit.commands.daily import (
    get_commits_since,
    format_commits_for_llm,
    calculate_stats,
    load_daily_prompt,
    LANGUAGE_NAMES,
)


class TestLanguageNames:
    """Tests for LANGUAGE_NAMES constant."""

    def test_contains_english(self):
        """Test that English is in language names."""
        assert "en" in LANGUAGE_NAMES
        assert LANGUAGE_NAMES["en"] == "English"

    def test_contains_turkish(self):
        """Test that Turkish is in language names."""
        assert "tr" in LANGUAGE_NAMES
        assert LANGUAGE_NAMES["tr"] == "Turkish"

    def test_contains_common_languages(self):
        """Test that common languages are included."""
        expected = ["en", "de", "fr", "es", "it", "pt", "ru", "zh", "ja", "ko"]
        for lang in expected:
            assert lang in LANGUAGE_NAMES

    def test_all_values_are_strings(self):
        """Test that all values are strings."""
        for code, name in LANGUAGE_NAMES.items():
            assert isinstance(code, str)
            assert isinstance(name, str)
            assert len(name) > 0


class TestDailyStateManager:
    """Tests for DailyStateManager class."""

    @pytest.fixture
    def state_manager(self, tmp_path):
        """Create a state manager with temp path."""
        import redgit.core.daily_state as daily_state_module

        # Override the path
        original_path = daily_state_module.DAILY_STATE_PATH
        daily_state_module.DAILY_STATE_PATH = tmp_path / ".redgit" / "daily_state.yaml"

        manager = DailyStateManager()

        yield manager

        # Restore
        daily_state_module.DAILY_STATE_PATH = original_path

    def test_load_returns_empty_dict_when_no_file(self, state_manager):
        """Test load returns empty dict when file doesn't exist."""
        result = state_manager.load()
        assert result == {}

    def test_save_and_load(self, state_manager):
        """Test save and load work together."""
        data = {"test_key": "test_value", "number": 42}
        state_manager.save(data)

        result = state_manager.load()
        assert result["test_key"] == "test_value"
        assert result["number"] == 42

    def test_get_last_run_returns_none_initially(self, state_manager):
        """Test get_last_run returns None when not set."""
        result = state_manager.get_last_run()
        assert result is None

    def test_set_and_get_last_run(self, state_manager):
        """Test set_last_run and get_last_run."""
        now = datetime.now()
        state_manager.set_last_run(now)

        result = state_manager.get_last_run()
        assert result is not None
        assert isinstance(result, datetime)
        # Allow 1 second tolerance for microseconds
        assert abs((result - now).total_seconds()) < 1

    def test_set_last_run_defaults_to_now(self, state_manager):
        """Test set_last_run defaults to current time."""
        before = datetime.now()
        state_manager.set_last_run()
        after = datetime.now()

        result = state_manager.get_last_run()
        assert result is not None
        assert before <= result <= after

    def test_get_since_timestamp_returns_last_run(self, state_manager):
        """Test get_since_timestamp returns last run if set."""
        last_run = datetime.now() - timedelta(hours=12)
        state_manager.set_last_run(last_run)

        result = state_manager.get_since_timestamp()
        assert abs((result - last_run).total_seconds()) < 1

    def test_get_since_timestamp_returns_24h_ago_if_not_set(self, state_manager):
        """Test get_since_timestamp returns 24h ago when never run."""
        before = datetime.now() - timedelta(hours=24, seconds=1)
        result = state_manager.get_since_timestamp()
        after = datetime.now() - timedelta(hours=24)

        assert before <= result <= after or abs((result - after).total_seconds()) < 2


class TestDailyStateManagerParseSinceOption:
    """Tests for DailyStateManager.parse_since_option method."""

    @pytest.fixture
    def state_manager(self, tmp_path):
        """Create a state manager with temp path."""
        import redgit.core.daily_state as daily_state_module

        original_path = daily_state_module.DAILY_STATE_PATH
        daily_state_module.DAILY_STATE_PATH = tmp_path / ".redgit" / "daily_state.yaml"

        manager = DailyStateManager()

        yield manager

        daily_state_module.DAILY_STATE_PATH = original_path

    def test_parse_hours(self, state_manager):
        """Test parsing hours (e.g., '24h')."""
        now = datetime.now()
        result = state_manager.parse_since_option("24h")

        expected = now - timedelta(hours=24)
        assert abs((result - expected).total_seconds()) < 2

    def test_parse_hours_various(self, state_manager):
        """Test parsing various hour values."""
        for hours in [1, 12, 48, 72]:
            result = state_manager.parse_since_option(f"{hours}h")
            expected = datetime.now() - timedelta(hours=hours)
            assert abs((result - expected).total_seconds()) < 2

    def test_parse_days(self, state_manager):
        """Test parsing days (e.g., '7d')."""
        now = datetime.now()
        result = state_manager.parse_since_option("7d")

        expected = now - timedelta(days=7)
        assert abs((result - expected).total_seconds()) < 2

    def test_parse_days_various(self, state_manager):
        """Test parsing various day values."""
        for days in [1, 2, 14, 30]:
            result = state_manager.parse_since_option(f"{days}d")
            expected = datetime.now() - timedelta(days=days)
            assert abs((result - expected).total_seconds()) < 2

    def test_parse_weeks(self, state_manager):
        """Test parsing weeks (e.g., '1w')."""
        now = datetime.now()
        result = state_manager.parse_since_option("1w")

        expected = now - timedelta(weeks=1)
        assert abs((result - expected).total_seconds()) < 2

    def test_parse_yesterday(self, state_manager):
        """Test parsing 'yesterday'."""
        result = state_manager.parse_since_option("yesterday")

        expected = (datetime.now() - timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        assert result == expected

    def test_parse_today(self, state_manager):
        """Test parsing 'today'."""
        result = state_manager.parse_since_option("today")

        expected = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        assert result == expected

    def test_parse_iso_date(self, state_manager):
        """Test parsing ISO date format."""
        result = state_manager.parse_since_option("2024-01-15")

        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15

    def test_parse_iso_datetime(self, state_manager):
        """Test parsing ISO datetime format."""
        result = state_manager.parse_since_option("2024-01-15T10:30:00")

        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15
        assert result.hour == 10
        assert result.minute == 30

    def test_parse_invalid_falls_back_to_24h(self, state_manager):
        """Test that invalid format falls back to 24h ago."""
        now = datetime.now()
        result = state_manager.parse_since_option("invalid-format")

        expected = now - timedelta(hours=24)
        assert abs((result - expected).total_seconds()) < 2

    def test_parse_case_insensitive(self, state_manager):
        """Test that parsing is case insensitive."""
        result_lower = state_manager.parse_since_option("yesterday")
        result_upper = state_manager.parse_since_option("YESTERDAY")

        assert result_lower == result_upper


class TestGetCommitsSince:
    """Tests for get_commits_since function."""

    def test_returns_list(self):
        """Test that function returns a list."""
        with patch('redgit.commands.daily.subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(stdout="", returncode=0)
            result = get_commits_since(datetime.now())
            assert isinstance(result, list)

    def test_returns_empty_list_on_no_commits(self):
        """Test returns empty list when no commits."""
        with patch('redgit.commands.daily.subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(stdout="", returncode=0)
            result = get_commits_since(datetime.now())
            assert result == []

    def test_parses_commit_data(self):
        """Test parsing of git log output."""
        git_output = """abc12345|John Doe|john@example.com|1704067200|feat: add feature
2	1	src/main.py
5	3	tests/test_main.py"""

        with patch('redgit.commands.daily.subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(stdout=git_output, returncode=0)
            result = get_commits_since(datetime.now() - timedelta(days=1))

            assert len(result) == 1
            commit = result[0]
            assert commit["hash"] == "abc12345"
            assert commit["author"] == "John Doe"
            assert commit["email"] == "john@example.com"
            assert commit["message"] == "feat: add feature"
            assert len(commit["files"]) == 2

    def test_calculates_additions_deletions(self):
        """Test that additions/deletions are calculated."""
        git_output = """abc12345|John Doe|john@example.com|1704067200|feat: test
10	5	file1.py
3	2	file2.py"""

        with patch('redgit.commands.daily.subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(stdout=git_output, returncode=0)
            result = get_commits_since(datetime.now() - timedelta(days=1))

            commit = result[0]
            assert commit["additions"] == 13  # 10 + 3
            assert commit["deletions"] == 7   # 5 + 2

    def test_handles_multiple_commits(self):
        """Test parsing multiple commits."""
        git_output = """abc12345|John Doe|john@example.com|1704067200|feat: first
1	0	file1.py
def67890|Jane Doe|jane@example.com|1704153600|fix: second
2	1	file2.py"""

        with patch('redgit.commands.daily.subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(stdout=git_output, returncode=0)
            result = get_commits_since(datetime.now() - timedelta(days=2))

            assert len(result) == 2
            assert result[0]["message"] == "feat: first"
            assert result[1]["message"] == "fix: second"

    def test_filters_by_author(self):
        """Test that author filter is applied."""
        with patch('redgit.commands.daily.subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(stdout="", returncode=0)
            get_commits_since(datetime.now(), author="John Doe")

            call_args = mock_run.call_args[0][0]
            assert "--author=John Doe" in call_args

    def test_handles_git_error(self):
        """Test handling of git command errors."""
        import subprocess

        with patch('redgit.commands.daily.subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, "git", stderr="error")
            with patch('redgit.commands.daily.console.print'):
                result = get_commits_since(datetime.now())
                assert result == []


class TestFormatCommitsForLlm:
    """Tests for format_commits_for_llm function."""

    def test_formats_single_commit(self):
        """Test formatting a single commit."""
        commits = [{
            "hash": "abc12345",
            "message": "feat: add feature",
            "author": "John Doe",
            "date": "2024-01-15 10:00",
            "files": [{"name": "main.py", "additions": 10, "deletions": 5}],
        }]

        result = format_commits_for_llm(commits)

        assert "abc12345" in result
        assert "feat: add feature" in result
        assert "John Doe" in result
        assert "main.py" in result
        assert "+10" in result
        assert "-5" in result

    def test_formats_multiple_commits(self):
        """Test formatting multiple commits."""
        commits = [
            {
                "hash": "abc12345",
                "message": "feat: first",
                "author": "John",
                "date": "2024-01-15 10:00",
                "files": [],
            },
            {
                "hash": "def67890",
                "message": "fix: second",
                "author": "Jane",
                "date": "2024-01-15 11:00",
                "files": [],
            },
        ]

        result = format_commits_for_llm(commits)

        assert "feat: first" in result
        assert "fix: second" in result

    def test_limits_files_per_commit(self):
        """Test that files are limited to 5 per commit."""
        files = [{"name": f"file{i}.py", "additions": 1, "deletions": 0} for i in range(10)]
        commits = [{
            "hash": "abc12345",
            "message": "feat: many files",
            "author": "John",
            "date": "2024-01-15 10:00",
            "files": files,
        }]

        result = format_commits_for_llm(commits)

        assert "file0.py" in result
        assert "file4.py" in result
        assert "5 more files" in result

    def test_handles_empty_files(self):
        """Test handling commits with no files."""
        commits = [{
            "hash": "abc12345",
            "message": "docs: update readme",
            "author": "John",
            "date": "2024-01-15 10:00",
            "files": [],
        }]

        result = format_commits_for_llm(commits)

        assert "abc12345" in result
        assert "docs: update readme" in result


class TestCalculateStats:
    """Tests for calculate_stats function."""

    def test_calculates_total_commits(self):
        """Test counting total commits."""
        commits = [
            {"additions": 0, "deletions": 0, "files": [], "author": "John"},
            {"additions": 0, "deletions": 0, "files": [], "author": "Jane"},
            {"additions": 0, "deletions": 0, "files": [], "author": "John"},
        ]

        stats = calculate_stats(commits)

        assert stats["total_commits"] == 3

    def test_calculates_additions_deletions(self):
        """Test summing additions and deletions."""
        commits = [
            {"additions": 10, "deletions": 5, "files": [], "author": "John"},
            {"additions": 20, "deletions": 3, "files": [], "author": "Jane"},
        ]

        stats = calculate_stats(commits)

        assert stats["total_additions"] == 30
        assert stats["total_deletions"] == 8

    def test_counts_unique_authors(self):
        """Test counting unique authors."""
        commits = [
            {"additions": 0, "deletions": 0, "files": [], "author": "John"},
            {"additions": 0, "deletions": 0, "files": [], "author": "Jane"},
            {"additions": 0, "deletions": 0, "files": [], "author": "John"},  # Duplicate
        ]

        stats = calculate_stats(commits)

        assert len(stats["authors"]) == 2
        assert "John" in stats["authors"]
        assert "Jane" in stats["authors"]

    def test_counts_unique_files(self):
        """Test counting unique files."""
        commits = [
            {"additions": 0, "deletions": 0, "author": "John", "files": [
                {"name": "file1.py", "additions": 1, "deletions": 0},
                {"name": "file2.py", "additions": 1, "deletions": 0},
            ]},
            {"additions": 0, "deletions": 0, "author": "Jane", "files": [
                {"name": "file1.py", "additions": 1, "deletions": 0},  # Same file
                {"name": "file3.py", "additions": 1, "deletions": 0},
            ]},
        ]

        stats = calculate_stats(commits)

        assert stats["total_files"] == 3  # file1, file2, file3

    def test_tracks_directories(self):
        """Test tracking affected directories."""
        commits = [
            {"additions": 0, "deletions": 0, "author": "John", "files": [
                {"name": "src/main.py", "additions": 1, "deletions": 0},
                {"name": "src/utils.py", "additions": 1, "deletions": 0},
                {"name": "tests/test_main.py", "additions": 1, "deletions": 0},
            ]},
        ]

        stats = calculate_stats(commits)

        assert "src" in stats["directories"]
        assert stats["directories"]["src"] == 2
        assert "tests" in stats["directories"]
        assert stats["directories"]["tests"] == 1

    def test_limits_directories_to_10(self):
        """Test that directories are limited to top 10."""
        files = [{"name": f"dir{i}/file.py", "additions": 1, "deletions": 0} for i in range(20)]
        commits = [{"additions": 0, "deletions": 0, "author": "John", "files": files}]

        stats = calculate_stats(commits)

        assert len(stats["directories"]) <= 10

    def test_handles_empty_commits(self):
        """Test handling empty commit list."""
        stats = calculate_stats([])

        assert stats["total_commits"] == 0
        assert stats["total_additions"] == 0
        assert stats["total_deletions"] == 0
        assert stats["total_files"] == 0
        assert stats["authors"] == []


class TestLoadDailyPrompt:
    """Tests for load_daily_prompt function."""

    def test_returns_string(self):
        """Test that function returns a string."""
        result = load_daily_prompt("English")
        assert isinstance(result, str)

    def test_returns_non_empty(self):
        """Test that function returns non-empty content."""
        result = load_daily_prompt("English")
        assert len(result) > 0

    def test_contains_placeholder(self):
        """Test that result contains COMMITS placeholder."""
        result = load_daily_prompt("English")
        assert "{{COMMITS}}" in result or "COMMITS" in result

    def test_uses_project_prompt_if_exists(self, tmp_path):
        """Test loading from project-specific prompt."""
        import redgit.core.config as config_module

        # Setup temp path
        original_dir = config_module.RETGIT_DIR
        config_module.RETGIT_DIR = tmp_path / ".redgit"
        prompt_dir = config_module.RETGIT_DIR / "prompts" / "daily"
        prompt_dir.mkdir(parents=True)
        (prompt_dir / "default.md").write_text("Custom project prompt {{COMMITS}}")

        try:
            with patch('redgit.commands.daily.RETGIT_DIR', config_module.RETGIT_DIR):
                result = load_daily_prompt("English")
                assert "Custom project prompt" in result
        finally:
            config_module.RETGIT_DIR = original_dir
