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
rg quality check

# Check specific commit
rg quality check --commit HEAD

# Full project scan
rg quality scan

# Show current settings
rg quality status
```

---

## Commands

### rg quality check

Analyze git changes (staged, commits, branches).

```bash
# Check staged changes (default)
rg quality check

# Check specific commit
rg quality check --commit HEAD
rg quality check -c abc123

# Compare branch with main
rg quality check --branch feature/my-feature
rg quality check -b feature/my-feature

# With quality threshold
rg quality check --threshold 80

# Verbose output
rg quality check -v

# Save report
rg quality check --format json -o report.json
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

### rg quality scan

Full project scan with Semgrep (not just git changes).

```bash
# Scan current directory
rg quality scan

# Scan specific directory
rg quality scan src/

# Use specific rule pack
rg quality scan -c p/security-audit

# Filter by severity
rg quality scan -s ERROR,WARNING

# Export as JSON
rg quality scan -o report.json -f json

# Verbose with suggestions
rg quality scan -v
```

**Options:**

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--config` | `-c` | Semgrep config (e.g., auto, p/security-audit) | auto |
| `--severity` | `-s` | Minimum severity: ERROR, WARNING, INFO | all |
| `--output` | `-o` | Save report to file | - |
| `--format` | `-f` | Output format: text, json | text |
| `--verbose` | `-v` | Show detailed output | false |

### rg quality status

Show quality settings and Semgrep status.

```bash
rg quality status

# Output:
# Quality Settings
#   Semgrep: Enabled
#   Rule Packs: auto, p/security-audit
#   Threshold: 70
```

### rg quality report

Generate comprehensive quality report.

```bash
rg quality report
rg quality report --format json -o report.json
rg quality report --format markdown -o QUALITY.md
```

---

## Semgrep Configuration

### Enable/Disable Semgrep

```bash
# Enable Semgrep (installs if needed)
rg config semgrep --enable

# Disable Semgrep
rg config semgrep --disable

# Check status
rg config semgrep
```

### Manage Rule Packs

```bash
# Add rule packs
rg config semgrep --add p/security-audit
rg config semgrep --add p/python
rg config semgrep --add p/javascript

# Remove rule pack
rg config semgrep --remove auto

# List available rule packs
rg config semgrep --list-rules
```

### Install Semgrep

```bash
# Install Semgrep binary
rg config semgrep --install
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
$ rg quality check

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
$ rg quality scan

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

Quality check runs automatically on `rg propose`:

```bash
# Propose will run quality check first
rg propose

# If quality fails, you'll see:
# ⚠️  Quality check failed (score: 45/70)
# Fix issues and try again, or use --skip-quality
```

### Skip Quality Check

```bash
# Skip quality check on propose
rg propose --skip-quality
```

### CI Integration

```bash
# Run in CI pipeline
rg quality check --format json -o quality-report.json

# Fail if below threshold
rg quality check --threshold 80 || exit 1
```

---

## Troubleshooting

### "Semgrep not found"

```bash
# Install Semgrep
rg config semgrep --install

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
rg quality scan -s ERROR

# Use specific rule packs instead of auto
rg config semgrep --remove auto
rg config semgrep --add p/security-audit
```

### "AI review not working"

Check LLM configuration:
```bash
rg config show
# Ensure llm.provider is configured
```

---

## See Also

- [Commands Reference](commands.md)
- [Configuration](configuration.md)
- [CI/CD Integration](ci.md)
