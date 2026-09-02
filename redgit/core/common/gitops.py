import contextlib
import os
import subprocess
import tempfile
import uuid
from pathlib import Path
from typing import List, Generator, Optional
import git
from git.exc import InvalidGitRepositoryError
from rich.console import Console

from ...utils.security import is_excluded
from .constants import (
    MAX_DIFF_LENGTH,
    GIT_CONFLICT_STATUSES,
    GIT_DELETED_CONFLICT_STATUSES,
)

_console = Console(stderr=True)


class NotAGitRepoError(Exception):
    """Raised when the current directory is not a git repository."""
    pass


def init_git_repo(remote_url: Optional[str] = None) -> git.Repo:
    """
    Initialize a new git repository in the current directory.

    Args:
        remote_url: Optional remote URL to add as origin

    Returns:
        The initialized git.Repo object
    """
    repo = git.Repo.init(".")

    # Add remote if provided
    if remote_url:
        repo.create_remote("origin", remote_url)

    return repo


class GitOps:
    def __init__(self, auto_init: bool = False, remote_url: Optional[str] = None):
        """
        Initialize GitOps.

        Args:
            auto_init: If True, automatically initialize git repo if not exists
            remote_url: Remote URL to add when auto-initializing
        """
        try:
            self.repo = git.Repo(".", search_parent_directories=True)
        except InvalidGitRepositoryError:
            if auto_init:
                self.repo = init_git_repo(remote_url)
            else:
                raise NotAGitRepoError(
                    "Not a git repository. Please run 'git init' first or navigate to a git repository."
                )
        self.original_branch = self.repo.active_branch.name if self.repo.head.is_valid() else "main"

    def get_changes(self, include_excluded: bool = False, staged_only: bool = False) -> List[dict]:
        """
        Get list of changed files in the repository.

        Args:
            include_excluded: If True, include sensitive/excluded files (not recommended)
            staged_only: If True, only return staged (index) changes, ignore unstaged/untracked

        Returns:
            List of {"file": path, "status": "U"|"M"|"A"|"D"|"C"} dicts
            C = Conflict (unmerged)
        """
        changes = []
        seen = set()

        # First, check for merge conflicts (unmerged files)
        # These need special handling as they don't appear in normal diffs
        # Note: Conflicts are always included even in staged_only mode
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                cwd=self.repo.working_dir
            )
            if result.returncode == 0:
                for line in result.stdout.strip().split("\n"):
                    if not line:
                        continue
                    # Porcelain format: XY filename
                    # X = index status, Y = worktree status
                    # Unmerged statuses: DD, AU, UD, UA, DU, AA, UU
                    if len(line) >= 3:
                        xy = line[:2]
                        filepath = line[3:].strip()
                        # Handle renamed files (old -> new format)
                        if " -> " in filepath:
                            filepath = filepath.split(" -> ")[-1]
                        # Check for unmerged (conflict) statuses
                        if xy in GIT_CONFLICT_STATUSES:
                            if filepath not in seen:
                                seen.add(filepath)
                                if include_excluded or not is_excluded(filepath):
                                    # For "deleted by them" (UD) or "deleted by us" (DU),
                                    # mark as deleted if we want to accept the deletion
                                    if xy in GIT_DELETED_CONFLICT_STATUSES:
                                        changes.append({"file": filepath, "status": "D", "conflict": True})
                                    else:
                                        changes.append({"file": filepath, "status": "C", "conflict": True})
        except Exception:
            pass

        # Skip untracked and unstaged if staged_only mode
        if not staged_only:
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

    def has_commits(self) -> bool:
        """Check if the repository has any commits."""
        try:
            self.repo.head.commit
            return True
        except ValueError:
            return False

    def get_diffs_for_files(self, files: List[str]) -> str:
        """
        Get combined diff output for a list of files.

        Args:
            files: List of file paths to get diffs for

        Returns:
            Combined diff string for all specified files
        """
        import subprocess

        diffs = []

        for file_path in files:
            try:
                # Try to get diff for staged or unstaged changes
                # First try unstaged
                result = subprocess.run(
                    ["git", "diff", "--", file_path],
                    capture_output=True,
                    text=True,
                    cwd=self.repo.working_dir
                )

                if result.stdout.strip():
                    diffs.append(f"# {file_path}\n{result.stdout}")
                    continue

                # Try staged
                result = subprocess.run(
                    ["git", "diff", "--cached", "--", file_path],
                    capture_output=True,
                    text=True,
                    cwd=self.repo.working_dir
                )

                if result.stdout.strip():
                    diffs.append(f"# {file_path}\n{result.stdout}")
                    continue

                # For untracked files, show the file content as "new file"
                from pathlib import Path
                path = Path(self.repo.working_dir) / file_path
                if path.exists() and path.is_file():
                    try:
                        content = path.read_text(encoding='utf-8', errors='ignore')
                        # Truncate large files
                        if len(content) > MAX_DIFF_LENGTH:
                            content = content[:MAX_DIFF_LENGTH] + "\n... (truncated)"
                        diffs.append(f"# {file_path} (new file)\n+++ {file_path}\n{content}")
                    except Exception:
                        pass

            except Exception:
                continue

        return "\n\n".join(diffs)

    def _find_stash_index(self, message_pattern: str) -> Optional[int]:
        """
        Find a stash index by its message pattern.

        Args:
            message_pattern: The pattern to search for in stash messages

        Returns:
            The stash index (0-based) if found, None otherwise
        """
        try:
            result = self.repo.git.stash("list")
            if not result:
                return None

            for line in result.split("\n"):
                if message_pattern in line:
                    # Format: stash@{0}: On branch: message
                    # Extract the index from stash@{N}
                    start = line.find("stash@{") + 7
                    end = line.find("}", start)
                    if start > 6 and end > start:
                        return int(line[start:end])
            return None
        except Exception:
            return None

    def _pop_stash_by_message(self, message_pattern: str) -> bool:
        """
        Pop a specific stash entry by its message pattern.

        This prevents mixing up stash entries when multiple groups are being processed.
        If the specific stash is not found, it will NOT pop any stash to avoid
        accidentally restoring unrelated files.

        Args:
            message_pattern: The pattern to search for in stash messages

        Returns:
            True if stash was found and popped, False otherwise
        """
        stash_index = self._find_stash_index(message_pattern)
        if stash_index is not None:
            try:
                self.repo.git.stash("pop", f"stash@{{{stash_index}}}")
                return True
            except Exception:
                return False
        return False

    def _pop_stash_or_warn(self, message_pattern: str) -> bool:
        """
        Pop a stash by message pattern; if the stash exists but the pop fails
        (e.g. conflict), warn the user loudly instead of failing silently.

        Returns:
            True if there was nothing to pop or the pop succeeded,
            False if the stash exists but could not be popped.
        """
        stash_index = self._find_stash_index(message_pattern)
        if stash_index is None:
            return True

        if self._pop_stash_by_message(message_pattern):
            return True

        _console.print(
            f"[red bold]⚠️  Stash geri yüklenemedi (muhtemel conflict): "
            f"'{message_pattern}'[/red bold]"
        )
        _console.print(
            "[yellow]   Değişiklikleriniz kaybolmadı, stash içinde bekliyor:[/yellow]"
        )
        _console.print(f"[dim]   git stash list                    # '{message_pattern}' girdisini bulun[/dim]")
        _console.print(f"[dim]   git stash pop stash@{{{stash_index}}}          # elle geri yükleyin[/dim]")
        return False

    @staticmethod
    def _unique_stash_token(prefix: str, name: str) -> str:
        """
        Build a per-run unique stash message so a stale stash from a previous
        failed run with the same branch name can never be matched/popped.
        """
        return f"{prefix}-{name}-{uuid.uuid4().hex[:8]}"

    def _classify_files(self, files: List[str]) -> tuple:
        """
        Classify requested files into (safe_files, deleted_files, missing_files).

        - safe_files: exist on disk, will be committed with worktree content
        - deleted_files: explicitly marked "D" in git status, deletion will be committed
        - missing_files: absent from disk but NOT marked deleted in git status.
          These are likely stuck in a stash from a previous failed run; they are
          NEVER committed as deletions. A loud warning is printed instead.
        """
        current_changes = {c["file"]: c["status"] for c in self.get_changes()}
        git_root = Path(self.repo.working_dir)

        safe_files = []
        deleted_files = []
        missing_files = []
        for f in files:
            if is_excluded(f):
                continue
            status = current_changes.get(f)
            file_path = git_root / f

            if status == "D":
                deleted_files.append(f)
            elif file_path.exists():
                safe_files.append(f)
            else:
                missing_files.append(f)

        if missing_files:
            _console.print(
                f"[red bold]⚠️  {len(missing_files)} dosya diskte yok ama git status silinmiş "
                f"olarak işaretlemiyor — silme OLARAK COMMITLENMEYECEK:[/red bold]"
            )
            for f in missing_files[:10]:
                _console.print(f"[yellow]   • {f}[/yellow]")
            _console.print("[dim]   Muhtemelen önceki bir çalışmadan stash içinde kaldılar: git stash list[/dim]")

        return safe_files, deleted_files, missing_files

    def _branch_exists(self, branch_name: str) -> bool:
        """Check if a local branch exists."""
        try:
            return branch_name in [b.name for b in self.repo.branches]
        except Exception:
            return False

    def _resolve_new_branch_name(self, branch_name: str) -> str:
        """
        Return a branch name that does not collide with an existing local branch.
        Never silently reuses an existing branch (its history may be stale).
        """
        if not self._branch_exists(branch_name):
            return branch_name
        candidate = f"{branch_name}-v2"
        if not self._branch_exists(candidate):
            _console.print(
                f"[yellow]⚠️  Branch '{branch_name}' zaten var, '{candidate}' kullanılıyor[/yellow]"
            )
            return candidate
        candidate = f"{branch_name}-{uuid.uuid4().hex[:6]}"
        _console.print(
            f"[yellow]⚠️  Branch '{branch_name}' zaten var, '{candidate}' kullanılıyor[/yellow]"
        )
        return candidate

    def commit_files_with_temp_index(
        self,
        files: List[str],
        deleted_files: List[str],
        message: str,
        parent_ref: str = "HEAD"
    ) -> Optional[str]:
        """
        Build a commit object containing only the given files on top of parent_ref,
        using a temporary index. The working tree and the real index are NEVER touched,
        so there is nothing to stash and nothing that can be lost.

        Args:
            files: Files to commit with their current worktree content
            deleted_files: Files whose deletion should be committed
            message: Commit message
            parent_ref: Parent commit ref (branch name or sha)

        Returns:
            New commit sha, or None if the resulting tree is identical to the
            parent's tree (nothing to commit — prevents empty commits).
        """
        git_dir = Path(self.repo.git_dir)
        fd, tmp_index = tempfile.mkstemp(prefix="redgit-index-", dir=str(git_dir))
        os.close(fd)
        try:
            with self.repo.git.custom_environment(GIT_INDEX_FILE=tmp_index):
                # Seed temp index from the parent tree
                self.repo.git.read_tree(parent_ref)

                # Stage selected worktree files into the temp index
                # (chunked to stay clear of ARG_MAX on huge file lists)
                for i in range(0, len(files), 100):
                    chunk = files[i:i + 100]
                    self.repo.git.add("--", *chunk)

                # Stage deletions
                for f in deleted_files:
                    try:
                        self.repo.git.update_index("--force-remove", "--", f)
                    except Exception:
                        pass

                tree_sha = self.repo.git.write_tree().strip()

            parent_tree = self.repo.git.rev_parse(f"{parent_ref}^{{tree}}").strip()
            if tree_sha == parent_tree:
                # Nothing actually changed relative to parent — refuse empty commit
                return None

            parent_sha = self.repo.git.rev_parse(parent_ref).strip()
            commit_sha = self.repo.git.commit_tree(
                tree_sha, "-p", parent_sha, "-m", message
            ).strip()
            return commit_sha
        finally:
            try:
                os.unlink(tmp_index)
            except OSError:
                pass

    def _advance_branch(self, branch: str, new_sha: str):
        """
        Move a branch ref to new_sha. If it is the currently checked-out branch,
        also sync the real index to the new HEAD (working tree untouched).
        """
        try:
            current = self.repo.active_branch.name
        except Exception:
            current = None

        if current == branch:
            self.repo.git.update_ref(f"refs/heads/{branch}", new_sha)
            # Sync index to new HEAD; --mixed never touches the working tree
            self.repo.git.reset("--mixed", "HEAD")
        else:
            self.repo.git.branch("-f", branch, new_sha)

    def _clean_worktree_after_commit(
        self,
        base_branch: str,
        safe_files: List[str],
        deleted_files: List[str]
    ):
        """
        After committing files to a separate branch (merge-request strategy),
        restore the base branch's version of those files in the working tree so
        they are not re-proposed. The committed content is already safely stored
        in the branch commit, so this cannot lose data.
        """
        git_root = Path(self.repo.working_dir)

        for f in safe_files:
            try:
                # Does the file exist in the base tree?
                self.repo.git.cat_file("-e", f"{base_branch}:{f}")
                in_base = True
            except Exception:
                in_base = False

            try:
                if in_base:
                    # Restores index + worktree to base version
                    self.repo.git.checkout(base_branch, "--", f)
                else:
                    # New file: unstage if staged, then remove worktree copy
                    # (content is preserved in the feature branch commit)
                    try:
                        self.repo.git.reset("HEAD", "--", f)
                    except Exception:
                        pass
                    (git_root / f).unlink(missing_ok=True)
            except Exception as e:
                _console.print(f"[yellow]⚠️  Worktree temizlenemedi: {f} ({e})[/yellow]")

        for f in deleted_files:
            # Deletion is committed on the branch; restore base version in worktree
            try:
                self.repo.git.checkout(base_branch, "--", f)
            except Exception:
                pass

    def create_branch_and_commit(
        self,
        branch_name: str,
        files: List[str],
        message: str,
        strategy: str = "local-merge"
    ) -> bool:
        """
        Create a branch and commit specific files WITHOUT touching the working tree.

        Uses a temporary index + git commit-tree, so no stash/checkout dance is
        needed and working directory changes can never be lost.

        Args:
            branch_name: Name of the branch to create
            files: List of files to commit
            message: Commit message
            strategy: "local-merge" (merge immediately) or "merge-request" (keep branch for PR)

        Returns:
            True if a commit was created, False if there was nothing to commit.

        local-merge:
        1. Build commit object from base tree + selected files (temp index)
        2. Point feature branch at it
        3. Build a no-ff style merge commit (two parents) and advance base branch
        4. Delete feature branch (merged)
        Working tree is never modified; committed files simply stop showing as changed.

        merge-request:
        1. Build commit object from base tree + selected files (temp index)
        2. Point feature branch at it (kept for later push/PR)
        3. Restore base version of committed files in the working tree so they
           are not re-proposed (content lives in the branch commit).
        """
        base_branch = self.original_branch
        is_empty_repo = not self.has_commits()

        safe_files, deleted_files, _missing = self._classify_files(files)

        if not safe_files and not deleted_files:
            return False

        # Special handling for empty repos (no commits yet)
        if is_empty_repo:
            return self._commit_to_empty_repo(
                branch_name, safe_files, deleted_files, message, strategy
            )

        # 1. Build the commit object (no worktree/index side effects)
        commit_sha = self.commit_files_with_temp_index(
            safe_files, deleted_files, message, parent_ref=base_branch
        )
        if commit_sha is None:
            _console.print(
                f"[yellow]⚠️  '{branch_name}': commit edilecek gerçek değişiklik yok "
                f"(boş commit engellendi)[/yellow]"
            )
            return False

        # 2. Create the feature branch pointing at the new commit
        actual_branch_name = self._resolve_new_branch_name(branch_name)
        self.repo.git.branch(actual_branch_name, commit_sha)

        if strategy == "local-merge":
            # 3. Build a no-ff style merge commit and advance the base branch
            base_sha = self.repo.git.rev_parse(base_branch).strip()
            tree_sha = self.repo.git.rev_parse(f"{commit_sha}^{{tree}}").strip()
            merge_sha = self.repo.git.commit_tree(
                tree_sha,
                "-p", base_sha,
                "-p", commit_sha,
                "-m", f"Merge {actual_branch_name}"
            ).strip()
            self._advance_branch(base_branch, merge_sha)

            # 4. Delete feature branch. The merge commit provably contains it
            # (it is a parent), so force-delete is safe even when HEAD is elsewhere.
            try:
                self.repo.git.branch("-d", actual_branch_name)
            except Exception:
                try:
                    self.repo.git.branch("-D", actual_branch_name)
                except Exception:
                    pass
        else:
            # merge-request: keep branch, clean committed changes from worktree
            self._clean_worktree_after_commit(base_branch, safe_files, deleted_files)

        return True

    @contextlib.contextmanager
    def isolated_branch(self, branch_name: str) -> Generator[None, None, None]:
        """
        DEPRECATED: Use create_branch_and_commit instead.

        Create an isolated branch for committing specific files.
        This method has issues with file preservation across multiple groups.
        """
        is_new_repo = not self.has_commits()
        original_branch = self.original_branch

        try:
            if is_new_repo:
                # New repo without commits - create orphan branch
                try:
                    self.repo.git.checkout("--orphan", branch_name)
                except Exception:
                    pass
            else:
                # Existing repo - create branch from HEAD
                try:
                    self.repo.git.checkout("-b", branch_name)
                except Exception:
                    try:
                        self.repo.git.checkout("-b", f"{branch_name}-v2")
                    except Exception:
                        pass

            yield

        finally:
            # After commit, return to original branch
            if is_new_repo:
                # For new repos, after first commit we can switch branches normally
                try:
                    # Check if we made a commit
                    if self.has_commits():
                        # Create/checkout main branch
                        try:
                            self.repo.git.checkout("-b", original_branch)
                        except Exception:
                            try:
                                self.repo.git.checkout(original_branch)
                            except Exception:
                                pass
                except Exception:
                    pass
            else:
                try:
                    self.repo.git.checkout(original_branch)
                except Exception:
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

        # Get git root directory for resolving relative paths
        git_root = Path(self.repo.working_dir)

        for f in files:
            # Skip excluded files - NEVER stage them
            if is_excluded(f):
                excluded.append(f)
                continue

            # Check if file exists relative to git root (not current directory)
            file_path = git_root / f
            if file_path.exists():
                self.repo.index.add([f])
                staged.append(f)

        return staged, excluded

    def commit(self, message: str, files: List[str] = None) -> Optional[str]:
        """
        Create a commit with the staged files.

        Args:
            message: Commit message
            files: If provided, reset these files in working directory after commit

        Returns:
            Commit sha, or None if nothing was staged (empty commit refused).
        """
        # Refuse empty commits: nothing staged relative to HEAD
        if self.has_commits():
            try:
                staged = self.repo.git.diff("--cached", "--name-only").strip()
            except Exception:
                staged = None
            if staged == "":
                _console.print(
                    "[yellow]⚠️  Stage'lenmiş değişiklik yok — boş commit engellendi[/yellow]"
                )
                return None

        sha = self.repo.index.commit(message).hexsha

        # After committing, the files are in the branch's history
        # We need to remove them from the working directory so they don't
        # appear as "modified" when we switch back to the original branch
        if files:
            for f in files:
                try:
                    # Reset the file to match HEAD (removes local changes)
                    self.repo.git.checkout("HEAD", "--", f)
                except Exception:
                    pass

        return sha

    def _commit_to_empty_repo(
        self,
        branch_name: str,
        safe_files: List[str],
        deleted_files: List[str],
        message: str,
        strategy: str = "local-merge"
    ) -> bool:
        """
        Handle commits in a repository with no commits yet.

        For empty repos, we can't create branches from a base since there's no commit.
        Instead, we commit directly to the current branch.

        After the first commit, subsequent commits in the same session will use
        the normal branch-based flow since the repo will have commits.

        Args:
            branch_name: Intended branch name (used for naming only in message)
            safe_files: List of files to commit
            deleted_files: List of deleted files to stage
            message: Commit message
            strategy: "local-merge" or "merge-request" (ignored for first commit)

        Returns:
            True if successful
        """
        try:
            # In empty repo, just stage and commit directly to current branch
            # The branch will be created on first commit

            # Stage the files
            for f in safe_files:
                try:
                    self.repo.index.add([f])
                except Exception:
                    pass

            # Stage deleted files (unlikely in empty repo but handle anyway)
            for f in deleted_files:
                try:
                    self.repo.index.remove([f], working_tree=False)
                except Exception:
                    pass

            # Commit - this creates the initial commit and the branch
            self.repo.index.commit(message)

            # Update original_branch now that we have a commit
            # This is crucial for subsequent commits to use normal branch flow
            self.original_branch = self.repo.active_branch.name

            return True

        except Exception as e:
            raise e

    def remote_branch_exists(self, branch_name: str, remote: str = "origin") -> bool:
        """
        Check if a branch exists on the remote.

        Args:
            branch_name: Name of the branch to check
            remote: Remote name (default: "origin")

        Returns:
            True if branch exists on remote, False otherwise
        """
        try:
            result = self.repo.git.ls_remote("--heads", remote, branch_name)
            return bool(result.strip())
        except Exception:
            return False

    def checkout(self, branch_name: str) -> bool:
        """
        Checkout an existing branch, preserving uncommitted changes via stash.

        Args:
            branch_name: Name of the branch to checkout

        Returns:
            True if successful, False otherwise
        """
        # Stash current changes first (unique token: stale stashes can never match)
        stash_token = self._unique_stash_token("redgit-checkout", branch_name)
        stash_created = False
        try:
            self.repo.git.stash("push", "-u", "-m", stash_token)
            stash_created = True
        except Exception:
            pass

        try:
            self.repo.git.checkout(branch_name)

            # Pop stash to restore changes (warn loudly if it fails)
            if stash_created:
                self._pop_stash_or_warn(stash_token)

            return True
        except Exception:
            # Recovery - try to pop stash even if checkout failed
            if stash_created:
                self._pop_stash_or_warn(stash_token)
            return False

    def push(self, branch_name: str = None, set_upstream: bool = True) -> bool:
        """
        Push a branch to remote.

        Args:
            branch_name: Name of the branch to push (default: current branch)
            set_upstream: Whether to set upstream tracking (-u flag)

        Returns:
            True if successful, False otherwise
        """
        try:
            if branch_name is None:
                branch_name = self.repo.active_branch.name

            if set_upstream:
                self.repo.git.push("-u", "origin", branch_name)
            else:
                self.repo.git.push("origin", branch_name)

            return True
        except Exception:
            return False

    def checkout_or_create_branch(
        self,
        branch_name: str,
        from_branch: str = None,
        pull_if_exists: bool = True
    ) -> tuple:
        """
        Checkout existing branch (pulling from remote if exists) or create new one.

        Args:
            branch_name: Name of the branch
            from_branch: Base branch to create from (if creating new)
            pull_if_exists: Whether to pull from remote if branch exists

        Returns:
            (success: bool, is_new: bool, error_message: str or None)
        """
        # Stash current changes first (unique token: stale stashes can never match)
        stash_token = self._unique_stash_token("redgit-checkout", branch_name)
        stash_created = False
        try:
            self.repo.git.stash("push", "-u", "-m", stash_token)
            stash_created = True
        except Exception:
            pass

        try:
            # Check if branch exists on remote
            if self.remote_branch_exists(branch_name):
                # Fetch the branch
                try:
                    self.repo.git.fetch("origin", branch_name)
                except Exception:
                    pass

                # Try to checkout (might exist locally already)
                try:
                    self.repo.git.checkout(branch_name)
                except Exception:
                    # Branch doesn't exist locally, create tracking branch
                    try:
                        self.repo.git.checkout("-b", branch_name, f"origin/{branch_name}")
                    except Exception as e:
                        if stash_created:
                            self._pop_stash_or_warn(stash_token)
                        return False, False, f"Failed to checkout remote branch: {e}"

                # Pull latest changes
                if pull_if_exists:
                    try:
                        self.repo.git.pull("origin", branch_name)
                    except Exception as e:
                        # Pop stash before returning error
                        if stash_created:
                            self._pop_stash_or_warn(stash_token)
                        return False, False, f"Pull failed (possible conflict): {e}"

                # Pop stash (warn loudly if it fails)
                if stash_created:
                    self._pop_stash_or_warn(stash_token)
                return True, False, None

            # Check if branch exists locally
            local_branches = [b.name for b in self.repo.branches]
            if branch_name in local_branches:
                self.repo.git.checkout(branch_name)
                if stash_created:
                    self._pop_stash_or_warn(stash_token)
                return True, False, None

            # Create new branch
            base = from_branch or self.original_branch
            self.repo.git.checkout("-b", branch_name, base)

            if stash_created:
                self._pop_stash_or_warn(stash_token)
            return True, True, None

        except Exception as e:
            # Recovery - try to go back
            if stash_created:
                self._pop_stash_or_warn(stash_token)
            return False, False, str(e)

    def check_base_freshness(self, base_branch: str = None) -> tuple:
        """
        Fetch the base branch from origin and report how far behind local is.

        Args:
            base_branch: Branch to check (default: original_branch)

        Returns:
            (fetched: bool, behind_count: int)
            fetched=False means origin/branch could not be fetched (no remote, offline, ...)
        """
        base = base_branch or self.original_branch
        try:
            self.repo.git.fetch("origin", base)
        except Exception:
            return False, 0

        try:
            behind = self.repo.git.rev_list("--count", f"{base}..origin/{base}")
            return True, int(behind.strip() or 0)
        except Exception:
            return True, 0

    def is_behind_branch(self, branch: str, base_branch: str = None) -> tuple:
        """
        Check if branch is behind base branch.

        Args:
            branch: Branch to check
            base_branch: Branch to compare against (default: original_branch)

        Returns:
            Tuple of (is_behind: bool, commit_count: int)
        """
        if base_branch is None:
            base_branch = self.original_branch

        try:
            # Count commits that are in base but not in branch
            count = self.repo.git.rev_list("--count", f"{branch}..{base_branch}")
            behind_count = int(count.strip())
            return (behind_count > 0, behind_count)
        except Exception:
            return (False, 0)

    def rebase_from_branch(self, target_branch: str, base_branch: str = None) -> tuple:
        """
        Rebase target branch onto base branch.

        Args:
            target_branch: Branch to rebase
            base_branch: Branch to rebase onto (default: original_branch)

        Returns:
            Tuple of (success: bool, error_message: str or None)
        """
        if base_branch is None:
            base_branch = self.original_branch

        try:
            # Ensure we're on target branch
            current = self.repo.active_branch.name
            if current != target_branch:
                self.repo.git.checkout(target_branch)

            # Perform rebase
            self.repo.git.rebase(base_branch)
            return (True, None)
        except Exception as e:
            # Rebase conflict - abort and return error
            try:
                self.repo.git.rebase("--abort")
            except Exception:
                pass
            return (False, str(e))

    def merge_branch(
        self,
        source_branch: str,
        target_branch: str,
        delete_source: bool = True,
        no_ff: bool = True
    ) -> tuple:
        """
        Merge source branch into target branch.

        Args:
            source_branch: Branch to merge from
            target_branch: Branch to merge into
            delete_source: Delete source branch after merge
            no_ff: Use --no-ff for merge (creates merge commit)

        Returns:
            (success: bool, error_message: str or None)
        """
        try:
            # Checkout target
            self.repo.git.checkout(target_branch)

            # Merge source
            if no_ff:
                try:
                    self.repo.git.merge(source_branch, "--no-ff", "-m", f"Merge {source_branch}")
                except Exception:
                    # Try fast-forward merge
                    self.repo.git.merge(source_branch)
            else:
                self.repo.git.merge(source_branch)

            # Delete source if requested
            if delete_source:
                try:
                    self.repo.git.branch("-d", source_branch)
                except Exception:
                    # Force delete if needed
                    try:
                        self.repo.git.branch("-D", source_branch)
                    except Exception:
                        pass

            return True, None

        except Exception as e:
            # Try to abort merge if in conflict state
            try:
                self.repo.git.merge("--abort")
            except Exception:
                pass
            return False, str(e)

    def create_subtask_branch_and_commit(
        self,
        subtask_branch: str,
        parent_branch: str,
        files: List[str],
        message: str
    ) -> bool:
        """
        Create a subtask branch from parent, commit files, merge back to parent.

        This is used for subtask mode where subtask branches are created from
        the parent task branch and merged back to it.

        Args:
            subtask_branch: Name of the subtask branch
            parent_branch: Parent branch to branch from and merge back to
            files: List of files to commit
            message: Commit message

        Returns:
            True if successful (committed and merged)
        """
        safe_files, deleted_files, _missing = self._classify_files(files)

        if not safe_files and not deleted_files:
            return False

        # 1. Build the commit object on top of the parent branch (no worktree side effects)
        commit_sha = self.commit_files_with_temp_index(
            safe_files, deleted_files, message, parent_ref=parent_branch
        )
        if commit_sha is None:
            _console.print(
                f"[yellow]⚠️  '{subtask_branch}': commit edilecek gerçek değişiklik yok "
                f"(boş commit engellendi)[/yellow]"
            )
            return False

        # 2. Create the subtask branch pointing at the new commit
        actual_branch_name = self._resolve_new_branch_name(subtask_branch)
        self.repo.git.branch(actual_branch_name, commit_sha)

        # 3. Build a no-ff style merge commit and advance the parent branch
        parent_sha = self.repo.git.rev_parse(parent_branch).strip()
        tree_sha = self.repo.git.rev_parse(f"{commit_sha}^{{tree}}").strip()
        merge_sha = self.repo.git.commit_tree(
            tree_sha,
            "-p", parent_sha,
            "-p", commit_sha,
            "-m", f"Merge {actual_branch_name}"
        ).strip()
        self._advance_branch(parent_branch, merge_sha)

        # 4. Delete subtask branch. The merge commit provably contains it
        # (it is a parent), so force-delete is safe even when HEAD is elsewhere.
        try:
            self.repo.git.branch("-d", actual_branch_name)
        except Exception:
            try:
                self.repo.git.branch("-D", actual_branch_name)
            except Exception:
                pass

        return True

    def get_project_name(self) -> str:
        """
        Get the project name from git remote URL or folder name.

        This extracts the repository name from the remote 'origin' URL.
        Falls back to the working directory name if no remote is configured.

        Returns:
            Project name (without .git suffix, lowercase)
        """
        import re
        try:
            # Try to get remote origin URL
            remote_url = self.repo.git.remote("get-url", "origin")
            if remote_url:
                # Extract repo name from various URL formats:
                # git@github.com:user/repo.git
                # https://github.com/user/repo.git
                # https://github.com/user/repo
                # git@bitbucket.org:user/repo.git

                # Remove .git suffix
                if remote_url.endswith(".git"):
                    remote_url = remote_url[:-4]

                # Get the last part (repo name)
                # Handle both SSH (git@host:user/repo) and HTTPS (https://host/user/repo)
                if ":" in remote_url and "@" in remote_url:
                    # SSH format: git@github.com:user/repo
                    repo_path = remote_url.split(":")[-1]
                else:
                    # HTTPS format: https://github.com/user/repo
                    repo_path = remote_url

                # Get just the repo name (last part of path)
                repo_name = repo_path.rstrip("/").split("/")[-1]
                return repo_name.lower()

        except Exception:
            pass

        # Fallback to working directory name
        return Path(self.repo.working_dir).name.lower()