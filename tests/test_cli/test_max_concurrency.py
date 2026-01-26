"""
Tests for max_concurrency CLI parameter validation across commands
"""

from click.testing import CliRunner
from unittest.mock import patch, Mock

from sceptre.cli.launch import launch_command
from sceptre.cli.create import create_command
from sceptre.cli.update import update_command


class TestMaxConcurrencyValidation:
    """Test max_concurrency parameter validation across CLI commands"""

    def setup_method(self, method):
        self.runner = CliRunner()

    def test_launch_command_accepts_valid_max_concurrency(self):
        """Test that launch command accepts valid max_concurrency values"""
        with patch("sceptre.cli.launch.Launcher") as mock_launcher:
            mock_launcher_instance = Mock()
            mock_launcher.return_value = mock_launcher_instance
            mock_launcher_instance.launch.return_value = 0
            mock_launcher_instance.print_operations.return_value = None

            # Mock the context object to have the required attributes
            mock_ctx_obj = {
                "project_path": "/fake/path",
                "user_variables": {},
                "options": {},
                "ignore_dependencies": False,
            }

            result = self.runner.invoke(
                launch_command,
                ["test-stack", "--max-concurrency", "5", "--yes"],
                obj=mock_ctx_obj,
            )

            # Should not have any validation errors
            assert "Invalid value" not in result.output

    def test_launch_command_rejects_zero_max_concurrency(self):
        """Test that launch command rejects max_concurrency=0"""
        result = self.runner.invoke(
            launch_command, ["test-stack", "--max-concurrency", "0"]
        )

        assert result.exit_code != 0
        assert "Invalid value" in result.output
        assert "0 is not in the range x>=1" in result.output

    def test_launch_command_rejects_negative_max_concurrency(self):
        """Test that launch command rejects negative max_concurrency"""
        result = self.runner.invoke(
            launch_command, ["test-stack", "--max-concurrency", "-1"]
        )

        assert result.exit_code != 0
        assert "Invalid value" in result.output

    def test_create_command_accepts_valid_max_concurrency(self):
        """Test that create command accepts valid max_concurrency values"""
        with patch("sceptre.plan.plan.SceptrePlan") as mock_plan:
            mock_plan_instance = Mock()
            mock_plan.return_value = mock_plan_instance
            mock_plan_instance.create.return_value = {}

            result = self.runner.invoke(
                create_command, ["test-stack", "--max-concurrency", "3", "--yes"]
            )

            # Should not have any validation errors
            assert "Invalid value" not in result.output

    def test_create_command_rejects_zero_max_concurrency(self):
        """Test that create command rejects max_concurrency=0"""
        result = self.runner.invoke(
            create_command, ["test-stack", "--max-concurrency", "0"]
        )

        assert result.exit_code != 0
        assert "Invalid value" in result.output

    def test_update_command_accepts_valid_max_concurrency(self):
        """Test that update command accepts valid max_concurrency values"""
        with patch("sceptre.plan.plan.SceptrePlan") as mock_plan:
            mock_plan_instance = Mock()
            mock_plan.return_value = mock_plan_instance
            mock_plan_instance.update.return_value = {}

            result = self.runner.invoke(
                update_command, ["test-stack", "--max-concurrency", "2", "--yes"]
            )

            # Should not have any validation errors
            assert "Invalid value" not in result.output

    def test_update_command_rejects_negative_max_concurrency(self):
        """Test that update command rejects negative max_concurrency"""
        result = self.runner.invoke(
            update_command, ["test-stack", "--max-concurrency", "-5"]
        )

        assert result.exit_code != 0
        assert "Invalid value" in result.output

    def test_launch_command_accepts_max_concurrency_one(self):
        """Test that launch command accepts max_concurrency=1 (minimum valid value)"""
        with patch("sceptre.cli.launch.Launcher") as mock_launcher:
            mock_launcher_instance = Mock()
            mock_launcher.return_value = mock_launcher_instance
            mock_launcher_instance.launch.return_value = 0
            mock_launcher_instance.print_operations.return_value = None

            # Mock the context object to have the required attributes
            mock_ctx_obj = {
                "project_path": "/fake/path",
                "user_variables": {},
                "options": {},
                "ignore_dependencies": False,
            }

            result = self.runner.invoke(
                launch_command,
                ["test-stack", "--max-concurrency", "1", "--yes"],
                obj=mock_ctx_obj,
            )

            # Should not have any validation errors
            assert "Invalid value" not in result.output
            assert result.exit_code == 0

    def test_commands_work_without_max_concurrency(self):
        """Test that commands work normally without max_concurrency parameter"""
        with patch("sceptre.cli.launch.Launcher") as mock_launcher:
            mock_launcher_instance = Mock()
            mock_launcher.return_value = mock_launcher_instance
            mock_launcher_instance.launch.return_value = 0
            mock_launcher_instance.print_operations.return_value = None

            # Mock the context object to have the required attributes
            mock_ctx_obj = {
                "project_path": "/fake/path",
                "user_variables": {},
                "options": {},
                "ignore_dependencies": False,
            }

            result = self.runner.invoke(
                launch_command, ["test-stack", "--yes"], obj=mock_ctx_obj
            )

            # Should work fine without max_concurrency
            assert result.exit_code == 0

    def test_max_concurrency_passed_to_context(self):
        """Test that max_concurrency parameter is passed to SceptreContext"""
        with patch("sceptre.cli.launch.SceptreContext") as mock_context, patch(
            "sceptre.cli.launch.Launcher"
        ) as mock_launcher:

            mock_launcher_instance = Mock()
            mock_launcher.return_value = mock_launcher_instance
            mock_launcher_instance.launch.return_value = 0
            mock_launcher_instance.print_operations.return_value = None

            # Mock the context object to have the required attributes
            mock_ctx_obj = {
                "project_path": "/fake/path",
                "user_variables": {},
                "options": {},
                "ignore_dependencies": False,
            }

            self.runner.invoke(
                launch_command,
                ["test-stack", "--max-concurrency", "7", "--yes"],
                obj=mock_ctx_obj,
            )

            # Verify SceptreContext was called with max_concurrency=7
            mock_context.assert_called_once()
            call_kwargs = mock_context.call_args[1]
            assert call_kwargs["max_concurrency"] == 7
