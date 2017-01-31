# -*- coding: utf-8 -*-

from mock import Mock,  patch, MagicMock
import pytest
from sceptre.config import Config
from sceptre.hooks.asg_scheduled_actions import ASGScheduledActions
from sceptre.exceptions import InvalidHookArgumentValueError
from sceptre.exceptions import InvalidHookArgumentTypeError


class TestASGScheduledActions(object):
    def setup_method(self, test_method):
        self.mock_asg_scheduled_actions = ASGScheduledActions()

    def test_get_stack_resources_sends_correct_request(self):
        mock_environment_config = MagicMock(spec=Config)
        mock_environment_config.__getitem__.return_value = "project_code"
        mock_environment_config.environment_path = "path"
        self.mock_asg_scheduled_actions.environment_config =\
            mock_environment_config
        mock_stack_config = MagicMock(spec=Config)
        mock_stack_config.name = "stack"
        self.mock_asg_scheduled_actions.stack_config = mock_stack_config
        mock_connection_manager = Mock()
        mock_connection_manager.call.return_value = {
            "StackResources": [
                {
                    "ResourceType": "AWS::AutoScaling::AutoScalingGroup",
                    'PhysicalResourceId': 'cloudreach-examples-asg'
                }
            ]
        }
        self.mock_asg_scheduled_actions.\
            connection_manager = mock_connection_manager
        self.mock_asg_scheduled_actions\
            ._get_stack_resources()
        mock_connection_manager.call.\
            assert_called_with(
                service="cloudformation",
                command="describe_stack_resources",
                kwargs={
                    "StackName": "project_code-path-stack",
                }
            )

    @patch(
        "sceptre.hooks.asg_scheduled_actions"
        ".ASGScheduledActions._get_stack_resources"
    )
    def test_find_autoscaling_groups_with_stack_with_asgs(
        self, mock_get_stack_resources
    ):
        mock_get_stack_resources.return_value = [{
            'LogicalResourceId': 'AutoScalingGroup',
            'PhysicalResourceId': 'cloudreach-examples-asg',
            'ResourceStatus': 'CREATE_COMPLETE',
            'ResourceType': 'AWS::AutoScaling::AutoScalingGroup',
            'StackId': 'arn:aws:...',
            'StackName': 'cloudreach-examples-dev-vpc'
        }]
        response = self.mock_asg_scheduled_actions.\
            _find_autoscaling_groups()

        assert response == ["cloudreach-examples-asg"]

    @patch(
        "sceptre.hooks.asg_scheduled_actions"
        ".ASGScheduledActions._get_stack_resources"
    )
    def test_find_autoscaling_groups_with_stack_without_asgs(
        self, mock_get_stack_resources
    ):
        mock_get_stack_resources.return_value = []
        response = self.mock_asg_scheduled_actions.\
            _find_autoscaling_groups()

        assert response == []

    @patch(
        "sceptre.hooks.asg_scheduled_actions"
        ".ASGScheduledActions._find_autoscaling_groups"
    )
    def test_run_with_resume_argument(self, mock_find_autoscaling_groups):
        self.mock_asg_scheduled_actions.argument = u"resume"
        mock_find_autoscaling_groups.return_value = ["autoscaling_group_1"]
        self.mock_asg_scheduled_actions.connection_manager = Mock()
        self.mock_asg_scheduled_actions.run()
        self.mock_asg_scheduled_actions.connection_manager\
            .call.assert_called_once_with(
                service="autoscaling",
                command="resume_processes",
                kwargs={
                    "AutoScalingGroupName": "autoscaling_group_1",
                    "ScalingProcesses": [
                        "ScheduledActions"
                    ]
                }
            )

    @patch(
        "sceptre.hooks.asg_scheduled_actions"
        ".ASGScheduledActions._find_autoscaling_groups"
    )
    def test_run_with_suspend_argument(self, mock_find_autoscaling_groups):
        self.mock_asg_scheduled_actions.argument = u"suspend"
        mock_find_autoscaling_groups.return_value = ["autoscaling_group_1"]
        self.mock_asg_scheduled_actions.connection_manager = Mock()
        self.mock_asg_scheduled_actions.run()
        self.mock_asg_scheduled_actions.connection_manager\
            .call.assert_called_once_with(
                service="autoscaling",
                command="suspend_processes",
                kwargs={
                    "AutoScalingGroupName": "autoscaling_group_1",
                    "ScalingProcesses": [
                        "ScheduledActions"
                    ]
                }
            )

    @patch(
        "sceptre.hooks.asg_scheduled_actions"
        ".ASGScheduledActions._find_autoscaling_groups"
    )
    def test_run_with_invalid_string_argument(
        self, mock_find_autoscaling_groups
    ):
        self.mock_asg_scheduled_actions.argument = u"invalid_string"
        mock_find_autoscaling_groups.return_value = ["autoscaling_group_1"]
        self.mock_asg_scheduled_actions.connection_manager = Mock()
        with pytest.raises(InvalidHookArgumentValueError):
            self.mock_asg_scheduled_actions.run()

    @patch(
        "sceptre.hooks.asg_scheduled_actions"
        ".ASGScheduledActions._find_autoscaling_groups"
    )
    def test_run_with_non_string_argument(self, mock_find_autoscaling_groups):
        self.mock_asg_scheduled_actions.argument = 10
        mock_find_autoscaling_groups.return_value = ["autoscaling_group_1"]
        self.mock_asg_scheduled_actions.connection_manager = Mock()
        with pytest.raises(InvalidHookArgumentTypeError):
            self.mock_asg_scheduled_actions.run()
