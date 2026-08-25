# CI/CD - Pipeline Management

Monitor and control CI/CD pipelines from the command line.

## Overview

RedGit integrates with popular CI/CD platforms to provide unified pipeline management. Trigger builds, watch progress, view logs, and handle failures without leaving your terminal.

## Prerequisites

Install a CI/CD integration:

```bash
rgt install github-actions
# or
rgt install gitlab-ci
# or
rgt install jenkins
```

## Supported Platforms

| Platform | Integration | Install Command |
|----------|-------------|-----------------|
| GitHub Actions | github-actions | `rgt install github-actions` |
| GitLab CI | gitlab-ci | `rgt install gitlab-ci` |
| Jenkins | jenkins | `rgt install jenkins` |
| CircleCI | circleci | `rgt install circleci` |
| Travis CI | travis-ci | `rgt install travis-ci` |
| Azure Pipelines | azure-pipelines | `rgt install azure-pipelines` |
| Bitbucket Pipelines | bitbucket-pipelines | `rgt install bitbucket-pipelines` |
| Drone CI | drone-ci | `rgt install drone-ci` |

---

## Quick Start

```bash
# Check pipeline status
rgt ci status

# List recent pipelines
rgt ci pipelines

# Trigger a new build
rgt ci trigger

# Watch pipeline progress
rgt ci watch
```

---

## Commands

### rgt ci status

Show current CI/CD status for the branch.

```bash
rgt ci status

# Output:
# Branch: feature/new-login
# Pipeline: #12345
# Status: running
# Started: 5 minutes ago
# Jobs: 3/5 completed
```

### rgt ci pipelines

List recent pipelines.

```bash
# List recent pipelines
rgt ci pipelines

# Filter by branch
rgt ci pipelines --branch main

# Filter by status
rgt ci pipelines --status failed

# Limit results
rgt ci pipelines --limit 20
```

**Options:**

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--branch` | `-b` | Filter by branch | current |
| `--status` | `-s` | Filter: running, passed, failed | all |
| `--limit` | `-l` | Number of results | 10 |

### rgt ci pipeline

Show details for a specific pipeline.

```bash
# Show pipeline details
rgt ci pipeline 12345

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

### rgt ci jobs

List jobs in a pipeline.

```bash
rgt ci jobs 12345

# Output:
# Pipeline #12345 Jobs
#
#   build       ✓ passed    1m 12s
#   test        ✓ passed    2m 45s
#   lint        ✓ passed    0m 23s
#   deploy      ⏳ running  0m 15s
#   notify      ○ pending   -
```

### rgt ci trigger

Trigger a new pipeline.

```bash
# Trigger on current branch
rgt ci trigger

# Trigger on specific branch
rgt ci trigger --branch main

# Trigger specific workflow
rgt ci trigger --workflow build

# With variables
rgt ci trigger --var DEPLOY_ENV=staging
```

**Options:**

| Option | Short | Description |
|--------|-------|-------------|
| `--branch` | `-b` | Target branch |
| `--workflow` | `-w` | Specific workflow/job |
| `--var` | | Pipeline variable (KEY=value) |

### rgt ci watch

Watch a pipeline until completion.

```bash
# Watch latest pipeline on current branch
rgt ci watch

# Watch specific pipeline
rgt ci watch 12345

# With refresh interval
rgt ci watch --interval 10
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

### rgt ci logs

View pipeline or job logs.

```bash
# View pipeline logs
rgt ci logs 12345

# View specific job logs
rgt ci logs 12345 --job build

# Tail logs (last N lines)
rgt ci logs 12345 --job test --tail 100

# Follow logs in real-time
rgt ci logs 12345 --job deploy --follow
```

**Options:**

| Option | Short | Description |
|--------|-------|-------------|
| `--job` | `-j` | Specific job name |
| `--tail` | `-n` | Last N lines |
| `--follow` | `-f` | Follow logs in real-time |

### rgt ci cancel

Cancel a running pipeline.

```bash
rgt ci cancel 12345

# Output:
# Pipeline #12345 cancelled
```

### rgt ci retry

Retry a failed pipeline.

```bash
rgt ci retry 12345

# Retry specific job
rgt ci retry 12345 --job deploy

# Output:
# Pipeline #12345 retried
# New pipeline: #12346
```

---

## Integration with Push

### Trigger on Push

```bash
# Push and trigger CI
rgt push --ci

# Push, trigger, and wait for completion
rgt push --ci --wait-ci

# Push without triggering CI
rgt push --no-ci
```

### Watch After Push

```bash
# Push and watch
rgt push --ci
rgt ci watch
```

---

## Workflow Examples

### Development Workflow

```bash
# Make changes
vim src/feature.py

# Commit
rgt propose

# Push and monitor
rgt push --ci
rgt ci watch
```

### Handling Failures

```bash
# Check what failed
rgt ci status
# Status: failed

# View failed job logs
rgt ci logs 12345 --job test --tail 50

# Fix the issue
vim src/broken_test.py

# Commit fix
rgt propose

# Push and retry
rgt push --ci
```

### Deploy Workflow

```bash
# Trigger deployment
rgt ci trigger --workflow deploy --var DEPLOY_ENV=production

# Watch deployment
rgt ci watch

# Check logs if issues
rgt ci logs --job deploy --follow
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
rgt push --ci --wait-ci

# On completion, notification is sent automatically
# if notification integration is configured
```

See [Notifications](notify.md) for setup.

---

## Troubleshooting

### "No CI/CD integration configured"

```bash
# Install an integration
rgt install github-actions

# Configure
rgt integration configure github-actions
```

### "Pipeline not found"

```bash
# List available pipelines
rgt ci pipelines --limit 20

# Check branch
rgt ci pipelines --branch main
```

### "Cannot trigger pipeline"

Check permissions:
```bash
# Verify integration status
rgt integration list

# Reconfigure if needed
rgt integration configure github-actions
```

### "Logs not available"

Some platforms have log retention limits:
```bash
# Check pipeline age
rgt ci pipeline 12345

# Logs may expire after 30-90 days
```

---

## See Also

- [Commands Reference](commands.md)
- [Push Command](commands.md#rgt-push)
- [Notifications](notify.md)
- [Quality Checks](quality.md)
