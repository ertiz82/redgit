# Notifications

Send notifications to team communication platforms.

## Overview

RedGit integrates with popular messaging platforms to keep your team informed about commits, pushes, PR creations, CI results, and more. Notifications can be automatic (triggered by events) or manual.

## Supported Platforms

| Platform | Integration | Install Command |
|----------|-------------|-----------------|
| Slack | slack | `rgt install slack` |
| Discord | discord | `rgt install discord` |
| Telegram | telegram | `rgt install telegram` |
| Microsoft Teams | ms-teams | `rgt install ms-teams` |
| Mattermost | mattermost | `rgt install mattermost` |
| Rocket.Chat | rocketchat | `rgt install rocketchat` |
| Zulip | zulip | `rgt install zulip` |

---

## Quick Start

```bash
# Install notification integration
rgt install telegram

# Configure
rgt integration configure telegram

# Test notification
rgt notify "Hello from RedGit!"
```

---

## Commands

### rgt notify

Send a custom notification.

```bash
# Simple message
rgt notify "Deployment complete!"

# With channel/chat specification
rgt notify "Build passed" --channel "#builds"

# With formatting
rgt notify "**Release v1.2.0** is live!" --format markdown
```

**Options:**

| Option | Short | Description |
|--------|-------|-------------|
| `--channel` | `-c` | Target channel/chat |
| `--format` | `-f` | Message format: text, markdown |

---

## Automatic Notifications

RedGit sends automatic notifications for various events when enabled.

### Event Types

| Event | Description | Default |
|-------|-------------|---------|
| `push` | Branch pushed to remote | enabled |
| `pr_created` | Pull request created | enabled |
| `commit` | Commit created | disabled |
| `ci_success` | CI pipeline passed | enabled |
| `ci_failure` | CI pipeline failed | enabled |
| `issue_created` | Issue created | disabled |
| `issue_completed` | Issue marked done | enabled |
| `quality_failed` | Quality check failed | enabled |
| `poker_session_started` | Planning Poker started | enabled |
| `poker_session_ended` | Planning Poker ended | enabled |
| `sprint_created` | Sprint created | enabled |

### Enable/Disable Events

```yaml
# In .redgit/config.yaml
notifications:
  events:
    push: true
    pr_created: true
    commit: false
    ci_success: true
    ci_failure: true
    issue_completed: true
    quality_failed: true
    poker_session_started: true
```

---

## Platform Setup

### Telegram

```bash
# Install
rgt install telegram

# Configure
rgt integration configure telegram

# Required:
#   - Bot Token (from @BotFather)
#   - Chat ID (group or user ID)
```

**Finding Chat ID:**
1. Add bot to group
2. Send a message
3. Visit: `https://api.telegram.org/bot<TOKEN>/getUpdates`
4. Find `chat.id` in response

### Slack

```bash
# Install
rgt install slack

# Configure with webhook URL
rgt integration configure slack

# Required:
#   - Webhook URL (from Slack app settings)
```

**Creating Webhook:**
1. Go to api.slack.com/apps
2. Create new app → Incoming Webhooks
3. Activate and add to workspace
4. Copy webhook URL

### Discord

```bash
# Install
rgt install discord

# Configure
rgt integration configure discord

# Required:
#   - Webhook URL
```

**Creating Webhook:**
1. Server Settings → Integrations
2. Create Webhook
3. Copy webhook URL

### Microsoft Teams

```bash
# Install
rgt install ms-teams

# Configure
rgt integration configure ms-teams

# Required:
#   - Webhook URL (from Teams connector)
```

---

## Message Examples

### Push Notification
```
📤 Pushed `feature/login` to remote
Issues: PROJ-123, PROJ-124
```

### PR Created
```
🔀 PR created for `feature/login` (PROJ-123)
https://github.com/user/repo/pull/42
```

### CI Result
```
✅ Pipeline for `main` completed successfully
https://github.com/user/repo/actions/runs/123

# or

❌ Pipeline for `feature/login` failed
https://github.com/user/repo/actions/runs/124
```

### Planning Poker
```
🃏 Planning Poker Session Started
👤 Leader: Mehmet
📋 Tasks: 5
👥 Expected: Ahmet, Ayşe, Can

🆔 Session: poker-abc123
💻 Join: rgt poker join poker-abc123
```

### Quality Failed
```
⚠️ Quality check failed: 45% (threshold: 70%)
```

---

## Configuration

Full notification settings:

```yaml
# .redgit/config.yaml

active:
  notification: telegram

integrations:
  telegram:
    bot_token: ${TELEGRAM_BOT_TOKEN}
    chat_id: "-1001234567890"

  slack:
    webhook_url: ${SLACK_WEBHOOK_URL}
    channel: "#dev-updates"

  discord:
    webhook_url: ${DISCORD_WEBHOOK_URL}

notifications:
  enabled: true
  events:
    push: true
    pr_created: true
    commit: false
    ci_success: true
    ci_failure: true
    issue_created: false
    issue_completed: true
    quality_failed: true
    poker_session_started: true
    poker_session_ended: true
    poker_tasks_distributed: true
    sprint_created: true
```

---

## Environment Variables

Sensitive data should use environment variables:

| Variable | Description |
|----------|-------------|
| `TELEGRAM_BOT_TOKEN` | Telegram bot token |
| `TELEGRAM_CHAT_ID` | Telegram chat ID |
| `SLACK_WEBHOOK_URL` | Slack webhook URL |
| `DISCORD_WEBHOOK_URL` | Discord webhook URL |
| `TEAMS_WEBHOOK_URL` | MS Teams webhook URL |

```bash
# Set in shell
export TELEGRAM_BOT_TOKEN="123456:ABC-DEF"
export TELEGRAM_CHAT_ID="-1001234567890"

# Or in .env file (not committed)
```

---

## Interactive Features

Some platforms support interactive messages:

### Buttons (Slack, Telegram)

```python
# Used internally for Planning Poker
# Claim task buttons
# Approve/Reject buttons
```

### Polls (Telegram)

```python
# Used for quick team votes
# Sprint planning decisions
```

---

## Troubleshooting

### "Notification not sent"

```bash
# Check integration status
rgt integration list

# Test with manual message
rgt notify "Test message"

# Check logs
rgt notify "Test" --verbose
```

### "Bot not responding" (Telegram)

1. Verify bot token is correct
2. Ensure bot is added to the group
3. Check chat ID (negative for groups)
4. Bot must be admin for some features

### "Webhook error" (Slack/Discord)

1. Verify webhook URL is valid
2. Check webhook hasn't been revoked
3. Ensure proper permissions

### "Event not triggering"

```bash
# Check event is enabled
rgt config show

# Verify in config:
# notifications.events.push: true
```

---

## Best Practices

### Channel Organization

```yaml
# Use specific channels for different events
notifications:
  channels:
    ci: "#ci-builds"
    releases: "#releases"
    issues: "#issues"
```

### Rate Limiting

Avoid notification spam:
```yaml
notifications:
  # Disable noisy events
  events:
    commit: false    # Too frequent

  # Or use batching
  batch:
    enabled: true
    interval: 300    # 5 minutes
```

### Security

```yaml
# Use environment variables for tokens
integrations:
  telegram:
    bot_token: ${TELEGRAM_BOT_TOKEN}  # Never hardcode!
```

---

## See Also

- [Commands Reference](commands.md)
- [Planning Poker](planning-poker.md)
- [CI/CD Integration](ci.md)
- [Configuration](configuration.md)
