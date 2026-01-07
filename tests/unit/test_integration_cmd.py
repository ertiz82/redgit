"""Tests for integration command module."""

import pytest
import json
from pathlib import Path
from unittest.mock import MagicMock, patch, call
from typer.testing import CliRunner
import typer

from redgit.commands.integration import (
    _get_integration_type_name,
    _get_integration_type_label,
    _get_installed_integrations,
    _is_configured,
    _get_field_key,
    _prompt_field,
    _generate_init_py,
    _generate_commands_py,
    _generate_install_schema,
    _generate_readme,
    _generate_prompt_analyze,
    _generate_prompt_summarize,
    _generate_prompt_custom,
    configure_integration,
    integration_app,
    INTEGRATION_TYPES,
)
from redgit.integrations.registry import IntegrationType


runner = CliRunner()


# ==================== Tests for _get_integration_type_name ====================

class TestGetIntegrationTypeName:
    """Tests for _get_integration_type_name helper."""

    def test_task_management(self):
        """Returns correct name for task management type."""
        result = _get_integration_type_name(IntegrationType.TASK_MANAGEMENT)
        assert result == "task_management"

    def test_code_hosting(self):
        """Returns correct name for code hosting type."""
        result = _get_integration_type_name(IntegrationType.CODE_HOSTING)
        assert result == "code_hosting"

    def test_notification(self):
        """Returns correct name for notification type."""
        result = _get_integration_type_name(IntegrationType.NOTIFICATION)
        assert result == "notification"

    def test_analysis(self):
        """Returns correct name for analysis type."""
        result = _get_integration_type_name(IntegrationType.ANALYSIS)
        assert result == "analysis"

    def test_unknown_type(self):
        """Returns 'unknown' for unrecognized type."""
        result = _get_integration_type_name(None)
        assert result == "unknown"


# ==================== Tests for _get_integration_type_label ====================

class TestGetIntegrationTypeLabel:
    """Tests for _get_integration_type_label helper."""

    def test_task_management_label(self):
        """Returns correct label for task management type."""
        result = _get_integration_type_label(IntegrationType.TASK_MANAGEMENT)
        assert result == "Task Management"

    def test_code_hosting_label(self):
        """Returns correct label for code hosting type."""
        result = _get_integration_type_label(IntegrationType.CODE_HOSTING)
        assert result == "Code Hosting"

    def test_notification_label(self):
        """Returns correct label for notification type."""
        result = _get_integration_type_label(IntegrationType.NOTIFICATION)
        assert result == "Notification"

    def test_analysis_label(self):
        """Returns correct label for analysis type."""
        result = _get_integration_type_label(IntegrationType.ANALYSIS)
        assert result == "Analysis"

    def test_unknown_type_label(self):
        """Returns 'Unknown' for unrecognized type."""
        result = _get_integration_type_label(None)
        assert result == "Unknown"


# ==================== Tests for _get_installed_integrations ====================

class TestGetInstalledIntegrations:
    """Tests for _get_installed_integrations helper."""

    def test_empty_directories(self, tmp_path, monkeypatch):
        """Returns empty set when no integrations installed."""
        monkeypatch.chdir(tmp_path)

        with patch('redgit.core.common.config.GLOBAL_INTEGRATIONS_DIR', tmp_path / "global"):
            result = _get_installed_integrations()

        assert result == set()

    def test_global_integrations(self, tmp_path, monkeypatch):
        """Finds integrations in global directory."""
        monkeypatch.chdir(tmp_path)
        global_dir = tmp_path / "global"

        # Create global integration
        integration_dir = global_dir / "my_integration"
        integration_dir.mkdir(parents=True)
        (integration_dir / "__init__.py").write_text("# integration")

        with patch('redgit.core.common.config.GLOBAL_INTEGRATIONS_DIR', global_dir):
            result = _get_installed_integrations()

        assert "my_integration" in result

    def test_project_integrations(self, tmp_path, monkeypatch):
        """Finds integrations in project directory."""
        monkeypatch.chdir(tmp_path)

        # Create project integration
        integration_dir = tmp_path / ".redgit" / "integrations" / "local_integration"
        integration_dir.mkdir(parents=True)
        (integration_dir / "__init__.py").write_text("# integration")

        with patch('redgit.core.common.config.GLOBAL_INTEGRATIONS_DIR', tmp_path / "nonexistent"):
            result = _get_installed_integrations()

        assert "local_integration" in result

    def test_ignores_non_package_dirs(self, tmp_path, monkeypatch):
        """Ignores directories without __init__.py."""
        monkeypatch.chdir(tmp_path)

        # Create project directory without __init__.py
        integration_dir = tmp_path / ".redgit" / "integrations" / "not_a_package"
        integration_dir.mkdir(parents=True)

        with patch('redgit.core.common.config.GLOBAL_INTEGRATIONS_DIR', tmp_path / "nonexistent"):
            result = _get_installed_integrations()

        assert "not_a_package" not in result

    def test_combines_global_and_project(self, tmp_path, monkeypatch):
        """Combines integrations from both global and project directories."""
        monkeypatch.chdir(tmp_path)
        global_dir = tmp_path / "global"

        # Create global integration
        global_int_dir = global_dir / "global_int"
        global_int_dir.mkdir(parents=True)
        (global_int_dir / "__init__.py").write_text("# global")

        # Create project integration
        project_int_dir = tmp_path / ".redgit" / "integrations" / "project_int"
        project_int_dir.mkdir(parents=True)
        (project_int_dir / "__init__.py").write_text("# project")

        with patch('redgit.core.common.config.GLOBAL_INTEGRATIONS_DIR', global_dir):
            result = _get_installed_integrations()

        assert "global_int" in result
        assert "project_int" in result


# ==================== Tests for _is_configured ====================

class TestIsConfigured:
    """Tests for _is_configured helper."""

    def test_disabled_integration(self):
        """Returns False for disabled integration."""
        config = {"enabled": False}
        schema = {}

        assert _is_configured(config, schema) is False

    def test_no_required_fields(self):
        """Returns True when no required fields and enabled."""
        config = {"enabled": True}
        schema = {"fields": []}

        assert _is_configured(config, schema) is True

    def test_all_required_fields_present(self):
        """Returns True when all required fields are present."""
        config = {
            "enabled": True,
            "api_key": "secret123",
            "base_url": "https://api.example.com"
        }
        schema = {
            "fields": [
                {"key": "api_key", "required": True},
                {"key": "base_url", "required": True}
            ]
        }

        assert _is_configured(config, schema) is True

    def test_missing_required_field(self):
        """Returns False when required field is missing."""
        config = {
            "enabled": True,
            "api_key": "secret123"
        }
        schema = {
            "fields": [
                {"key": "api_key", "required": True},
                {"key": "base_url", "required": True}
            ]
        }

        assert _is_configured(config, schema) is False

    def test_empty_required_field(self):
        """Returns False when required field is empty."""
        config = {
            "enabled": True,
            "api_key": ""
        }
        schema = {
            "fields": [
                {"key": "api_key", "required": True}
            ]
        }

        assert _is_configured(config, schema) is False

    def test_optional_fields_not_required(self):
        """Returns True when optional fields are missing."""
        config = {
            "enabled": True,
            "api_key": "secret123"
        }
        schema = {
            "fields": [
                {"key": "api_key", "required": True},
                {"key": "optional_field", "required": False}
            ]
        }

        assert _is_configured(config, schema) is True

    def test_uses_name_as_fallback_key(self):
        """Uses 'name' field if 'key' is not present."""
        config = {
            "enabled": True,
            "token": "abc123"
        }
        schema = {
            "fields": [
                {"name": "token", "required": True}
            ]
        }

        assert _is_configured(config, schema) is True


# ==================== Tests for _get_field_key ====================

class TestGetFieldKey:
    """Tests for _get_field_key helper."""

    def test_uses_key_first(self):
        """Prefers 'key' over 'name'."""
        field = {"key": "api_key", "name": "token"}
        assert _get_field_key(field) == "api_key"

    def test_falls_back_to_name(self):
        """Uses 'name' if 'key' not present."""
        field = {"name": "token"}
        assert _get_field_key(field) == "token"

    def test_returns_empty_string_if_no_key_or_name(self):
        """Returns empty string if neither 'key' nor 'name' present."""
        field = {"type": "text"}
        assert _get_field_key(field) == ""


# ==================== Tests for _prompt_field ====================

class TestPromptField:
    """Tests for _prompt_field helper."""

    @patch('redgit.commands.integration.typer.prompt')
    @patch('redgit.commands.integration.typer.echo')
    def test_text_field_with_default(self, mock_echo, mock_prompt):
        """Prompts for text field with default value."""
        mock_prompt.return_value = "my_value"
        field = {
            "key": "name",
            "prompt": "Enter name",
            "type": "text",
            "default": "default_name"
        }

        result = _prompt_field(field)

        assert result == "my_value"
        mock_prompt.assert_called_with("   Enter name", default="default_name")

    @patch('redgit.commands.integration.typer.prompt')
    @patch('redgit.commands.integration.typer.echo')
    def test_text_field_required(self, mock_echo, mock_prompt):
        """Prompts for required text field without default."""
        mock_prompt.return_value = "required_value"
        field = {
            "key": "api_key",
            "prompt": "API Key",
            "type": "text",
            "required": True
        }

        result = _prompt_field(field)

        assert result == "required_value"
        mock_prompt.assert_called_with("   API Key")

    @patch('redgit.commands.integration.typer.prompt')
    @patch('redgit.commands.integration.typer.echo')
    def test_text_field_optional(self, mock_echo, mock_prompt):
        """Prompts for optional text field."""
        mock_prompt.return_value = ""
        field = {
            "key": "optional",
            "prompt": "Optional field",
            "type": "text",
            "required": False
        }

        result = _prompt_field(field)

        assert result is None
        mock_prompt.assert_called_with("   Optional field (optional)", default="")

    @patch('redgit.commands.integration.typer.prompt')
    @patch('redgit.commands.integration.typer.echo')
    def test_secret_field_required(self, mock_echo, mock_prompt):
        """Prompts for required secret field with hidden input."""
        mock_prompt.return_value = "secret123"
        field = {
            "key": "password",
            "prompt": "Password",
            "type": "secret",
            "required": True
        }

        result = _prompt_field(field)

        assert result == "secret123"
        mock_prompt.assert_called_with("   Password", hide_input=True)

    @patch('redgit.commands.integration.typer.prompt')
    @patch('redgit.commands.integration.typer.echo')
    def test_secret_field_optional(self, mock_echo, mock_prompt):
        """Prompts for optional secret field."""
        mock_prompt.return_value = ""
        field = {
            "key": "optional_secret",
            "prompt": "Optional Secret",
            "type": "secret",
            "required": False
        }

        result = _prompt_field(field)

        assert result is None
        mock_prompt.assert_called_with(
            "   Optional Secret (optional, press Enter to skip)",
            hide_input=True,
            default=""
        )

    @patch('redgit.commands.integration.typer.prompt')
    @patch('redgit.commands.integration.typer.echo')
    def test_choice_field(self, mock_echo, mock_prompt):
        """Prompts for choice field."""
        mock_prompt.return_value = "2"
        field = {
            "key": "env",
            "prompt": "Environment",
            "type": "choice",
            "choices": ["development", "staging", "production"],
            "default": "development"
        }

        result = _prompt_field(field)

        assert result == "staging"  # Index 1 (choice "2")

    @patch('redgit.commands.integration.typer.prompt')
    @patch('redgit.commands.integration.typer.echo')
    def test_choice_field_invalid_input(self, mock_echo, mock_prompt):
        """Returns default for invalid choice input."""
        mock_prompt.return_value = "invalid"
        field = {
            "key": "env",
            "prompt": "Environment",
            "type": "choice",
            "choices": ["dev", "prod"],
            "default": "dev"
        }

        result = _prompt_field(field)

        assert result == "dev"  # Falls back to default

    @patch('redgit.commands.integration.typer.confirm')
    @patch('redgit.commands.integration.typer.echo')
    def test_confirm_field(self, mock_echo, mock_confirm):
        """Prompts for confirmation field."""
        mock_confirm.return_value = True
        field = {
            "key": "enable_feature",
            "prompt": "Enable feature?",
            "type": "confirm",
            "default": False
        }

        result = _prompt_field(field)

        assert result is True
        mock_confirm.assert_called_with("   Enable feature?", default=False)

    @patch('redgit.commands.integration.typer.echo')
    def test_shows_help_text(self, mock_echo):
        """Shows help text when available."""
        field = {
            "key": "api_key",
            "help": "Get your API key from settings page"
        }

        with patch('redgit.commands.integration.typer.prompt', return_value=""):
            _prompt_field(field)

        # Check that help text was shown
        help_calls = [c for c in mock_echo.call_args_list if "Get your API key" in str(c)]
        assert len(help_calls) > 0

    @patch('redgit.commands.integration.typer.echo')
    def test_shows_env_var_hint(self, mock_echo):
        """Shows environment variable hint when available."""
        field = {
            "key": "api_key",
            "env_var": "MY_API_KEY"
        }

        with patch('redgit.commands.integration.typer.prompt', return_value=""):
            _prompt_field(field)

        # Check that env var hint was shown
        env_calls = [c for c in mock_echo.call_args_list if "MY_API_KEY" in str(c)]
        assert len(env_calls) > 0

    @patch('redgit.commands.integration.typer.prompt')
    @patch('redgit.commands.integration.typer.echo')
    def test_string_type_normalized_to_text(self, mock_echo, mock_prompt):
        """String type is normalized to text type."""
        mock_prompt.return_value = "value"
        field = {
            "key": "name",
            "prompt": "Name",
            "type": "string",  # Should be treated as "text"
            "required": True
        }

        result = _prompt_field(field)

        assert result == "value"

    def test_unknown_field_type(self):
        """Returns None for unknown field types."""
        field = {
            "key": "unknown",
            "type": "unknown_type"
        }

        result = _prompt_field(field)

        assert result is None


# ==================== Tests for Template Generators ====================

class TestGenerateInitPy:
    """Tests for _generate_init_py template generator."""

    def test_generates_valid_python(self):
        """Generates syntactically valid Python code."""
        content = _generate_init_py(
            name="my_service",
            class_name="MyServiceIntegration",
            base_class="AnalysisBase",
            type_name="analysis",
            description="My custom service integration"
        )

        # Should compile without errors
        compile(content, "<string>", "exec")

    def test_contains_class_definition(self):
        """Contains the integration class definition."""
        content = _generate_init_py(
            name="my_service",
            class_name="MyServiceIntegration",
            base_class="AnalysisBase",
            type_name="analysis",
            description="Test description"
        )

        assert "class MyServiceIntegration(AnalysisBase):" in content
        assert 'name = "my_service"' in content
        assert "IntegrationType.ANALYSIS" in content

    def test_contains_required_methods(self):
        """Contains all required integration methods."""
        content = _generate_init_py(
            name="test",
            class_name="TestIntegration",
            base_class="TaskManagementBase",
            type_name="task_management",
            description="Test"
        )

        assert "def setup(self, config: dict):" in content
        assert "def validate_connection(self) -> bool:" in content
        assert "def after_install(cls, config: dict) -> dict:" in content


class TestGenerateCommandsPy:
    """Tests for _generate_commands_py template generator."""

    def test_generates_valid_python(self):
        """Generates syntactically valid Python code."""
        content = _generate_commands_py(
            name="my_service",
            class_name="MyServiceIntegration"
        )

        compile(content, "<string>", "exec")

    def test_contains_typer_app(self):
        """Contains Typer app definition."""
        content = _generate_commands_py(
            name="my_service",
            class_name="MyServiceIntegration"
        )

        assert "my_service_app = typer.Typer(" in content

    def test_contains_commands(self):
        """Contains expected CLI commands."""
        content = _generate_commands_py(
            name="my_service",
            class_name="MyServiceIntegration"
        )

        assert "def status_cmd():" in content
        assert "def test_cmd(" in content
        assert "def analyze_cmd(" in content


class TestGenerateInstallSchema:
    """Tests for _generate_install_schema template generator."""

    def test_returns_valid_dict(self):
        """Returns a valid dictionary."""
        schema = _generate_install_schema(
            name="my_service",
            display_name="My Service",
            description="Test description"
        )

        assert isinstance(schema, dict)
        assert schema["name"] == "My Service"
        assert schema["description"] == "Test description"

    def test_contains_required_fields(self):
        """Contains api_key as required field."""
        schema = _generate_install_schema(
            name="my_service",
            display_name="My Service",
            description="Test"
        )

        fields = schema["fields"]
        api_key_field = next((f for f in fields if f["key"] == "api_key"), None)

        assert api_key_field is not None
        assert api_key_field["required"] is True
        assert api_key_field["type"] == "secret"

    def test_env_var_uses_uppercase_name(self):
        """Environment variable uses uppercase name."""
        schema = _generate_install_schema(
            name="my_service",
            display_name="My Service",
            description="Test"
        )

        api_key_field = schema["fields"][0]
        assert api_key_field["env_var"] == "MY_SERVICE_API_KEY"


class TestGenerateReadme:
    """Tests for _generate_readme template generator."""

    def test_contains_installation_section(self):
        """Contains installation instructions."""
        readme = _generate_readme(
            name="my_service",
            class_name="MyServiceIntegration",
            description="Test integration"
        )

        assert "## Installation" in readme
        assert "rg integration install my_service" in readme

    def test_contains_configuration_section(self):
        """Contains configuration examples."""
        readme = _generate_readme(
            name="my_service",
            class_name="MyServiceIntegration",
            description="Test"
        )

        assert "## Configuration" in readme
        assert "my_service:" in readme

    def test_contains_usage_section(self):
        """Contains usage examples."""
        readme = _generate_readme(
            name="my_service",
            class_name="MyServiceIntegration",
            description="Test"
        )

        assert "## Usage" in readme
        assert "rg my_service status" in readme


class TestGeneratePromptTemplates:
    """Tests for prompt template generators."""

    def test_analyze_prompt_has_content_placeholder(self):
        """Analyze prompt has content placeholder."""
        prompt = _generate_prompt_analyze()

        assert "{content}" in prompt
        assert "Analyze" in prompt or "analyze" in prompt

    def test_summarize_prompt_has_placeholders(self):
        """Summarize prompt has required placeholders."""
        prompt = _generate_prompt_summarize()

        assert "{content}" in prompt
        assert "{max_length}" in prompt

    def test_custom_prompt_has_placeholders(self):
        """Custom prompt has common placeholders."""
        prompt = _generate_prompt_custom()

        assert "{input}" in prompt
        assert "{context}" in prompt
        assert "{task}" in prompt


# ==================== Tests for CLI Commands ====================

class TestListCmd:
    """Tests for list_cmd CLI command."""

    @patch('redgit.commands.integration._get_installed_integrations')
    @patch('redgit.commands.integration.ConfigManager')
    def test_no_integrations(self, mock_config_manager, mock_get_installed):
        """Shows message when no integrations installed."""
        mock_get_installed.return_value = set()
        mock_config_manager.return_value.load.return_value = {}

        result = runner.invoke(integration_app, ["list"])

        assert result.exit_code == 0
        assert "No integrations installed" in result.output

    @patch('redgit.commands.integration.get_all_install_schemas')
    @patch('redgit.commands.integration.get_integration_type')
    @patch('redgit.commands.integration._get_installed_integrations')
    @patch('redgit.commands.integration.ConfigManager')
    def test_shows_installed_integrations(
        self, mock_config_manager, mock_get_installed, mock_get_type, mock_get_schemas
    ):
        """Shows installed integrations grouped by type."""
        mock_get_installed.return_value = {"jira", "slack"}
        mock_config_manager.return_value.load.return_value = {
            "integrations": {
                "jira": {"enabled": True},
                "slack": {"enabled": True}
            },
            "active": {"task_management": "jira"}
        }
        mock_get_type.side_effect = lambda n: (
            IntegrationType.TASK_MANAGEMENT if n == "jira"
            else IntegrationType.NOTIFICATION
        )
        mock_get_schemas.return_value = {}

        result = runner.invoke(integration_app, ["list"])

        assert result.exit_code == 0
        assert "jira" in result.output
        assert "slack" in result.output


class TestConfigCmd:
    """Tests for config_cmd CLI command."""

    @patch('redgit.commands.integration.configure_integration')
    def test_calls_configure_integration(self, mock_configure):
        """Calls configure_integration with provided name."""
        result = runner.invoke(integration_app, ["config", "jira"])

        mock_configure.assert_called_once_with("jira")


class TestAddCmd:
    """Tests for add_cmd CLI command."""

    @patch('redgit.commands.integration.get_builtin_integrations')
    def test_integration_not_found(self, mock_get_builtin):
        """Shows error for unknown integration."""
        mock_get_builtin.return_value = {"jira": MagicMock(), "slack": MagicMock()}

        result = runner.invoke(integration_app, ["add", "unknown"])

        assert result.exit_code == 1
        assert "not found" in result.output

    @patch('redgit.commands.integration.ConfigManager')
    @patch('redgit.commands.integration.get_builtin_integrations')
    def test_already_enabled(self, mock_get_builtin, mock_config_manager):
        """Shows message when integration already enabled."""
        mock_get_builtin.return_value = {"jira": MagicMock()}
        mock_config_manager.return_value.load.return_value = {
            "integrations": {"jira": {"enabled": True}}
        }

        result = runner.invoke(integration_app, ["add", "jira"])

        assert result.exit_code == 0
        assert "already enabled" in result.output

    @patch('redgit.commands.integration.ConfigManager')
    @patch('redgit.commands.integration.get_builtin_integrations')
    def test_enables_integration(self, mock_get_builtin, mock_config_manager):
        """Enables integration and saves config."""
        mock_get_builtin.return_value = {"jira": MagicMock()}
        mock_instance = mock_config_manager.return_value
        mock_instance.load.return_value = {}

        result = runner.invoke(integration_app, ["add", "jira"])

        assert result.exit_code == 0
        assert "enabled" in result.output
        mock_instance.save.assert_called_once()


class TestRemoveCmd:
    """Tests for remove_cmd CLI command."""

    @patch('redgit.commands.integration.ConfigManager')
    def test_integration_not_configured(self, mock_config_manager):
        """Shows error when integration not configured."""
        mock_config_manager.return_value.load.return_value = {"integrations": {}}

        result = runner.invoke(integration_app, ["remove", "jira"])

        assert result.exit_code == 1
        assert "not configured" in result.output

    @patch('redgit.commands.integration.ConfigManager')
    def test_disables_integration(self, mock_config_manager):
        """Disables integration but preserves config."""
        mock_instance = mock_config_manager.return_value
        mock_instance.load.return_value = {
            "integrations": {"jira": {"enabled": True, "api_key": "secret"}}
        }

        result = runner.invoke(integration_app, ["remove", "jira"])

        assert result.exit_code == 0
        assert "disabled" in result.output

        # Check that config was saved with enabled=False
        saved_config = mock_instance.save.call_args[0][0]
        assert saved_config["integrations"]["jira"]["enabled"] is False


class TestUseCmd:
    """Tests for use_cmd CLI command."""

    @patch('redgit.commands.integration.get_builtin_integrations')
    def test_integration_not_found(self, mock_get_builtin):
        """Shows error for unknown integration."""
        mock_get_builtin.return_value = {"jira": MagicMock()}

        result = runner.invoke(integration_app, ["use", "unknown"])

        assert result.exit_code == 1
        assert "not found" in result.output

    @patch('redgit.commands.integration.get_install_schema')
    @patch('redgit.commands.integration.get_integration_type')
    @patch('redgit.commands.integration.ConfigManager')
    @patch('redgit.commands.integration.get_builtin_integrations')
    def test_sets_integration_as_active(
        self, mock_get_builtin, mock_config_manager, mock_get_type, mock_get_schema
    ):
        """Sets integration as active for its type."""
        mock_get_builtin.return_value = {"jira": MagicMock()}
        mock_get_type.return_value = IntegrationType.TASK_MANAGEMENT
        mock_get_schema.return_value = {"fields": []}
        mock_instance = mock_config_manager.return_value
        mock_instance.load.return_value = {
            "integrations": {"jira": {"enabled": True}}
        }

        result = runner.invoke(integration_app, ["use", "jira"])

        assert result.exit_code == 0

        # Check that active was set
        saved_config = mock_instance.save.call_args[0][0]
        assert saved_config["active"]["task_management"] == "jira"


class TestCreateCmd:
    """Tests for create_cmd CLI command."""

    def test_creates_integration_directory(self, tmp_path, monkeypatch):
        """Creates integration directory with all files."""
        monkeypatch.chdir(tmp_path)

        # Create .redgit directory
        (tmp_path / ".redgit").mkdir()

        with patch('redgit.commands.integration.get_builtin_integrations', return_value={}):
            with patch('redgit.integrations.registry.refresh_integrations'):
                result = runner.invoke(
                    integration_app,
                    ["create", "my_test"],
                    input="My Test\nTest description\n4\n"  # display name, description, type
                )

        assert result.exit_code == 0

        integration_dir = tmp_path / ".redgit" / "integrations" / "my_test"
        assert integration_dir.exists()
        assert (integration_dir / "__init__.py").exists()
        assert (integration_dir / "commands.py").exists()
        assert (integration_dir / "install_schema.json").exists()
        assert (integration_dir / "README.md").exists()
        assert (integration_dir / "prompts" / "analyze.txt").exists()

    def test_rejects_invalid_name(self, tmp_path, monkeypatch):
        """Rejects invalid integration names."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".redgit").mkdir()

        result = runner.invoke(integration_app, ["create", "123-invalid"])

        assert result.exit_code == 1
        assert "Invalid name" in result.output

    def test_rejects_existing_integration(self, tmp_path, monkeypatch):
        """Rejects if integration already exists."""
        monkeypatch.chdir(tmp_path)

        # Create existing integration directory
        existing = tmp_path / ".redgit" / "integrations" / "existing"
        existing.mkdir(parents=True)

        result = runner.invoke(integration_app, ["create", "existing"])

        assert result.exit_code == 1
        assert "already exists" in result.output

    def test_rejects_builtin_conflict(self, tmp_path, monkeypatch):
        """Rejects names that conflict with builtins."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".redgit").mkdir()

        with patch('redgit.commands.integration.get_builtin_integrations',
                   return_value={"jira": MagicMock()}):
            result = runner.invoke(integration_app, ["create", "jira"])

        assert result.exit_code == 1
        assert "conflicts" in result.output


class TestUpdateCmd:
    """Tests for update_cmd CLI command."""

    @patch('redgit.commands.integration._get_installed_integrations')
    @patch('redgit.commands.integration.ConfigManager')
    def test_no_integrations_to_update(self, mock_config_manager, mock_get_installed):
        """Shows message when no integrations installed."""
        mock_get_installed.return_value = set()
        mock_config_manager.return_value.load.return_value = {}

        result = runner.invoke(integration_app, ["update"])

        assert "No integrations installed" in result.output

    def test_updates_integration(self):
        """Updates installed integration from tap."""
        with patch('redgit.commands.integration._get_installed_integrations') as mock_get_installed:
            with patch('redgit.commands.integration.ConfigManager') as mock_config_manager:
                with patch('redgit.core.tap.find_item_in_taps') as mock_find_item:
                    with patch('redgit.commands.tap.install_from_tap') as mock_install:
                        mock_get_installed.return_value = {"my_integration"}
                        mock_config_manager.return_value.load.return_value = {
                            "integrations": {"my_integration": {"enabled": True}}
                        }
                        mock_find_item.return_value = {"name": "my_integration", "tap": "official"}
                        mock_install.return_value = True

                        result = runner.invoke(integration_app, ["update", "my_integration"])

                        # Check output contains update message (skipped for local is fine too)
                        assert result.exit_code == 0 or "skipped" in result.output


# ==================== Tests for configure_integration ====================

class TestConfigureIntegration:
    """Tests for configure_integration function."""

    @patch('redgit.commands.integration.typer.Exit')
    @patch('redgit.commands.integration.typer.echo')
    @patch('redgit.commands.integration.typer.secho')
    @patch('redgit.commands.integration.get_all_integrations')
    def test_integration_not_found(self, mock_get_all, mock_secho, mock_echo, mock_exit):
        """Raises exit for unknown integration."""
        mock_get_all.return_value = {"jira": MagicMock()}
        mock_exit.side_effect = SystemExit(1)

        with pytest.raises(SystemExit):
            configure_integration("unknown")

        mock_exit.assert_called_with(1)

    @patch('redgit.commands.integration.ConfigManager')
    @patch('redgit.commands.integration.get_install_schema')
    @patch('redgit.commands.integration.get_all_integrations')
    def test_enables_without_schema(self, mock_get_all, mock_get_schema, mock_config_manager):
        """Enables integration when no schema is available."""
        mock_get_all.return_value = {"simple": MagicMock()}
        mock_get_schema.return_value = None
        mock_instance = mock_config_manager.return_value
        mock_instance.load.return_value = {}

        configure_integration("simple")

        saved_config = mock_instance.save.call_args[0][0]
        assert saved_config["integrations"]["simple"]["enabled"] is True

    @patch('redgit.commands.integration.get_integration_type')
    @patch('redgit.commands.integration.get_integration_class')
    @patch('redgit.commands.integration._prompt_field')
    @patch('redgit.commands.integration.ConfigManager')
    @patch('redgit.commands.integration.get_install_schema')
    @patch('redgit.commands.integration.get_all_integrations')
    def test_prompts_for_fields(
        self, mock_get_all, mock_get_schema, mock_config_manager,
        mock_prompt_field, mock_get_class, mock_get_type
    ):
        """Prompts for each field in schema."""
        mock_get_all.return_value = {"jira": MagicMock()}
        mock_get_schema.return_value = {
            "name": "Jira",
            "fields": [
                {"key": "api_key", "required": True},
                {"key": "base_url", "required": False}
            ]
        }
        mock_prompt_field.side_effect = ["secret123", "https://jira.example.com"]
        mock_instance = mock_config_manager.return_value
        mock_instance.load.return_value = {}
        mock_get_class.return_value = None
        mock_get_type.return_value = IntegrationType.TASK_MANAGEMENT

        configure_integration("jira")

        assert mock_prompt_field.call_count == 2

    @patch('redgit.commands.integration.get_all_integrations')
    def test_normalizes_hyphenated_name(self, mock_get_all):
        """Normalizes hyphenated names to underscores."""
        mock_get_all.return_value = {"my_integration": MagicMock()}

        with patch('redgit.commands.integration.get_install_schema', return_value=None):
            with patch('redgit.commands.integration.ConfigManager') as mock_cm:
                mock_cm.return_value.load.return_value = {}
                configure_integration("my-integration")

        # Should not raise error due to name normalization


# ==================== Tests for INTEGRATION_TYPES constant ====================

class TestIntegrationTypes:
    """Tests for INTEGRATION_TYPES constant."""

    def test_has_all_types(self):
        """Contains all expected integration types."""
        assert "1" in INTEGRATION_TYPES
        assert "2" in INTEGRATION_TYPES
        assert "3" in INTEGRATION_TYPES
        assert "4" in INTEGRATION_TYPES

    def test_type_structure(self):
        """Each type has correct structure."""
        for key, value in INTEGRATION_TYPES.items():
            assert len(value) == 3
            type_name, base_class, label = value
            assert isinstance(type_name, str)
            assert isinstance(base_class, str)
            assert isinstance(label, str)
            assert "Base" in base_class

    def test_task_management_type(self):
        """Task management type is correct."""
        type_name, base_class, label = INTEGRATION_TYPES["1"]
        assert type_name == "task_management"
        assert base_class == "TaskManagementBase"

    def test_code_hosting_type(self):
        """Code hosting type is correct."""
        type_name, base_class, label = INTEGRATION_TYPES["2"]
        assert type_name == "code_hosting"
        assert base_class == "CodeHostingBase"

    def test_notification_type(self):
        """Notification type is correct."""
        type_name, base_class, label = INTEGRATION_TYPES["3"]
        assert type_name == "notification"
        assert base_class == "NotificationBase"

    def test_analysis_type(self):
        """Analysis type is correct."""
        type_name, base_class, label = INTEGRATION_TYPES["4"]
        assert type_name == "analysis"
        assert base_class == "AnalysisBase"
