# Release - Version & Changelog

Semantic versioning and automatic changelog generation.

## Overview

RedGit Release manages your project versions using semantic versioning (SemVer) and automatically generates changelogs from commit history. It integrates with git tags and can publish releases to GitHub/GitLab.

## Prerequisites

Enable the version and changelog plugins:

```bash
rg plugin enable version
rg plugin enable changelog
```

---

## Quick Start

```bash
# Initialize versioning
rg version init

# Create a release
rg release minor

# Generate changelog
rg changelog generate
```

---

## Version Management

### Initialize Versioning

```bash
rg version init

# Output:
# Version plugin initialized
# Current version: 0.1.0
# Version file: VERSION
```

This creates:
- `VERSION` file with initial version
- Updates `package.json` or `pyproject.toml` if present

### Show Current Version

```bash
rg version show

# Output:
# Current version: 1.2.3
# Last tag: v1.2.3
# Commits since tag: 5
```

### Bump Version

```bash
# Bump patch (0.0.x) - bug fixes
rg version release patch
# 1.2.3 → 1.2.4

# Bump minor (0.x.0) - new features
rg version release minor
# 1.2.3 → 1.3.0

# Bump major (x.0.0) - breaking changes
rg version release major
# 1.2.3 → 2.0.0
```

---

## Release Command

The `rg release` command is a shortcut for version releases:

```bash
# Bump and tag
rg release patch     # 0.0.x - Bug fixes
rg release minor     # 0.x.0 - New features
rg release major     # x.0.0 - Breaking changes

# Tag current version (no bump)
rg release current

# Force replace existing tag
rg release patch --force
```

### What Release Does

1. Bumps version in VERSION file
2. Updates package.json/pyproject.toml if present
3. Generates changelog entries
4. Creates git commit
5. Creates git tag
6. Optionally pushes to remote

### Release Options

| Option | Description |
|--------|-------------|
| `--force` | Replace existing tag |
| `--no-tag` | Skip git tag creation |
| `--no-push` | Skip pushing to remote |
| `--message` | Custom tag message |

### Examples

```bash
# Standard release
rg release minor
# → Bump 1.2.0 → 1.3.0
# → Update CHANGELOG.md
# → Commit "chore(release): v1.3.0"
# → Tag v1.3.0
# → Push to remote

# Release without push
rg release patch --no-push

# Release with custom message
rg release major --message "Breaking: New API version"

# Just tag current version
rg release current
```

---

## Changelog Management

### Initialize Changelog

```bash
rg changelog init

# Creates CHANGELOG.md with template
```

### Generate Changelog

```bash
# Generate from commits since last tag
rg changelog generate

# Generate for specific version range
rg changelog generate --from v1.0.0 --to v1.1.0

# Preview without writing
rg changelog generate --dry-run
```

### Show Changelog

```bash
# Show current changelog
rg changelog show

# Show specific version
rg changelog show --version 1.2.0
```

### Changelog Format

Generated changelog follows [Keep a Changelog](https://keepachangelog.com/) format:

```markdown
# Changelog

## [1.3.0] - 2024-01-15

### Added
- User authentication with OAuth2
- Dashboard analytics

### Changed
- Improved API response times
- Updated dependencies

### Fixed
- Login redirect issue
- Memory leak in cache

## [1.2.0] - 2024-01-01
...
```

---

## Commit Convention

RedGit uses conventional commits to categorize changes:

| Prefix | Changelog Section |
|--------|-------------------|
| `feat:` | Added |
| `fix:` | Fixed |
| `docs:` | Documentation |
| `style:` | (hidden) |
| `refactor:` | Changed |
| `perf:` | Changed |
| `test:` | (hidden) |
| `chore:` | (hidden) |
| `BREAKING CHANGE:` | Breaking |

### Examples

```bash
# These commits...
git commit -m "feat: add user login"
git commit -m "fix: resolve memory leak"
git commit -m "refactor: simplify auth flow"

# Generate this changelog...
### Added
- Add user login

### Fixed
- Resolve memory leak

### Changed
- Simplify auth flow
```

---

## Configuration

Release settings in `.redgit/config.yaml`:

```yaml
plugins:
  version:
    enabled: true
    file: VERSION              # Version file location
    tag_prefix: v              # Tag prefix (v1.0.0)
    update_files:              # Files to update
      - package.json
      - pyproject.toml

  changelog:
    enabled: true
    file: CHANGELOG.md         # Changelog file
    format: keepachangelog     # Format style
    sections:                  # Custom section mapping
      feat: Added
      fix: Fixed
      refactor: Changed
      perf: Performance
      docs: Documentation
```

---

## Workflow Examples

### Standard Release Flow

```bash
# 1. Ensure all changes are committed
git status

# 2. Create release
rg release minor

# 3. Push with CI
rg push --ci --wait-ci

# 4. Verify on GitHub/GitLab
```

### Pre-release / Beta

```bash
# Create pre-release version
rg version set 2.0.0-beta.1

# Tag as pre-release
git tag -a v2.0.0-beta.1 -m "Beta release"
git push --tags
```

### Hotfix Release

```bash
# On main branch after hotfix merge
rg release patch

# Output:
# Version: 1.2.3 → 1.2.4
# Changelog updated
# Tagged: v1.2.4
# Pushed to remote
```

### Changelog Only

```bash
# Just update changelog without version bump
rg changelog generate

# Commit changelog
git add CHANGELOG.md
git commit -m "docs: update changelog"
```

---

## Integration with GitHub/GitLab

### GitHub Releases

When pushing tags, RedGit can create GitHub releases:

```bash
# Release with GitHub release notes
rg release minor --github-release

# Uses changelog entry as release notes
```

### GitLab Releases

```bash
# Release with GitLab release
rg release minor --gitlab-release
```

---

## Troubleshooting

### "No version file found"

```bash
# Initialize versioning first
rg version init
```

### "Tag already exists"

```bash
# Force replace tag
rg release patch --force

# Or delete tag first
git tag -d v1.2.3
git push origin :refs/tags/v1.2.3
```

### "No commits since last tag"

```bash
# Check commits
git log v1.2.3..HEAD --oneline

# If empty, make changes first or use --force
```

### "Changelog generation failed"

```bash
# Check commit format
git log --oneline -10

# Commits should follow conventional format
# feat: description
# fix: description
```

---

## See Also

- [Commands Reference](commands.md)
- [Plugins Overview](plugins/index.md)
- [CI/CD Integration](ci.md)
