import pytest
from mock import MagicMock, patch, sentinel

from sceptre.context import SceptreContext
from sceptre.stack import Stack
from sceptre.config.reader import ConfigReader
from sceptre.plan.plan import SceptrePlan


class TestSceptrePlan(object):

    def setup_method(self, test_method):
        self.patcher_SceptrePlan = patch("sceptre.plan.plan.SceptrePlan")
        self.stack = Stack(
            name='dev/app/stack', project_code=sentinel.project_code,
            template_path=sentinel.template_path, region=sentinel.region,
            profile=sentinel.profile, parameters={"key1": "val1"},
            sceptre_user_data=sentinel.sceptre_user_data, hooks={},
            s3_details=None, dependencies=sentinel.dependencies,
            role_arn=sentinel.role_arn, protected=False,
            tags={"tag1": "val1"}, external_name=sentinel.external_name,
            notifications=[sentinel.notification],
            on_failure=sentinel.on_failure,
            stack_timeout=sentinel.stack_timeout
        )
        self.mock_context = MagicMock(spec=SceptreContext)
        self.mock_config_reader = MagicMock(spec=ConfigReader)
        self.mock_context.project_path = sentinel.project_path
        self.mock_context.command_path = sentinel.command_path
        self.mock_context.config_file = sentinel.config_file
        self.mock_context.full_config_path.return_value =\
            sentinel.full_config_path
        self.mock_context.user_variables = {}
        self.mock_context.options = {}
        self.mock_context.no_colour = True
        self.mock_config_reader.context = self.mock_context

    def test_planner_executes_without_params(self):
        plan = MagicMock(spec=SceptrePlan)
        plan.context = self.mock_context
        plan.launch.return_value = sentinel.success
        result = plan.launch()
        plan.launch.assert_called_once_with()
        assert result == sentinel.success

    def test_planner_executes_with_params(self):
        plan = MagicMock(spec=SceptrePlan)
        plan.context = self.mock_context
        plan.launch.return_value = sentinel.success
        result = plan.launch('test-attribute')
        plan.launch.assert_called_once_with('test-attribute')
        assert result == sentinel.success

    def test_command_not_found_error_raised(self):
        with pytest.raises(AttributeError):
            plan = MagicMock(spec=SceptrePlan)
            plan.context = self.mock_context
            plan.invalid_command()
