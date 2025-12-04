# 🧠 SmartCommit

> **AI-powered Git workflow assistant with task management integration**

SmartCommit analyzes your code changes, groups them logically, matches them with your active tasks (Jira, Linear, etc.), and creates well-structured commits automatically.

## ✨ Features

- **AI-Powered Grouping**: Automatically groups related file changes
- **Task Management Integration**: Matches changes with active Jira/Linear issues
- **Smart Branch Naming**: Creates branches based on issue keys
- **Auto Issue Creation**: Creates new issues for unmatched changes
- **Workflow Automation**: Transitions issues through statuses automatically
- **Plugin System**: Framework-specific prompts (Laravel, Vue, etc.)
- **Security**: Never commits sensitive files (.env, credentials, etc.)

---

## 📦 Installation

### Requirements

- Python 3.9+
- Git
- One of the supported LLM providers

### Install SmartCommit

```bash
# From PyPI (when published)
pip install smart-commit

# From source
git clone https://github.com/yourusername/smartcommit.git
cd smartcommit
pip install -e .
```

### LLM Provider Setup

SmartCommit supports multiple LLM providers. Choose one:

#### Option 1: Claude Code (Recommended)
```bash
npm install -g @anthropic-ai/claude-code
```

#### Option 2: Qwen Code
```bash
npm install -g @anthropic-ai/qwen-code
```

#### Option 3: OpenAI API
```bash
export OPENAI_API_KEY="your-api-key"
```

#### Option 4: Ollama (Local)
```bash
# Install Ollama from https://ollama.ai
ollama pull qwen2.5-coder:7b
```

---

## 🚀 Quick Start

```bash
# 1. Initialize in your project
cd your-project
sgc init

# 2. Make some changes to your code
# ...

# 3. Analyze and create commits
sgc propose

# 4. Push and complete issues
sgc push
```

---

## 📖 Commands

### `sgc init`

Initialize SmartCommit in your project. Creates `.smartcommit/config.yaml`.

```bash
sgc init
```

Interactive wizard will help you configure:
- LLM provider selection
- Task management integration (Jira, etc.)
- Plugins (Laravel, Vue, etc.)
- Workflow settings

### `sgc propose`

Analyze changes and create commits.

```bash
# Basic usage
sgc propose

# With specific prompt/plugin
sgc propose -p laravel

# Skip task management
sgc propose --no-task
```

**What it does:**
1. Detects all file changes in your repo
2. Fetches your active issues from task management
3. Uses AI to group files and match with issues
4. Creates branches and commits for each group
5. Transitions issues to "In Progress"

### `sgc push`

Push branches and complete issues.

```bash
# Push current branch
sgc push

# Push with specific issue
sgc push -i PROJ-123

# Create pull request
sgc push --pr

# Don't complete issues
sgc push --no-complete
```

### `sgc integration`

Manage integrations.

```bash
# List available integrations
sgc integration list

# Install an integration
sgc integration install jira

# Show integration status
sgc integration status
```

### `sgc plugin`

Manage plugins.

```bash
# List available plugins
sgc plugin list

# Enable a plugin
sgc plugin enable laravel

# Disable a plugin
sgc plugin disable laravel
```

---

## ⚙️ Configuration

Configuration is stored in `.smartcommit/config.yaml`:

```yaml
# Active integrations by type
active:
  task_management: jira      # jira | linear | none
  code_hosting: github       # github | gitlab | none

# Workflow settings
workflow:
  strategy: local-merge      # local-merge | merge-request
  auto_transition: true      # Auto-move issues through statuses
  create_missing_issues: ask # ask | auto | skip
  default_issue_type: task   # Default type for new issues

# LLM configuration
llm:
  provider: claude-code      # claude-code | qwen-code | openai | ollama
  model: null                # Model override (optional)

# Plugins
plugins:
  enabled:
    - laravel

# Integration configurations
integrations:
  jira:
    site: https://your-domain.atlassian.net
    email: you@example.com
    project_key: PROJ
    board_type: scrum        # scrum | kanban | none
    # token: stored in JIRA_API_TOKEN env var

  github:
    owner: username
    repo: reponame
    default_base: main
    # token: stored in GITHUB_TOKEN env var
```

---

## 🔌 Integrations

### Task Management

#### Jira

Full Jira Cloud support with Scrum/Kanban boards.

**Setup:**
```bash
sgc integration install jira
```

**Required fields:**
- `site`: Your Jira site URL (e.g., `https://company.atlassian.net`)
- `email`: Your Jira account email
- `project_key`: Project key (e.g., `PROJ`, `SCRUM`)
- `token`: API token ([Create here](https://id.atlassian.com/manage-profile/security/api-tokens))

**Features:**
- Fetch active issues assigned to you
- Match commits with issues
- Add comments to issues on commit
- Transition issues (To Do → In Progress → Done)
- Sprint support for Scrum boards
- Auto-detect board ID

**Config example:**
```yaml
integrations:
  jira:
    site: https://company.atlassian.net
    email: dev@company.com
    project_key: PROJ
    board_type: scrum
    story_points_field: customfield_10016  # Optional
```

### Code Hosting

#### GitHub

GitHub integration for PR creation.

**Setup:**
```bash
sgc integration install github
```

**Required fields:**
- `owner`: Repository owner (username or org)
- `repo`: Repository name
- `token`: Personal Access Token ([Create here](https://github.com/settings/tokens))

**Features:**
- Create pull requests
- Link PRs with issues

---

## 🧩 Plugins

Plugins provide framework-specific prompts for better AI understanding.

### Available Plugins

| Plugin | Description |
|--------|-------------|
| `laravel` | Laravel/PHP projects |
| `vue` | Vue.js projects |
| `react` | React projects |
| `django` | Django/Python projects |

### Enable a Plugin

```bash
sgc plugin enable laravel
```

Or in config:
```yaml
plugins:
  enabled:
    - laravel
```

### Using Plugin Prompts

```bash
# Use plugin's prompt directly
sgc propose -p laravel
```

### Creating Custom Plugins

Create `.smartcommit/plugins/my-plugin.py`:

```python
class MyPlugin:
    name = "my-plugin"

    def get_prompt(self):
        return """
        You are analyzing a MyFramework project.

        Group files by:
        - Controllers in app/Http/Controllers
        - Models in app/Models
        - Views in resources/views

        {{FILES}}
        """
```

---

## 🔒 Security

SmartCommit automatically excludes sensitive files from:
1. Being sent to AI
2. Being committed

### Always Excluded

```
.smartcommit/          # Config directory
.env, .env.*           # Environment files
*.pem, *.key           # Private keys
credentials.*, secrets.* # Credential files
id_rsa, id_ed25519     # SSH keys
*.sqlite, *.db         # Databases
```

### Sensitive Warnings

These files trigger warnings but aren't blocked:
```
config.json, config.yaml
settings.json
appsettings.json
application.properties
```

---

## 🔄 Workflow Strategies

### Local Merge (Default)

Branches are merged locally into your base branch, then pushed.

```
feature/PROJ-123-add-auth  ─┐
feature/PROJ-124-fix-bug   ─┼─► dev (merged) ─► push
feature/PROJ-125-update-ui ─┘
```

**Best for:** Solo developers, small teams

### Merge Request

Each branch is pushed separately, PRs are created.

```
feature/PROJ-123-add-auth  ─► push ─► PR
feature/PROJ-124-fix-bug   ─► push ─► PR
feature/PROJ-125-update-ui ─► push ─► PR
```

**Best for:** Teams with code review requirements

Set in config:
```yaml
workflow:
  strategy: merge-request  # or local-merge
```

---

## 📝 Custom Prompts

Create custom prompts in `.smartcommit/prompts/`:

**`.smartcommit/prompts/my-prompt.md`:**
```markdown
# My Custom Prompt

Analyze the following file changes and group them logically.

## Rules
- Group by feature
- Keep tests with their implementations
- Separate refactoring from features

## Files
{{FILES}}
```

Use it:
```bash
sgc propose -p my-prompt
```

---

## 🌍 Environment Variables

| Variable | Description |
|----------|-------------|
| `JIRA_API_TOKEN` | Jira API token |
| `GITHUB_TOKEN` | GitHub personal access token |
| `OPENAI_API_KEY` | OpenAI API key |
| `ANTHROPIC_API_KEY` | Anthropic API key |

---

## 🛠️ Troubleshooting

### "No changes found"
Make sure you have uncommitted changes:
```bash
git status
```

### "LLM not found"
Install a supported LLM provider:
```bash
npm install -g @anthropic-ai/claude-code
```

### SSH Push Issues
If `sgc push` hangs, ensure your SSH agent is running:
```bash
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_rsa
```

### Jira Connection Issues
1. Verify your site URL includes `https://`
2. Check API token is valid
3. Ensure project key is correct (case-sensitive)

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

## 🤝 Contributing

Contributions are welcome! Please read our contributing guidelines before submitting PRs.

---

**Made with ❤️ for developers who want smarter commits**