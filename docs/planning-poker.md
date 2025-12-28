# Planning Poker

Real-time story point estimation for sprint planning meetings.

## Overview

Planning Poker (also known as Scrum Poker) is a consensus-based technique for estimating story points. RedGit provides a CLI-based implementation that allows distributed teams to estimate tasks together in real-time.

## Features

| Feature | Description |
|---------|-------------|
| Real-time collaboration | WebSocket-based instant updates |
| CLI-based interface | No browser needed |
| Tunnel support | Remote teams via ngrok, cloudflare, etc. |
| Task management integration | Jira, Linear, Asana story point updates |
| AI-assisted voting | AI participant provides estimates with reasoning |
| Task distribution | Assign tasks to team members after estimation |
| Sprint creation | Create sprints with estimated tasks |
| Notifications | Telegram/Slack notifications for session events |
| Fibonacci voting | 1, 2, 3, 5, 8, 13, 21 (customizable) |
| Divergence detection | Highlights large differences for discussion |

## Prerequisites

```bash
# Install websockets dependency
pip install redgit[poker]

# Install a tunnel integration (for remote teams)
rg install ngrok
```

## Quick Start

### Starting a Session (Leader)

```bash
# Start with active sprint tasks
rg poker start --sprint active

# Start with specific issues
rg poker start --issues PROJ-123,PROJ-124,PROJ-125

# Start with custom settings
rg poker start --sprint active --port 8765
```

### Joining a Session (Participant)

```bash
# Join via session ID
rg poker join abc123

# Join via URL
rg poker join https://abc123.ngrok.io
```

---

## Session Flow

### 1. Leader Starts Session

```
$ rg poker start --sprint active

Detected user: Mehmet

Team Members:
  * 1. Mehmet
    2. Ahmet
    3. Ayşe
    4. Can

Press Enter to include all, or enter numbers to exclude (e.g., 2,4)
Exclude:

Session Settings
How to update Jira after voting?
  [1] Ask for confirmation each time (default)
  [2] Auto-update with average
  [3] Only update at session end (batch)
Choice: 1

Minimum participants [2]: 3
Vote timeout (seconds, 0=unlimited) [60]: 60

Session started!
   Session ID: poker-abc123
   Public URL: https://abc123.ngrok.io

Participants can join with:
   rg poker join poker-abc123
   rg poker join https://abc123.ngrok.io

Waiting for participants (3 minimum)...
```

### 2. Participants Join

```
$ rg poker join poker-abc123

Detected user: Ahmet

Connected!
   Session: poker-abc123
   Leader: Mehmet
   Participants: Ahmet, Ayşe, Can

Waiting for voting to start...
```

### 3. Voting

**Leader sees:**
```
Tasks:
  1. [ ] PROJ-101: User login page
  2. [ ] PROJ-102: Dashboard API
  3. [ ] PROJ-103: Notification system

Actions:
  [S] Start voting on current task
  [N] Next task
  [1-9] Select task by number
  [L] List participants
  [E] End session
  [D] Distribute tasks and end

Action: S
```

**Participants see:**
```
╭─ PROJ-101 ──────────────────────────────────────╮
│ User login page                                  │
│                                                  │
│ OAuth2 integration with Google/GitHub login     │
│ - Login form UI                                 │
│ - OAuth callback handler                        │
│ - Session management                            │
╰──────────────────────────────────────────────────╯

Options: 1, 2, 3, 5, 8, 13, 21, ? (uncertain)
Your vote: 5

Vote submitted: 5
Waiting for others... (2/3 votes)
```

### 4. Reveal & Decision

```
Voting Results
┏━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━━━━━━━━┓
┃ Participant    ┃ Points┃                    ┃
┡━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━━━━━━━━┩
│ Ahmet          │ 5     │ ████████           │
│ Ayşe           │ 8     │ ████████████       │
│ Can            │ 5     │ ████████           │
│ AI Assistant   │ 5     │ ████████           │
└────────────────┴───────┴────────────────────┘

╭─ AI Assistant Reasoning ────────────────────────╮
│ This task involves OAuth2 integration which is  │
│ moderately complex. The login UI is standard,   │
│ but callback handling requires careful state    │
│ management.                                     │
│                                                 │
│ Confidence: high                                │
│                                                 │
│ Factors considered:                             │
│   - OAuth2 complexity                           │
│   - UI components                               │
│   - Session management                          │
╰─────────────────────────────────────────────────╯

Statistics
Average: 5.75
Median: 5
Range: 5 - 8 (Divergence: 3)

Choose final story points:
  [M] Median: 5 (Recommended)
  [A] Average: 6
  [X] Custom value
  [T] Re-vote

> M

PROJ-101 story point: 5 set!
Update PROJ-101 in Jira with 5 points? [Y/n]: y
Updated PROJ-101 in Jira
```

### 5. Divergent Votes

When votes differ significantly:

```
Voting Results
┏━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━━━━━━━━┓
┃ Participant ┃ Points┃                    ┃
┡━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━━━━━━━━┩
│ Ahmet       │ 2     │ ███                │
│ Ayşe        │ 13    │ █████████████████  │
│ Can         │ 5     │ ████████           │
└─────────────┴───────┴────────────────────┘

╭─ Discussion Needed ─────────────────────────────╮
│ LARGE DIVERGENCE!                               │
│                                                 │
│ Lowest (2): Ahmet                               │
│ Highest (13): Ayşe                              │
│                                                 │
│ Discussion recommended before final decision.  │
╰─────────────────────────────────────────────────╯

  [M] Median: 5
  [T] Re-vote
  [X] Custom value
```

---

## Task Distribution

After estimation, leader can distribute tasks to team members:

### Starting Distribution

```
Actions:
  [E] End session
  [D] Distribute tasks and end

Action: D
Start task distribution? [y/N]: y

Resolving participant IDs...

Task Distribution
Tasks will be offered to participants for claiming
```

### Task Claiming Flow

**All participants see simultaneously:**
```
╭─ Task Available ────────────────────────────────╮
│ PROJ-101                                        │
│ User login page                                 │
│                                                 │
│ Points: 5                                       │
╰─────────────────────────────────────────────────╯

Do you want to take this task?
Claim task [y/N]: y
Claim sent!
Waiting for leader decision...
```

**Leader sees:**
```
╭─ Task Distribution ─────────────────────────────╮
│ PROJ-101                                        │
│ User login page                                 │
│                                                 │
│ Points: 5                                       │
│                                                 │
│ Claimed by: Ahmet                               │
╰─────────────────────────────────────────────────╯

[C] Confirm  [R] Reassign  [S] Skip
Action: C
```

**If no one claims:**
```
╭─ Task Distribution ─────────────────────────────╮
│ PROJ-102                                        │
│ Dashboard API                                   │
│                                                 │
│ Points: 8                                       │
│                                                 │
│ No claims yet                                   │
╰─────────────────────────────────────────────────╯

[A] Assign to someone  [S] Skip
Action: A

Select participant:
  [1] Ahmet
  [2] Ayşe
  [3] Can
Choice: 2
```

### Distribution Summary

```
╭─ Task Distribution Summary ─────────────────────╮
│ Task       │ Points │ Assigned To              │
│────────────┼────────┼──────────────────────────│
│ PROJ-101   │ 5      │ Ahmet                    │
│ PROJ-102   │ 8      │ Ayşe                     │
│ PROJ-103   │ 13     │ Can                      │
│                                                 │
│ Assigned: 3  |  Skipped: 0                     │
╰─────────────────────────────────────────────────╯

Assign tasks in task management? [y/N]: y
Assigned 3/3 tasks
```

---

## Sprint Creation

After distribution (or regular session end), leader can create a new sprint:

```
Sprint Creation
Create a new sprint with the estimated tasks? [y/N]: y

Sprint Settings

Sprint name [Sprint 2024-12-28]: Sprint 25
Date format: YYYY-MM-DD
Start date [2024-12-28]: 2024-12-30
End date [2025-01-13]: 2025-01-13
Sprint goal (optional): Complete authentication module

Creating sprint...
Sprint created: Sprint 25
Moving 3 tasks to sprint...
Moved 3/3 tasks to sprint
Start the sprint now? [y/N]: y
Sprint started!
```

---

## Session Summary

```
╭─ Session Summary ──────────────────────────────╮
│                                                 │
│ PROJ-101: User login          →  5 points ✓    │
│ PROJ-102: Dashboard API       →  8 points ✓    │
│ PROJ-103: Notification system → 13 points ✓    │
│                                                 │
│ Total: 26 story points                         │
│ Participants: Ahmet, Ayşe, Can                 │
│ Duration: 15 minutes                           │
╰─────────────────────────────────────────────────╯

All points updated in Jira!
```

---

## Notifications

When a notification integration is configured (Telegram, Slack, etc.):

### Session Started
```
🃏 Planning Poker Session Started
👤 Leader: Mehmet
📁 Project: PROJ
📋 Tasks: 5
👥 Expected: Ahmet, Ayşe, Can

🆔 Session: poker-abc123
💻 Join: rg poker join poker-abc123
```

### Session Ended
```
🏁 Planning Poker Session Ended
👤 Leader: Mehmet
✅ Tasks Estimated: 5
📊 Total Points: 26
👥 Participants: Ahmet, Ayşe, Can
```

### Tasks Distributed
```
📋 Tasks Distributed
👤 Leader: Mehmet

📌 Assignments:
  • PROJ-101: Ahmet (5 pts)
  • PROJ-102: Ayşe (8 pts)
  • PROJ-103: Can (13 pts)

✅ Tasks assigned in task management
```

### Sprint Created
```
🏃 Sprint Created
👤 Leader: Mehmet
📋 Sprint: Sprint 25
📊 Tasks: 5
🎯 Total Points: 26

✅ Sprint started!
```

---

## Configuration

### Session Settings

| Setting | Description | Default |
|---------|-------------|---------|
| `min_participants` | Minimum participants to start | 2 |
| `vote_timeout` | Voting timeout in seconds (0=unlimited) | 60 |
| `fibonacci` | Point values | [1, 2, 3, 5, 8, 13, 21] |
| `allow_question_mark` | Allow "?" vote for uncertain | true |
| `divergence_threshold` | Points difference to trigger discussion | 8 |

### Jira Update Modes

1. **Confirm each** (default) - Ask for confirmation after each task
2. **Auto-update** - Automatically update with the chosen value
3. **Batch update** - Only update at session end

---

## Tunnel Integration

For remote teams, use a tunnel integration:

```bash
# Install a tunnel
rg install ngrok      # Popular, free tier available
rg install serveo     # No installation needed (uses SSH)
rg install bore       # Fast, written in Rust

# Configure
rg integration configure ngrok

# Poker will automatically use the configured tunnel
rg poker start --sprint active
```

See [Tunnel Documentation](tunnel.md) for more details.

---

## AI Voting

When an LLM provider is configured, an AI assistant participates in voting:

- Analyzes task description and context
- Provides estimate based on complexity factors
- Shows reasoning after votes are revealed
- Helps calibrate team estimates

The AI vote is displayed alongside human votes but leader makes final decision.

---

## Commands Reference

```bash
# Start a session
rg poker start [OPTIONS]
  --sprint, -s    Sprint ID or 'active'
  --issues, -i    Comma-separated issue keys
  --port, -p      Server port (default: 8765)
  --name, -n      Your name as leader

# Join a session
rg poker join <SESSION>
  SESSION         Session ID or URL
  --name, -n      Your name

# Check status
rg poker status
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Leader Terminal                          │
│  rg poker start                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  PokerSession (Server)                               │   │
│  │  - WebSocket server                                  │   │
│  │  - Session state management                          │   │
│  │  - Task management integration                       │   │
│  │  - AI voter (optional)                               │   │
│  └─────────────────────────────────────────────────────┘   │
│                          │                                  │
│                    ngrok tunnel                             │
│                          │                                  │
└──────────────────────────┼──────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│ Participant 1 │  │ Participant 2 │  │ Participant 3 │
│ rg poker join │  │ rg poker join │  │ rg poker join │
│               │  │               │  │               │
│ WebSocket     │  │ WebSocket     │  │ WebSocket     │
│ Client        │  │ Client        │  │ Client        │
└───────────────┘  └───────────────┘  └───────────────┘
```

---

## API Reference

### Session State

```python
from redgit.core.poker import PokerSession, SessionSettings, Task

# Create session
settings = SessionSettings(
    min_participants=3,
    vote_timeout=60,
    fibonacci=[1, 2, 3, 5, 8, 13, 21]
)

tasks = [
    Task(key="PROJ-101", summary="User login", description="..."),
    Task(key="PROJ-102", summary="Dashboard", description="...")
]

session = PokerSession(
    leader_name="Mehmet",
    tasks=tasks,
    settings=settings
)
```

### WebSocket Messages

| Type | Direction | Description |
|------|-----------|-------------|
| `join` | Client→Server | Join the session |
| `vote` | Client→Server | Submit a vote |
| `claim_task` | Client→Server | Claim a task during distribution |
| `start_voting` | Leader→Server | Start voting on a task |
| `reveal` | Leader→Server | Reveal all votes |
| `set_points` | Leader→Server | Set final story points |
| `welcome` | Server→Client | Session info on join |
| `voting_started` | Server→Client | Voting has started |
| `vote_count_update` | Server→Client | Vote count changed |
| `voting_revealed` | Server→Client | Votes are revealed |
| `distribution_started` | Server→Client | Task distribution phase started |
| `task_offer` | Server→Client | Task offered for claiming |
| `task_claimed` | Server→Client | Task claimed by someone |
| `task_assigned` | Server→Client | Task assignment confirmed |
| `distribution_complete` | Server→Client | All tasks distributed |
| `session_ended` | Server→Client | Session has ended |

---

## Troubleshooting

### "websockets package is required"

Install the poker dependencies:
```bash
pip install redgit[poker]
```

### "No tunnel integration configured"

Install and configure a tunnel:
```bash
rg install ngrok
rg integration configure ngrok
```

### Connection Issues

1. Check firewall settings
2. Verify the tunnel is running: `rg tunnel status`
3. Try a different tunnel integration

### Participant can't join

1. Ensure the tunnel URL is correct
2. Check if the session is still active
3. Verify websockets is installed on participant's machine

### Task management assignment fails

1. Verify participant names match team member names in task management
2. Check if the integration has proper permissions
3. Try manual assignment in the task management UI

---

## See Also

- [Tunnel Integrations](tunnel.md)
- [Task Management Integrations](integrations/index.md)
- [Notification Integrations](integrations/index.md#notifications)
