# Quality - Code Analysis

Code quality checks with AI analysis and Semgrep integration.

## Overview

RedGit Quality combines AI-powered code review with Semgrep static analysis to catch issues before they reach production. It supports 35+ programming languages and provides actionable feedback.

## Features

| Feature | Description |
|---------|-------------|
| AI Analysis | Intelligent code review using LLM |
| Semgrep Integration | Multi-language static analysis |
| Git-aware | Analyze staged changes, commits, or branches |
| OWASP Detection | Security vulnerability scanning |
| Custom Rules | Add your own Semgrep rule packs |

---

## Quick Start

```bash
# Check staged changes
rgt quality check

# Check specific commit
rgt quality check --commit HEAD

# Full project scan
rgt quality scan

# Show current settings
rgt quality status
```

---

## Commands

### rgt quality check

Analyze git changes (staged, commits, branches).

```bash
# Check staged changes (default)
rgt quality check

# Check specific commit
rgt quality check --commit HEAD
rgt quality check -c abc123

# Compare branch with main
rgt quality check --branch feature/my-feature
rgt quality check -b feature/my-feature

# With quality threshold
rgt quality check --threshold 80

# Verbose output
rgt quality check -v

# Save report
rgt quality check --format json -o report.json
```

**Options:**

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--commit` | `-c` | Analyze specific commit | - |
| `--branch` | `-b` | Compare branch with main | - |
| `--threshold` | `-t` | Quality threshold (0-100) | 70 |
| `--verbose` | `-v` | Show detailed output | false |
| `--output` | `-o` | Save report to file | - |
| `--format` | `-f` | Output format: text, json | text |

### rgt quality scan

Full project scan with Semgrep (not just git changes).

```bash
# Scan current directory
rgt quality scan

# Scan specific directory
rgt quality scan src/

# Use specific rule pack
rgt quality scan -c p/security-audit

# Filter by severity
rgt quality scan -s ERROR,WARNING

# Export as JSON
rgt quality scan -o report.json -f json

# Verbose with suggestions
rgt quality scan -v
```

**Options:**

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--config` | `-c` | Semgrep config (e.g., auto, p/security-audit) | auto |
| `--severity` | `-s` | Minimum severity: ERROR, WARNING, INFO | all |
| `--output` | `-o` | Save report to file | - |
| `--format` | `-f` | Output format: text, json | text |
| `--verbose` | `-v` | Show detailed output | false |

### rgt quality status

Show quality settings and Semgrep status.

```bash
rgt quality status

# Output:
# Quality Settings
#   Semgrep: Enabled
#   Rule Packs: auto, p/security-audit
#   Threshold: 70
```

### rgt quality report

Generate comprehensive quality report.

```bash
rgt quality report
rgt quality report --format json -o report.json
rgt quality report --format markdown -o QUALITY.md
```

---

## Semgrep Configuration

### Enable/Disable Semgrep

```bash
# Enable Semgrep (installs if needed)
rgt config semgrep --enable

# Disable Semgrep
rgt config semgrep --disable

# Check status
rgt config semgrep
```

### Manage Rule Packs

```bash
# Add rule packs
rgt config semgrep --add p/security-audit
rgt config semgrep --add p/python
rgt config semgrep --add p/javascript

# Remove rule pack
rgt config semgrep --remove auto

# List available rule packs
rgt config semgrep --list-rules
```

### Install Semgrep

```bash
# Install Semgrep binary
rgt config semgrep --install
```

---

## Available Rule Packs

| Pack | Description | Languages |
|------|-------------|-----------|
| `auto` | Auto-detect based on project | All |
| `p/security-audit` | Security vulnerabilities | All |
| `p/owasp-top-ten` | OWASP Top 10 | All |
| `p/python` | Python best practices | Python |
| `p/javascript` | JavaScript/TypeScript | JS/TS |
| `p/typescript` | TypeScript specific | TypeScript |
| `p/react` | React patterns | React |
| `p/nodejs` | Node.js security | Node.js |
| `p/php` | PHP rules | PHP |
| `p/golang` | Go rules | Go |
| `p/java` | Java rules | Java |
| `p/ruby` | Ruby rules | Ruby |
| `p/rust` | Rust rules | Rust |
| `p/csharp` | C# rules | C# |
| `p/kotlin` | Kotlin rules | Kotlin |
| `p/swift` | Swift rules | Swift |
| `p/docker` | Dockerfile rules | Docker |
| `p/terraform` | Terraform/HCL rules | Terraform |
| `p/kubernetes` | K8s manifests | YAML |
| `p/secrets` | Secret detection | All |
| `p/sql-injection` | SQL injection | All |
| `p/xss` | XSS vulnerabilities | Web |

See more at: https://semgrep.dev/explore

---

## Configuration

Quality settings in `.redgit/config.yaml`:

```yaml
quality:
  enabled: true
  threshold: 70              # Minimum score (0-100)

  # AI analysis settings
  ai_review: true            # Enable AI code review
  ai_suggestions: true       # Show fix suggestions

  # Semgrep settings
  semgrep:
    enabled: true
    rule_packs:
      - auto
      - p/security-audit
    severity: WARNING        # Minimum severity
    exclude:
      - tests/
      - vendor/
```

---

## Example Output

### Quality Check

```
$ rgt quality check

🔍 Analyzing staged changes...

📊 Quality Score: 75/100

⚠️  Issues Found:

  src/api/users.py:45
    [WARNING] Potential SQL injection
    Recommendation: Use parameterized queries

  src/utils/auth.py:23
    [INFO] Consider using constant-time comparison
    for password verification

🤖 AI Suggestions:
  - Add input validation for user email
  - Consider rate limiting on login endpoint

✅ Passed threshold (70)
```

### Full Scan

```
$ rgt quality scan

🔍 Scanning project with Semgrep...

Rule Packs: auto, p/security-audit
Files scanned: 156

📊 Results:

  ERROR (2)
    src/db/queries.py:89 - sql-injection
    src/api/upload.py:34 - path-traversal

  WARNING (5)
    src/auth/login.py:12 - hardcoded-secret
    src/utils/crypto.py:45 - weak-hash
    ...

  INFO (12)
    ...

Summary: 2 errors, 5 warnings, 12 info
```

---

## Integration with Workflow

### Pre-commit Quality Check

Quality check runs automatically on `rgt propose`:

```bash
# Propose will run quality check first
rgt propose

# If quality fails, you'll see:
# ⚠️  Quality check failed (score: 45/70)
# Fix issues and try again, or use --skip-quality
```

### Skip Quality Check

```bash
# Skip quality check on propose
rgt propose --skip-quality
```

### CI Integration

```bash
# Run in CI pipeline
rgt quality check --format json -o quality-report.json

# Fail if below threshold
rgt quality check --threshold 80 || exit 1
```

---

## Troubleshooting

### "Semgrep not found"

```bash
# Install Semgrep
rgt config semgrep --install

# Or manually
pip install semgrep
# or
brew install semgrep
```

### "Scan taking too long"

For large projects:
```bash
# Exclude directories
# In .redgit/config.yaml:
quality:
  semgrep:
    exclude:
      - node_modules/
      - vendor/
      - dist/
```

### "Too many false positives"

```bash
# Adjust severity
rgt quality scan -s ERROR

# Use specific rule packs instead of auto
rgt config semgrep --remove auto
rgt config semgrep --add p/security-audit
```

### "AI review not working"

Check LLM configuration:
```bash
rgt config show
# Ensure llm.provider is configured
```

---

## See Also

- [Commands Reference](commands.md)
- [Configuration](configuration.md)
- [CI/CD Integration](ci.md)
