# -*- coding: utf-8 -*-
import pytest
from mock import patch, MagicMock

from sceptre.exceptions import InvalidHookArgumentValueError
from sceptre.exceptions import InvalidHookArgumentSyntaxError
from sceptre.exceptions import InvalidHookArgumentTypeError

from sceptre.connection_manager import ConnectionManager
from sceptre.hooks.asg_scaling_processes import ASGScalingProcesses
from sceptre.stack import Stack


class TestASGScalingProcesses(object):
    def setup_method(self, test_method):
        self.stack = MagicMock(spec=Stack)
        self.stack.connection_manager = MagicMock(spec=ConnectionManager)
        self.stack.external_name = "external_name"
        self.asg_scaling_processes = ASGScalingProcesses(None, self.stack)

    def test_get_stack_resources_sends_correct_request(self):
        self.stack.connection_manager.call.return_value = {
            "StackResources": [
                {
                    "ResourceType": "AWS::AutoScaling::AutoScalingGroup",
                    'PhysicalResourceId': 'cloudreach-examples-asg'
                }
            ]
        }
        self.asg_scaling_processes._get_stack_resources()
        self.stack.connection_manager.call.assert_called_with(
                service="cloudformation",
                command="describe_stack_resources",
                kwargs={
                    "StackName": "external_name",
                }
            )

    @patch(
        "sceptre.hooks.asg_scaling_processes"
        ".ASGScalingProcesses._get_stack_resources"
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
        response = self.asg_scaling_processes._find_autoscaling_groups()

        assert response == ["cloudreach-examples-asg"]

    @patch(
        "sceptre.hooks.asg_scaling_processes"
        ".ASGScalingProcesses._get_stack_resources"
    )
    def test_find_autoscaling_groups_with_stack_without_asgs(
        self, mock_get_stack_resources
    ):
        mock_get_stack_resources.return_value = []
        response = self.asg_scaling_processes._find_autoscaling_groups()

        assert response == []

    @patch(
        "sceptre.hooks.asg_scaling_processes"
        ".ASGScalingProcesses._find_autoscaling_groups"
    )
    def test_run_with_resume_argument(self, mock_find_autoscaling_groups):
        self.asg_scaling_processes.argument = u"resume::ScheduledActions"
        mock_find_autoscaling_groups.return_value = ["autoscaling_group_1"]
        self.asg_scaling_processes.run()
        self.stack.connection_manager.call.assert_called_once_with(
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
        "sceptre.hooks.asg_scaling_processes"
        ".ASGScalingProcesses._find_autoscaling_groups"
    )
    def test_run_with_suspend_argument(self, mock_find_autoscaling_groups):
        self.asg_scaling_processes.argument = "suspend::ScheduledActions"
        mock_find_autoscaling_groups.return_value = ["autoscaling_group_1"]
        self.asg_scaling_processes.run()
        self.stack.connection_manager.call.assert_called_once_with(
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
        "sceptre.hooks.asg_scaling_processes"
        ".ASGScalingProcesses._find_autoscaling_groups"
    )
    def test_run_with_invalid_string_argument(
        self, mock_find_autoscaling_groups
    ):
        self.asg_scaling_processes.argument = u"invalid_string"
        mock_find_autoscaling_groups.return_value = ["autoscaling_group_1"]
        with pytest.raises(InvalidHookArgumentSyntaxError):
            self.asg_scaling_processes.run()

    @patch(
        "sceptre.hooks.asg_scaling_processes"
        ".ASGScalingProcesses._find_autoscaling_groups"
    )
    def test_run_with_unsupported_argument(self, mock_find_autoscaling_groups):
        self.asg_scaling_processes.argument = "start::Healthcheck"
        mock_find_autoscaling_groups.return_value = ["autoscaling_group_1"]
        with pytest.raises(InvalidHookArgumentValueError):
            self.asg_scaling_processes.run()

    @patch(
        "sceptre.hooks.asg_scaling_processes"
        ".ASGScalingProcesses._find_autoscaling_groups"
    )
    def test_run_with_non_string_argument(self, mock_find_autoscaling_groups):
        self.asg_scaling_processes.argument = 10
        mock_find_autoscaling_groups.return_value = ["autoscaling_group_1"]
        with pytest.raises(InvalidHookArgumentTypeError):
            self.asg_scaling_processes.run()
