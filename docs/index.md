# RedGit Documentation

Welcome to the RedGit documentation. RedGit is an AI-powered Git workflow assistant that analyzes your code changes, groups them logically, matches them with your active tasks, and creates well-structured commits automatically.

## Quick Navigation

### Core Documentation

| Section | Description |
|---------|-------------|
| [Getting Started](getting-started.md) | Installation and first steps |
| [Commands Reference](commands.md) | All CLI commands |
| [Configuration](configuration.md) | Config file options |
| [Workflows](workflows.md) | Local merge vs merge request strategies |
| [Troubleshooting](troubleshooting.md) | Common issues and solutions |

### Features

| Feature | Description | Command |
|---------|-------------|---------|
| [Scout](scout.md) | AI-powered project analysis | `rgt scout` |
| [Quality](quality.md) | Code quality with Semgrep | `rgt quality` |
| [CI/CD](ci.md) | Pipeline management | `rgt ci` |
| [Release](release.md) | Version & changelog | `rgt release` |
| [Notifications](notify.md) | Team notifications | `rgt notify` |
| [Planning Poker](planning-poker.md) | Sprint estimation | `rgt poker` |
| [Tunnel](tunnel.md) | Port forwarding | `rgt tunnel` |

### Integrations & Plugins

| Section | Description |
|---------|-------------|
| [Integrations](integrations/index.md) | Task management, code hosting, CI/CD, notifications |
| [Plugins](plugins/index.md) | Framework plugins and release management |
| [RedGit Tap](tap.md) | Community integrations repository |

---

## Overview

### What RedGit Does

1. **Analyzes** your uncommitted changes
2. **Groups** related files using AI
3. **Matches** changes with your active issues (Jira, Linear, etc.)
4. **Creates** branches and commits for each group
5. **Transitions** issues through workflow statuses
6. **Pushes** and optionally creates pull requests

### Core Commands

```bash
rgt init      # Initialize RedGit in your project
rgt propose   # Analyze changes and create commits
rgt push      # Push branches and complete issues
rgt scout     # AI-powered project analysis and planning
```

### Core Features

| Feature | Description | Command |
|---------|-------------|---------|
| AI Commit Grouping | Intelligently groups related file changes | `rgt propose` |
| Push & Complete | Push branches and transition issues to Done | `rgt push` |
| [Scout](scout.md) | AI-powered project analysis and task planning | `rgt scout` |
| [Quality](quality.md) | Code quality analysis with Semgrep + AI | `rgt quality` |
| [Release](release.md) | Create releases with changelog generation | `rgt release` |
| [CI/CD](ci.md) | Pipeline management and monitoring | `rgt ci` |
| [Notifications](notify.md) | Team communication and alerts | `rgt notify` |
| [Planning Poker](planning-poker.md) | Real-time sprint estimation | `rgt poker` |
| [Tunnel](tunnel.md) | Expose local ports for webhooks and remote access | `rgt tunnel` |

### Integration Types (from Tap)

All integrations are available from [RedGit Tap](https://github.com/ertiz82/redgit-tap):

| Type | Purpose | Examples |
|------|---------|----------|
| Task Management | Issue tracking | Jira, Linear, Asana, Notion |
| Code Hosting | Git hosting, PRs | GitHub, GitLab, Bitbucket |
| CI/CD | Pipelines, builds | GitHub Actions, Jenkins |
| Notifications | Alerts, messages | Slack, Discord, Telegram |
| Code Quality | Analysis, scanning | SonarQube, Snyk |
| Tunnel | Port forwarding | ngrok, Cloudflare Tunnel, bore |

---

## Documentation Structure

```
docs/
├── index.md                 # This file
├── getting-started.md       # Installation and quick start
├── commands.md              # Core CLI commands
├── configuration.md         # Config file options
├── workflows.md             # Workflow strategies
├── troubleshooting.md       # Common issues
│
├── # Feature Documentation
├── scout.md                 # AI project analysis
├── quality.md               # Code quality & Semgrep
├── ci.md                    # CI/CD pipeline management
├── release.md               # Version & changelog
├── notify.md                # Notifications
├── planning-poker.md        # Sprint estimation
├── tunnel.md                # Port forwarding
│
├── # Integrations & Plugins
├── tap.md                   # RedGit Tap repository
├── integrations/
│   ├── index.md             # Integrations overview
│   └── custom.md            # Custom integration guide
└── plugins/
    ├── index.md             # Plugin overview
    └── custom.md            # Custom plugin guide
```

---

## Install Integrations from Tap

All integrations are available from **[RedGit Tap](https://github.com/ertiz82/redgit-tap)**:

```bash
# Task Management
rgt install jira
rgt install linear

# Notifications
rgt install slack
rgt install discord

# Code Hosting
rgt install github
rgt install gitlab

# CI/CD
rgt install github-actions
rgt install jenkins

# List available
rgt integration list --all
```

---

## Getting Help

- **GitHub Issues**: [github.com/ertiz82/redgit/issues](https://github.com/ertiz82/redgit/issues)
- **Troubleshooting**: [troubleshooting.md](troubleshooting.md)