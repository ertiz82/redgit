import contextlib
from pathlib import Path
from typing import List, Generator
import git

from ..utils.security import is_excluded


class GitOps:
    def __init__(self):
        self.repo = git.Repo(".")
        self.original_branch = self.repo.active_branch.name if self.repo.head.is_valid() else "main"

    def get_changes(self, include_excluded: bool = False) -> List[dict]:
        """
        Get list of changed files in the repository.

        Args:
            include_excluded: If True, include sensitive/excluded files (not recommended)

        Returns:
            List of {"file": path, "status": "U"|"M"|"A"|"D"} dicts
        """
        changes = []
        seen = set()

        # Untracked files (new files not yet added to git)
        for f in self.repo.untracked_files:
            if f not in seen:
                seen.add(f)
                if include_excluded or not is_excluded(f):
                    changes.append({"file": f, "status": "U"})

        # Unstaged changes (modified in working directory but not staged)
        for item in self.repo.index.diff(None):
            f = item.a_path or item.b_path
            if f not in seen:
                seen.add(f)
                if include_excluded or not is_excluded(f):
                    status = "D" if item.deleted_file else "M"
                    changes.append({"file": f, "status": status})

        # Staged changes (added to index, ready to commit)
        if self.repo.head.is_valid():
            for item in self.repo.index.diff("HEAD"):
                f = item.a_path or item.b_path
                if f not in seen:
                    seen.add(f)
                    if include_excluded or not is_excluded(f):
                        if item.new_file:
                            status = "A"
                        elif item.deleted_file:
                            status = "D"
                        else:
                            status = "M"
                        changes.append({"file": f, "status": status})

        return changes

    def get_excluded_changes(self) -> List[str]:
        """
        Get list of excluded files that have changes.
        Useful for showing user what was filtered out.
        """
        excluded = []
        seen = set()

        # Check untracked files
        for f in self.repo.untracked_files:
            if f not in seen and is_excluded(f):
                seen.add(f)
                excluded.append(f)

        # Check unstaged changes
        for item in self.repo.index.diff(None):
            f = item.a_path or item.b_path
            if f not in seen and is_excluded(f):
                seen.add(f)
                excluded.append(f)

        # Check staged changes
        if self.repo.head.is_valid():
            for item in self.repo.index.diff("HEAD"):
                f = item.a_path or item.b_path
                if f not in seen and is_excluded(f):
                    seen.add(f)
                    excluded.append(f)

        return excluded

    @contextlib.contextmanager
    def isolated_branch(self, branch_name: str) -> Generator[None, None, None]:
        had_stash = False
        try:
            if self.repo.is_dirty(untracked_files=True):
                self.repo.git.stash("push", "--keep-index", "-m", "smart-commit temp")
                had_stash = True
            try:
                self.repo.git.checkout("-b", branch_name)
            except:
                self.repo.git.checkout("-b", f"{branch_name}-v2")
            yield
        finally:
            try:
                self.repo.git.checkout(self.original_branch)
            except:
                pass
            if had_stash:
                try:
                    self.repo.git.stash("pop")
                except:
                    pass

    def stage_files(self, files: List[str]) -> tuple:
        """
        Stage files for commit, excluding sensitive files.

        Args:
            files: List of file paths to stage

        Returns:
            (staged_files, excluded_files) tuple
        """
        staged = []
        excluded = []

        for f in files:
            # Skip excluded files - NEVER stage them
            if is_excluded(f):
                excluded.append(f)
                continue

            # Only stage if file exists
            if Path(f).exists():
                self.repo.index.add([f])
                staged.append(f)

        return staged, excluded

    def commit(self, message: str):
        """Create a commit with the staged files."""
        self.repo.index.commit(message)