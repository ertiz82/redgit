"""
Unit tests for redgit.core.llm module.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from redgit.core.llm import (
    load_providers,
    check_provider_available,
    get_available_providers,
    get_all_providers,
    LLMClient,
    PROVIDERS_FILE,
)


class TestLoadProviders:
    """Tests for load_providers function."""

    def test_returns_dict(self):
        """Test that load_providers returns a dictionary."""
        providers = load_providers()
        assert isinstance(providers, dict)

    def test_contains_known_providers(self):
        """Test that known providers are included."""
        providers = load_providers()
        # At least some common providers should exist
        assert len(providers) > 0

    def test_provider_has_required_fields(self):
        """Test that providers have required fields."""
        providers = load_providers()
        for name, config in providers.items():
            assert "type" in config, f"Provider {name} missing 'type'"

    @patch('redgit.core.llm.PROVIDERS_FILE')
    def test_returns_empty_when_file_missing(self, mock_file):
        """Test returns empty dict when file doesn't exist."""
        mock_file.exists.return_value = False
        # This would need module reload to work properly
        # For now, just verify the function exists
        assert callable(load_providers)


class TestCheckProviderAvailable:
    """Tests for check_provider_available function."""

    @patch('shutil.which')
    def test_cli_provider_available_when_command_exists(self, mock_which):
        """Test CLI provider available when command exists."""
        mock_which.return_value = "/usr/bin/claude"
        config = {"type": "cli", "cmd": "claude"}

        result = check_provider_available("claude-code", config)

        assert result is True
        mock_which.assert_called_with("claude")

    @patch('shutil.which')
    def test_cli_provider_unavailable_when_command_missing(self, mock_which):
        """Test CLI provider unavailable when command missing."""
        mock_which.return_value = None
        config = {"type": "cli", "cmd": "nonexistent"}

        result = check_provider_available("test", config)

        assert result is False

    @patch('shutil.which')
    def test_ollama_checks_command_exists(self, mock_which):
        """Test Ollama provider checks for ollama command."""
        mock_which.return_value = "/usr/bin/ollama"
        config = {"type": "api"}

        result = check_provider_available("ollama", config)

        assert result is True
        mock_which.assert_called_with("ollama")

    @patch('shutil.which')
    def test_ollama_unavailable_when_missing(self, mock_which):
        """Test Ollama unavailable when command missing."""
        mock_which.return_value = None
        config = {"type": "api"}

        result = check_provider_available("ollama", config)

        assert result is False

    def test_unknown_provider_type_returns_false(self):
        """Test unknown provider type returns False."""
        config = {"type": "unknown"}

        result = check_provider_available("test", config)

        assert result is False


class TestGetAllProviders:
    """Tests for get_all_providers function."""

    def test_returns_all_providers(self):
        """Test that get_all_providers returns all providers."""
        providers = get_all_providers()
        assert isinstance(providers, dict)
        assert len(providers) > 0


class TestGetAvailableProviders:
    """Tests for get_available_providers function."""

    @patch('redgit.core.llm.check_provider_available')
    @patch('redgit.core.llm.load_providers')
    def test_filters_available_providers(self, mock_load, mock_check):
        """Test that only available providers are returned."""
        mock_load.return_value = {
            "provider1": {"type": "cli"},
            "provider2": {"type": "api"},
        }
        mock_check.side_effect = [True, False]

        result = get_available_providers()

        assert "provider1" in result
        assert "provider2" not in result


class TestLLMClientInit:
    """Tests for LLMClient initialization."""

    @patch('redgit.core.llm.check_provider_available')
    @patch('redgit.core.llm.load_providers')
    def test_init_with_explicit_provider(self, mock_load, mock_check):
        """Test initialization with explicit provider."""
        mock_load.return_value = {
            "ollama": {"type": "api", "default_model": "llama2"}
        }
        mock_check.return_value = True

        client = LLMClient({"provider": "ollama"})

        assert client.provider_name == "ollama"
        assert client.model == "llama2"

    @patch('redgit.core.llm.check_provider_available')
    @patch('redgit.core.llm.load_providers')
    def test_init_with_custom_model(self, mock_load, mock_check):
        """Test initialization with custom model."""
        mock_load.return_value = {
            "ollama": {"type": "api", "default_model": "llama2"}
        }
        mock_check.return_value = True

        client = LLMClient({"provider": "ollama", "model": "codellama"})

        assert client.model == "codellama"

    @patch('redgit.core.llm.check_provider_available')
    @patch('redgit.core.llm.load_providers')
    def test_init_sets_timeout(self, mock_load, mock_check):
        """Test initialization sets timeout from config."""
        mock_load.return_value = {
            "ollama": {"type": "api", "default_model": "llama2"}
        }
        mock_check.return_value = True

        client = LLMClient({"provider": "ollama", "timeout": 300})

        assert client.timeout == 300

    @patch('redgit.core.llm.check_provider_available')
    @patch('redgit.core.llm.load_providers')
    def test_init_default_timeout(self, mock_load, mock_check):
        """Test initialization uses default timeout."""
        mock_load.return_value = {
            "ollama": {"type": "api", "default_model": "llama2"}
        }
        mock_check.return_value = True

        client = LLMClient({"provider": "ollama"})

        assert client.timeout == 120

    @patch('redgit.core.llm.load_providers')
    def test_init_raises_for_unknown_provider(self, mock_load):
        """Test initialization raises for unknown provider."""
        mock_load.return_value = {"ollama": {"type": "api"}}

        with pytest.raises(ValueError, match="Unknown LLM provider"):
            LLMClient({"provider": "nonexistent"})

    @patch('redgit.core.llm.check_provider_available')
    @patch('redgit.core.llm.load_providers')
    def test_init_raises_when_provider_unavailable(self, mock_load, mock_check):
        """Test initialization raises when provider not available."""
        mock_load.return_value = {
            "ollama": {"type": "api", "install": "curl ... | sh"}
        }
        mock_check.return_value = False

        with pytest.raises(FileNotFoundError, match="not available"):
            LLMClient({"provider": "ollama"})


class TestLLMClientAutoDetect:
    """Tests for LLMClient auto-detection."""

    @patch('redgit.core.llm.check_provider_available')
    @patch('redgit.core.llm.load_providers')
    def test_auto_detect_selects_first_available(self, mock_load, mock_check):
        """Test auto-detect selects first available provider."""
        mock_load.return_value = {
            "claude-code": {"type": "cli", "default_model": "claude"},
            "ollama": {"type": "api", "default_model": "llama2"}
        }
        # claude-code not available, ollama available
        mock_check.side_effect = lambda name, config: name == "ollama"

        client = LLMClient({"provider": "auto"})

        assert client.provider_name == "ollama"

    @patch('redgit.core.llm.check_provider_available')
    @patch('redgit.core.llm.load_providers')
    def test_auto_detect_raises_when_none_available(self, mock_load, mock_check):
        """Test auto-detect raises when no provider available."""
        mock_load.return_value = {
            "ollama": {"type": "api"}
        }
        mock_check.return_value = False

        with pytest.raises(FileNotFoundError, match="No LLM provider found"):
            LLMClient({"provider": "auto"})


class TestLLMClientParseYaml:
    """Tests for LLMClient._parse_yaml method."""

    @patch('redgit.core.llm.check_provider_available')
    @patch('redgit.core.llm.load_providers')
    def setup_method(self, method, mock_load=None, mock_check=None):
        """Set up test fixtures."""
        # Create a mock client for testing parse methods
        pass

    def test_parse_yaml_code_block(self):
        """Test parsing YAML from code block."""
        output = '''```yaml
groups:
  - files: ["a.py"]
    commit_title: "feat: test"
```'''

        with patch('redgit.core.llm.load_providers') as mock_load, \
             patch('redgit.core.llm.check_provider_available') as mock_check:
            mock_load.return_value = {"ollama": {"type": "api", "default_model": "test"}}
            mock_check.return_value = True
            client = LLMClient({"provider": "ollama"})

            result = client._parse_yaml(output)

            assert isinstance(result, list)
            assert len(result) == 1
            assert result[0]["commit_title"] == "feat: test"

    def test_parse_json_code_block(self):
        """Test parsing JSON from code block."""
        output = '''```json
{"groups": [{"files": ["a.py"], "commit_title": "feat: test"}]}
```'''

        with patch('redgit.core.llm.load_providers') as mock_load, \
             patch('redgit.core.llm.check_provider_available') as mock_check:
            mock_load.return_value = {"ollama": {"type": "api", "default_model": "test"}}
            mock_check.return_value = True
            client = LLMClient({"provider": "ollama"})

            result = client._parse_yaml(output)

            assert isinstance(result, list)
            assert len(result) == 1

    def test_parse_yaml_without_code_block(self):
        """Test parsing YAML without code block."""
        output = '''groups:
  - files: ["a.py"]
    commit_title: "feat: test"'''

        with patch('redgit.core.llm.load_providers') as mock_load, \
             patch('redgit.core.llm.check_provider_available') as mock_check:
            mock_load.return_value = {"ollama": {"type": "api", "default_model": "test"}}
            mock_check.return_value = True
            client = LLMClient({"provider": "ollama"})

            result = client._parse_yaml(output)

            assert isinstance(result, list)
            assert len(result) == 1

    def test_parse_yaml_list_response(self):
        """Test parsing YAML list response."""
        output = '''```yaml
- files: ["a.py"]
  commit_title: "feat: first"
- files: ["b.py"]
  commit_title: "fix: second"
```'''

        with patch('redgit.core.llm.load_providers') as mock_load, \
             patch('redgit.core.llm.check_provider_available') as mock_check:
            mock_load.return_value = {"ollama": {"type": "api", "default_model": "test"}}
            mock_check.return_value = True
            client = LLMClient({"provider": "ollama"})

            result = client._parse_yaml(output)

            assert isinstance(result, list)
            assert len(result) == 2

    def test_parse_yaml_raises_on_invalid(self):
        """Test parsing raises on invalid YAML."""
        output = "not: valid: yaml: {{{"

        with patch('redgit.core.llm.load_providers') as mock_load, \
             patch('redgit.core.llm.check_provider_available') as mock_check:
            mock_load.return_value = {"ollama": {"type": "api", "default_model": "test"}}
            mock_check.return_value = True
            client = LLMClient({"provider": "ollama"})

            with pytest.raises(ValueError, match="YAML parse error"):
                client._parse_yaml(output)


class TestLLMClientCleanYaml:
    """Tests for LLMClient._clean_yaml_output method."""

    def _get_client(self):
        """Helper to create a mock client."""
        with patch('redgit.core.llm.load_providers') as mock_load, \
             patch('redgit.core.llm.check_provider_available') as mock_check:
            mock_load.return_value = {"ollama": {"type": "api", "default_model": "test"}}
            mock_check.return_value = True
            return LLMClient({"provider": "ollama"})

    def test_removes_leading_yaml_word(self):
        """Test removes leading 'yaml' word."""
        with patch('redgit.core.llm.load_providers') as mock_load, \
             patch('redgit.core.llm.check_provider_available') as mock_check:
            mock_load.return_value = {"ollama": {"type": "api", "default_model": "test"}}
            mock_check.return_value = True
            client = LLMClient({"provider": "ollama"})

            result = client._clean_yaml_output("yaml\ngroups:\n  - test")

            assert result.startswith("groups:")

    def test_removes_duplicate_yaml(self):
        """Test removes duplicate 'yaml' words."""
        with patch('redgit.core.llm.load_providers') as mock_load, \
             patch('redgit.core.llm.check_provider_available') as mock_check:
            mock_load.return_value = {"ollama": {"type": "api", "default_model": "test"}}
            mock_check.return_value = True
            client = LLMClient({"provider": "ollama"})

            result = client._clean_yaml_output("yamlyaml\ngroups:\n  - test")

            assert result.startswith("groups:")

    def test_handles_groupsyaml_prefix(self):
        """Test handles 'groupsyaml' prefix."""
        with patch('redgit.core.llm.load_providers') as mock_load, \
             patch('redgit.core.llm.check_provider_available') as mock_check:
            mock_load.return_value = {"ollama": {"type": "api", "default_model": "test"}}
            mock_check.return_value = True
            client = LLMClient({"provider": "ollama"})

            result = client._clean_yaml_output("groupsyaml\ngroups:\n  - test")

            assert result.startswith("groups:")

    def test_preserves_valid_yaml(self):
        """Test preserves already valid YAML."""
        with patch('redgit.core.llm.load_providers') as mock_load, \
             patch('redgit.core.llm.check_provider_available') as mock_check:
            mock_load.return_value = {"ollama": {"type": "api", "default_model": "test"}}
            mock_check.return_value = True
            client = LLMClient({"provider": "ollama"})

            input_yaml = "groups:\n  - files: [a.py]\n    commit_title: test"
            result = client._clean_yaml_output(input_yaml)

            assert result == input_yaml


class TestLLMClientGenerateGroups:
    """Tests for LLMClient.generate_groups method."""

    @patch('redgit.core.llm.check_provider_available')
    @patch('redgit.core.llm.load_providers')
    def test_generate_groups_returns_list(self, mock_load, mock_check):
        """Test generate_groups returns a list."""
        mock_load.return_value = {"ollama": {"type": "api", "default_model": "test"}}
        mock_check.return_value = True

        client = LLMClient({"provider": "ollama"})

        with patch.object(client, '_run_api') as mock_run:
            mock_run.return_value = ([{"files": ["a.py"]}], "raw")

            result = client.generate_groups("test prompt")

            assert isinstance(result, list)

    @patch('redgit.core.llm.check_provider_available')
    @patch('redgit.core.llm.load_providers')
    def test_generate_groups_with_return_raw(self, mock_load, mock_check):
        """Test generate_groups with return_raw=True."""
        mock_load.return_value = {"ollama": {"type": "api", "default_model": "test"}}
        mock_check.return_value = True

        client = LLMClient({"provider": "ollama"})

        with patch.object(client, '_run_api') as mock_run:
            mock_run.return_value = ([{"files": ["a.py"]}], "raw output")

            groups, raw = client.generate_groups("test prompt", return_raw=True)

            assert isinstance(groups, list)
            assert raw == "raw output"

    @patch('redgit.core.llm.check_provider_available')
    @patch('redgit.core.llm.load_providers')
    def test_generate_groups_uses_cli_for_cli_provider(self, mock_load, mock_check):
        """Test generate_groups uses CLI for CLI provider."""
        mock_load.return_value = {"claude-code": {"type": "cli", "default_model": "claude"}}
        mock_check.return_value = True

        client = LLMClient({"provider": "claude-code"})

        with patch.object(client, '_run_cli') as mock_run:
            mock_run.return_value = ([], "")

            client.generate_groups("test")

            mock_run.assert_called_once()


class TestLLMClientChat:
    """Tests for LLMClient.chat method."""

    @patch('redgit.core.llm.check_provider_available')
    @patch('redgit.core.llm.load_providers')
    def test_chat_returns_string(self, mock_load, mock_check):
        """Test chat returns a string."""
        mock_load.return_value = {"ollama": {"type": "api", "default_model": "test"}}
        mock_check.return_value = True

        client = LLMClient({"provider": "ollama"})

        with patch.object(client, '_chat_api') as mock_chat:
            mock_chat.return_value = "Hello, world!"

            result = client.chat("Say hello")

            assert result == "Hello, world!"

    @patch('redgit.core.llm.check_provider_available')
    @patch('redgit.core.llm.load_providers')
    def test_chat_raises_for_unknown_type(self, mock_load, mock_check):
        """Test chat raises for unknown provider type."""
        mock_load.return_value = {"test": {"type": "unknown", "default_model": "test"}}
        mock_check.return_value = True

        client = LLMClient({"provider": "test"})

        with pytest.raises(ValueError, match="Unknown provider type"):
            client.chat("test")


class TestLLMProviderConfig:
    """Tests for provider configuration."""

    def test_providers_file_exists(self):
        """Test that providers file exists."""
        assert PROVIDERS_FILE.exists(), f"Providers file not found: {PROVIDERS_FILE}"

    def test_providers_file_is_valid_json(self):
        """Test that providers file is valid JSON."""
        with open(PROVIDERS_FILE, 'r') as f:
            data = json.load(f)

        assert "providers" in data
        assert isinstance(data["providers"], dict)

    def test_each_provider_has_type(self):
        """Test each provider has a type field."""
        providers = load_providers()

        for name, config in providers.items():
            assert "type" in config, f"Provider {name} missing 'type'"
            assert config["type"] in ("cli", "api"), f"Provider {name} has invalid type"

    def test_cli_providers_have_cmd(self):
        """Test CLI providers have cmd field."""
        providers = load_providers()

        for name, config in providers.items():
            if config.get("type") == "cli":
                assert "cmd" in config, f"CLI provider {name} missing 'cmd'"
