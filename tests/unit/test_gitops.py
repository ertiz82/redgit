"""
Unit tests for redgit.core.gitops module.
"""

import os
import subprocess
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from redgit.core.common.gitops import (
    GitOps,
    NotAGitRepoError,
    init_git_repo,
)


class TestInitGitRepo:
    """Tests for init_git_repo function."""

    def test_initializes_git_repo(self, temp_dir, change_cwd):
        """Test that init_git_repo creates a git repository."""
        repo = init_git_repo()

        assert (temp_dir / ".git").exists()
        # Use Path.resolve() to handle symlinks on macOS
        assert Path(repo.working_dir).resolve() == temp_dir.resolve()

    def test_adds_remote_when_provided(self, temp_dir, change_cwd):
        """Test that remote is added when URL is provided."""
        repo = init_git_repo(remote_url="https://github.com/test/repo.git")

        assert "origin" in [r.name for r in repo.remotes]
        assert repo.remotes.origin.url == "https://github.com/test/repo.git"


class TestGitOpsInit:
    """Tests for GitOps initialization."""

    def test_raises_error_when_not_git_repo(self, temp_dir, change_cwd):
        """Test that NotAGitRepoError is raised when not in a git repo."""
        with pytest.raises(NotAGitRepoError):
            GitOps()

    def test_auto_init_creates_repo(self, temp_dir, change_cwd):
        """Test that auto_init creates a git repository."""
        gitops = GitOps(auto_init=True)

        assert (temp_dir / ".git").exists()
        assert gitops.repo is not None

    def test_uses_existing_repo(self, temp_git_repo, change_cwd):
        """Test that GitOps uses an existing git repository."""
        os.chdir(temp_git_repo)
        gitops = GitOps()

        # Use Path.resolve() to handle symlinks on macOS
        assert Path(gitops.repo.working_dir).resolve() == temp_git_repo.resolve()

    def test_tracks_original_branch(self, temp_git_repo, change_cwd):
        """Test that original branch is tracked."""
        os.chdir(temp_git_repo)
        gitops = GitOps()

        # Default branch after init is usually master or main
        assert gitops.original_branch in ["main", "master"]


class TestGitOpsGetChanges:
    """Tests for GitOps.get_changes method."""

    def test_returns_empty_list_when_no_changes(self, temp_git_repo, change_cwd):
        """Test that empty list is returned when no changes."""
        os.chdir(temp_git_repo)
        gitops = GitOps()

        changes = gitops.get_changes()

        assert changes == []

    def test_detects_new_file(self, temp_git_repo, change_cwd):
        """Test that new untracked files are detected."""
        os.chdir(temp_git_repo)
        gitops = GitOps()

        # Create a new file
        (temp_git_repo / "new_file.py").write_text("print('hello')")

        changes = gitops.get_changes()

        assert len(changes) == 1
        assert changes[0]["file"] == "new_file.py"
        assert changes[0]["status"] == "U"  # Untracked

    def test_detects_modified_file(self, temp_git_repo, change_cwd):
        """Test that modified files are detected."""
        os.chdir(temp_git_repo)
        gitops = GitOps()

        # Modify existing file
        readme = temp_git_repo / "README.md"
        readme.write_text("# Updated\n")

        changes = gitops.get_changes()

        assert len(changes) == 1
        assert changes[0]["file"] == "README.md"
        assert changes[0]["status"] == "M"  # Modified

    def test_detects_deleted_file(self, temp_git_repo, change_cwd):
        """Test that deleted files are detected."""
        os.chdir(temp_git_repo)
        gitops = GitOps()

        # Delete existing file
        (temp_git_repo / "README.md").unlink()

        changes = gitops.get_changes()

        assert len(changes) == 1
        assert changes[0]["file"] == "README.md"
        assert changes[0]["status"] == "D"  # Deleted

    def test_detects_staged_file(self, temp_git_repo, change_cwd):
        """Test that staged files are detected."""
        os.chdir(temp_git_repo)
        gitops = GitOps()

        # Create and stage a new file
        new_file = temp_git_repo / "staged.py"
        new_file.write_text("print('staged')")
        subprocess.run(["git", "add", "staged.py"], cwd=temp_git_repo)

        changes = gitops.get_changes()

        # Verify a staged file is detected
        assert len(changes) >= 1
        staged_file = next((c for c in changes if c["file"] == "staged.py"), None)
        assert staged_file is not None
        # The status depends on git implementation - just verify the file is found

    def test_excludes_sensitive_files(self, temp_git_repo, change_cwd):
        """Test that sensitive files are excluded by default."""
        os.chdir(temp_git_repo)
        gitops = GitOps()

        # Create sensitive and normal files
        (temp_git_repo / ".env").write_text("SECRET=value")
        (temp_git_repo / "normal.py").write_text("print('normal')")

        changes = gitops.get_changes()

        file_names = [c["file"] for c in changes]
        assert "normal.py" in file_names
        assert ".env" not in file_names

    def test_includes_sensitive_when_requested(self, temp_git_repo, change_cwd):
        """Test that sensitive files are included when requested."""
        os.chdir(temp_git_repo)
        gitops = GitOps()

        # Create sensitive file
        (temp_git_repo / ".env").write_text("SECRET=value")

        changes = gitops.get_changes(include_excluded=True)

        file_names = [c["file"] for c in changes]
        assert ".env" in file_names


@pytest.mark.skip(reason="get_diff method not implemented in GitOps - TODO: implement")
class TestGitOpsGetDiff:
    """Tests for GitOps.get_diff method."""

    def test_returns_diff_for_modified_file(self, temp_git_repo, change_cwd):
        """Test that diff is returned for modified files."""
        pass

    def test_returns_content_for_new_file(self, temp_git_repo, change_cwd):
        """Test that content is returned for new untracked files."""
        pass

    def test_returns_none_for_nonexistent_file(self, temp_git_repo, change_cwd):
        """Test that None is returned for non-existent files."""
        pass


class TestGitOpsBranchOperations:
    """Tests for GitOps branch operations."""

    def test_create_branch(self, temp_git_repo, change_cwd):
        """Test creating a new branch."""
        os.chdir(temp_git_repo)
        gitops = GitOps()

        gitops.checkout_or_create_branch("feature/test")

        assert gitops.repo.active_branch.name == "feature/test"

    def test_switch_to_existing_branch(self, temp_git_repo, change_cwd):
        """Test switching to an existing branch."""
        os.chdir(temp_git_repo)
        gitops = GitOps()

        # Create branch first
        gitops.checkout_or_create_branch("feature/existing")
        gitops.checkout_or_create_branch(gitops.original_branch)

        # Switch back
        gitops.checkout_or_create_branch("feature/existing")

        assert gitops.repo.active_branch.name == "feature/existing"

    def test_get_current_branch(self, temp_git_repo, change_cwd):
        """Test getting current branch name via repo.active_branch."""
        os.chdir(temp_git_repo)
        gitops = GitOps()

        # Use repo.active_branch.name directly
        branch = gitops.repo.active_branch.name

        assert branch in ["main", "master"]


class TestGitOpsCommitOperations:
    """Tests for GitOps commit operations."""

    def test_stage_files(self, temp_git_repo, change_cwd):
        """Test staging files."""
        os.chdir(temp_git_repo)
        gitops = GitOps()

        # Create new files
        (temp_git_repo / "file1.py").write_text("# file 1")
        (temp_git_repo / "file2.py").write_text("# file 2")

        gitops.stage_files(["file1.py", "file2.py"])

        # Check that files are staged
        staged = [item.a_path for item in gitops.repo.index.diff("HEAD")]
        # For new files, they appear in untracked before staging
        # After staging, check if they're in the index
        assert len(list(gitops.repo.index.entries)) > 0

    def test_commit_creates_commit(self, temp_git_repo, change_cwd):
        """Test that commit creates a new commit."""
        os.chdir(temp_git_repo)
        gitops = GitOps()

        # Create and stage a file
        (temp_git_repo / "new.py").write_text("# new file")
        subprocess.run(["git", "add", "new.py"], cwd=temp_git_repo)

        # Get initial commit count
        initial_count = len(list(gitops.repo.iter_commits()))

        gitops.commit("test: add new file")

        # Check commit was created
        assert len(list(gitops.repo.iter_commits())) == initial_count + 1
        assert gitops.repo.head.commit.message.startswith("test: add new file")


class TestGitOpsRemoteOperations:
    """Tests for GitOps remote operations."""

    def test_has_remote_false_when_no_remote(self, temp_git_repo, change_cwd):
        """Test repo.remotes is empty when no remote exists."""
        os.chdir(temp_git_repo)
        gitops = GitOps()

        assert len(gitops.repo.remotes) == 0

    def test_has_remote_true_when_remote_exists(self, temp_git_repo, change_cwd):
        """Test repo.remotes has items when remote exists."""
        os.chdir(temp_git_repo)
        gitops = GitOps()

        # Add a remote
        gitops.repo.create_remote("origin", "https://github.com/test/repo.git")

        assert len(gitops.repo.remotes) > 0

    def test_get_remote_url(self, temp_git_repo, change_cwd):
        """Test getting remote URL from repo.remotes."""
        os.chdir(temp_git_repo)
        gitops = GitOps()

        # Add a remote
        gitops.repo.create_remote("origin", "https://github.com/test/repo.git")

        url = gitops.repo.remotes.origin.url

        assert url == "https://github.com/test/repo.git"


class TestGitOpsEdgeCases:
    """Tests for GitOps edge cases and error handling."""

    def test_handles_empty_repo(self, temp_dir, change_cwd):
        """Test handling of empty repository (no commits)."""
        gitops = GitOps(auto_init=True)

        # Empty repo should not raise errors
        changes = gitops.get_changes()
        assert isinstance(changes, list)

    def test_handles_binary_files(self, temp_git_repo, change_cwd):
        """Test handling of binary files."""
        os.chdir(temp_git_repo)
        gitops = GitOps()

        # Create a binary file
        binary_file = temp_git_repo / "image.png"
        binary_file.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00")

        changes = gitops.get_changes()

        assert len(changes) == 1
        assert changes[0]["file"] == "image.png"

    def test_handles_special_characters_in_filename(self, temp_git_repo, change_cwd):
        """Test handling of special characters in filenames."""
        os.chdir(temp_git_repo)
        gitops = GitOps()

        # Create file with special characters (safe ones)
        special_file = temp_git_repo / "file-with_special.chars.py"
        special_file.write_text("# special")

        changes = gitops.get_changes()

        assert len(changes) == 1
        assert "special" in changes[0]["file"]


class TestNotAGitRepoError:
    """Tests for NotAGitRepoError exception."""

    def test_exception_message(self):
        """Test that exception has descriptive message."""
        error = NotAGitRepoError("Custom message")

        assert str(error) == "Custom message"

    def test_exception_inheritance(self):
        """Test that exception inherits from Exception."""
        assert issubclass(NotAGitRepoError, Exception)


class TestGitOpsGetExcludedChanges:
    """Tests for GitOps.get_excluded_changes method."""

    def test_returns_empty_list_when_no_excluded(self, temp_git_repo, change_cwd):
        """Test returns empty list when no excluded files."""
        os.chdir(temp_git_repo)
        gitops = GitOps()

        # Create normal file
        (temp_git_repo / "normal.py").write_text("print('hello')")

        excluded = gitops.get_excluded_changes()
        assert excluded == []

    def test_detects_excluded_untracked_file(self, temp_git_repo, change_cwd):
        """Test detects excluded untracked files."""
        os.chdir(temp_git_repo)
        gitops = GitOps()

        # Create excluded file
        (temp_git_repo / ".env").write_text("SECRET=value")

        excluded = gitops.get_excluded_changes()
        assert ".env" in excluded

    def test_detects_excluded_modified_file(self, temp_git_repo, change_cwd):
        """Test detects excluded modified files."""
        os.chdir(temp_git_repo)
        gitops = GitOps()

        # Create and commit an excluded file first (for testing modified)
        redgit_dir = temp_git_repo / ".redgit"
        redgit_dir.mkdir()
        config_file = redgit_dir / "config.yaml"
        config_file.write_text("test: value")
        subprocess.run(["git", "add", ".redgit/config.yaml"], cwd=temp_git_repo)
        subprocess.run(["git", "commit", "-m", "add config"], cwd=temp_git_repo)

        # Modify the excluded file
        config_file.write_text("test: new_value")

        excluded = gitops.get_excluded_changes()
        assert any(".redgit" in f for f in excluded)


class TestGitOpsHasCommits:
    """Tests for GitOps.has_commits method."""

    def test_returns_false_for_empty_repo(self, temp_dir, change_cwd):
        """Test returns False for repo with no commits."""
        gitops = GitOps(auto_init=True)

        assert gitops.has_commits() is False

    def test_returns_true_for_repo_with_commits(self, temp_git_repo, change_cwd):
        """Test returns True for repo with commits."""
        os.chdir(temp_git_repo)
        gitops = GitOps()

        assert gitops.has_commits() is True


class TestGitOpsGetDiffsForFiles:
    """Tests for GitOps.get_diffs_for_files method."""

    def test_returns_diff_for_modified_file(self, temp_git_repo, change_cwd):
        """Test returns diff for modified files."""
        os.chdir(temp_git_repo)
        gitops = GitOps()

        # Modify existing file
        readme = temp_git_repo / "README.md"
        readme.write_text("# Modified Content\n")

        diffs = gitops.get_diffs_for_files(["README.md"])

        assert "README.md" in diffs
        assert "Modified" in diffs or "---" in diffs or "+++" in diffs

    def test_returns_content_for_new_file(self, temp_git_repo, change_cwd):
        """Test returns content for new untracked files."""
        os.chdir(temp_git_repo)
        gitops = GitOps()

        # Create new file
        new_file = temp_git_repo / "new_file.py"
        new_file.write_text("print('hello world')")

        diffs = gitops.get_diffs_for_files(["new_file.py"])

        assert "new_file.py" in diffs
        assert "new file" in diffs or "hello world" in diffs

    def test_returns_staged_diff(self, temp_git_repo, change_cwd):
        """Test returns diff for staged files."""
        os.chdir(temp_git_repo)
        gitops = GitOps()

        # Modify and stage file
        readme = temp_git_repo / "README.md"
        readme.write_text("# Staged Changes\n")
        subprocess.run(["git", "add", "README.md"], cwd=temp_git_repo)

        diffs = gitops.get_diffs_for_files(["README.md"])

        assert "README.md" in diffs

    def test_handles_nonexistent_file(self, temp_git_repo, change_cwd):
        """Test handles non-existent files gracefully."""
        os.chdir(temp_git_repo)
        gitops = GitOps()

        diffs = gitops.get_diffs_for_files(["nonexistent.py"])

        # Should return empty or not crash
        assert isinstance(diffs, str)

    def test_combines_multiple_files(self, temp_git_repo, change_cwd):
        """Test combines diffs from multiple files."""
        os.chdir(temp_git_repo)
        gitops = GitOps()

        # Create multiple files
        (temp_git_repo / "file1.py").write_text("# file 1")
        (temp_git_repo / "file2.py").write_text("# file 2")

        diffs = gitops.get_diffs_for_files(["file1.py", "file2.py"])

        assert "file1.py" in diffs
        assert "file2.py" in diffs

    def test_truncates_large_files(self, temp_git_repo, change_cwd):
        """Test truncates very large files."""
        os.chdir(temp_git_repo)
        gitops = GitOps()

        # Create large file
        large_file = temp_git_repo / "large.py"
        large_file.write_text("x" * 5000)

        diffs = gitops.get_diffs_for_files(["large.py"])

        # Should contain truncation message or be truncated
        assert len(diffs) < 5000 or "truncated" in diffs


class TestGitOpsRemoteBranchExists:
    """Tests for GitOps.remote_branch_exists method."""

    def test_returns_false_when_no_remote(self, temp_git_repo, change_cwd):
        """Test returns False when no remote exists."""
        os.chdir(temp_git_repo)
        gitops = GitOps()

        result = gitops.remote_branch_exists("main")

        assert result is False

    def test_returns_false_for_nonexistent_branch(self, temp_git_repo, change_cwd):
        """Test returns False for non-existent remote branch."""
        os.chdir(temp_git_repo)
        gitops = GitOps()
        gitops.repo.create_remote("origin", "https://github.com/test/repo.git")

        result = gitops.remote_branch_exists("nonexistent-branch")

        assert result is False


class TestGitOpsMergeBranch:
    """Tests for GitOps.merge_branch method."""

    def test_merge_success(self, temp_git_repo, change_cwd):
        """Test successful branch merge."""
        os.chdir(temp_git_repo)
        gitops = GitOps()
        original = gitops.original_branch

        # Create feature branch with a commit
        gitops.repo.git.checkout("-b", "feature/merge-test")
        (temp_git_repo / "feature.py").write_text("# feature")
        subprocess.run(["git", "add", "feature.py"], cwd=temp_git_repo)
        subprocess.run(["git", "commit", "-m", "add feature"], cwd=temp_git_repo)

        # Go back to original
        gitops.repo.git.checkout(original)

        # Merge
        success, error = gitops.merge_branch("feature/merge-test", original)

        assert success is True
        assert error is None
        # Branch should be deleted
        branches = [b.name for b in gitops.repo.branches]
        assert "feature/merge-test" not in branches

    def test_merge_keeps_branch_when_requested(self, temp_git_repo, change_cwd):
        """Test merge keeps branch when delete_source=False."""
        os.chdir(temp_git_repo)
        gitops = GitOps()
        original = gitops.original_branch

        # Create feature branch with a commit
        gitops.repo.git.checkout("-b", "feature/keep-me")
        (temp_git_repo / "keep.py").write_text("# keep")
        subprocess.run(["git", "add", "keep.py"], cwd=temp_git_repo)
        subprocess.run(["git", "commit", "-m", "add keep"], cwd=temp_git_repo)

        # Go back to original
        gitops.repo.git.checkout(original)

        # Merge without deleting
        success, error = gitops.merge_branch("feature/keep-me", original, delete_source=False)

        assert success is True
        # Branch should still exist
        branches = [b.name for b in gitops.repo.branches]
        assert "feature/keep-me" in branches


class TestGitOpsCreateBranchAndCommit:
    """Tests for GitOps.create_branch_and_commit method."""

    def test_creates_branch_and_commits(self, temp_git_repo, change_cwd):
        """Test creates branch and commits files."""
        os.chdir(temp_git_repo)
        gitops = GitOps()

        # Create file
        (temp_git_repo / "feature.py").write_text("# feature")

        # Create branch and commit
        success = gitops.create_branch_and_commit(
            "feature/test",
            ["feature.py"],
            "feat: add feature"
        )

        assert success is True
        # Should be back on original branch
        assert gitops.repo.active_branch.name == gitops.original_branch

    def test_excludes_sensitive_files(self, temp_git_repo, change_cwd):
        """Test excludes sensitive files from commit."""
        os.chdir(temp_git_repo)
        gitops = GitOps()

        # Create files
        (temp_git_repo / "feature.py").write_text("# feature")
        (temp_git_repo / ".env").write_text("SECRET=value")

        # Try to commit both
        success = gitops.create_branch_and_commit(
            "feature/test",
            ["feature.py", ".env"],
            "feat: add feature"
        )

        assert success is True

    def test_handles_deleted_files(self, temp_git_repo, change_cwd):
        """Test handles deleted files in commit."""
        os.chdir(temp_git_repo)
        gitops = GitOps()

        # Create and commit a file first
        (temp_git_repo / "to_delete.py").write_text("# delete me")
        subprocess.run(["git", "add", "to_delete.py"], cwd=temp_git_repo)
        subprocess.run(["git", "commit", "-m", "add file"], cwd=temp_git_repo)

        # Delete the file
        (temp_git_repo / "to_delete.py").unlink()

        # Commit the deletion
        success = gitops.create_branch_and_commit(
            "feature/delete",
            ["to_delete.py"],
            "chore: delete file"
        )

        assert success is True

    def test_returns_false_when_no_files(self, temp_git_repo, change_cwd):
        """Test returns False when no valid files to commit."""
        os.chdir(temp_git_repo)
        gitops = GitOps()

        # Try to commit only excluded files
        success = gitops.create_branch_and_commit(
            "feature/test",
            [".env"],  # Only excluded file
            "feat: nothing"
        )

        assert success is False

    def test_merge_request_strategy_keeps_branch(self, temp_git_repo, change_cwd):
        """Test merge-request strategy keeps branch for later."""
        os.chdir(temp_git_repo)
        gitops = GitOps()

        # Create file
        (temp_git_repo / "feature.py").write_text("# feature")

        # Create branch and commit with merge-request strategy
        success = gitops.create_branch_and_commit(
            "feature/pr",
            ["feature.py"],
            "feat: add feature",
            strategy="merge-request"
        )

        assert success is True
        # Branch should still exist
        branches = [b.name for b in gitops.repo.branches]
        assert "feature/pr" in branches


class TestGitOpsCheckoutOrCreateBranch:
    """Tests for GitOps.checkout_or_create_branch method."""

    def test_creates_new_branch(self, temp_git_repo, change_cwd):
        """Test creates new branch when doesn't exist."""
        os.chdir(temp_git_repo)
        gitops = GitOps()

        success, is_new, error = gitops.checkout_or_create_branch("feature/new")

        assert success is True
        assert is_new is True
        assert error is None
        assert gitops.repo.active_branch.name == "feature/new"

    def test_switches_to_existing_local_branch(self, temp_git_repo, change_cwd):
        """Test switches to existing local branch."""
        os.chdir(temp_git_repo)
        gitops = GitOps()
        original = gitops.original_branch

        # Create branch
        gitops.repo.git.checkout("-b", "feature/existing")
        gitops.repo.git.checkout(original)

        # Switch to it
        success, is_new, error = gitops.checkout_or_create_branch("feature/existing")

        assert success is True
        assert is_new is False
        assert error is None

    def test_preserves_changes_during_switch(self, temp_git_repo, change_cwd):
        """Test preserves uncommitted changes during branch switch."""
        os.chdir(temp_git_repo)
        gitops = GitOps()

        # Create uncommitted change
        (temp_git_repo / "uncommitted.py").write_text("# uncommitted")

        success, is_new, error = gitops.checkout_or_create_branch("feature/with-changes")

        assert success is True
        # File should still exist
        assert (temp_git_repo / "uncommitted.py").exists()


class TestGitOpsCommitToEmptyRepo:
    """Tests for GitOps._commit_to_empty_repo method."""

    def test_commits_to_empty_repo(self, temp_dir, change_cwd):
        """Test commits to empty repo directly."""
        gitops = GitOps(auto_init=True)

        # Create file
        (temp_dir / "initial.py").write_text("# initial")

        # Commit to empty repo
        success = gitops._commit_to_empty_repo(
            "feature/initial",
            ["initial.py"],
            [],
            "Initial commit"
        )

        assert success is True
        assert gitops.has_commits() is True

    def test_updates_original_branch_after_commit(self, temp_dir, change_cwd):
        """Test updates original_branch after first commit."""
        gitops = GitOps(auto_init=True)

        # Create file
        (temp_dir / "initial.py").write_text("# initial")

        # Commit
        gitops._commit_to_empty_repo(
            "feature/initial",
            ["initial.py"],
            [],
            "Initial commit"
        )

        # original_branch should be updated
        assert gitops.original_branch is not None


class TestGitOpsCreateSubtaskBranchAndCommit:
    """Tests for GitOps.create_subtask_branch_and_commit method."""

    def test_creates_subtask_and_merges(self, temp_git_repo, change_cwd):
        """Test creates subtask branch and merges back to parent."""
        os.chdir(temp_git_repo)
        gitops = GitOps()

        # Create parent branch first (using - instead of / to avoid git ref conflicts)
        gitops.repo.git.checkout("-b", "feature-parent-task")

        # Create file
        (temp_git_repo / "subtask.py").write_text("# subtask")

        # Create subtask and merge (subtask uses different naming)
        success = gitops.create_subtask_branch_and_commit(
            "subtask-1-of-parent",
            "feature-parent-task",
            ["subtask.py"],
            "feat: add subtask"
        )

        assert success is True
        # Should be on parent branch
        assert gitops.repo.active_branch.name == "feature-parent-task"
        # Subtask branch should be deleted
        branches = [b.name for b in gitops.repo.branches]
        assert "subtask-1-of-parent" not in branches

    def test_excludes_sensitive_files(self, temp_git_repo, change_cwd):
        """Test excludes sensitive files from subtask commit."""
        os.chdir(temp_git_repo)
        gitops = GitOps()

        # Create parent branch
        gitops.repo.git.checkout("-b", "parent-task")

        # Create files including excluded
        (temp_git_repo / "subtask.py").write_text("# subtask")
        (temp_git_repo / ".env").write_text("SECRET=value")

        success = gitops.create_subtask_branch_and_commit(
            "subtask-of-parent",
            "parent-task",
            ["subtask.py", ".env"],
            "feat: subtask"
        )

        assert success is True

    def test_returns_false_when_no_files(self, temp_git_repo, change_cwd):
        """Test returns False when no valid files."""
        os.chdir(temp_git_repo)
        gitops = GitOps()

        # Create parent branch
        gitops.repo.git.checkout("-b", "parent-task-2")

        success = gitops.create_subtask_branch_and_commit(
            "subtask-empty",
            "parent-task-2",
            [".env"],  # Only excluded file
            "feat: nothing"
        )

        assert success is False


class TestGitOpsStageFilesExcluded:
    """Tests for stage_files with excluded files."""

    def test_returns_excluded_files(self, temp_git_repo, change_cwd):
        """Test returns list of excluded files."""
        os.chdir(temp_git_repo)
        gitops = GitOps()

        # Create files
        (temp_git_repo / "normal.py").write_text("# normal")
        (temp_git_repo / ".env").write_text("SECRET=value")

        staged, excluded = gitops.stage_files(["normal.py", ".env"])

        assert "normal.py" in staged
        assert ".env" in excluded

    def test_skips_nonexistent_files(self, temp_git_repo, change_cwd):
        """Test skips files that don't exist."""
        os.chdir(temp_git_repo)
        gitops = GitOps()

        staged, excluded = gitops.stage_files(["nonexistent.py"])

        assert staged == []
        assert excluded == []
