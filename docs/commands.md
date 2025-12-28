# Commands Reference

Complete reference for all RedGit CLI commands. Use either `redgit` or the short alias `rg`.

---

## Core Commands

### `rg init`

Initialize RedGit in your project. Creates `.redgit/config.yaml`.

```bash
rg init
```

Interactive wizard configures:
- LLM provider selection
- Task management integration
- Plugins
- Workflow settings

---

### `rg propose`

Analyze changes and create commits using AI.

```bash
# Basic usage - AI analyzes and groups changes
rg propose

# With specific prompt/plugin
rg propose -p laravel

# Skip task management
rg propose --no-task

# Task-Filtered Mode: Smart subtask creation under parent task
rg propose -t PROJ-123
rg propose --task 858

# Dry-run: See what would happen without making changes
rg propose --dry-run
rg propose -n

# Verbose mode: Show prompts, AI responses, and debug info
rg propose --verbose
rg propose -v

# Detailed mode: Generate better messages using file diffs
rg propose --detailed
rg propose -d

# Combine flags for debugging
rg propose -v -n -d
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
rg propose -n
```

Shows:
- How changes would be grouped
- Which issues would be matched or created
- Branch names that would be created
- No commits, branches, or issues are actually created

#### Verbose Mode

Show detailed information about the AI analysis process:

```bash
rg propose -v
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
rg propose -d
```

Benefits:
- More accurate commit messages based on actual code changes
- Better issue descriptions with technical details
- Localized issue titles/descriptions (respects `issue_language` setting)

#### Task-Filtered Mode

Smart subtask creation mode that analyzes file relevance to a parent task:

```bash
# Explicit task ID
rg propose -t PROJ-123

# Just the number (project key added automatically)
rg propose -t 123
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

When on a task branch (e.g., `feature/PROJ-123-some-work`), running `rg propose` will:
1. Detect the task ID from the branch name
2. Ask if you want to use task-filtered mode

---

### `rg push`

Push branches and complete issues.

```bash
# Push current branch
rg push

# Push with specific issue
rg push -i PROJ-123

# Create pull request
rg push --pr

# Don't complete issues
rg push --no-complete

# Trigger CI/CD pipeline after push
rg push --ci

# Wait for CI/CD pipeline to complete
rg push --ci --wait-ci

# Push without triggering CI
rg push --no-ci
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
| `rg scout` | AI-powered project analysis | [Scout](scout.md) |
| `rg quality` | Code quality with Semgrep | [Quality](quality.md) |
| `rg ci` | CI/CD pipeline management | [CI/CD](ci.md) |
| `rg release` | Version & changelog management | [Release](release.md) |
| `rg notify` | Send notifications | [Notifications](notify.md) |
| `rg poker` | Planning Poker sessions | [Planning Poker](planning-poker.md) |
| `rg tunnel` | Expose local ports | [Tunnel](tunnel.md) |

---

## Utility Commands

### `rg config`

Manage configuration.

```bash
# Show current config
rg config show

# Set a value
rg config set llm.provider ollama
rg config set workflow.strategy merge-request

# Get a value
rg config get llm.provider
```

See [Configuration](configuration.md) for all options.

---

### `rg install`

Install integration or plugin from RedGit Tap.

```bash
# Install integration
rg install jira
rg install slack

# Install plugin
rg install plugin:laravel

# Install specific version
rg install slack@v1.0.0

# Skip configuration wizard
rg install slack --no-configure
```

See [RedGit Tap](tap.md) for available integrations.

---

### `rg integration`

Manage installed integrations.

```bash
# List installed integrations
rg integration list

# List all available from taps
rg integration list --all

# Reconfigure an integration
rg integration configure jira

# Set active integration for its type
rg integration use linear

# Remove an integration
rg integration remove jira
```

See [Integrations](integrations/index.md) for more details.

---

### `rg plugin`

Manage plugins.

```bash
# List available plugins
rg plugin list

# Enable a plugin
rg plugin enable laravel

# Disable a plugin
rg plugin disable laravel
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
rg integration list      # Check integrations

# Make changes...

# Commit with AI grouping
rg propose

# Push when ready
rg push
```

### Team Workflow with PRs

```bash
# Configure merge-request strategy
rg config set workflow.strategy merge-request

# Make changes...
rg propose

# Push and create PRs
rg push --pr
```

### Quick Commit to Specific Task

```bash
# All changes go to one task as subtasks
rg propose --task PROJ-123
rg push
```

### Release Workflow

```bash
# Bump version and tag
rg release minor

# Generate changelog
rg changelog generate

# Push with CI
rg push --ci --wait-ci
```

---

## See Also

- [Getting Started](getting-started.md)
- [Configuration](configuration.md)
- [Workflows](workflows.md)
