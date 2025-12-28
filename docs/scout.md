# Scout - AI Project Analysis

AI-powered project analysis and task planning.

## Overview

Scout analyzes your codebase using AI to understand the project structure, identify areas for improvement, and generate actionable task breakdowns. It's your intelligent assistant for sprint planning and technical discovery.

## Features

| Feature | Description |
|---------|-------------|
| Project Structure Analysis | Understand codebase organization |
| Task Suggestions | AI-generated improvement tasks |
| Feature Planning | Break down features into subtasks |
| Code Pattern Detection | Identify patterns and anti-patterns |
| Multiple Output Formats | Text, JSON, Markdown |

## Quick Start

```bash
# Analyze current project
rg scout

# Analyze specific directory
rg scout src/

# Generate task breakdown for a feature
rg scout --feature "add user authentication"
```

---

## Commands

### Basic Analysis

```bash
# Quick project overview
rg scout

# Detailed analysis
rg scout --depth detailed

# Analyze specific directory
rg scout src/api/
```

### Feature Planning

```bash
# Break down a feature into tasks
rg scout --feature "add user authentication"

# With specific depth
rg scout --feature "refactor database layer" --depth detailed
```

### Output Options

```bash
# Save as JSON
rg scout --format json -o analysis.json

# Save as Markdown
rg scout --format markdown -o analysis.md

# Limit file count for large projects
rg scout --max-files 100
```

---

## Options Reference

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--depth` | `-d` | Analysis depth: quick, normal, detailed | normal |
| `--feature` | `-f` | Analyze specific feature or task | - |
| `--format` | | Output format: text, json, markdown | text |
| `--output` | `-o` | Save analysis to file | - |
| `--max-files` | | Maximum files to analyze | 500 |
| `--verbose` | `-v` | Show detailed output | false |

---

## Analysis Depths

### Quick (`--depth quick`)
- Project structure overview
- Primary language detection
- Key directories identification
- ~5 seconds for most projects

### Normal (`--depth normal`) - Default
- Full structure analysis
- Suggested tasks
- Code quality observations
- ~15 seconds for most projects

### Detailed (`--depth detailed`)
- Deep code pattern analysis
- Comprehensive task breakdown
- Architecture recommendations
- Implementation notes
- ~30+ seconds for larger projects

---

## Example Output

### Text Format (Default)

```
$ rg scout

🔍 Project Analysis: my-project

📊 Structure:
   - 45 source files
   - 12 test files
   - Primary language: Python
   - Framework: FastAPI

🎯 Suggested Tasks:
   1. Add input validation to user forms
      Priority: High | Effort: Medium
      Files: src/api/users.py, src/models/user.py

   2. Implement caching for API responses
      Priority: Medium | Effort: High
      Recommendation: Consider Redis for session data

   3. Add unit tests for auth module
      Priority: High | Effort: Low
      Coverage: 45% → Target: 80%

📝 Implementation Notes:
   - Consider using Pydantic for validation
   - Redis recommended for caching layer
   - pytest-cov for coverage reporting
```

### JSON Format

```bash
rg scout --format json -o analysis.json
```

```json
{
  "project": "my-project",
  "language": "Python",
  "framework": "FastAPI",
  "files": {
    "source": 45,
    "test": 12
  },
  "tasks": [
    {
      "title": "Add input validation to user forms",
      "priority": "high",
      "effort": "medium",
      "files": ["src/api/users.py", "src/models/user.py"]
    }
  ],
  "recommendations": [
    "Consider using Pydantic for validation",
    "Redis recommended for caching layer"
  ]
}
```

---

## Use Cases

### Sprint Planning

```bash
# Get task suggestions for next sprint
rg scout --depth detailed

# Focus on specific area
rg scout src/api/ --depth detailed
```

### Feature Implementation

```bash
# Break down a feature before starting
rg scout --feature "implement OAuth2 login"

# Output:
# Feature: OAuth2 Login Implementation
#
# Subtasks:
#   1. Add OAuth provider configuration
#   2. Create callback endpoint
#   3. Implement token storage
#   4. Add session management
#   5. Create login/logout UI components
#   6. Add tests for OAuth flow
```

### Code Review Preparation

```bash
# Analyze changes before review
rg scout --depth quick

# Check specific module
rg scout src/payments/ --depth detailed
```

### New Team Member Onboarding

```bash
# Generate project overview
rg scout --format markdown -o PROJECT_OVERVIEW.md

# Share with team member for quick understanding
```

---

## Integration with Task Management

Scout works with your configured task management integration:

```bash
# Generate tasks and create in Jira
rg scout --create-tasks

# Preview tasks without creating
rg scout --create-tasks --dry-run
```

When `--create-tasks` is used:
1. Scout analyzes the project
2. Generates task suggestions
3. Asks for confirmation
4. Creates issues in your task management system

---

## Configuration

Scout uses settings from `.redgit/config.yaml`:

```yaml
scout:
  depth: normal              # Default analysis depth
  max_files: 500            # File limit
  exclude_patterns:         # Directories to skip
    - node_modules
    - .git
    - __pycache__
    - dist
    - build
```

---

## Troubleshooting

### "Analysis taking too long"

Large projects may take longer. Try:
```bash
# Limit files
rg scout --max-files 100

# Use quick depth
rg scout --depth quick

# Analyze specific directory
rg scout src/core/
```

### "No tasks suggested"

This may happen with very clean or small projects:
```bash
# Try detailed analysis
rg scout --depth detailed

# Focus on feature planning instead
rg scout --feature "add new feature X"
```

### "LLM timeout"

For very large projects:
```bash
# Reduce scope
rg scout src/ --max-files 50

# Check LLM configuration
rg config show
```

---

## See Also

- [Commands Reference](commands.md)
- [Configuration](configuration.md)
- [Task Management Integrations](integrations/index.md)
