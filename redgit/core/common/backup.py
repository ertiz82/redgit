"""
Backup Manager for RedGit.

Provides working tree backup and restore functionality
to protect user changes during rg propose operations.
"""

import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import yaml


class BackupManager:
    """Manages working tree backups for safe propose operations."""

    BACKUP_DIR = ".redgit/backups"

    def __init__(self, gitops=None, repo_path: str = "."):
        """
        Initialize BackupManager.

        Args:
            gitops: Optional GitOps instance (for git state info)
            repo_path: Repository root path
        """
        self.gitops = gitops
        self.repo_path = Path(repo_path).resolve()
        self.backup_path = self.repo_path / self.BACKUP_DIR

    def create_backup(self, command: str, changes: List[dict]) -> str:
        """
        Create a full backup of working tree before propose.

        Args:
            command: The command being executed (for logging)
            changes: List of changed files from gitops.get_changes()

        Returns:
            Backup ID (timestamp string)
        """
        # 1. Generate backup ID
        backup_id = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
        backup_dir = self.backup_path / backup_id

        # 2. Create directory structure
        backup_dir.mkdir(parents=True, exist_ok=True)
        files_dir = backup_dir / "files"
        files_dir.mkdir()

        # 3. Copy all changed files (preserve directory structure)
        for change in changes:
            # Support both "file" (from gitops) and "path" keys
            file_path = change.get("file") or change.get("path", "")
            if not file_path:
                continue

            src = self.repo_path / file_path
            if src.exists() and src.is_file():
                dest = files_dir / file_path
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dest)

        # 4. Get git state info
        branch_name = "unknown"
        head_commit = "unknown"
        stash_list = []

        if self.gitops and hasattr(self.gitops, 'repo'):
            try:
                branch_name = self.gitops.repo.active_branch.name
            except Exception:
                branch_name = "detached"

            try:
                head_commit = self.gitops.repo.head.commit.hexsha[:8]
            except Exception:
                pass

            stash_list = self._get_stash_list()

        # 5. Save manifest
        manifest = {
            "id": backup_id,
            "created_at": datetime.now().isoformat(),
            "command": command,
            "base_branch": branch_name,
            "head_commit": head_commit,
            "status": "created",
            "files": [
                {
                    "file": c.get("file") or c.get("path", ""),
                    "status": c.get("status", "M"),
                    "staged": c.get("staged", False)
                }
                for c in changes
            ],
            "error": None
        }
        self._save_yaml(backup_dir / "manifest.yaml", manifest)

        # 6. Save git state
        git_state = {
            "branch": branch_name,
            "head": head_commit,
            "stash_list": stash_list
        }
        self._save_yaml(backup_dir / "git-state.yaml", git_state)

        # 7. Update latest symlink
        self._update_latest_symlink(backup_id)

        return backup_id

    def restore_backup(self, backup_id: str = "latest") -> dict:
        """
        Restore working tree from backup.

        Args:
            backup_id: Specific backup ID or "latest"

        Returns:
            Manifest dict of restored backup

        Raises:
            ValueError: If backup not found
        """
        # 1. Resolve backup path
        backup_dir = self._resolve_backup(backup_id)
        if not backup_dir.exists():
            raise ValueError(f"Backup not found: {backup_id}")

        # 2. Load manifest
        manifest = self._load_yaml(backup_dir / "manifest.yaml")
        git_state = self._load_yaml(backup_dir / "git-state.yaml")

        # 3. Checkout original branch if needed
        if self.gitops and hasattr(self.gitops, 'repo'):
            target_branch = git_state.get("branch", "")
            try:
                current_branch = self.gitops.repo.active_branch.name
                if current_branch != target_branch and target_branch:
                    # Stash current changes first
                    try:
                        self.gitops.repo.git.stash("push", "-m", "redgit-restore-temp")
                    except Exception:
                        pass
                    try:
                        self.gitops.repo.git.checkout(target_branch)
                    except Exception:
                        pass
            except Exception:
                pass

        # 4. Restore files
        files_dir = backup_dir / "files"
        for file_info in manifest.get("files", []):
            # Support both "file" and "path" keys
            file_path = file_info.get("file") or file_info.get("path", "")
            if not file_path:
                continue

            src = files_dir / file_path
            dest = self.repo_path / file_path

            if src.exists():
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dest)
            elif file_info.get("status") in ("D", "deleted"):
                # File was deleted in backup, remove it
                if dest.exists():
                    dest.unlink()

        # 5. Restore staging state if gitops available
        if self.gitops and hasattr(self.gitops, 'repo'):
            try:
                # Reset index first
                self.gitops.repo.git.reset("HEAD")
                # Re-stage files that were staged
                for file_info in manifest.get("files", []):
                    if file_info.get("staged"):
                        file_path = file_info.get("file") or file_info.get("path", "")
                        if file_path:
                            try:
                                self.gitops.repo.git.add(file_path)
                            except Exception:
                                pass
            except Exception:
                pass

        # 6. Update manifest status
        manifest["status"] = "restored"
        self._save_yaml(backup_dir / "manifest.yaml", manifest)

        return manifest

    def mark_completed(self, backup_id: str):
        """Mark backup as completed (propose succeeded)."""
        backup_dir = self._resolve_backup(backup_id)
        if not backup_dir.exists():
            return

        manifest = self._load_yaml(backup_dir / "manifest.yaml")
        manifest["status"] = "completed"
        self._save_yaml(backup_dir / "manifest.yaml", manifest)

    def mark_failed(self, backup_id: str, error: str):
        """Mark backup as failed with error details."""
        backup_dir = self._resolve_backup(backup_id)
        if not backup_dir.exists():
            return

        manifest = self._load_yaml(backup_dir / "manifest.yaml")
        manifest["status"] = "failed"
        manifest["error"] = error
        self._save_yaml(backup_dir / "manifest.yaml", manifest)

    def list_backups(self) -> List[dict]:
        """List all backups with their status, sorted by newest first."""
        backups = []
        if not self.backup_path.exists():
            return backups

        for item in sorted(self.backup_path.iterdir(), reverse=True):
            if item.is_dir() and item.name != "latest":
                manifest_path = item / "manifest.yaml"
                if manifest_path.exists():
                    try:
                        manifest = self._load_yaml(manifest_path)
                        backups.append(manifest)
                    except Exception:
                        pass

        return backups

    def get_backup(self, backup_id: str = "latest") -> Optional[dict]:
        """Get a specific backup manifest."""
        backup_dir = self._resolve_backup(backup_id)
        if not backup_dir.exists():
            return None

        manifest_path = backup_dir / "manifest.yaml"
        if manifest_path.exists():
            return self._load_yaml(manifest_path)
        return None

    def cleanup_old_backups(self, keep: int = 5):
        """
        Remove old backups, keeping the N most recent.

        Args:
            keep: Number of backups to keep
        """
        backups = self.list_backups()
        for backup in backups[keep:]:
            backup_id = backup.get("id", "")
            if backup_id:
                backup_dir = self.backup_path / backup_id
                if backup_dir.exists():
                    shutil.rmtree(backup_dir, ignore_errors=True)

        # Update latest symlink if needed
        remaining = self.list_backups()
        if remaining:
            self._update_latest_symlink(remaining[0]["id"])
        else:
            # Remove latest symlink if no backups left
            latest = self.backup_path / "latest"
            if latest.is_symlink():
                latest.unlink()

    def _resolve_backup(self, backup_id: str) -> Path:
        """Resolve backup ID to path, handling 'latest' symlink."""
        if backup_id == "latest":
            latest = self.backup_path / "latest"
            if latest.is_symlink():
                return latest.resolve()
            elif latest.exists():
                return latest
            # No latest, try to find most recent
            backups = self.list_backups()
            if backups:
                return self.backup_path / backups[0]["id"]
            raise ValueError("No backup found")
        return self.backup_path / backup_id

    def _update_latest_symlink(self, backup_id: str):
        """Update the 'latest' symlink to point to given backup."""
        latest = self.backup_path / "latest"

        # Remove existing symlink
        if latest.is_symlink() or latest.exists():
            if latest.is_symlink():
                latest.unlink()
            elif latest.is_dir():
                shutil.rmtree(latest)

        # Create new symlink (relative path)
        try:
            latest.symlink_to(backup_id)
        except Exception:
            pass

    def _get_stash_list(self) -> List[str]:
        """Get list of git stashes."""
        if not self.gitops or not hasattr(self.gitops, 'repo'):
            return []

        try:
            result = self.gitops.repo.git.stash("list")
            if result:
                return result.strip().split("\n")
        except Exception:
            pass
        return []

    def _save_yaml(self, path: Path, data: dict):
        """Save data to YAML file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True, sort_keys=False, default_flow_style=False)

    def _load_yaml(self, path: Path) -> dict:
        """Load data from YAML file."""
        if not path.exists():
            return {}
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
