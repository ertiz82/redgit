"""
Unit tests for redgit.integrations.base module.
"""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from redgit.integrations.base import (
    IntegrationType,
    Issue,
    Sprint,
    PipelineRun,
    PipelineJob,
    QualityReport,
    SecurityIssue,
    CoverageReport,
    IntegrationBase,
    TaskManagementBase,
    CodeHostingBase,
    NotificationBase,
    AnalysisBase,
    CICDBase,
    CodeQualityBase,
)


class TestIntegrationType:
    """Tests for IntegrationType enum."""

    def test_has_task_management_type(self):
        """Test TASK_MANAGEMENT enum value."""
        assert IntegrationType.TASK_MANAGEMENT.value == "task_management"

    def test_has_code_hosting_type(self):
        """Test CODE_HOSTING enum value."""
        assert IntegrationType.CODE_HOSTING.value == "code_hosting"

    def test_has_notification_type(self):
        """Test NOTIFICATION enum value."""
        assert IntegrationType.NOTIFICATION.value == "notification"

    def test_has_analysis_type(self):
        """Test ANALYSIS enum value."""
        assert IntegrationType.ANALYSIS.value == "analysis"

    def test_has_ci_cd_type(self):
        """Test CI_CD enum value."""
        assert IntegrationType.CI_CD.value == "ci_cd"

    def test_has_code_quality_type(self):
        """Test CODE_QUALITY enum value."""
        assert IntegrationType.CODE_QUALITY.value == "code_quality"

    def test_all_types_count(self):
        """Test that all expected types exist."""
        assert len(IntegrationType) == 7


class TestIssueDataclass:
    """Tests for Issue dataclass."""

    def test_creates_issue_with_required_fields(self):
        """Test Issue creation with required fields."""
        issue = Issue(
            key="PROJ-123",
            summary="Test issue",
            description="Test description",
            status="Open",
            issue_type="bug"
        )

        assert issue.key == "PROJ-123"
        assert issue.summary == "Test issue"
        assert issue.description == "Test description"
        assert issue.status == "Open"
        assert issue.issue_type == "bug"

    def test_optional_fields_default_to_none(self):
        """Test that optional fields default to None."""
        issue = Issue(
            key="PROJ-1",
            summary="Test",
            description="Desc",
            status="Open",
            issue_type="task"
        )

        assert issue.assignee is None
        assert issue.url is None
        assert issue.sprint is None
        assert issue.story_points is None
        assert issue.labels is None

    def test_optional_fields_can_be_set(self):
        """Test setting optional fields."""
        issue = Issue(
            key="PROJ-1",
            summary="Test",
            description="Desc",
            status="In Progress",
            issue_type="story",
            assignee="user@example.com",
            url="https://jira.example.com/PROJ-1",
            sprint="Sprint 5",
            story_points=3.0,
            labels=["frontend", "urgent"]
        )

        assert issue.assignee == "user@example.com"
        assert issue.url == "https://jira.example.com/PROJ-1"
        assert issue.sprint == "Sprint 5"
        assert issue.story_points == 3.0
        assert issue.labels == ["frontend", "urgent"]


class TestSprintDataclass:
    """Tests for Sprint dataclass."""

    def test_creates_sprint_with_required_fields(self):
        """Test Sprint creation with required fields."""
        sprint = Sprint(
            id="sprint-1",
            name="Sprint 1",
            state="active"
        )

        assert sprint.id == "sprint-1"
        assert sprint.name == "Sprint 1"
        assert sprint.state == "active"

    def test_optional_sprint_fields(self):
        """Test Sprint optional fields."""
        sprint = Sprint(
            id="sprint-2",
            name="Sprint 2",
            state="future",
            start_date="2024-01-01",
            end_date="2024-01-14",
            goal="Complete feature X"
        )

        assert sprint.start_date == "2024-01-01"
        assert sprint.end_date == "2024-01-14"
        assert sprint.goal == "Complete feature X"


class TestPipelineRunDataclass:
    """Tests for PipelineRun dataclass."""

    def test_creates_pipeline_run(self):
        """Test PipelineRun creation."""
        run = PipelineRun(
            id="run-123",
            name="CI Pipeline",
            status="success"
        )

        assert run.id == "run-123"
        assert run.name == "CI Pipeline"
        assert run.status == "success"

    def test_pipeline_run_optional_fields(self):
        """Test PipelineRun optional fields."""
        run = PipelineRun(
            id="run-456",
            name="Deploy",
            status="running",
            branch="main",
            commit_sha="abc123",
            url="https://ci.example.com/run/456",
            started_at="2024-01-01T10:00:00Z",
            duration=300,
            trigger="push"
        )

        assert run.branch == "main"
        assert run.commit_sha == "abc123"
        assert run.duration == 300
        assert run.trigger == "push"


class TestPipelineJobDataclass:
    """Tests for PipelineJob dataclass."""

    def test_creates_pipeline_job(self):
        """Test PipelineJob creation."""
        job = PipelineJob(
            id="job-1",
            name="Build",
            status="success"
        )

        assert job.id == "job-1"
        assert job.name == "Build"
        assert job.status == "success"

    def test_pipeline_job_optional_fields(self):
        """Test PipelineJob optional fields."""
        job = PipelineJob(
            id="job-2",
            name="Test",
            status="running",
            stage="test",
            duration=120,
            logs_url="https://ci.example.com/logs/job-2"
        )

        assert job.stage == "test"
        assert job.duration == 120
        assert job.logs_url == "https://ci.example.com/logs/job-2"


class TestQualityReportDataclass:
    """Tests for QualityReport dataclass."""

    def test_creates_quality_report(self):
        """Test QualityReport creation."""
        report = QualityReport(
            id="report-1",
            status="passed"
        )

        assert report.id == "report-1"
        assert report.status == "passed"

    def test_quality_report_metrics(self):
        """Test QualityReport metric fields."""
        report = QualityReport(
            id="report-2",
            status="warning",
            bugs=5,
            vulnerabilities=2,
            code_smells=50,
            coverage=75.5,
            duplications=3.2,
            technical_debt="2h 30min",
            quality_gate_status="passed"
        )

        assert report.bugs == 5
        assert report.vulnerabilities == 2
        assert report.code_smells == 50
        assert report.coverage == 75.5
        assert report.duplications == 3.2
        assert report.technical_debt == "2h 30min"


class TestSecurityIssueDataclass:
    """Tests for SecurityIssue dataclass."""

    def test_creates_security_issue(self):
        """Test SecurityIssue creation."""
        issue = SecurityIssue(
            id="sec-1",
            severity="high",
            title="SQL Injection vulnerability"
        )

        assert issue.id == "sec-1"
        assert issue.severity == "high"
        assert issue.title == "SQL Injection vulnerability"

    def test_security_issue_optional_fields(self):
        """Test SecurityIssue optional fields."""
        issue = SecurityIssue(
            id="sec-2",
            severity="critical",
            title="Remote Code Execution",
            package="vulnerable-lib",
            version="1.0.0",
            fixed_in="1.0.1",
            cve="CVE-2024-1234",
            cwe="CWE-94",
            file_path="src/app.py",
            line_number=42
        )

        assert issue.package == "vulnerable-lib"
        assert issue.cve == "CVE-2024-1234"
        assert issue.cwe == "CWE-94"
        assert issue.line_number == 42


class TestCoverageReportDataclass:
    """Tests for CoverageReport dataclass."""

    def test_creates_coverage_report(self):
        """Test CoverageReport creation."""
        report = CoverageReport(id="cov-1")

        assert report.id == "cov-1"

    def test_coverage_report_metrics(self):
        """Test CoverageReport metric fields."""
        report = CoverageReport(
            id="cov-2",
            commit_sha="abc123",
            branch="main",
            line_coverage=85.5,
            branch_coverage=72.3,
            function_coverage=90.0,
            lines_covered=1000,
            lines_total=1170,
            coverage_change=2.5,
            base_coverage=83.0
        )

        assert report.line_coverage == 85.5
        assert report.branch_coverage == 72.3
        assert report.lines_covered == 1000
        assert report.coverage_change == 2.5


class TestIntegrationBase:
    """Tests for IntegrationBase class."""

    def test_set_config_stores_config(self):
        """Test that set_config stores the config."""
        # Create a concrete implementation for testing
        class ConcreteIntegration(IntegrationBase):
            def setup(self, config):
                pass

        integration = ConcreteIntegration()
        test_config = {"key": "value", "nested": {"a": 1}}

        integration.set_config(test_config)

        assert integration._config == test_config
        assert integration._config["key"] == "value"

    def test_init_sets_defaults(self):
        """Test that __init__ sets default values."""
        class ConcreteIntegration(IntegrationBase):
            def setup(self, config):
                pass

        integration = ConcreteIntegration()

        assert integration.enabled is False
        assert integration._config == {}

    def test_on_commit_does_nothing_by_default(self):
        """Test that on_commit is a no-op by default."""
        class ConcreteIntegration(IntegrationBase):
            def setup(self, config):
                pass

        integration = ConcreteIntegration()
        # Should not raise
        integration.on_commit({"files": []}, {"issue_key": "PROJ-1"})

    def test_get_notification_events_returns_class_events(self):
        """Test get_notification_events returns class-defined events."""
        class ConcreteIntegration(IntegrationBase):
            notification_events = {
                "custom_event": {"description": "A custom event", "default": True}
            }
            def setup(self, config):
                pass

        events = ConcreteIntegration.get_notification_events()

        assert "custom_event" in events
        assert events["custom_event"]["default"] is True

    def test_after_install_returns_config(self):
        """Test after_install returns config unchanged by default."""
        config = {"key": "value"}

        result = IntegrationBase.after_install(config)

        assert result == config
        assert result["key"] == "value"


class TestTaskManagementBase:
    """Tests for TaskManagementBase class."""

    def test_integration_type_is_task_management(self):
        """Test that integration_type is TASK_MANAGEMENT."""
        assert TaskManagementBase.integration_type == IntegrationType.TASK_MANAGEMENT

    def test_default_issue_language_is_english(self):
        """Test default issue_language is 'en'."""
        assert TaskManagementBase.issue_language == "en"

    def test_get_commit_prefix_returns_project_key(self):
        """Test get_commit_prefix returns project_key."""
        class ConcreteTask(TaskManagementBase):
            project_key = "PROJ"
            def setup(self, config): pass
            def get_my_active_issues(self): return []
            def get_issue(self, key): return None
            def create_issue(self, *args, **kwargs): return None
            def add_comment(self, *args): return False
            def transition_issue(self, *args): return False
            def format_branch_name(self, *args): return ""

        task = ConcreteTask()
        assert task.get_commit_prefix() == "PROJ"

    def test_supports_sprints_returns_false_by_default(self):
        """Test supports_sprints returns False by default."""
        class ConcreteTask(TaskManagementBase):
            def setup(self, config): pass
            def get_my_active_issues(self): return []
            def get_issue(self, key): return None
            def create_issue(self, *args, **kwargs): return None
            def add_comment(self, *args): return False
            def transition_issue(self, *args): return False
            def format_branch_name(self, *args): return ""

        task = ConcreteTask()
        assert task.supports_sprints() is False

    def test_get_active_sprint_returns_none_by_default(self):
        """Test get_active_sprint returns None by default."""
        class ConcreteTask(TaskManagementBase):
            def setup(self, config): pass
            def get_my_active_issues(self): return []
            def get_issue(self, key): return None
            def create_issue(self, *args, **kwargs): return None
            def add_comment(self, *args): return False
            def transition_issue(self, *args): return False
            def format_branch_name(self, *args): return ""

        task = ConcreteTask()
        assert task.get_active_sprint() is None

    def test_get_sprint_issues_returns_empty_list(self):
        """Test get_sprint_issues returns empty list by default."""
        class ConcreteTask(TaskManagementBase):
            def setup(self, config): pass
            def get_my_active_issues(self): return []
            def get_issue(self, key): return None
            def create_issue(self, *args, **kwargs): return None
            def add_comment(self, *args): return False
            def transition_issue(self, *args): return False
            def format_branch_name(self, *args): return ""

        task = ConcreteTask()
        assert task.get_sprint_issues() == []

    def test_add_issue_to_sprint_returns_false(self):
        """Test add_issue_to_sprint returns False by default."""
        class ConcreteTask(TaskManagementBase):
            def setup(self, config): pass
            def get_my_active_issues(self): return []
            def get_issue(self, key): return None
            def create_issue(self, *args, **kwargs): return None
            def add_comment(self, *args): return False
            def transition_issue(self, *args): return False
            def format_branch_name(self, *args): return ""

        task = ConcreteTask()
        assert task.add_issue_to_sprint("PROJ-1", "sprint-1") is False

    def test_get_builtin_prompt_returns_default_prompts(self):
        """Test _get_builtin_prompt returns default prompts."""
        class ConcreteTask(TaskManagementBase):
            def setup(self, config): pass
            def get_my_active_issues(self): return []
            def get_issue(self, key): return None
            def create_issue(self, *args, **kwargs): return None
            def add_comment(self, *args): return False
            def transition_issue(self, *args): return False
            def format_branch_name(self, *args): return ""

        task = ConcreteTask()

        title_prompt = task._get_builtin_prompt("issue_title")
        desc_prompt = task._get_builtin_prompt("issue_description")

        assert title_prompt is not None
        assert "issue title" in title_prompt.lower()
        assert desc_prompt is not None
        assert "description" in desc_prompt.lower()

    def test_get_builtin_prompt_returns_none_for_unknown(self):
        """Test _get_builtin_prompt returns None for unknown prompt."""
        class ConcreteTask(TaskManagementBase):
            def setup(self, config): pass
            def get_my_active_issues(self): return []
            def get_issue(self, key): return None
            def create_issue(self, *args, **kwargs): return None
            def add_comment(self, *args): return False
            def transition_issue(self, *args): return False
            def format_branch_name(self, *args): return ""

        task = ConcreteTask()
        result = task._get_builtin_prompt("unknown_prompt")
        assert result is None

    def test_generate_issue_content_returns_defaults_without_llm(self):
        """Test generate_issue_content returns defaults when no LLM."""
        class ConcreteTask(TaskManagementBase):
            def setup(self, config): pass
            def get_my_active_issues(self): return []
            def get_issue(self, key): return None
            def create_issue(self, *args, **kwargs): return None
            def add_comment(self, *args): return False
            def transition_issue(self, *args): return False
            def format_branch_name(self, *args): return ""

        task = ConcreteTask()
        commit_info = {
            "commit_title": "feat: add new feature",
            "commit_body": "Some description",
            "files": ["a.py", "b.py"]
        }

        result = task.generate_issue_content(commit_info)

        assert result["title"] == "feat: add new feature"
        assert result["description"] == "Some description"


class TestCodeHostingBase:
    """Tests for CodeHostingBase class."""

    def test_integration_type_is_code_hosting(self):
        """Test that integration_type is CODE_HOSTING."""
        assert CodeHostingBase.integration_type == IntegrationType.CODE_HOSTING

    def test_get_default_branch_returns_main(self):
        """Test get_default_branch returns 'main'."""
        class ConcreteCodeHosting(CodeHostingBase):
            def setup(self, config): pass
            def create_pull_request(self, *args): return None
            def push_branch(self, branch): return False

        hosting = ConcreteCodeHosting()
        assert hosting.get_default_branch() == "main"


class TestNotificationBase:
    """Tests for NotificationBase class."""

    def test_integration_type_is_notification(self):
        """Test that integration_type is NOTIFICATION."""
        assert NotificationBase.integration_type == IntegrationType.NOTIFICATION

    def test_notify_formats_message(self):
        """Test that notify formats message correctly."""
        class ConcreteNotification(NotificationBase):
            def __init__(self):
                super().__init__()
                self.last_message = None

            def setup(self, config): pass
            def send_message(self, message, channel=None):
                self.last_message = message
                return True

        notif = ConcreteNotification()
        notif.notify(
            event_type="test",
            title="Test Title",
            message="Test message",
            fields={"Key": "Value"},
            url="https://example.com"
        )

        assert "[TEST]" in notif.last_message
        assert "Test Title" in notif.last_message
        assert "Test message" in notif.last_message
        assert "Key: Value" in notif.last_message
        assert "https://example.com" in notif.last_message

    def test_notify_commit_includes_branch(self):
        """Test notify_commit includes branch in fields."""
        class ConcreteNotification(NotificationBase):
            def __init__(self):
                super().__init__()
                self.last_message = None

            def setup(self, config): pass
            def send_message(self, message, channel=None):
                self.last_message = message
                return True

        notif = ConcreteNotification()
        notif.notify_commit(
            branch="feature/test",
            message="feat: add feature",
            author="developer",
            files=["a.py", "b.py"]
        )

        assert "feature/test" in notif.last_message
        assert "developer" in notif.last_message

    def test_notify_branch_includes_issue_key(self):
        """Test notify_branch includes issue key when provided."""
        class ConcreteNotification(NotificationBase):
            def __init__(self):
                super().__init__()
                self.last_message = None

            def setup(self, config): pass
            def send_message(self, message, channel=None):
                self.last_message = message
                return True

        notif = ConcreteNotification()
        notif.notify_branch("feature/PROJ-123", issue_key="PROJ-123")

        assert "PROJ-123" in notif.last_message
        assert "feature/PROJ-123" in notif.last_message

    def test_notify_pr_includes_url(self):
        """Test notify_pr includes URL."""
        class ConcreteNotification(NotificationBase):
            def __init__(self):
                super().__init__()
                self.last_message = None

            def setup(self, config): pass
            def send_message(self, message, channel=None):
                self.last_message = message
                return True

        notif = ConcreteNotification()
        notif.notify_pr(
            title="Add feature",
            url="https://github.com/test/repo/pull/1",
            head="feature/test",
            base="main"
        )

        assert "https://github.com/test/repo/pull/1" in notif.last_message
        assert "feature/test" in notif.last_message

    def test_notify_task_formats_action(self):
        """Test notify_task capitalizes action."""
        class ConcreteNotification(NotificationBase):
            def __init__(self):
                super().__init__()
                self.last_message = None

            def setup(self, config): pass
            def send_message(self, message, channel=None):
                self.last_message = message
                return True

        notif = ConcreteNotification()
        notif.notify_task(
            action="created",
            issue_key="PROJ-123",
            summary="New task"
        )

        assert "Created" in notif.last_message
        assert "PROJ-123" in notif.last_message

    def test_notify_alert_uses_level(self):
        """Test notify_alert accepts level parameter."""
        class ConcreteNotification(NotificationBase):
            def __init__(self):
                super().__init__()
                self.last_message = None

            def setup(self, config): pass
            def send_message(self, message, channel=None):
                self.last_message = message
                return True

        notif = ConcreteNotification()
        result = notif.notify_alert(
            title="Warning",
            message="Something happened",
            level="warning"
        )

        assert result is True
        assert "Warning" in notif.last_message


class TestCICDBase:
    """Tests for CICDBase class."""

    def test_integration_type_is_ci_cd(self):
        """Test that integration_type is CI_CD."""
        assert CICDBase.integration_type == IntegrationType.CI_CD

    def test_get_pipeline_jobs_returns_empty_list(self):
        """Test get_pipeline_jobs returns empty list by default."""
        class ConcreteCICD(CICDBase):
            def setup(self, config): pass
            def trigger_pipeline(self, *args, **kwargs): return None
            def get_pipeline_status(self, run_id): return None
            def list_pipelines(self, *args, **kwargs): return []
            def cancel_pipeline(self, run_id): return False

        cicd = ConcreteCICD()
        assert cicd.get_pipeline_jobs("run-1") == []

    def test_retry_pipeline_returns_none(self):
        """Test retry_pipeline returns None by default."""
        class ConcreteCICD(CICDBase):
            def setup(self, config): pass
            def trigger_pipeline(self, *args, **kwargs): return None
            def get_pipeline_status(self, run_id): return None
            def list_pipelines(self, *args, **kwargs): return []
            def cancel_pipeline(self, run_id): return False

        cicd = ConcreteCICD()
        assert cicd.retry_pipeline("run-1") is None

    def test_get_pipeline_logs_returns_none(self):
        """Test get_pipeline_logs returns None by default."""
        class ConcreteCICD(CICDBase):
            def setup(self, config): pass
            def trigger_pipeline(self, *args, **kwargs): return None
            def get_pipeline_status(self, run_id): return None
            def list_pipelines(self, *args, **kwargs): return []
            def cancel_pipeline(self, run_id): return False

        cicd = ConcreteCICD()
        assert cicd.get_pipeline_logs("run-1") is None

    def test_list_workflows_returns_empty_list(self):
        """Test list_workflows returns empty list by default."""
        class ConcreteCICD(CICDBase):
            def setup(self, config): pass
            def trigger_pipeline(self, *args, **kwargs): return None
            def get_pipeline_status(self, run_id): return None
            def list_pipelines(self, *args, **kwargs): return []
            def cancel_pipeline(self, run_id): return False

        cicd = ConcreteCICD()
        assert cicd.list_workflows() == []

    def test_get_latest_run_returns_first_from_list(self):
        """Test get_latest_run returns first item from list_pipelines."""
        class ConcreteCICD(CICDBase):
            def setup(self, config): pass
            def trigger_pipeline(self, *args, **kwargs): return None
            def get_pipeline_status(self, run_id): return None
            def list_pipelines(self, *args, **kwargs):
                return [PipelineRun(id="run-1", name="CI", status="success")]
            def cancel_pipeline(self, run_id): return False

        cicd = ConcreteCICD()
        result = cicd.get_latest_run()

        assert result is not None
        assert result.id == "run-1"

    def test_get_latest_run_returns_none_when_empty(self):
        """Test get_latest_run returns None when no pipelines."""
        class ConcreteCICD(CICDBase):
            def setup(self, config): pass
            def trigger_pipeline(self, *args, **kwargs): return None
            def get_pipeline_status(self, run_id): return None
            def list_pipelines(self, *args, **kwargs): return []
            def cancel_pipeline(self, run_id): return False

        cicd = ConcreteCICD()
        assert cicd.get_latest_run() is None


class TestCodeQualityBase:
    """Tests for CodeQualityBase class."""

    def test_integration_type_is_code_quality(self):
        """Test that integration_type is CODE_QUALITY."""
        assert CodeQualityBase.integration_type == IntegrationType.CODE_QUALITY

    def test_trigger_analysis_returns_false(self):
        """Test trigger_analysis returns False by default."""
        class ConcreteQuality(CodeQualityBase):
            def setup(self, config): pass
            def get_quality_status(self, *args): return None
            def get_project_metrics(self): return None

        quality = ConcreteQuality()
        assert quality.trigger_analysis() is False

    def test_get_issues_returns_empty_list(self):
        """Test get_issues returns empty list by default."""
        class ConcreteQuality(CodeQualityBase):
            def setup(self, config): pass
            def get_quality_status(self, *args): return None
            def get_project_metrics(self): return None

        quality = ConcreteQuality()
        assert quality.get_issues() == []

    def test_get_security_issues_returns_empty_list(self):
        """Test get_security_issues returns empty list by default."""
        class ConcreteQuality(CodeQualityBase):
            def setup(self, config): pass
            def get_quality_status(self, *args): return None
            def get_project_metrics(self): return None

        quality = ConcreteQuality()
        assert quality.get_security_issues() == []

    def test_get_coverage_returns_none(self):
        """Test get_coverage returns None by default."""
        class ConcreteQuality(CodeQualityBase):
            def setup(self, config): pass
            def get_quality_status(self, *args): return None
            def get_project_metrics(self): return None

        quality = ConcreteQuality()
        assert quality.get_coverage() is None

    def test_get_quality_gate_status_returns_none(self):
        """Test get_quality_gate_status returns None by default."""
        class ConcreteQuality(CodeQualityBase):
            def setup(self, config): pass
            def get_quality_status(self, *args): return None
            def get_project_metrics(self): return None

        quality = ConcreteQuality()
        assert quality.get_quality_gate_status() is None

    def test_get_dependencies_returns_empty_list(self):
        """Test get_dependencies returns empty list by default."""
        class ConcreteQuality(CodeQualityBase):
            def setup(self, config): pass
            def get_quality_status(self, *args): return None
            def get_project_metrics(self): return None

        quality = ConcreteQuality()
        assert quality.get_dependencies() == []

    def test_get_outdated_dependencies_returns_empty_list(self):
        """Test get_outdated_dependencies returns empty list by default."""
        class ConcreteQuality(CodeQualityBase):
            def setup(self, config): pass
            def get_quality_status(self, *args): return None
            def get_project_metrics(self): return None

        quality = ConcreteQuality()
        assert quality.get_outdated_dependencies() == []

    def test_get_pr_analysis_returns_none(self):
        """Test get_pr_analysis returns None by default."""
        class ConcreteQuality(CodeQualityBase):
            def setup(self, config): pass
            def get_quality_status(self, *args): return None
            def get_project_metrics(self): return None

        quality = ConcreteQuality()
        assert quality.get_pr_analysis(123) is None

    def test_compare_branches_returns_none(self):
        """Test compare_branches returns None by default."""
        class ConcreteQuality(CodeQualityBase):
            def setup(self, config): pass
            def get_quality_status(self, *args): return None
            def get_project_metrics(self): return None

        quality = ConcreteQuality()
        assert quality.compare_branches("feature", "main") is None


class TestBackwardCompatibility:
    """Tests for backward compatibility."""

    def test_integration_alias_exists(self):
        """Test that Integration alias points to IntegrationBase."""
        from redgit.integrations.base import Integration
        assert Integration is IntegrationBase
