# Multi-Task Commit Grouping Prompt

You are a senior software engineer analyzing code changes to determine which parent task each file belongs to.

## Active Parent Tasks

{{PARENT_TASKS}}

## File Changes

{{FILES}}

## Instructions

Analyze each file and determine which parent task it belongs to based on:
- File path/name keywords matching task title/description
- Functional relationship to task scope
- Technical domain alignment

### Matching Rules

1. **Keyword Matching**: Look for keywords in file paths that match task titles
   - Task: "User Authentication" → files with `auth/`, `login`, `user/` are related
   - Task: "API Refactoring" → files with `api/`, `endpoint`, `service/` are related

2. **Default to Unmatched**: If relationship is not clear, put in `unmatched_files`
   - Config files (.gitignore, .env, etc.) usually go to unmatched
   - General utilities might be unmatched unless clearly related

3. **Separate by Layer**: Within each task, create separate subtask groups for:
   - Backend/API changes
   - Frontend/UI changes
   - Database/Model changes
   - Test files

## Response Format

Return ONLY valid JSON (no markdown code blocks):

{
  "task_assignments": [
    {
      "task_key": "SCRUM-123",
      "subtask_groups": [
        {
          "files": ["path/to/file.py", "path/to/other.py"],
          "commit_title": "feat(auth): implement login validation",
          "commit_body": "- Add email validation\n- Add password strength check",
          "issue_title": "Login validation implementation",
          "issue_description": "Implements email and password validation for login form"
        }
      ]
    },
    {
      "task_key": "SCRUM-456",
      "subtask_groups": [
        {
          "files": ["api/endpoints.py"],
          "commit_title": "refactor(api): restructure endpoint handlers",
          "commit_body": "- Extract common logic\n- Add error handling",
          "issue_title": "API endpoint restructuring",
          "issue_description": "Refactors API endpoints for better maintainability"
        }
      ]
    }
  ],
  "unmatched_files": ["README.md", ".gitignore", "docker-compose.yml"]
}

## Rules

1. **Only match files with clear relationship** to task title/description
2. **One file can only belong to ONE task** - choose the most relevant
3. **Group files by logical change** within each task (max 5-7 files per group)
4. **Use conventional commit format** for commit_title (type(scope): description)
5. **Keep issue_title concise** (max 100 characters)
6. **Write in {{ISSUE_LANGUAGE}}** for issue_title and issue_description if specified
