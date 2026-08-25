# Workflow Strategies

RedGit supports two workflow strategies for handling commits and branches.

## Overview

| Strategy | Best For | Branches | Push Behavior |
|----------|----------|----------|---------------|
| `local-merge` | Solo developers, small teams | Merged immediately | Push current branch |
| `merge-request` | Teams with code review | Kept for PR | Push each branch + create PR |

## Configuration

Set your strategy in `.redgit/config.yaml`:

```yaml
workflow:
  strategy: local-merge    # or: merge-request
  auto_transition: true
  create_missing_issues: ask
  default_issue_type: task
```

## Local Merge Strategy (Default)

The `local-merge` strategy immediately merges feature branches into your current branch after committing.

### How It Works

```
rgt propose
```

1. AI analyzes changes and groups them
2. For each group:
   - Creates a feature branch from current branch
   - Commits the grouped files
   - Merges back into current branch
   - Deletes the feature branch
3. All commits are now on your current branch

```
rgt push
```

4. Pushes current branch to remote
5. Optionally completes issues in task management

### Flow Diagram

```
Before:
  main ─────○ (HEAD)

After rgt propose:
  main ─────○───●───●───● (HEAD, all commits merged)
               │   │   │
               └───┴───┴── feature branches (deleted)

After rgt push:
  main ─────○───●───●───● (pushed to origin)
```

### When to Use

- Solo development
- Small teams without formal code review
- Fast iteration cycles
- Local feature development

### Example

```bash
# Make changes to multiple files
vim src/auth.py
vim src/models/user.py
vim tests/test_auth.py

# Propose commits
rgt propose
# Output:
#   ✓ Committed and merged feature/PROJ-123-auth-system
#   ✓ Committed and merged feature/PROJ-124-user-model

# Push everything
rgt push
# Output:
#   📤 Pushing current branch: main
#   ✓ Pushed to origin/main
```

## Merge Request Strategy

The `merge-request` strategy keeps feature branches separate for pull/merge request workflows.

### How It Works

```
rgt propose
```

1. AI analyzes changes and groups them
2. For each group:
   - Creates a feature branch from current branch
   - Commits the grouped files
   - Returns to current branch (branch is kept)
3. Feature branches remain for later push

```
rgt push --pr
```

4. Pushes each feature branch to remote
5. Creates pull/merge requests (if code_hosting configured)
6. Optionally completes issues

### Flow Diagram

```
Before:
  main ─────○ (HEAD)

After rgt propose:
  main ─────○ (HEAD)
             ├── feature/PROJ-123-auth ────●
             └── feature/PROJ-124-user ────●

After rgt push --pr:
  main ─────○ (HEAD)
             ├── feature/PROJ-123-auth ────● (pushed, PR created)
             └── feature/PROJ-124-user ────● (pushed, PR created)
```

### When to Use

- Team development with code review
- Projects requiring PR approval
- CI/CD pipelines triggered by PRs
- Open source contributions

### Example

```bash
# Configure merge-request strategy
# In .redgit/config.yaml:
# workflow:
#   strategy: merge-request

# Make changes
vim src/auth.py
vim src/models/user.py

# Propose commits
rgt propose
# Output:
#   ✓ Committed to feature/PROJ-123-auth-system
#   ✓ Committed to feature/PROJ-124-user-model
#
#   Branches ready for push and PR creation.
#   Run 'rgt push --pr' to push branches and create pull requests

# Push and create PRs
rgt push --pr
# Output:
#   📦 Session: 2 branches, 2 issues
#
#   Pushing branches...
#   • feature/PROJ-123-auth-system
#     ✓ Pushed to origin/feature/PROJ-123-auth-system
#     ✓ PR created: https://github.com/user/repo/pull/42
#
#   • feature/PROJ-124-user-model
#     ✓ Pushed to origin/feature/PROJ-124-user-model
#     ✓ PR created: https://github.com/user/repo/pull/43
```

## Comparison

| Feature | local-merge | merge-request |
|---------|-------------|---------------|
| Branch lifetime | Temporary (deleted after merge) | Persistent (until PR merged) |
| Code review | After push (optional) | Before merge (via PR) |
| CI/CD trigger | On push to main | On PR creation |
| Conflict resolution | During propose | During PR merge |
| History | Linear (merge commits) | Branch-based |

## Switching Strategies

You can switch strategies at any time:

```yaml
# .redgit/config.yaml
workflow:
  strategy: merge-request  # Change from local-merge
```

**Note:** Switching strategies won't affect existing sessions. Complete or clear your current session before switching.

```bash
# Clear existing session
rgt push  # or manually clear
```

## Code Hosting Integration

The `merge-request` strategy works best with code hosting integration:

```yaml
# .redgit/config.yaml
active:
  code_hosting: github

integrations:
  github:
    enabled: true
    owner: your-username
    repo: your-repo
    token: ${GITHUB_TOKEN}
```

With this configured, `rgt push --pr` will automatically create pull requests.

## Task-Filtered Mode (Subtask Workflow)

The task-filtered mode is designed for breaking down large tasks into subtasks automatically.

### Overview

When you have a parent task (e.g., "Admin panel improvements") and make multiple changes, RedGit can:

1. Analyze which files relate to the parent task
2. Create subtasks for related file groups
3. Match unrelated files to your other open tasks
4. Leave truly unmatched files in working directory

### How It Works

```
rgt propose -t SCRUM-858
```

1. **Parent task is fetched** from task management
2. **Files are analyzed** by AI for relevance to parent task
3. **Related files** become subtasks under the parent
4. **Parent branch is created** from your current branch
5. **Subtask branches are created** from parent branch
6. **Each subtask is merged** back to parent branch
7. **Ask about pushing** parent branch
8. **Return to original branch** - always returns to where you started

### Flow Diagram

```
Before:
  dev ─────○ (HEAD, you start here)

After rgt propose -t SCRUM-858:
  dev ─────○ (returned here after completion)
             │
             └── feature/SCRUM-858-admin-panel (parent)
                   ├── feature/SCRUM-900-user-mgmt ───● (merged to parent)
                   └── feature/SCRUM-901-settings ───● (merged to parent)

Push parent (optional):
  origin/feature/SCRUM-858-admin-panel (contains all subtask commits)
```

### Auto-Detection from Branch

When you're already on a task branch, RedGit can detect the task automatically:

```bash
# You're on: feature/SCRUM-858-admin-panel
$ rgt propose

# Output:
# Branch'ten task tespit edildi: SCRUM-858
# Task-filtered mode ile devam edilsin mi? [Y/n]
```

This works when:
- Your branch name contains a task pattern (e.g., `PROJ-123`)
- Task management integration is configured with a `project_key`

### Push Behavior

After all subtasks are processed, you're asked:

```
✓ Tüm subtask'lar SCRUM-858 parent branch'ine merge edildi.
Parent branch: feature/SCRUM-858-admin-panel
Merge stratejisi: merge-request

Parent branch'i pushlamak istiyor musunuz? [y/N]
```

- **Yes**: Push parent branch to remote, show PR creation command
- **No**: Skip push, work continues locally, manual push later

**Note:** Default is **No** because you might still be working on the task.

### Branch Restoration

**Important:** RedGit always returns to your original branch:

```bash
# Started on dev
$ rgt propose -t SCRUM-858
# ... subtasks created ...
# ... asked about push ...

# Always returns to dev
✓ dev branch'ine dönüldü
```

This happens even if:
- You push the parent branch
- An error occurs (uses try/finally)
- You cancel mid-process

### Example: Complete Workflow

```bash
# 1. Start on dev branch
git checkout dev

# 2. Make changes to multiple files
vim src/admin/users.py
vim src/admin/settings.py
vim src/api/auth.py
vim README.md

# 3. Run task-filtered mode
rgt propose -t SCRUM-858

# Output:
# Başlangıç branch: dev
# ✓ Parent task: SCRUM-858 - Admin panel improvements
#
# Analysis Results:
#   ✓ 2 subtask(s) for SCRUM-858
#   → 1 group(s) match other tasks (SCRUM-900)
#   ○ 1 file(s) unmatched (README.md)
#
# Creating subtasks under SCRUM-858...
#   ✓ Created subtask: SCRUM-901 - Admin user management
#   ✓ Created subtask: SCRUM-902 - Admin settings
#
# Processing matches with other tasks...
#   SCRUM-900: src/api/auth.py
#
# ✓ Tüm subtask'lar SCRUM-858 parent branch'ine merge edildi.
# Parent branch'i pushlamak istiyor musunuz? [y/N] n
#
# Parent branch push atlandı.
# Manuel push: git push -u origin feature/SCRUM-858-admin-panel
#
# ✓ dev branch'ine dönüldü

# 4. Check current branch
git branch
# * dev
```

### When to Use

| Scenario | Recommendation |
|----------|----------------|
| Large feature with multiple components | Use `-t` to create subtasks |
| Working on single file for a task | Use basic `rgt propose` |
| Already on task branch | Just run `rgt propose` (auto-detects) |
| Need to preview first | Use `rgt propose -t TASK -n` (dry-run) |

### Configuration

Task-filtered mode uses your workflow strategy for subtask handling:

```yaml
# .redgit/config.yaml
workflow:
  strategy: merge-request  # or local-merge
  auto_transition: true
```

The strategy affects how subtask branches are handled after merging to parent.

## See Also

- [Configuration](configuration.md)
- [Commands Reference](commands.md)
- [GitHub Integration](integrations/github.md)
- [Jira Integration](integrations/jira.md)