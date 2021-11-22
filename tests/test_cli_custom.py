from click.testing import CliRunner
from mock import MagicMock, patch

from sceptre.cli import cli
from sceptre.config.reader import ConfigReader
from sceptre.stack import Stack
from sceptre.plan.actions import StackActions


class TestCliCustom(object):

    def setup_method(self, test_method):
        self.patcher_ConfigReader = patch("sceptre.plan.plan.ConfigReader")
        self.patcher_StackActions = patch("sceptre.plan.executor.StackActions")

        self.mock_ConfigReader = self.patcher_ConfigReader.start()
        self.mock_StackActions = self.patcher_StackActions.start()

        self.mock_config_reader = MagicMock(spec=ConfigReader)
        self.mock_stack_actions = MagicMock(spec=StackActions)

        self.mock_stack = MagicMock(spec=Stack)

        self.mock_stack.name = 'mock-stack'
        self.mock_stack.region = None
        self.mock_stack.profile = None
        self.mock_stack.external_name = None
        self.mock_stack.dependencies = []

        self.mock_config_reader.construct_stacks.return_value = \
            set([self.mock_stack]), set([self.mock_stack])

        self.mock_stack_actions.stack = self.mock_stack

        self.mock_ConfigReader.return_value = self.mock_config_reader
        self.mock_StackActions.return_value = self.mock_stack_actions

        self.runner = CliRunner()

    def teardown_method(self, test_method):
        self.patcher_ConfigReader.stop()
        self.patcher_StackActions.stop()

    def test_stack_name(self):
        self.mock_stack_actions.stack_name.return_value = "mock-stack"
        result = self.runner.invoke(
            cli, ["stack-name", "dev/vpc.yaml"]
        )
        assert result.exit_code == 0
        assert result.output == "mock-stack\n"

    def test_detect_stack_drift(self):
        self.mock_stack_actions.detect_stack_drift.return_value = [
            "mock-stack", {"some": "json"}
        ]
        result = self.runner.invoke(
            cli, ["detect-stack-drift", "dev/vpc.yaml"]
        )
        assert result.exit_code == 0
        assert result.output == '{\n  "mock-stack": {\n    "some": "json"\n  }\n}\n'
