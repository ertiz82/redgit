# CI/CD - Pipeline Management

Monitor and control CI/CD pipelines from the command line.

## Overview

RedGit integrates with popular CI/CD platforms to provide unified pipeline management. Trigger builds, watch progress, view logs, and handle failures without leaving your terminal.

## Prerequisites

Install a CI/CD integration:

```bash
rg install github-actions
# or
rg install gitlab-ci
# or
rg install jenkins
```

## Supported Platforms

| Platform | Integration | Install Command |
|----------|-------------|-----------------|
| GitHub Actions | github-actions | `rg install github-actions` |
| GitLab CI | gitlab-ci | `rg install gitlab-ci` |
| Jenkins | jenkins | `rg install jenkins` |
| CircleCI | circleci | `rg install circleci` |
| Travis CI | travis-ci | `rg install travis-ci` |
| Azure Pipelines | azure-pipelines | `rg install azure-pipelines` |
| Bitbucket Pipelines | bitbucket-pipelines | `rg install bitbucket-pipelines` |
| Drone CI | drone-ci | `rg install drone-ci` |

---

## Quick Start

```bash
# Check pipeline status
rg ci status

# List recent pipelines
rg ci pipelines

# Trigger a new build
rg ci trigger

# Watch pipeline progress
rg ci watch
```

---

## Commands

### rg ci status

Show current CI/CD status for the branch.

```bash
rg ci status

# Output:
# Branch: feature/new-login
# Pipeline: #12345
# Status: running
# Started: 5 minutes ago
# Jobs: 3/5 completed
```

### rg ci pipelines

List recent pipelines.

```bash
# List recent pipelines
rg ci pipelines

# Filter by branch
rg ci pipelines --branch main

# Filter by status
rg ci pipelines --status failed

# Limit results
rg ci pipelines --limit 20
```

**Options:**

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--branch` | `-b` | Filter by branch | current |
| `--status` | `-s` | Filter: running, passed, failed | all |
| `--limit` | `-l` | Number of results | 10 |

### rg ci pipeline

Show details for a specific pipeline.

```bash
# Show pipeline details
rg ci pipeline 12345

# Output:
# Pipeline #12345
# Branch: main
# Commit: abc1234 "Add user authentication"
# Status: passed
# Duration: 4m 32s
#
# Jobs:
#   ✓ build (1m 12s)
#   ✓ test (2m 45s)
#   ✓ deploy (0m 35s)
```

### rg ci jobs

List jobs in a pipeline.

```bash
rg ci jobs 12345

# Output:
# Pipeline #12345 Jobs
#
#   build       ✓ passed    1m 12s
#   test        ✓ passed    2m 45s
#   lint        ✓ passed    0m 23s
#   deploy      ⏳ running  0m 15s
#   notify      ○ pending   -
```

### rg ci trigger

Trigger a new pipeline.

```bash
# Trigger on current branch
rg ci trigger

# Trigger on specific branch
rg ci trigger --branch main

# Trigger specific workflow
rg ci trigger --workflow build

# With variables
rg ci trigger --var DEPLOY_ENV=staging
```

**Options:**

| Option | Short | Description |
|--------|-------|-------------|
| `--branch` | `-b` | Target branch |
| `--workflow` | `-w` | Specific workflow/job |
| `--var` | | Pipeline variable (KEY=value) |

### rg ci watch

Watch a pipeline until completion.

```bash
# Watch latest pipeline on current branch
rg ci watch

# Watch specific pipeline
rg ci watch 12345

# With refresh interval
rg ci watch --interval 10
```

**Output:**
```
Watching Pipeline #12345...

  build       ✓ passed    1m 12s
  test        ⏳ running  1m 45s  ████████░░░░
  lint        ○ pending   -
  deploy      ○ pending   -

Elapsed: 2m 57s | Refresh: 5s | Ctrl+C to exit
```

### rg ci logs

View pipeline or job logs.

```bash
# View pipeline logs
rg ci logs 12345

# View specific job logs
rg ci logs 12345 --job build

# Tail logs (last N lines)
rg ci logs 12345 --job test --tail 100

# Follow logs in real-time
rg ci logs 12345 --job deploy --follow
```

**Options:**

| Option | Short | Description |
|--------|-------|-------------|
| `--job` | `-j` | Specific job name |
| `--tail` | `-n` | Last N lines |
| `--follow` | `-f` | Follow logs in real-time |

### rg ci cancel

Cancel a running pipeline.

```bash
rg ci cancel 12345

# Output:
# Pipeline #12345 cancelled
```

### rg ci retry

Retry a failed pipeline.

```bash
rg ci retry 12345

# Retry specific job
rg ci retry 12345 --job deploy

# Output:
# Pipeline #12345 retried
# New pipeline: #12346
```

---

## Integration with Push

### Trigger on Push

```bash
# Push and trigger CI
rg push --ci

# Push, trigger, and wait for completion
rg push --ci --wait-ci

# Push without triggering CI
rg push --no-ci
```

### Watch After Push

```bash
# Push and watch
rg push --ci
rg ci watch
```

---

## Workflow Examples

### Development Workflow

```bash
# Make changes
vim src/feature.py

# Commit
rg propose

# Push and monitor
rg push --ci
rg ci watch
```

### Handling Failures

```bash
# Check what failed
rg ci status
# Status: failed

# View failed job logs
rg ci logs 12345 --job test --tail 50

# Fix the issue
vim src/broken_test.py

# Commit fix
rg propose

# Push and retry
rg push --ci
```

### Deploy Workflow

```bash
# Trigger deployment
rg ci trigger --workflow deploy --var DEPLOY_ENV=production

# Watch deployment
rg ci watch

# Check logs if issues
rg ci logs --job deploy --follow
```

---

## Configuration

CI/CD settings in `.redgit/config.yaml`:

```yaml
active:
  ci: github-actions

integrations:
  github-actions:
    # Auto-configured from GitHub integration

  gitlab-ci:
    url: https://gitlab.com
    token: ${GITLAB_TOKEN}

  jenkins:
    url: https://jenkins.example.com
    user: admin
    token: ${JENKINS_TOKEN}
```

---

## Notifications

Combine with notification integrations:

```bash
# Get notified when pipeline completes
rg push --ci --wait-ci

# On completion, notification is sent automatically
# if notification integration is configured
```

See [Notifications](notify.md) for setup.

---

## Troubleshooting

### "No CI/CD integration configured"

```bash
# Install an integration
rg install github-actions

# Configure
rg integration configure github-actions
```

### "Pipeline not found"

```bash
# List available pipelines
rg ci pipelines --limit 20

# Check branch
rg ci pipelines --branch main
```

### "Cannot trigger pipeline"

Check permissions:
```bash
# Verify integration status
rg integration list

# Reconfigure if needed
rg integration configure github-actions
```

### "Logs not available"

Some platforms have log retention limits:
```bash
# Check pipeline age
rg ci pipeline 12345

# Logs may expire after 30-90 days
```

---

## See Also

- [Commands Reference](commands.md)
- [Push Command](commands.md#rg-push)
- [Notifications](notify.md)
- [Quality Checks](quality.md)
