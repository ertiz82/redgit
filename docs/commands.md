# Commands Reference

Complete reference for all RedGit CLI commands. Use either `redgit` or the short alias `rgt`.

---

## Core Commands

### `rgt init`

Initialize RedGit in your project. Creates `.redgit/config.yaml`.

```bash
rgt init
```

Interactive wizard configures:
- LLM provider selection
- Task management integration
- Plugins
- Workflow settings

---

### `rgt propose`

Analyze changes and create commits using AI.

```bash
# Basic usage - AI analyzes and groups changes
rgt propose

# With specific prompt/plugin
rgt propose -p laravel

# Skip task management
rgt propose --no-task

# Task-Filtered Mode: Smart subtask creation under parent task
rgt propose -t PROJ-123
rgt propose --task 858

# Dry-run: See what would happen without making changes
rgt propose --dry-run
rgt propose -n

# Verbose mode: Show prompts, AI responses, and debug info
rgt propose --verbose
rgt propose -v

# Detailed mode: Generate better messages using file diffs
rgt propose --detailed
rgt propose -d

# Combine flags for debugging
rgt propose -v -n -d
```

**Options:**

| Option | Short | Description |
|--------|-------|-------------|
| `--prompt` | `-p` | Use specific prompt or plugin |
| `--task` | `-t` | Task-filtered mode: create subtasks under parent task |
| `--no-task` | | Skip task management integration |
| `--dry-run` | `-n` | Analyze without making changes (preview mode) |
| `--verbose` | `-v` | Show detailed output (prompts, responses, debug) |
| `--detailed` | `-d` | Generate detailed messages using file diffs |

#### Dry-Run Mode

Preview what RedGit would do without making any changes:

```bash
rgt propose -n
```

Shows:
- How changes would be grouped
- Which issues would be matched or created
- Branch names that would be created
- No commits, branches, or issues are actually created

#### Verbose Mode

Show detailed information about the AI analysis process:

```bash
rgt propose -v
```

Displays:
- Config paths and sources
- Task Management settings
- Full AI prompt sent to LLM
- Raw AI response
- Parsed groups

#### Detailed Mode

Generate more accurate commit messages by analyzing actual file diffs:

```bash
rgt propose -d
```

Benefits:
- More accurate commit messages based on actual code changes
- Better issue descriptions with technical details
- Localized issue titles/descriptions (respects `issue_language` setting)

#### Task-Filtered Mode

Smart subtask creation mode that analyzes file relevance to a parent task:

```bash
# Explicit task ID
rgt propose -t PROJ-123

# Just the number (project key added automatically)
rgt propose -t 123
```

**How it works:**

1. Fetches parent task details from task management
2. Analyzes file relevance using AI
3. Creates subtasks only for related files under the parent task
4. Matches other files to user's other open tasks
5. Reports unmatched files
6. Asks about pushing parent branch
7. Returns to original branch

**Auto-detection from branch:**

When on a task branch (e.g., `feature/PROJ-123-some-work`), running `rgt propose` will:
1. Detect the task ID from the branch name
2. Ask if you want to use task-filtered mode

---

### `rgt push`

Push branches and complete issues.

```bash
# Push current branch
rgt push

# Push with specific issue
rgt push -i PROJ-123

# Create pull request
rgt push --pr

# Don't complete issues
rgt push --no-complete

# Trigger CI/CD pipeline after push
rgt push --ci

# Wait for CI/CD pipeline to complete
rgt push --ci --wait-ci

# Push without triggering CI
rgt push --no-ci
```

**Options:**

| Option | Short | Description |
|--------|-------|-------------|
| `--issue` | `-i` | Complete specific issue |
| `--pr` | | Create pull request |
| `--no-complete` | | Don't transition issues to Done |
| `--ci` | | Trigger CI/CD pipeline |
| `--wait-ci` | | Wait for CI/CD to complete |
| `--no-ci` | | Skip CI/CD trigger |

---

## Feature Commands

Detailed documentation for feature commands:

| Command | Description | Documentation |
|---------|-------------|---------------|
| `rgt scout` | AI-powered project analysis | [Scout](scout.md) |
| `rgt quality` | Code quality with Semgrep | [Quality](quality.md) |
| `rgt ci` | CI/CD pipeline management | [CI/CD](ci.md) |
| `rgt release` | Version & changelog management | [Release](release.md) |
| `rgt notify` | Send notifications | [Notifications](notify.md) |
| `rgt poker` | Planning Poker sessions | [Planning Poker](planning-poker.md) |
| `rgt tunnel` | Expose local ports | [Tunnel](tunnel.md) |

---

## Utility Commands

### `rgt config`

Manage configuration.

```bash
# Show current config
rgt config show

# Set a value
rgt config set llm.provider ollama
rgt config set workflow.strategy merge-request

# Get a value
rgt config get llm.provider
```

See [Configuration](configuration.md) for all options.

---

### `rgt install`

Install integration or plugin from RedGit Tap.

```bash
# Install integration
rgt install jira
rgt install slack

# Install plugin
rgt install plugin:laravel

# Install specific version
rgt install slack@v1.0.0

# Skip configuration wizard
rgt install slack --no-configure
```

See [RedGit Tap](tap.md) for available integrations.

---

### `rgt integration`

Manage installed integrations.

```bash
# List installed integrations
rgt integration list

# List all available from taps
rgt integration list --all

# Reconfigure an integration
rgt integration configure jira

# Set active integration for its type
rgt integration use linear

# Remove an integration
rgt integration remove jira
```

See [Integrations](integrations/index.md) for more details.

---

### `rgt plugin`

Manage plugins.

```bash
# List available plugins
rgt plugin list

# Enable a plugin
rgt plugin enable laravel

# Disable a plugin
rgt plugin disable laravel
```

See [Plugins](plugins/index.md) for available plugins.

---

## Global Options

These options work with most commands:

| Option | Short | Description |
|--------|-------|-------------|
| `--help` | `-h` | Show help message |
| `--version` | | Show version |
| `--verbose` | `-v` | Verbose output |
| `--quiet` | `-q` | Minimal output |
| `--config` | `-c` | Use custom config file |

---

## Examples

### Daily Workflow

```bash
# Start your day
cd my-project
rgt integration list      # Check integrations

# Make changes...

# Commit with AI grouping
rgt propose

# Push when ready
rgt push
```

### Team Workflow with PRs

```bash
# Configure merge-request strategy
rgt config set workflow.strategy merge-request

# Make changes...
rgt propose

# Push and create PRs
rgt push --pr
```

### Quick Commit to Specific Task

```bash
# All changes go to one task as subtasks
rgt propose --task PROJ-123
rgt push
```

### Release Workflow

```bash
# Bump version and tag
rgt release minor

# Generate changelog
rgt changelog generate

# Push with CI
rgt push --ci --wait-ci
```

---

## See Also

- [Getting Started](getting-started.md)
- [Configuration](configuration.md)
- [Workflows](workflows.md)
