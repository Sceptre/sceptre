# -*- coding: utf-8 -*-
import datetime
import json
from unittest.mock import patch, sentinel, Mock, call, ANY

import pytest
from botocore.exceptions import ClientError
from dateutil.tz import tzutc

from sceptre.exceptions import (
    CannotUpdateFailedStackError,
    ProtectedStackError,
    StackDoesNotExistError,
    UnknownStackChangeSetStatusError,
    UnknownStackStatusError,
)
from sceptre.plan.actions import StackActions
from sceptre.stack import Stack
from sceptre.stack_status import StackChangeSetStatus, StackStatus
from sceptre.template import Template


class TestStackActions(object):
    def setup_method(self, test_method):
        self.patcher_connection_manager = patch(
            "sceptre.plan.actions.ConnectionManager"
        )
        self.mock_ConnectionManager = self.patcher_connection_manager.start()
        self.stack = Stack(
            name="prod/app/stack",
            project_code=sentinel.project_code,
            template_path=sentinel.template_path,
            region=sentinel.region,
            profile=sentinel.profile,
            parameters={"key1": "val1"},
            sceptre_user_data=sentinel.sceptre_user_data,
            hooks={},
            s3_details=None,
            dependencies=sentinel.dependencies,
            role_arn=sentinel.role_arn,
            protected=False,
            tags={"tag1": "val1"},
            external_name=sentinel.external_name,
            notifications=[sentinel.notification],
            on_failure=sentinel.on_failure,
            disable_rollback=False,
            stack_timeout=sentinel.stack_timeout,
        )
        self.actions = StackActions(self.stack)
        self.stack_group_config = {}
        self.template = Template(
            "fixtures/templates",
            self.stack.template_handler_config,
            self.stack.sceptre_user_data,
            self.stack_group_config,
            self.actions.connection_manager,
            self.stack.s3_details,
        )
        self.template._body = json.dumps(
            {
                "AWSTemplateFormatVersion": "2010-09-09",
                "Resources": {"Bucket": {"Type": "AWS::S3::Bucket", "Properties": {}}},
            }
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
            name="prod/app/stack",
            handler_config={"type": "file", "path": sentinel.template_path},
            sceptre_user_data=sentinel.sceptre_user_data,
            stack_group_config={},
            connection_manager=self.stack.connection_manager,
            s3_details=None,
        )
        assert response == sentinel.template

    def test_template_returns_template_if_it_exists(self):
        self.actions.stack._template = sentinel.template
        response = self.actions.stack._template
        assert response == sentinel.template

    def test_external_name_with_custom_stack_name(self):
        stack = Stack(
            name="stack_name",
            project_code="project_code",
            template_path="template_path",
            region="region",
            external_name="external_name",
        )

        assert stack.external_name == "external_name"

    @patch("sceptre.plan.actions.StackActions._wait_for_completion")
    @patch("sceptre.plan.actions.StackActions._get_stack_timeout")
    def test_create_sends_correct_request(
        self, mock_get_stack_timeout, mock_wait_for_completion
    ):
        self.template._body = sentinel.template

        mock_get_stack_timeout.return_value = {"TimeoutInMinutes": sentinel.timeout}

        self.actions.create()
        self.actions.connection_manager.call.assert_called_with(
            service="cloudformation",
            command="create_stack",
            kwargs={
                "StackName": sentinel.external_name,
                "TemplateBody": sentinel.template,
                "Parameters": [{"ParameterKey": "key1", "ParameterValue": "val1"}],
                "Capabilities": [
                    "CAPABILITY_IAM",
                    "CAPABILITY_NAMED_IAM",
                    "CAPABILITY_AUTO_EXPAND",
                ],
                "RoleARN": sentinel.role_arn,
                "NotificationARNs": [sentinel.notification],
                "Tags": [{"Key": "tag1", "Value": "val1"}],
                "OnFailure": sentinel.on_failure,
                "TimeoutInMinutes": sentinel.timeout,
            },
        )
        mock_wait_for_completion.assert_called_once_with(boto_response=ANY)

    @patch("sceptre.plan.actions.StackActions._wait_for_completion")
    @patch("sceptre.plan.actions.StackActions._get_stack_timeout")
    def test_create_disable_rollback_overrides_on_failure(
        self, mock_get_stack_timeout, mock_wait_for_completion
    ):
        self.template._body = sentinel.template
        self.actions.stack.on_failure = "ROLLBACK"
        self.actions.stack.disable_rollback = True

        mock_get_stack_timeout.return_value = {"TimeoutInMinutes": sentinel.timeout}

        self.actions.create()
        self.actions.connection_manager.call.assert_called_with(
            service="cloudformation",
            command="create_stack",
            kwargs={
                "StackName": sentinel.external_name,
                "TemplateBody": sentinel.template,
                "Parameters": [{"ParameterKey": "key1", "ParameterValue": "val1"}],
                "Capabilities": [
                    "CAPABILITY_IAM",
                    "CAPABILITY_NAMED_IAM",
                    "CAPABILITY_AUTO_EXPAND",
                ],
                "RoleARN": sentinel.role_arn,
                "NotificationARNs": [sentinel.notification],
                "Tags": [{"Key": "tag1", "Value": "val1"}],
                "DisableRollback": True,
                "TimeoutInMinutes": sentinel.timeout,
            },
        )
        mock_wait_for_completion.assert_called_once_with(boto_response=ANY)

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
                "Parameters": [{"ParameterKey": "key1", "ParameterValue": "val1"}],
                "Capabilities": [
                    "CAPABILITY_IAM",
                    "CAPABILITY_NAMED_IAM",
                    "CAPABILITY_AUTO_EXPAND",
                ],
                "RoleARN": sentinel.role_arn,
                "NotificationARNs": [],
                "Tags": [{"Key": "tag1", "Value": "val1"}],
                "OnFailure": sentinel.on_failure,
                "TimeoutInMinutes": sentinel.stack_timeout,
            },
        )
        mock_wait_for_completion.assert_called_once_with(boto_response=ANY)

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
                "Parameters": [{"ParameterKey": "key1", "ParameterValue": "val1"}],
                "Capabilities": [
                    "CAPABILITY_IAM",
                    "CAPABILITY_NAMED_IAM",
                    "CAPABILITY_AUTO_EXPAND",
                ],
                "RoleARN": sentinel.role_arn,
                "NotificationARNs": [sentinel.notification],
                "Tags": [{"Key": "tag1", "Value": "val1"}],
            },
        )

        mock_wait_for_completion.assert_called_once_with(boto_response=ANY)

    @patch("sceptre.plan.actions.StackActions._wait_for_completion")
    def test_create_stack_already_exists(self, mock_wait_for_completion):
        self.actions.stack._template = Mock(spec=Template)
        self.actions.stack._template.get_boto_call_parameter.return_value = {
            "Template": sentinel.template
        }
        mock_wait_for_completion.side_effect = ClientError(
            {
                "Error": {
                    "Code": "AlreadyExistsException",
                    "Message": "Stack already [{}] exists".format(
                        self.actions.stack.name
                    ),
                }
            },
            sentinel.operation,
        )
        response = self.actions.create()
        assert response == StackStatus.COMPLETE

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
                "Parameters": [{"ParameterKey": "key1", "ParameterValue": "val1"}],
                "Capabilities": [
                    "CAPABILITY_IAM",
                    "CAPABILITY_NAMED_IAM",
                    "CAPABILITY_AUTO_EXPAND",
                ],
                "RoleARN": sentinel.role_arn,
                "NotificationARNs": [sentinel.notification],
                "Tags": [{"Key": "tag1", "Value": "val1"}],
            },
        )
        mock_wait_for_completion.assert_called_once_with(
            sentinel.stack_timeout, boto_response=ANY
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
                    "Parameters": [{"ParameterKey": "key1", "ParameterValue": "val1"}],
                    "Capabilities": [
                        "CAPABILITY_IAM",
                        "CAPABILITY_NAMED_IAM",
                        "CAPABILITY_AUTO_EXPAND",
                    ],
                    "RoleARN": sentinel.role_arn,
                    "NotificationARNs": [sentinel.notification],
                    "Tags": [{"Key": "tag1", "Value": "val1"}],
                },
            ),
            call(
                service="cloudformation",
                command="cancel_update_stack",
                kwargs={"StackName": sentinel.external_name},
            ),
        ]
        self.actions.connection_manager.call.assert_has_calls(calls)
        mock_wait_for_completion.assert_has_calls(
            [call(sentinel.stack_timeout, boto_response=ANY), call(boto_response=ANY)]
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
                "Parameters": [{"ParameterKey": "key1", "ParameterValue": "val1"}],
                "Capabilities": [
                    "CAPABILITY_IAM",
                    "CAPABILITY_NAMED_IAM",
                    "CAPABILITY_AUTO_EXPAND",
                ],
                "RoleARN": sentinel.role_arn,
                "NotificationARNs": [],
                "Tags": [{"Key": "tag1", "Value": "val1"}],
            },
        )
        mock_wait_for_completion.assert_called_once_with(
            sentinel.stack_timeout, boto_response=ANY
        )

    @patch("sceptre.plan.actions.StackActions._wait_for_completion")
    def test_update_with_complete_stack_with_no_updates_to_perform(
        self, mock_wait_for_completion
    ):
        self.actions.stack._template = Mock(spec=Template)
        self.actions.stack._template.get_boto_call_parameter.return_value = {
            "Template": sentinel.template
        }
        mock_wait_for_completion.side_effect = ClientError(
            {
                "Error": {
                    "Code": "NoUpdateToPerformError",
                    "Message": "No updates are to be performed.",
                }
            },
            sentinel.operation,
        )
        response = self.actions.update()
        assert response == StackStatus.COMPLETE

    @patch("sceptre.plan.actions.StackActions._wait_for_completion")
    def test_cancel_update_sends_correct_request(self, mock_wait_for_completion):
        self.actions.cancel_stack_update()
        self.actions.connection_manager.call.assert_called_once_with(
            service="cloudformation",
            command="cancel_update_stack",
            kwargs={"StackName": sentinel.external_name},
        )
        mock_wait_for_completion.assert_called_once_with(boto_response=ANY)

    @patch("sceptre.plan.actions.StackActions.create")
    @patch("sceptre.plan.actions.StackActions._get_status")
    def test_launch_with_stack_that_does_not_exist(self, mock_get_status, mock_create):
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
        mock_update.return_value = StackStatus.COMPLETE
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
            {"Error": {"Code": "Boom!", "Message": "Boom!"}}, sentinel.operation
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
    def test_delete_with_created_stack(self, mock_get_status, mock_wait_for_completion):
        mock_get_status.return_value = "CREATE_COMPLETE"

        self.actions.delete()
        self.actions.connection_manager.call.assert_called_with(
            service="cloudformation",
            command="delete_stack",
            kwargs={"StackName": sentinel.external_name, "RoleARN": sentinel.role_arn},
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
                    "Message": "Stack does not exist",
                }
            },
            sentinel.operation,
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
            {"Error": {"Code": "DoesNotExistException", "Message": "Boom"}},
            sentinel.operation,
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
            kwargs={"StackName": sentinel.external_name},
        )

    def test_describe_events_sends_correct_request(self):
        self.actions.describe_events()
        self.actions.connection_manager.call.assert_called_with(
            service="cloudformation",
            command="describe_stack_events",
            kwargs={"StackName": sentinel.external_name},
        )

    def test_describe_resources_sends_correct_request(self):
        self.actions.connection_manager.call.return_value = {
            "StackResources": [
                {
                    "LogicalResourceId": sentinel.logical_resource_id,
                    "PhysicalResourceId": sentinel.physical_resource_id,
                    "OtherParam": sentinel.other_param,
                }
            ]
        }
        response = self.actions.describe_resources()
        self.actions.connection_manager.call.assert_called_with(
            service="cloudformation",
            command="describe_stack_resources",
            kwargs={"StackName": sentinel.external_name},
        )
        assert response == {
            self.stack.name: [
                {
                    "LogicalResourceId": sentinel.logical_resource_id,
                    "PhysicalResourceId": sentinel.physical_resource_id,
                }
            ]
        }

    @patch("sceptre.plan.actions.StackActions._describe")
    def test_describe_outputs_sends_correct_request(self, mock_describe):
        mock_describe.return_value = {"Stacks": [{"Outputs": sentinel.outputs}]}
        response = self.actions.describe_outputs()
        mock_describe.assert_called_once_with()
        assert response == {self.stack.name: sentinel.outputs}

    @patch("sceptre.plan.actions.StackActions._describe")
    def test_describe_outputs_handles_stack_with_no_outputs(self, mock_describe):
        mock_describe.return_value = {"Stacks": [{}]}
        response = self.actions.describe_outputs()
        assert response == {self.stack.name: []}

    def test_continue_update_rollback_sends_correct_request(self):
        self.actions.continue_update_rollback()
        self.actions.connection_manager.call.assert_called_with(
            service="cloudformation",
            command="continue_update_rollback",
            kwargs={"StackName": sentinel.external_name, "RoleARN": sentinel.role_arn},
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
""",
            },
        )

    @patch("sceptre.plan.actions.json")
    def test_get_stack_policy_sends_correct_request(self, mock_Json):
        mock_Json.loads.return_value = "{}"
        mock_Json.dumps.return_value = "{}"
        response = self.actions.get_policy()
        self.actions.connection_manager.call.assert_called_with(
            service="cloudformation",
            command="get_stack_policy",
            kwargs={"StackName": sentinel.external_name},
        )

        assert response == {"prod/app/stack": "{}"}

    def test_create_change_set_sends_correct_request(self):
        self.template._body = sentinel.template

        self.actions.create_change_set(sentinel.change_set_name)
        self.actions.connection_manager.call.assert_called_with(
            service="cloudformation",
            command="create_change_set",
            kwargs={
                "StackName": sentinel.external_name,
                "TemplateBody": sentinel.template,
                "Parameters": [{"ParameterKey": "key1", "ParameterValue": "val1"}],
                "Capabilities": [
                    "CAPABILITY_IAM",
                    "CAPABILITY_NAMED_IAM",
                    "CAPABILITY_AUTO_EXPAND",
                ],
                "ChangeSetName": sentinel.change_set_name,
                "RoleARN": sentinel.role_arn,
                "NotificationARNs": [sentinel.notification],
                "Tags": [{"Key": "tag1", "Value": "val1"}],
            },
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
                "Parameters": [{"ParameterKey": "key1", "ParameterValue": "val1"}],
                "Capabilities": [
                    "CAPABILITY_IAM",
                    "CAPABILITY_NAMED_IAM",
                    "CAPABILITY_AUTO_EXPAND",
                ],
                "ChangeSetName": sentinel.change_set_name,
                "RoleARN": sentinel.role_arn,
                "NotificationARNs": [],
                "Tags": [{"Key": "tag1", "Value": "val1"}],
            },
        )

    def test_delete_change_set_sends_correct_request(self):
        self.actions.delete_change_set(sentinel.change_set_name)
        self.actions.connection_manager.call.assert_called_with(
            service="cloudformation",
            command="delete_change_set",
            kwargs={
                "ChangeSetName": sentinel.change_set_name,
                "StackName": sentinel.external_name,
            },
        )

    def test_describe_change_set_sends_correct_request(self):
        self.actions.describe_change_set(sentinel.change_set_name)
        self.actions.connection_manager.call.assert_called_with(
            service="cloudformation",
            command="describe_change_set",
            kwargs={
                "ChangeSetName": sentinel.change_set_name,
                "StackName": sentinel.external_name,
            },
        )

    @patch("sceptre.plan.actions.StackActions._wait_for_completion")
    def test_execute_change_set_sends_correct_request(self, mock_wait_for_completion):
        self.actions.execute_change_set(sentinel.change_set_name)
        self.actions.connection_manager.call.assert_called_with(
            service="cloudformation",
            command="execute_change_set",
            kwargs={
                "ChangeSetName": sentinel.change_set_name,
                "StackName": sentinel.external_name,
            },
        )
        mock_wait_for_completion.assert_called_once_with(boto_response=ANY)

    def test_execute_change_set__change_set_is_failed_for_no_changes__returns_0(self):
        def fake_describe(service, command, kwargs):
            assert (service, command) == ("cloudformation", "describe_change_set")
            return {
                "Status": "FAILED",
                "StatusReason": "The submitted information didn't contain changes",
            }

        self.actions.connection_manager.call.side_effect = fake_describe
        result = self.actions.execute_change_set(sentinel.change_set_name)
        assert result == 0

    def test_execute_change_set__change_set_is_failed_for_no_updates__returns_0(self):
        def fake_describe(service, command, kwargs):
            assert (service, command) == ("cloudformation", "describe_change_set")
            return {
                "Status": "FAILED",
                "StatusReason": "No updates are to be performed",
            }

        self.actions.connection_manager.call.side_effect = fake_describe
        result = self.actions.execute_change_set(sentinel.change_set_name)
        assert result == 0

    def test_list_change_sets_sends_correct_request(self):
        self.actions.list_change_sets()
        self.actions.connection_manager.call.assert_called_with(
            service="cloudformation",
            command="list_change_sets",
            kwargs={"StackName": sentinel.external_name},
        )

    @patch("sceptre.plan.actions.StackActions._list_change_sets")
    def test_list_change_sets(self, mock_list_change_sets):
        mock_list_change_sets_return_value = {"Summaries": []}
        expected_responses = []

        for num in ["1", "2"]:
            response = [
                {"ChangeSetId": "mychangesetid{num}", "StackId": "mystackid{num}"}
            ]
            mock_list_change_sets_return_value["Summaries"].append(response)
            expected_responses.append(response)

        mock_list_change_sets.return_value = mock_list_change_sets_return_value

        response = self.actions.list_change_sets(url=False)
        assert response == {"prod/app/stack": expected_responses}

    @patch("sceptre.plan.actions.urllib.parse.urlencode")
    @patch("sceptre.plan.actions.StackActions._list_change_sets")
    def test_list_change_sets_url_mode(self, mock_list_change_sets, mock_urlencode):
        mock_list_change_sets_return_value = {"Summaries": []}
        mock_urlencode_side_effect = []
        expected_urls = []

        for num in ["1", "2"]:
            mock_list_change_sets_return_value["Summaries"].append(
                {"ChangeSetId": "mychangesetid{num}", "StackId": "mystackid{num}"}
            )
            urlencoded = "stackId=mystackid{num}&changeSetId=mychangesetid{num}"
            mock_urlencode_side_effect.append(urlencoded)
            expected_urls.append(
                "https://sentinel.region.console.aws.amazon.com/cloudformation/home?"
                f"region=sentinel.region#/stacks/changesets/changes?{urlencoded}"
            )

        mock_list_change_sets.return_value = mock_list_change_sets_return_value
        mock_urlencode.side_effect = mock_urlencode_side_effect

        response = self.actions.list_change_sets(url=True)
        assert response == {"prod/app/stack": expected_urls}

    @pytest.mark.parametrize("url_mode", [True, False])
    @patch("sceptre.plan.actions.StackActions._list_change_sets")
    def test_list_change_sets_empty(self, mock_list_change_sets, url_mode):
        mock_list_change_sets.return_value = {"Summaries": []}
        response = self.actions.list_change_sets(url=url_mode)
        assert response == {"prod/app/stack": []}

    @patch("sceptre.plan.actions.StackActions.set_policy")
    @patch("os.path.join")
    def test_lock_calls_set_stack_policy_with_policy(self, mock_join, mock_set_policy):
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
        parameters = {"key1": "value1", "key2": "value2", "key3": "value3"}
        formatted_parameters = self.actions._format_parameters(parameters)
        sorted_formatted_parameters = sorted(
            formatted_parameters, key=lambda x: x["ParameterKey"]
        )
        assert sorted_formatted_parameters == [
            {"ParameterKey": "key1", "ParameterValue": "value1"},
            {"ParameterKey": "key2", "ParameterValue": "value2"},
            {"ParameterKey": "key3", "ParameterValue": "value3"},
        ]

    def test_format_parameters_with_none_values(self):
        parameters = {"key1": None, "key2": None, "key3": None}
        formatted_parameters = self.actions._format_parameters(parameters)
        sorted_formatted_parameters = sorted(
            formatted_parameters, key=lambda x: x["ParameterKey"]
        )
        assert sorted_formatted_parameters == []

    def test_format_parameters_with_none_and_string_values(self):
        parameters = {"key1": "value1", "key2": None, "key3": "value3"}
        formatted_parameters = self.actions._format_parameters(parameters)
        sorted_formatted_parameters = sorted(
            formatted_parameters, key=lambda x: x["ParameterKey"]
        )
        assert sorted_formatted_parameters == [
            {"ParameterKey": "key1", "ParameterValue": "value1"},
            {"ParameterKey": "key3", "ParameterValue": "value3"},
        ]

    def test_format_parameters_with_list_values(self):
        parameters = {
            "key1": ["value1", "value2", "value3"],
            "key2": ["value4", "value5", "value6"],
            "key3": ["value7", "value8", "value9"],
        }
        formatted_parameters = self.actions._format_parameters(parameters)
        sorted_formatted_parameters = sorted(
            formatted_parameters, key=lambda x: x["ParameterKey"]
        )
        assert sorted_formatted_parameters == [
            {"ParameterKey": "key1", "ParameterValue": "value1,value2,value3"},
            {"ParameterKey": "key2", "ParameterValue": "value4,value5,value6"},
            {"ParameterKey": "key3", "ParameterValue": "value7,value8,value9"},
        ]

    def test_format_parameters_with_none_and_list_values(self):
        parameters = {
            "key1": ["value1", "value2", "value3"],
            "key2": None,
            "key3": ["value7", "value8", "value9"],
        }
        formatted_parameters = self.actions._format_parameters(parameters)
        sorted_formatted_parameters = sorted(
            formatted_parameters, key=lambda x: x["ParameterKey"]
        )
        assert sorted_formatted_parameters == [
            {"ParameterKey": "key1", "ParameterValue": "value1,value2,value3"},
            {"ParameterKey": "key3", "ParameterValue": "value7,value8,value9"},
        ]

    def test_format_parameters_with_list_and_string_values(self):
        parameters = {
            "key1": ["value1", "value2", "value3"],
            "key2": "value4",
            "key3": ["value5", "value6", "value7"],
        }
        formatted_parameters = self.actions._format_parameters(parameters)
        sorted_formatted_parameters = sorted(
            formatted_parameters, key=lambda x: x["ParameterKey"]
        )
        assert sorted_formatted_parameters == [
            {"ParameterKey": "key1", "ParameterValue": "value1,value2,value3"},
            {"ParameterKey": "key2", "ParameterValue": "value4"},
            {"ParameterKey": "key3", "ParameterValue": "value5,value6,value7"},
        ]

    def test_format_parameters_with_none_list_and_string_values(self):
        parameters = {
            "key1": ["value1", "value2", "value3"],
            "key2": "value4",
            "key3": None,
        }
        formatted_parameters = self.actions._format_parameters(parameters)
        sorted_formatted_parameters = sorted(
            formatted_parameters, key=lambda x: x["ParameterKey"]
        )
        assert sorted_formatted_parameters == [
            {"ParameterKey": "key1", "ParameterValue": "value1,value2,value3"},
            {"ParameterKey": "key2", "ParameterValue": "value4"},
        ]

    @patch("sceptre.plan.actions.StackActions._describe")
    def test_get_status_with_created_stack(self, mock_describe):
        mock_describe.return_value = {"Stacks": [{"StackStatus": "CREATE_COMPLETE"}]}
        status = self.actions.get_status()
        assert status == "CREATE_COMPLETE"

    @patch("sceptre.plan.actions.StackActions._describe")
    def test_get_status_with_non_existent_stack(self, mock_describe):
        mock_describe.side_effect = ClientError(
            {
                "Error": {
                    "Code": "DoesNotExistException",
                    "Message": "Stack does not exist",
                }
            },
            sentinel.operation,
        )
        assert self.actions.get_status() == "PENDING"

    @patch("sceptre.plan.actions.StackActions._describe")
    def test_get_status_with_unknown_clinet_error(self, mock_describe):
        mock_describe.side_effect = ClientError(
            {"Error": {"Code": "DoesNotExistException", "Message": "Boom!"}},
            sentinel.operation,
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
        self, mock_get_simplified_status, mock_get_status, mock_log_new_events
    ):
        mock_get_simplified_status.return_value = StackStatus.COMPLETE

        self.actions._wait_for_completion()
        mock_log_new_events.assert_called_once()
        assert type(mock_log_new_events.mock_calls[0].args[0]) is datetime.datetime

    @pytest.mark.parametrize(
        "test_input,expected",
        [
            ("ROLLBACK_COMPLETE", StackStatus.FAILED),
            ("STACK_COMPLETE", StackStatus.COMPLETE),
            ("STACK_IN_PROGRESS", StackStatus.IN_PROGRESS),
            ("STACK_FAILED", StackStatus.FAILED),
        ],
    )
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
        mock_describe_events.return_value = {"StackEvents": []}
        self.actions._log_new_events(datetime.datetime.utcnow())
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
                    "ResourceStatus": "resource-status",
                },
                {
                    "Timestamp": datetime.datetime(
                        2016, 3, 15, 14, 1, 0, 0, tzinfo=tzutc()
                    ),
                    "LogicalResourceId": "id-1",
                    "ResourceType": "type-1",
                    "ResourceStatus": "resource",
                    "ResourceStatusReason": "User Initiated",
                },
            ]
        }
        self.actions._log_new_events(
            datetime.datetime(2016, 3, 15, 14, 0, 0, 0, tzinfo=tzutc())
        )

    @patch("sceptre.plan.actions.StackActions._get_cs_status")
    def test_wait_for_cs_completion_calls_get_cs_status(self, mock_get_cs_status):
        mock_get_cs_status.side_effect = [
            StackChangeSetStatus.PENDING,
            StackChangeSetStatus.READY,
        ]

        self.actions.wait_for_cs_completion(sentinel.change_set_name)
        mock_get_cs_status.assert_called_with(sentinel.change_set_name)

    @patch("sceptre.plan.actions.StackActions.describe_change_set")
    def test_get_cs_status_handles_all_statuses(self, mock_describe_change_set):
        scss = StackChangeSetStatus
        return_values = {  # NOQA
            "Status": (
                "CREATE_PENDING",
                "CREATE_IN_PROGRESS",
                "CREATE_COMPLETE",
                "DELETE_COMPLETE",
                "FAILED",
            ),  # NOQA
            "ExecutionStatus": {  # NOQA
                "UNAVAILABLE": (
                    scss.PENDING,
                    scss.PENDING,
                    scss.PENDING,
                    scss.DEFUNCT,
                    scss.DEFUNCT,
                ),  # NOQA
                "AVAILABLE": (
                    scss.PENDING,
                    scss.PENDING,
                    scss.READY,
                    scss.DEFUNCT,
                    scss.DEFUNCT,
                ),  # NOQA
                "EXECUTE_IN_PROGRESS": (
                    scss.DEFUNCT,
                    scss.DEFUNCT,
                    scss.DEFUNCT,
                    scss.DEFUNCT,
                    scss.DEFUNCT,
                ),  # NOQA
                "EXECUTE_COMPLETE": (
                    scss.DEFUNCT,
                    scss.DEFUNCT,
                    scss.DEFUNCT,
                    scss.DEFUNCT,
                    scss.DEFUNCT,
                ),  # NOQA
                "EXECUTE_FAILED": (
                    scss.DEFUNCT,
                    scss.DEFUNCT,
                    scss.DEFUNCT,
                    scss.DEFUNCT,
                    scss.DEFUNCT,
                ),  # NOQA
                "OBSOLETE": (
                    scss.DEFUNCT,
                    scss.DEFUNCT,
                    scss.DEFUNCT,
                    scss.DEFUNCT,
                    scss.DEFUNCT,
                ),  # NOQA
            },  # NOQA
        }  # NOQA

        for i, status in enumerate(return_values["Status"]):
            for exec_status, returns in return_values["ExecutionStatus"].items():
                mock_describe_change_set.return_value = {
                    "Status": status,
                    "ExecutionStatus": exec_status,
                }
                response = self.actions._get_cs_status(sentinel.change_set_name)
                assert response == returns[i]

        for status in return_values["Status"]:
            mock_describe_change_set.return_value = {
                "Status": status,
                "ExecutionStatus": "UNKOWN_STATUS",
            }
            with pytest.raises(UnknownStackChangeSetStatusError):
                self.actions._get_cs_status(sentinel.change_set_name)

        for exec_status in return_values["ExecutionStatus"].keys():
            mock_describe_change_set.return_value = {
                "Status": "UNKOWN_STATUS",
                "ExecutionStatus": exec_status,
            }
            with pytest.raises(UnknownStackChangeSetStatusError):
                self.actions._get_cs_status(sentinel.change_set_name)

        mock_describe_change_set.return_value = {
            "Status": "UNKOWN_STATUS",
            "ExecutionStatus": "UNKOWN_STATUS",
        }
        with pytest.raises(UnknownStackChangeSetStatusError):
            self.actions._get_cs_status(sentinel.change_set_name)

    @patch("sceptre.plan.actions.StackActions.describe_change_set")
    def test_get_cs_status_raises_unexpected_exceptions(self, mock_describe_change_set):
        mock_describe_change_set.side_effect = ClientError(
            {
                "Error": {
                    "Code": "ChangeSetNotFound",
                    "Message": "ChangeSet [*] does not exist",
                }
            },
            sentinel.operation,
        )
        with pytest.raises(ClientError):
            self.actions._get_cs_status(sentinel.change_set_name)

    def test_fetch_remote_template__cloudformation_returns_validation_error__returns_none(
        self,
    ):
        self.actions.connection_manager.call.side_effect = ClientError(
            {
                "Error": {
                    "Code": "ValidationError",
                    "Message": "An error occurred (ValidationError) "
                    "when calling the GetTemplate operation: "
                    "Stack with id foo does not exist",
                }
            },
            sentinel.operation,
        )

        result = self.actions.fetch_remote_template()
        assert result is None

    def test_fetch_remote_template__calls_cloudformation_get_template(self):
        self.actions.connection_manager.call.return_value = {"TemplateBody": ""}
        self.actions.fetch_remote_template()

        self.actions.connection_manager.call.assert_called_with(
            service="cloudformation",
            command="get_template",
            kwargs={"StackName": self.stack.external_name, "TemplateStage": "Original"},
        )

    def test_fetch_remote_template__dict_template__returns_json(self):
        template_body = {"AWSTemplateFormatVersion": "2010-09-09", "Resources": {}}
        self.actions.connection_manager.call.return_value = {
            "TemplateBody": template_body
        }
        expected = json.dumps(template_body, indent=4)

        result = self.actions.fetch_remote_template()
        assert result == expected

    def test_fetch_remote_template__cloudformation_returns_string_template__returns_that_string(
        self,
    ):
        template_body = "This is my template"
        self.actions.connection_manager.call.return_value = {
            "TemplateBody": template_body
        }
        result = self.actions.fetch_remote_template()
        assert result == template_body

    def test_fetch_remote_template_summary__calls_cloudformation_get_template_summary(
        self,
    ):
        self.actions.fetch_remote_template_summary()

        self.actions.connection_manager.call.assert_called_with(
            service="cloudformation",
            command="get_template_summary",
            kwargs={
                "StackName": self.stack.external_name,
            },
        )

    def test_fetch_remote_template_summary__returns_response_from_cloudformation(self):
        def get_template_summary(service, command, kwargs):
            assert (service, command) == ("cloudformation", "get_template_summary")
            return {"template": "summary"}

        self.actions.connection_manager.call.side_effect = get_template_summary
        result = self.actions.fetch_remote_template_summary()
        assert result == {"template": "summary"}

    def test_fetch_local_template_summary__calls_cloudformation_get_template_summary(
        self,
    ):
        self.actions.fetch_local_template_summary()

        self.actions.connection_manager.call.assert_called_with(
            service="cloudformation",
            command="get_template_summary",
            kwargs={
                "TemplateBody": self.stack.template.body,
            },
        )

    def test_fetch_local_template_summary__returns_response_from_cloudformation(self):
        def get_template_summary(service, command, kwargs):
            assert (service, command) == ("cloudformation", "get_template_summary")
            return {"template": "summary"}

        self.actions.connection_manager.call.side_effect = get_template_summary
        result = self.actions.fetch_local_template_summary()
        assert result == {"template": "summary"}

    def test_fetch_local_template_summary__cloudformation_returns_validation_error_invalid_stack__raises_it(
        self,
    ):
        self.actions.connection_manager.call.side_effect = ClientError(
            {
                "Error": {
                    "Code": "ValidationError",
                    "Message": "Template format error: Resource name {Invalid::Resource} is "
                    "non alphanumeric.'",
                }
            },
            sentinel.operation,
        )
        with pytest.raises(ClientError):
            self.actions.fetch_local_template_summary()

    def test_fetch_remote_template_summary__cloudformation_returns_validation_error_for_no_stack__returns_none(
        self,
    ):
        self.actions.connection_manager.call.side_effect = ClientError(
            {
                "Error": {
                    "Code": "ValidationError",
                    "Message": "An error occurred (ValidationError) "
                    "when calling the GetTemplate operation: "
                    "Stack with id foo does not exist",
                }
            },
            sentinel.operation,
        )
        result = self.actions.fetch_remote_template_summary()
        assert result is None

    def test_diff__invokes_diff_method_on_injected_differ_with_self(self):
        differ = Mock()
        self.actions.diff(differ)
        differ.diff.assert_called_with(self.actions)

    def test_diff__returns_result_of_injected_differs_diff_method(self):
        differ = Mock()
        result = self.actions.diff(differ)
        assert result == differ.diff.return_value

    @patch("sceptre.plan.actions.StackActions._describe_stack_drift_detection_status")
    @patch("sceptre.plan.actions.StackActions._detect_stack_drift")
    @patch("time.sleep")
    def test_drift_detect(
        self,
        mock_sleep,
        mock_detect_stack_drift,
        mock_describe_stack_drift_detection_status,
    ):
        mock_sleep.return_value = None

        mock_detect_stack_drift.return_value = {
            "StackDriftDetectionId": "3fb76910-f660-11eb-80ac-0246f7a6da62"
        }

        first_response = {
            "StackId": "fake-stack-id",
            "StackDriftDetectionId": "3fb76910-f660-11eb-80ac-0246f7a6da62",
            "DetectionStatus": "DETECTION_IN_PROGRESS",
            "StackDriftStatus": "NOT_CHECKED",
            "DetectionStatusReason": "User Initiated",
        }

        final_response = {
            "StackId": "fake-stack-id",
            "StackDriftDetectionId": "3fb76910-f660-11eb-80ac-0246f7a6da62",
            "StackDriftStatus": "IN_SYNC",
            "DetectionStatus": "DETECTION_COMPLETE",
            "DriftedStackResourceCount": 0,
        }

        mock_describe_stack_drift_detection_status.side_effect = [
            first_response,
            final_response,
        ]

        response = self.actions.drift_detect()
        assert response == final_response

    @pytest.mark.parametrize(
        "detection_status", ["DETECTION_COMPLETE", "DETECTION_FAILED"]
    )
    @patch("sceptre.plan.actions.StackActions._describe_stack_resource_drifts")
    @patch("sceptre.plan.actions.StackActions._describe_stack_drift_detection_status")
    @patch("sceptre.plan.actions.StackActions._detect_stack_drift")
    @patch("time.sleep")
    def test_drift_show(
        self,
        mock_sleep,
        mock_detect_stack_drift,
        mock_describe_stack_drift_detection_status,
        mock_describe_stack_resource_drifts,
        detection_status,
    ):
        mock_sleep.return_value = None

        mock_detect_stack_drift.return_value = {
            "StackDriftDetectionId": "3fb76910-f660-11eb-80ac-0246f7a6da62"
        }
        mock_describe_stack_drift_detection_status.side_effect = [
            {
                "StackId": "fake-stack-id",
                "StackDriftDetectionId": "3fb76910-f660-11eb-80ac-0246f7a6da62",
                "DetectionStatus": "DETECTION_IN_PROGRESS",
                "StackDriftStatus": "FOO",
                "DetectionStatusReason": "User Initiated",
            },
            {
                "StackId": "fake-stack-id",
                "StackDriftDetectionId": "3fb76910-f660-11eb-80ac-0246f7a6da62",
                "StackDriftStatus": "FOO",
                "DetectionStatus": detection_status,
                "DriftedStackResourceCount": 0,
            },
        ]

        expected_drifts = {
            "StackResourceDrifts": [
                {
                    "StackId": "fake-stack-id",
                    "LogicalResourceId": "VPC",
                    "PhysicalResourceId": "vpc-028c655dea7c65227",
                    "ResourceType": "AWS::EC2::VPC",
                    "ExpectedProperties": '{"foo":"bar"}',
                    "ActualProperties": '{"foo":"bar"}',
                    "PropertyDifferences": [],
                    "StackResourceDriftStatus": detection_status,
                }
            ]
        }

        mock_describe_stack_resource_drifts.return_value = expected_drifts
        expected_response = (detection_status, expected_drifts)

        response = self.actions.drift_show(drifted=False)

        assert response == expected_response

    @patch("sceptre.plan.actions.StackActions._describe_stack_resource_drifts")
    @patch("sceptre.plan.actions.StackActions._describe_stack_drift_detection_status")
    @patch("sceptre.plan.actions.StackActions._detect_stack_drift")
    @patch("time.sleep")
    def test_drift_show_drift_only(
        self,
        mock_sleep,
        mock_detect_stack_drift,
        mock_describe_stack_drift_detection_status,
        mock_describe_stack_resource_drifts,
    ):
        mock_sleep.return_value = None

        mock_detect_stack_drift.return_value = {
            "StackDriftDetectionId": "3fb76910-f660-11eb-80ac-0246f7a6da62"
        }
        mock_describe_stack_drift_detection_status.return_value = {
            "StackId": "fake-stack-id",
            "StackDriftDetectionId": "3fb76910-f660-11eb-80ac-0246f7a6da62",
            "StackDriftStatus": "DRIFTED",
            "DetectionStatus": "DETECTION_COMPLETE",
            "DriftedStackResourceCount": 0,
        }

        input_drifts = {
            "StackResourceDrifts": [
                {
                    "LogicalResourceId": "ServerLoadBalancer",
                    "PhysicalResourceId": "bi-tablea-ServerLo-1E133TWLWYLON",
                    "ResourceType": "AWS::ElasticLoadBalancing::LoadBalancer",
                    "StackId": "fake-stack-id",
                    "StackResourceDriftStatus": "IN_SYNC",
                },
                {
                    "LogicalResourceId": "TableauServer",
                    "PhysicalResourceId": "i-08c16bc1c5e2cd185",
                    "ResourceType": "AWS::EC2::Instance",
                    "StackId": "fake-stack-id",
                    "StackResourceDriftStatus": "DELETED",
                },
            ]
        }
        mock_describe_stack_resource_drifts.return_value = input_drifts

        expected_response = (
            "DETECTION_COMPLETE",
            {"StackResourceDrifts": [input_drifts["StackResourceDrifts"][1]]},
        )

        response = self.actions.drift_show(drifted=True)

        assert response == expected_response

    @patch("sceptre.plan.actions.StackActions._get_status")
    def test_drift_show_with_stack_that_does_not_exist(self, mock_get_status):
        mock_get_status.side_effect = StackDoesNotExistError()
        response = self.actions.drift_show(drifted=False)
        assert response == (
            "STACK_DOES_NOT_EXIST",
            {"StackResourceDriftStatus": "STACK_DOES_NOT_EXIST"},
        )

    @patch("sceptre.plan.actions.StackActions._describe_stack_resource_drifts")
    @patch("sceptre.plan.actions.StackActions._describe_stack_drift_detection_status")
    @patch("sceptre.plan.actions.StackActions._detect_stack_drift")
    @patch("time.sleep")
    def test_drift_show_times_out(
        self,
        mock_sleep,
        mock_detect_stack_drift,
        mock_describe_stack_drift_detection_status,
        mock_describe_stack_resource_drifts,
    ):
        mock_sleep.return_value = None

        mock_detect_stack_drift.return_value = {
            "StackDriftDetectionId": "3fb76910-f660-11eb-80ac-0246f7a6da62"
        }

        response = {
            "StackId": "fake-stack-id",
            "StackDriftDetectionId": "3fb76910-f660-11eb-80ac-0246f7a6da62",
            "DetectionStatus": "DETECTION_IN_PROGRESS",
            "StackDriftStatus": "FOO",
            "DetectionStatusReason": "User Initiated",
        }

        side_effect = []
        for _ in range(0, 60):
            side_effect.append(response)
        mock_describe_stack_drift_detection_status.side_effect = side_effect

        expected_drifts = {
            "StackResourceDrifts": [
                {
                    "StackId": "fake-stack-id",
                    "LogicalResourceId": "VPC",
                    "PhysicalResourceId": "vpc-028c655dea7c65227",
                    "ResourceType": "AWS::EC2::VPC",
                    "ExpectedProperties": '{"foo":"bar"}',
                    "ActualProperties": '{"foo":"bar"}',
                    "PropertyDifferences": [],
                    "StackResourceDriftStatus": "DETECTION_IN_PROGRESS",
                }
            ]
        }

        mock_describe_stack_resource_drifts.return_value = expected_drifts
        expected_response = ("TIMED_OUT", {"StackResourceDriftStatus": "TIMED_OUT"})

        response = self.actions.drift_show(drifted=False)

        assert response == expected_response
