from pathlib import Path
from typing import Optional
from .base import Plugin


class LaravelPlugin(Plugin):
    """Laravel framework plugin - Laravel-specific file grouping and prompts"""
    name = "laravel"

    # Laravel-specific prompt
    LARAVEL_PROMPT = """# Laravel Project Commit Grouping

You are a senior Laravel developer. Analyze the following file changes and group them into logical commits.

## Laravel-Specific Guidelines

1. **Group by domain/feature**: Keep related MVC components together
   - Model + Migration + Controller + Views for same feature = one group
   - API controllers separate from web controllers

2. **Separate infrastructure changes**:
   - Config files (config/*.php) → separate group
   - Service providers → separate group
   - Middleware → separate group

3. **Database changes**:
   - Migrations should be grouped by feature, not all together
   - Seeders with their related migrations

4. **Laravel conventions**:
   - Use Laravel naming conventions in commit messages
   - Reference Eloquent models, not "database tables"

## File Categories

- `app/Models/` → Eloquent models
- `app/Http/Controllers/` → Controllers
- `app/Http/Middleware/` → Middleware
- `app/Providers/` → Service providers
- `database/migrations/` → Database migrations
- `database/seeders/` → Database seeders
- `routes/` → Route definitions
- `resources/views/` → Blade templates
- `config/` → Configuration files
- `tests/` → Test files

## File Changes

{{FILES}}

## Instructions

- Group files by feature/domain when possible
- Keep related MVC components together
- Separate config/infrastructure changes
- Use conventional commits (feat/fix/refactor/chore)
"""

    def match(self) -> bool:
        """Check if this is a Laravel project"""
        if not Path("artisan").exists():
            return False
        if not Path("composer.json").exists():
            return False
        try:
            return "laravel/framework" in Path("composer.json").read_text().lower()
        except Exception:
            return False

    def get_prompt(self) -> Optional[str]:
        """Return Laravel-specific prompt"""
        return self.LARAVEL_PROMPT

    def get_groups(self, changes: list) -> list:
        """
        Laravel-specific grouping rules.

        Returns empty list to let AI handle grouping with Laravel prompt.
        Override this to implement custom grouping logic.
        """
        # Let AI handle grouping with Laravel-specific prompt
        return []