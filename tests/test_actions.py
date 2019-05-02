# -*- coding: utf-8 -*-

import pytest
from mock import patch, sentinel, Mock, call

import datetime
from dateutil.tz import tzutc

from botocore.exceptions import ClientError

from sceptre.stack import Stack
from sceptre.plan.actions import StackActions
from sceptre.template import Template
from sceptre.stack_status import StackStatus
from sceptre.stack_status import StackChangeSetStatus
from sceptre.exceptions import CannotUpdateFailedStackError
from sceptre.exceptions import UnknownStackStatusError
from sceptre.exceptions import UnknownStackChangeSetStatusError
from sceptre.exceptions import StackDoesNotExistError
from sceptre.exceptions import ProtectedStackError


class TestStackActions(object):

    def setup_method(self, test_method):
        self.patcher_connection_manager = patch(
            "sceptre.plan.actions.ConnectionManager"
        )
        self.mock_ConnectionManager = self.patcher_connection_manager.start()
        self.stack = Stack(
            name='prod/app/stack', project_code=sentinel.project_code,
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
        self.actions = StackActions(self.stack)
        self.template = Template(
            "fixtures/templates", self.stack.sceptre_user_data,
            self.actions.connection_manager, self.stack.s3_details
        )
        self.stack._template = self.template

    def teardown_method(self, test_method):
        self.patcher_connection_manager.stop()

    @patch("sceptre.stack.Template")
    def test_template_loads_template(self, mock_Template):
        self.stack._template = None
        mock_Template.return_value = sentinel.template
        response = self.stack.template

        mock_Template.assert_called_once_with(
            path=sentinel.template_path,
            sceptre_user_data=sentinel.sceptre_user_data,
            connection_manager=self.stack.connection_manager,
            s3_details=None
        )
        assert response == sentinel.template

    def test_template_returns_template_if_it_exists(self):
        self.actions.stack._template = sentinel.template
        response = self.actions.stack._template
        assert response == sentinel.template

    def test_external_name_with_custom_stack_name(self):
        stack = Stack(
            name="stack_name", project_code="project_code",
            template_path="template_path", region="region",
            external_name="external_name"
        )

        assert stack.external_name == "external_name"

    @patch("sceptre.plan.actions.StackActions._wait_for_completion")
    @patch("sceptre.plan.actions.StackActions._get_stack_timeout")
    def test_create_sends_correct_request(
            self, mock_get_stack_timeout, mock_wait_for_completion
    ):
        self.template._body = sentinel.template

        mock_get_stack_timeout.return_value = {
            "TimeoutInMinutes": sentinel.timeout
        }

        self.actions.create()
        self.actions.connection_manager.call.assert_called_with(
            service="cloudformation",
            command="create_stack",
            kwargs={
                "StackName": sentinel.external_name,
                "TemplateBody": sentinel.template,
                "Parameters": [{
                    "ParameterKey": "key1",
                    "ParameterValue": "val1"
                }],
                "Capabilities": ['CAPABILITY_IAM',
                                 'CAPABILITY_NAMED_IAM',
                                 'CAPABILITY_AUTO_EXPAND'],
                "RoleARN": sentinel.role_arn,
                "NotificationARNs": [sentinel.notification],
                "Tags": [
                    {"Key": "tag1", "Value": "val1"}
                ],
                "OnFailure": sentinel.on_failure,
                "TimeoutInMinutes": sentinel.timeout
            }
        )
        mock_wait_for_completion.assert_called_once_with()

    @patch("sceptre.plan.actions.StackActions._wait_for_completion")
    def test_create_sends_correct_request_no_notifications(
        self, mock_wait_for_completion
    ):
        self.actions.stack._template = Mock(spec=Template)
        self.actions.stack._template.get_boto_call_parameter.return_value = {
            "Template": sentinel.template
        }
        self.actions.stack.notifications = []

        self.actions.create()
        self.actions.connection_manager.call.assert_called_with(
            service="cloudformation",
            command="create_stack",
            kwargs={
                "StackName": sentinel.external_name,
                "Template": sentinel.template,
                "Parameters": [{
                    "ParameterKey": "key1",
                    "ParameterValue": "val1"
                }],
                "Capabilities": ['CAPABILITY_IAM',
                                 'CAPABILITY_NAMED_IAM',
                                 'CAPABILITY_AUTO_EXPAND'],
                "RoleARN": sentinel.role_arn,
                "NotificationARNs": [],
                "Tags": [
                    {"Key": "tag1", "Value": "val1"}
                ],
                "OnFailure": sentinel.on_failure,
                "TimeoutInMinutes": sentinel.stack_timeout
            }
        )
        mock_wait_for_completion.assert_called_once_with()

    @patch("sceptre.plan.actions.StackActions._wait_for_completion")
    def test_create_sends_correct_request_with_no_failure_no_timeout(
        self, mock_wait_for_completion
    ):
        self.template._body = sentinel.template
        self.actions.stack.on_failure = None
        self.actions.stack.stack_timeout = 0

        self.actions.create()

        self.actions.connection_manager.call.assert_called_with(
            service="cloudformation",
            command="create_stack",
            kwargs={
                "StackName": sentinel.external_name,
                "TemplateBody": sentinel.template,
                "Parameters": [{
                    "ParameterKey": "key1",
                    "ParameterValue": "val1"
                }],
                "Capabilities": ['CAPABILITY_IAM',
                                 'CAPABILITY_NAMED_IAM',
                                 'CAPABILITY_AUTO_EXPAND'],
                "RoleARN": sentinel.role_arn,
                "NotificationARNs": [sentinel.notification],
                "Tags": [
                    {"Key": "tag1", "Value": "val1"}
                ]
            }
        )
        mock_wait_for_completion.assert_called_once_with()

    @patch("sceptre.plan.actions.StackActions._wait_for_completion")
    def test_update_sends_correct_request(self, mock_wait_for_completion):
        self.actions.stack._template = Mock(spec=Template)
        self.actions.stack._template.get_boto_call_parameter.return_value = {
            "Template": sentinel.template
        }

        self.actions.update()
        self.actions.connection_manager.call.assert_called_with(
            service="cloudformation",
            command="update_stack",
            kwargs={
                "StackName": sentinel.external_name,
                "Template": sentinel.template,
                "Parameters": [{
                    "ParameterKey": "key1",
                    "ParameterValue": "val1"
                }],
                "Capabilities": ['CAPABILITY_IAM',
                                 'CAPABILITY_NAMED_IAM',
                                 'CAPABILITY_AUTO_EXPAND'],
                "RoleARN": sentinel.role_arn,
                "NotificationARNs": [sentinel.notification],
                "Tags": [
                    {"Key": "tag1", "Value": "val1"}
                ]
            }
        )
        mock_wait_for_completion.assert_called_once_with(
            sentinel.stack_timeout
        )

    @patch("sceptre.plan.actions.StackActions._wait_for_completion")
    def test_update_cancels_after_timeout(self, mock_wait_for_completion):
        self.actions.stack._template = Mock(spec=Template)
        self.actions.stack._template.get_boto_call_parameter.return_value = {
            "Template": sentinel.template
        }
        mock_wait_for_completion.return_value = StackStatus.IN_PROGRESS

        self.actions.update()
        calls = [
            call(
                service="cloudformation",
                command="update_stack",
                kwargs={
                    "StackName": sentinel.external_name,
                    "Template": sentinel.template,
                    "Parameters": [{
                        "ParameterKey": "key1",
                        "ParameterValue": "val1"
                    }],
                    "Capabilities": ['CAPABILITY_IAM',
                                     'CAPABILITY_NAMED_IAM',
                                     'CAPABILITY_AUTO_EXPAND'],
                    "RoleARN": sentinel.role_arn,
                    "NotificationARNs": [sentinel.notification],
                    "Tags": [
                        {"Key": "tag1", "Value": "val1"}
                    ]
                }),
            call(
                service="cloudformation",
                command="cancel_update_stack",
                kwargs={"StackName": sentinel.external_name})
        ]
        self.actions.connection_manager.call.assert_has_calls(calls)
        mock_wait_for_completion.assert_has_calls(
            [call(sentinel.stack_timeout), call()]
        )

    @patch("sceptre.plan.actions.StackActions._wait_for_completion")
    def test_update_sends_correct_request_no_notification(
            self, mock_wait_for_completion
    ):
        self.actions.stack._template = Mock(spec=Template)
        self.actions.stack._template.get_boto_call_parameter.return_value = {
            "Template": sentinel.template
        }

        self.actions.stack.notifications = []
        self.actions.update()
        self.actions.connection_manager.call.assert_called_with(
            service="cloudformation",
            command="update_stack",
            kwargs={
                "StackName": sentinel.external_name,
                "Template": sentinel.template,
                "Parameters": [{
                    "ParameterKey": "key1",
                    "ParameterValue": "val1"
                }],
                "Capabilities": ['CAPABILITY_IAM',
                                 'CAPABILITY_NAMED_IAM',
                                 'CAPABILITY_AUTO_EXPAND'],
                "RoleARN": sentinel.role_arn,
                "NotificationARNs": [],
                "Tags": [
                    {"Key": "tag1", "Value": "val1"}
                ]
            }
        )
        mock_wait_for_completion.assert_called_once_with(
            sentinel.stack_timeout
        )

    @patch("sceptre.plan.actions.StackActions._wait_for_completion")
    def test_cancel_update_sends_correct_request(
            self, mock_wait_for_completion
    ):
        self.actions.cancel_stack_update()
        self.actions.connection_manager.call.assert_called_once_with(
            service="cloudformation",
            command="cancel_update_stack",
            kwargs={"StackName": sentinel.external_name}
        )
        mock_wait_for_completion.assert_called_once_with()

    @patch("sceptre.plan.actions.StackActions.create")
    @patch("sceptre.plan.actions.StackActions._get_status")
    def test_launch_with_stack_that_does_not_exist(
            self, mock_get_status, mock_create
    ):
        mock_get_status.side_effect = StackDoesNotExistError()
        mock_create.return_value = sentinel.launch_response
        response = self.actions.launch()
        mock_create.assert_called_once_with()
        assert response == sentinel.launch_response

    @patch("sceptre.plan.actions.StackActions.create")
    @patch("sceptre.plan.actions.StackActions.delete")
    @patch("sceptre.plan.actions.StackActions._get_status")
    def test_launch_with_stack_that_failed_to_create(
            self, mock_get_status, mock_delete, mock_create
    ):
        mock_get_status.return_value = "CREATE_FAILED"
        mock_create.return_value = sentinel.launch_response
        response = self.actions.launch()
        mock_delete.assert_called_once_with()
        mock_create.assert_called_once_with()
        assert response == sentinel.launch_response

    @patch("sceptre.plan.actions.StackActions.update")
    @patch("sceptre.plan.actions.StackActions._get_status")
    def test_launch_with_complete_stack_with_updates_to_perform(
            self, mock_get_status, mock_update
    ):
        mock_get_status.return_value = "CREATE_COMPLETE"
        mock_update.return_value = sentinel.launch_response
        response = self.actions.launch()
        mock_update.assert_called_once_with()
        assert response == sentinel.launch_response

    @patch("sceptre.plan.actions.StackActions.update")
    @patch("sceptre.plan.actions.StackActions._get_status")
    def test_launch_with_complete_stack_with_no_updates_to_perform(
            self, mock_get_status, mock_update
    ):
        mock_get_status.return_value = "CREATE_COMPLETE"
        mock_update.side_effect = ClientError(
            {
                "Error": {
                    "Code": "NoUpdateToPerformError",
                    "Message": "No updates are to be performed."
                }
            },
            sentinel.operation
        )
        response = self.actions.launch()
        mock_update.assert_called_once_with()
        assert response == StackStatus.COMPLETE

    @patch("sceptre.plan.actions.StackActions.update")
    @patch("sceptre.plan.actions.StackActions._get_status")
    def test_launch_with_complete_stack_with_unknown_client_error(
            self, mock_get_status, mock_update
    ):
        mock_get_status.return_value = "CREATE_COMPLETE"
        mock_update.side_effect = ClientError(
            {
                "Error": {
                    "Code": "Boom!",
                    "Message": "Boom!"
                }
            },
            sentinel.operation
        )
        with pytest.raises(ClientError):
            self.actions.launch()

    @patch("sceptre.plan.actions.StackActions._get_status")
    def test_launch_with_in_progress_stack(self, mock_get_status):
        mock_get_status.return_value = "CREATE_IN_PROGRESS"
        response = self.actions.launch()
        assert response == StackStatus.IN_PROGRESS

    @patch("sceptre.plan.actions.StackActions._get_status")
    def test_launch_with_failed_stack(self, mock_get_status):
        mock_get_status.return_value = "UPDATE_FAILED"
        with pytest.raises(CannotUpdateFailedStackError):
            response = self.actions.launch()
            assert response == StackStatus.FAILED

    @patch("sceptre.plan.actions.StackActions._get_status")
    def test_launch_with_unknown_stack_status(self, mock_get_status):
        mock_get_status.return_value = "UNKNOWN_STATUS"
        with pytest.raises(UnknownStackStatusError):
            self.actions.launch()

    @patch("sceptre.plan.actions.StackActions._wait_for_completion")
    @patch("sceptre.plan.actions.StackActions._get_status")
    def test_delete_with_created_stack(
            self, mock_get_status, mock_wait_for_completion
    ):
        mock_get_status.return_value = "CREATE_COMPLETE"

        self.actions.delete()
        self.actions.connection_manager.call.assert_called_with(
            service="cloudformation",
            command="delete_stack",
            kwargs={
                "StackName": sentinel.external_name,
                "RoleARN": sentinel.role_arn
            }
        )

    @patch("sceptre.plan.actions.StackActions._wait_for_completion")
    @patch("sceptre.plan.actions.StackActions._get_status")
    def test_delete_when_wait_for_completion_raises_stack_does_not_exist_error(
            self, mock_get_status, mock_wait_for_completion
    ):
        mock_get_status.return_value = "CREATE_COMPLETE"
        mock_wait_for_completion.side_effect = StackDoesNotExistError()
        status = self.actions.delete()
        assert status == StackStatus.COMPLETE

    @patch("sceptre.plan.actions.StackActions._wait_for_completion")
    @patch("sceptre.plan.actions.StackActions._get_status")
    def test_delete_when_wait_for_completion_raises_non_existent_client_error(
            self, mock_get_status, mock_wait_for_completion
    ):
        mock_get_status.return_value = "CREATE_COMPLETE"
        mock_wait_for_completion.side_effect = ClientError(
            {
                "Error": {
                    "Code": "DoesNotExistException",
                    "Message": "Stack does not exist"
                }
            },
            sentinel.operation
        )
        status = self.actions.delete()
        assert status == StackStatus.COMPLETE

    @patch("sceptre.plan.actions.StackActions._wait_for_completion")
    @patch("sceptre.plan.actions.StackActions._get_status")
    def test_delete_when_wait_for_completion_raises_unexpected_client_error(
            self, mock_get_status, mock_wait_for_completion
    ):
        mock_get_status.return_value = "CREATE_COMPLETE"
        mock_wait_for_completion.side_effect = ClientError(
            {
                "Error": {
                    "Code": "DoesNotExistException",
                    "Message": "Boom"
                }
            },
            sentinel.operation
        )
        with pytest.raises(ClientError):
            self.actions.delete()

    @patch("sceptre.plan.actions.StackActions._wait_for_completion")
    @patch("sceptre.plan.actions.StackActions._get_status")
    def test_delete_with_non_existent_stack(
            self, mock_get_status, mock_wait_for_completion
    ):
        mock_get_status.side_effect = StackDoesNotExistError()
        status = self.actions.delete()
        assert status == StackStatus.COMPLETE

    def test_describe_stack_sends_correct_request(self):
        self.actions.describe()
        self.actions.connection_manager.call.assert_called_with(
            service="cloudformation",
            command="describe_stacks",
            kwargs={"StackName": sentinel.external_name}
        )

    def test_describe_events_sends_correct_request(self):
        self.actions.describe_events()
        self.actions.connection_manager.call.assert_called_with(
            service="cloudformation",
            command="describe_stack_events",
            kwargs={"StackName": sentinel.external_name}
        )

    def test_describe_resources_sends_correct_request(self):
        self.actions.connection_manager.call.return_value = {
            "StackResources": [
                {
                    "LogicalResourceId": sentinel.logical_resource_id,
                    "PhysicalResourceId": sentinel.physical_resource_id,
                    "OtherParam": sentinel.other_param
                }
            ]
        }
        response = self.actions.describe_resources()
        self.actions.connection_manager.call.assert_called_with(
            service="cloudformation",
            command="describe_stack_resources",
            kwargs={"StackName": sentinel.external_name}
        )
        assert response == {self.stack.name: [
            {
                "LogicalResourceId": sentinel.logical_resource_id,
                "PhysicalResourceId": sentinel.physical_resource_id
            }
        ]}

    @patch("sceptre.plan.actions.StackActions._describe")
    def test_describe_outputs_sends_correct_request(self, mock_describe):
        mock_describe.return_value = {
            "Stacks": [{
                "Outputs": sentinel.outputs
            }]
        }
        response = self.actions.describe_outputs()
        mock_describe.assert_called_once_with()
        assert response == {self.stack.name: sentinel.outputs}

    @patch("sceptre.plan.actions.StackActions._describe")
    def test_describe_outputs_handles_stack_with_no_outputs(
            self, mock_describe
    ):
        mock_describe.return_value = {
            "Stacks": [{}]
        }
        response = self.actions.describe_outputs()
        assert response == {self.stack.name: []}

    def test_continue_update_rollback_sends_correct_request(self):
        self.actions.continue_update_rollback()
        self.actions.connection_manager.call.assert_called_with(
            service="cloudformation",
            command="continue_update_rollback",
            kwargs={
                "StackName": sentinel.external_name,
                "RoleARN": sentinel.role_arn
            }
        )

    def test_set_stack_policy_sends_correct_request(self):
        self.actions.set_policy("tests/fixtures/stack_policies/unlock.json")
        self.actions.connection_manager.call.assert_called_with(
            service="cloudformation",
            command="set_stack_policy",
            kwargs={
                "StackName": sentinel.external_name,
                "StackPolicyBody": """{
  "Statement" : [
    {
      "Effect" : "Allow",
      "Action" : "Update:*",
      "Principal": "*",
      "Resource" : "*"
    }
  ]
}
"""
            }
        )

    @patch("sceptre.plan.actions.json")
    def test_get_stack_policy_sends_correct_request(self, mock_Json):
        mock_Json.loads.return_value = '{}'
        mock_Json.dumps.return_value = '{}'
        response = self.actions.get_policy()
        self.actions.connection_manager.call.assert_called_with(
            service="cloudformation",
            command="get_stack_policy",
            kwargs={
                "StackName": sentinel.external_name
            }
        )

        assert response == {'prod/app/stack': '{}'}

    def test_create_change_set_sends_correct_request(self):
        self.template._body = sentinel.template

        self.actions.create_change_set(sentinel.change_set_name)
        self.actions.connection_manager.call.assert_called_with(
            service="cloudformation",
            command="create_change_set",
            kwargs={
                "StackName": sentinel.external_name,
                "TemplateBody": sentinel.template,
                "Parameters": [{
                    "ParameterKey": "key1",
                    "ParameterValue": "val1"
                }],
                "Capabilities": ['CAPABILITY_IAM',
                                 'CAPABILITY_NAMED_IAM',
                                 'CAPABILITY_AUTO_EXPAND'],
                "ChangeSetName": sentinel.change_set_name,
                "RoleARN": sentinel.role_arn,
                "NotificationARNs": [sentinel.notification],
                "Tags": [
                    {"Key": "tag1", "Value": "val1"}
                ]
            }
        )

    def test_create_change_set_sends_correct_request_no_notifications(self):
        self.actions.stack._template = Mock(spec=Template)
        self.actions.stack._template.get_boto_call_parameter.return_value = {
            "Template": sentinel.template
        }
        self.actions.stack.notifications = []

        self.actions.create_change_set(sentinel.change_set_name)
        self.actions.connection_manager.call.assert_called_with(
            service="cloudformation",
            command="create_change_set",
            kwargs={
                "StackName": sentinel.external_name,
                "Template": sentinel.template,
                "Parameters": [{
                    "ParameterKey": "key1",
                    "ParameterValue": "val1"
                }],
                "Capabilities": ['CAPABILITY_IAM',
                                 'CAPABILITY_NAMED_IAM',
                                 'CAPABILITY_AUTO_EXPAND'],
                "ChangeSetName": sentinel.change_set_name,
                "RoleARN": sentinel.role_arn,
                "NotificationARNs": [],
                "Tags": [
                    {"Key": "tag1", "Value": "val1"}
                ]
            }
        )

    def test_delete_change_set_sends_correct_request(self):
        self.actions.delete_change_set(sentinel.change_set_name)
        self.actions.connection_manager.call.assert_called_with(
            service="cloudformation",
            command="delete_change_set",
            kwargs={
                "ChangeSetName": sentinel.change_set_name,
                "StackName": sentinel.external_name
            }
        )

    def test_describe_change_set_sends_correct_request(self):
        self.actions.describe_change_set(sentinel.change_set_name)
        self.actions.connection_manager.call.assert_called_with(
            service="cloudformation",
            command="describe_change_set",
            kwargs={
                "ChangeSetName": sentinel.change_set_name,
                "StackName": sentinel.external_name
            }
        )

    @patch("sceptre.plan.actions.StackActions._wait_for_completion")
    def test_execute_change_set_sends_correct_request(
        self, mock_wait_for_completion
    ):
        self.actions.execute_change_set(sentinel.change_set_name)
        self.actions.connection_manager.call.assert_called_with(
            service="cloudformation",
            command="execute_change_set",
            kwargs={
                "ChangeSetName": sentinel.change_set_name,
                "StackName": sentinel.external_name
            }
        )
        mock_wait_for_completion.assert_called_once_with()

    def test_list_change_sets_sends_correct_request(self):
        self.actions.list_change_sets()
        self.actions.connection_manager.call.assert_called_with(
            service="cloudformation",
            command="list_change_sets",
            kwargs={"StackName": sentinel.external_name}
        )

    @patch("sceptre.plan.actions.StackActions.set_policy")
    @patch("os.path.join")
    def test_lock_calls_set_stack_policy_with_policy(
            self, mock_join, mock_set_policy
    ):
        mock_join.return_value = "tests/fixtures/stack_policies/lock.json"
        self.actions.lock()
        mock_set_policy.assert_called_once_with(
            "tests/fixtures/stack_policies/lock.json"
        )

    @patch("sceptre.plan.actions.StackActions.set_policy")
    @patch("os.path.join")
    def test_unlock_calls_set_stack_policy_with_policy(
            self, mock_join, mock_set_policy
    ):
        mock_join.return_value = "tests/fixtures/stack_policies/unlock.json"
        self.actions.unlock()
        mock_set_policy.assert_called_once_with(
            "tests/fixtures/stack_policies/unlock.json"
        )

    def test_format_parameters_with_sting_values(self):
        parameters = {
            "key1": "value1",
            "key2": "value2",
            "key3": "value3"
        }
        formatted_parameters = self.actions._format_parameters(parameters)
        sorted_formatted_parameters = sorted(
            formatted_parameters,
            key=lambda x: x["ParameterKey"]
        )
        assert sorted_formatted_parameters == [
            {"ParameterKey": "key1", "ParameterValue": "value1"},
            {"ParameterKey": "key2", "ParameterValue": "value2"},
            {"ParameterKey": "key3", "ParameterValue": "value3"}
        ]

    def test_format_parameters_with_none_values(self):
        parameters = {
            "key1": None,
            "key2": None,
            "key3": None
        }
        formatted_parameters = self.actions._format_parameters(parameters)
        sorted_formatted_parameters = sorted(
            formatted_parameters,
            key=lambda x: x["ParameterKey"]
        )
        assert sorted_formatted_parameters == []

    def test_format_parameters_with_none_and_string_values(self):
        parameters = {
            "key1": "value1",
            "key2": None,
            "key3": "value3"
        }
        formatted_parameters = self.actions._format_parameters(parameters)
        sorted_formatted_parameters = sorted(
            formatted_parameters,
            key=lambda x: x["ParameterKey"]
        )
        assert sorted_formatted_parameters == [
            {"ParameterKey": "key1", "ParameterValue": "value1"},
            {"ParameterKey": "key3", "ParameterValue": "value3"}
        ]

    def test_format_parameters_with_list_values(self):
        parameters = {
            "key1": ["value1", "value2", "value3"],
            "key2": ["value4", "value5", "value6"],
            "key3": ["value7", "value8", "value9"]
        }
        formatted_parameters = self.actions._format_parameters(parameters)
        sorted_formatted_parameters = sorted(
            formatted_parameters,
            key=lambda x: x["ParameterKey"]
        )
        assert sorted_formatted_parameters == [
            {"ParameterKey": "key1", "ParameterValue": "value1,value2,value3"},
            {"ParameterKey": "key2", "ParameterValue": "value4,value5,value6"},
            {"ParameterKey": "key3", "ParameterValue": "value7,value8,value9"}
        ]

    def test_format_parameters_with_none_and_list_values(self):
        parameters = {
            "key1": ["value1", "value2", "value3"],
            "key2": None,
            "key3": ["value7", "value8", "value9"]
        }
        formatted_parameters = self.actions._format_parameters(parameters)
        sorted_formatted_parameters = sorted(
            formatted_parameters,
            key=lambda x: x["ParameterKey"]
        )
        assert sorted_formatted_parameters == [
            {"ParameterKey": "key1", "ParameterValue": "value1,value2,value3"},
            {"ParameterKey": "key3", "ParameterValue": "value7,value8,value9"}
        ]

    def test_format_parameters_with_list_and_string_values(self):
        parameters = {
            "key1": ["value1", "value2", "value3"],
            "key2": "value4",
            "key3": ["value5", "value6", "value7"]
        }
        formatted_parameters = self.actions._format_parameters(parameters)
        sorted_formatted_parameters = sorted(
            formatted_parameters,
            key=lambda x: x["ParameterKey"]
        )
        assert sorted_formatted_parameters == [
            {"ParameterKey": "key1", "ParameterValue": "value1,value2,value3"},
            {"ParameterKey": "key2", "ParameterValue": "value4"},
            {"ParameterKey": "key3", "ParameterValue": "value5,value6,value7"}
        ]

    def test_format_parameters_with_none_list_and_string_values(self):
        parameters = {
            "key1": ["value1", "value2", "value3"],
            "key2": "value4",
            "key3": None
        }
        formatted_parameters = self.actions._format_parameters(parameters)
        sorted_formatted_parameters = sorted(
            formatted_parameters,
            key=lambda x: x["ParameterKey"]
        )
        assert sorted_formatted_parameters == [
            {"ParameterKey": "key1", "ParameterValue": "value1,value2,value3"},
            {"ParameterKey": "key2", "ParameterValue": "value4"},
        ]

    @patch("sceptre.plan.actions.StackActions._describe")
    def test_get_status_with_created_stack(self, mock_describe):
        mock_describe.return_value = {
            "Stacks": [{"StackStatus": "CREATE_COMPLETE"}]
        }
        status = self.actions.get_status()
        assert status == "CREATE_COMPLETE"

    @patch("sceptre.plan.actions.StackActions._describe")
    def test_get_status_with_non_existent_stack(self, mock_describe):
        mock_describe.side_effect = ClientError(
            {
                "Error": {
                    "Code": "DoesNotExistException",
                    "Message": "Stack does not exist"
                }
            },
            sentinel.operation
        )
        assert self.actions.get_status() == "PENDING"

    @patch("sceptre.plan.actions.StackActions._describe")
    def test_get_status_with_unknown_clinet_error(self, mock_describe):
        mock_describe.side_effect = ClientError(
            {
                "Error": {
                    "Code": "DoesNotExistException",
                    "Message": "Boom!"
                }
            },
            sentinel.operation
        )
        with pytest.raises(ClientError):
            self.actions.get_status()

    def test_get_role_arn_without_role(self):
        self.actions.stack.role_arn = None
        assert self.actions._get_role_arn() == {}

    def test_get_role_arn_with_role(self):
        assert self.actions._get_role_arn() == {"RoleARN": sentinel.role_arn}

    def test_protect_execution_without_protection(self):
        # Function should do nothing if protect == False
        self.actions._protect_execution()

    def test_protect_execution_without_explicit_protection(self):
        self.actions._protect_execution()

    def test_protect_execution_with_protection(self):
        self.actions.stack.protected = True
        with pytest.raises(ProtectedStackError):
            self.actions._protect_execution()

    @patch("sceptre.plan.actions.StackActions._log_new_events")
    @patch("sceptre.plan.actions.StackActions._get_status")
    @patch("sceptre.plan.actions.StackActions._get_simplified_status")
    def test_wait_for_completion_calls_log_new_events(
            self, mock_get_simplified_status, mock_get_status,
            mock_log_new_events
    ):
        mock_get_simplified_status.return_value = StackStatus.COMPLETE

        self.actions._wait_for_completion()
        mock_log_new_events.assert_called_once_with()

    @pytest.mark.parametrize("test_input,expected", [
        ("ROLLBACK_COMPLETE", StackStatus.FAILED),
        ("STACK_COMPLETE", StackStatus.COMPLETE),
        ("STACK_IN_PROGRESS", StackStatus.IN_PROGRESS),
        ("STACK_FAILED", StackStatus.FAILED)
    ])
    def test_get_simplified_status_with_known_stack_statuses(
            self, test_input, expected
    ):
        response = self.actions._get_simplified_status(test_input)
        assert response == expected

    def test_get_simplified_status_with_stack_in_unknown_state(self):
        with pytest.raises(UnknownStackStatusError):
            self.actions._get_simplified_status("UNKOWN_STATUS")

    @patch("sceptre.plan.actions.StackActions.describe_events")
    def test_log_new_events_calls_describe_events(self, mock_describe_events):
        mock_describe_events.return_value = {
            "StackEvents": []
        }
        self.actions._log_new_events()
        self.actions.describe_events.assert_called_once_with()

    @patch("sceptre.plan.actions.StackActions.describe_events")
    def test_log_new_events_prints_correct_event(self, mock_describe_events):
        self.actions.stack.name = "stack-name"
        mock_describe_events.return_value = {
            "StackEvents": [
                {
                    "Timestamp": datetime.datetime(
                        2016, 3, 15, 14, 2, 0, 0, tzinfo=tzutc()
                    ),
                    "LogicalResourceId": "id-2",
                    "ResourceType": "type-2",
                    "ResourceStatus": "resource-status"
                },
                {
                    "Timestamp": datetime.datetime(
                        2016, 3, 15, 14, 1, 0, 0, tzinfo=tzutc()
                    ),
                    "LogicalResourceId": "id-1",
                    "ResourceType": "type-1",
                    "ResourceStatus": "resource",
                    "ResourceStatusReason": "User Initiated"
                }
            ]
        }
        self.actions.most_recent_event_datetime = (
            datetime.datetime(2016, 3, 15, 14, 0, 0, 0, tzinfo=tzutc())
        )
        self.actions._log_new_events()

    @patch("sceptre.plan.actions.StackActions._get_cs_status")
    def test_wait_for_cs_completion_calls_get_cs_status(
        self, mock_get_cs_status
    ):
        mock_get_cs_status.side_effect = [
            StackChangeSetStatus.PENDING, StackChangeSetStatus.READY
        ]

        self.actions.wait_for_cs_completion(sentinel.change_set_name)
        mock_get_cs_status.assert_called_with(sentinel.change_set_name)

    @patch("sceptre.plan.actions.StackActions.describe_change_set")
    def test_get_cs_status_handles_all_statuses(
        self, mock_describe_change_set
    ):
        scss = StackChangeSetStatus
        return_values = {                                                                                                     # NOQA
                 "Status":    ('CREATE_PENDING', 'CREATE_IN_PROGRESS', 'CREATE_COMPLETE', 'DELETE_COMPLETE', 'FAILED'),       # NOQA
        "ExecutionStatus": {                                                                                                  # NOQA
        'UNAVAILABLE':         (scss.PENDING,     scss.PENDING,         scss.PENDING,      scss.DEFUNCT,      scss.DEFUNCT),  # NOQA
        'AVAILABLE':           (scss.PENDING,     scss.PENDING,         scss.READY,        scss.DEFUNCT,      scss.DEFUNCT),  # NOQA
        'EXECUTE_IN_PROGRESS': (scss.DEFUNCT,     scss.DEFUNCT,         scss.DEFUNCT,      scss.DEFUNCT,      scss.DEFUNCT),  # NOQA
        'EXECUTE_COMPLETE':    (scss.DEFUNCT,     scss.DEFUNCT,         scss.DEFUNCT,      scss.DEFUNCT,      scss.DEFUNCT),  # NOQA
        'EXECUTE_FAILED':      (scss.DEFUNCT,     scss.DEFUNCT,         scss.DEFUNCT,      scss.DEFUNCT,      scss.DEFUNCT),  # NOQA
        'OBSOLETE':            (scss.DEFUNCT,     scss.DEFUNCT,         scss.DEFUNCT,      scss.DEFUNCT,      scss.DEFUNCT),  # NOQA
        }                                                                                                                     # NOQA
        }                                                                                                                     # NOQA

        for i, status in enumerate(return_values['Status']):
            for exec_status, returns in \
                    return_values['ExecutionStatus'].items():
                mock_describe_change_set.return_value = {
                    "Status": status,
                    "ExecutionStatus": exec_status
                }
                response = self.actions._get_cs_status(
                    sentinel.change_set_name
                )
                assert response == returns[i]

        for status in return_values['Status']:
            mock_describe_change_set.return_value = {
                "Status": status,
                "ExecutionStatus": 'UNKOWN_STATUS'
            }
            with pytest.raises(UnknownStackChangeSetStatusError):
                self.actions._get_cs_status(sentinel.change_set_name)

        for exec_status in return_values['ExecutionStatus'].keys():
            mock_describe_change_set.return_value = {
                "Status": 'UNKOWN_STATUS',
                "ExecutionStatus": exec_status
            }
            with pytest.raises(UnknownStackChangeSetStatusError):
                self.actions._get_cs_status(sentinel.change_set_name)

        mock_describe_change_set.return_value = {
            "Status": 'UNKOWN_STATUS',
            "ExecutionStatus": 'UNKOWN_STATUS',
        }
        with pytest.raises(UnknownStackChangeSetStatusError):
            self.actions._get_cs_status(sentinel.change_set_name)

    @patch("sceptre.plan.actions.StackActions.describe_change_set")
    def test_get_cs_status_raises_unexpected_exceptions(
        self, mock_describe_change_set
    ):
        mock_describe_change_set.side_effect = ClientError(
            {
                "Error": {
                    "Code": "ChangeSetNotFound",
                    "Message": "ChangeSet [*] does not exist"
                }
            },
            sentinel.operation
        )
        with pytest.raises(ClientError):
            self.actions._get_cs_status(sentinel.change_set_name)
