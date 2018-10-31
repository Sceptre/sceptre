import pytest
from mock import Mock, patch, sentinel

from sceptre.stack import Stack
from sceptre.stack_group import StackGroup
from sceptre.plan.plan import SceptrePlan
from sceptre.plan.type import PlanType


class TestSceptrePlan(object):

    def setup_method(self, test_method):
        self.patcher_SceptrePlanner = patch("sceptre.plan.plan.SceptrePlanner")
        self.stack = Stack(
            name=sentinel.stack_name, project_code=sentinel.project_code,
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

        self.stack_group = StackGroup(
            path="path",
            options=sentinel.options
        )

    def test_planner_executes_without_params(self):
        plan = SceptrePlan('test/path', 'test-command', self.stack_group)
        plan.execute = Mock(name="execute")
        plan.execute.return_value = sentinel.success

        result = plan.execute()
        plan.execute.assert_called_once_with()
        assert result == sentinel.success

    def test_planner_executes_with_params(self):
        plan = SceptrePlan('test/path', 'test-command', self.stack_group)
        plan.execute = Mock(name='execute')
        plan.execute.return_value = sentinel.success

        result = plan.execute('test-attribute')
        plan.execute.assert_called_once_with('test-attribute')
        assert result == sentinel.success

    def test_stack_group_type_is_set(self):
        plan = SceptrePlan('test/path', 'test-command', self.stack_group)
        assert plan.plan_type == PlanType.STACK_GROUP

    def test_stack_type_is_set(self):
        plan = SceptrePlan('test/path', 'test-command', self.stack)
        assert plan.plan_type == PlanType.STACK

    def test_command_not_found_error_raised(self):
        with pytest.raises(AttributeError):
            plan = SceptrePlan('test/path', 'test-command', self.stack)
            plan.execute()

    def test_command_not_callable_error_raised(self):
        with pytest.raises(TypeError):
            plan = SceptrePlan('test/path', 'name', self.stack)
            plan.execute()
