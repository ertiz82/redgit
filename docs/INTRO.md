# RedGit — AI-Powered Git Workflow Assistant

RedGit transforms the way developers commit code. Instead of manually staging files, writing commit messages, and updating task trackers, RedGit analyzes your changes with AI, groups them into logical commits, and links each one to your active tasks — all with a single command.

At its core, RedGit understands your code. When you run `rgt propose`, it examines every modified file, identifies related changes, and organizes them into clean, well-structured commits following Conventional Commits standards. Then `rgt push` sends your work upstream, opens pull requests with proper descriptions, and moves your Jira or ClickUp issues through their workflow automatically — from To Do to In Progress to Done.

RedGit integrates deeply with the tools teams already use. It connects to Jira, Linear, Asana, Trello, and ClickUp for task management, creates branches from issue keys (`feature/PROJ-123-description`), and detects the active task directly from your branch name. Notifications flow to Slack or Microsoft Teams, and built-in CI/CD support lets you trigger and monitor pipelines without leaving the terminal.

Quality is built in, not bolted on. Every commit can pass through ruff/flake8 checks, AI-driven code analysis, and Semgrep static analysis covering 35+ languages for security and best practices. Before any destructive operation, RedGit snapshots your working tree, so recovery is always one command away.

Beyond commits, RedGit helps teams plan. Real-time Planning Poker sessions run over WebSocket for sprint estimation, AI-driven project analysis generates task plans, and sprint planning by team capacity keeps workloads balanced. A flexible plugin system adds framework-specific intelligence for Laravel, Django, and more, while multiple LLM providers (OpenAI, Anthropic, Ollama) let you choose your engine — including fully local, private options.

Open source under the MIT license, installable via `pip install redgit`, and running on Python 3.9+. Stop writing commit messages. Start shipping.
