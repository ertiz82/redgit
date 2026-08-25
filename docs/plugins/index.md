# Plugins

Plugins extend RedGit with framework-specific features and additional functionality like version management and changelog generation.

---

## Plugin Types

| Type                    | Purpose                              | Examples              |
|-------------------------|--------------------------------------|-----------------------|
| **Framework**           | Smart file grouping, custom prompts  | Laravel, Django       |
| **Release Management**  | Versioning, changelogs, git tags     | Version, Changelog    |

---

## How Plugins Work

1. **Auto-Detection** - Framework plugins detect project type automatically
2. **Enable/Disable** - Manually control which plugins are active
3. **Configure** - Set plugin-specific options in config
4. **Use** - Plugins enhance `rgt propose` and add new commands

### Plugin Commands

```bash
# List installed and available plugins
rgt plugin list
rgt plugin list --all

# Enable/disable a plugin
rgt plugin enable laravel
rgt plugin disable laravel
```

---

## Installing Plugins

Plugins are available from [RedGit Tap](../tap.md):

```bash
# Install a plugin
rgt install plugin:laravel
rgt install plugin:django

# List available
rgt plugin list --all
```

---

## Configuration

Plugins are configured in `.redgit/config.yaml`:

```yaml
plugins:
  enabled:
    - laravel
    - version
    - changelog

  # Plugin-specific settings
  version:
    current: "1.0.0"
    tag_prefix: "v"

  changelog:
    output_dir: changelogs
    group_by_type: true
```

---

## Built-in Plugins

### Version Plugin

Semantic versioning with automatic file updates and git tagging.

```bash
rgt version init           # Initialize versioning
rgt version show           # Show current version
rgt release patch          # Bump patch (1.0.x)
rgt release minor          # Bump minor (1.x.0)
rgt release major          # Bump major (x.0.0)
```

### Changelog Plugin

Automatic changelog generation from commit history.

```bash
rgt changelog init         # Initialize changelog
rgt changelog generate     # Generate from commits
rgt changelog show         # Show current changelog
```

---

## Creating Custom Plugins

You can create custom plugins for your framework or workflow. Place them in `.redgit/plugins/`:

```
.redgit/plugins/my-plugin/
├── __init__.py          # Plugin class (required)
└── prompt.md            # Custom prompt (optional)
```

See [Custom Plugin Guide](custom.md) for detailed instructions.

---

## See Also

- [RedGit Tap](../tap.md) - Browse and install plugins
- [Custom Plugins](custom.md) - Create your own
- [Configuration](../configuration.md) - Full config reference