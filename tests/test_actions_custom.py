# -*- coding: utf-8 -*-

from mock import patch, sentinel

from sceptre.stack import Stack
from sceptre.plan.actions import StackActions
from sceptre.template import Template


class TestStackActions(object):

    def setup_method(self, test_method):
        self.patcher_connection_manager = patch(
            "sceptre.plan.actions.ConnectionManager"
        )
        self.mock_ConnectionManager = self.patcher_connection_manager.start()
        self.stack = Stack(
            name='prod/app/stack', project_code=sentinel.project_code,
            template_path=sentinel.template_path, region=sentinel.region,
            profile=sentinel.profile, parameters={"key1": "val1"}, sceptre_user_data=sentinel.sceptre_user_data,
            hooks={}, s3_details=None, dependencies=sentinel.dependencies,
            role_arn=sentinel.role_arn, protected=False,
            tags={"tag1": "val1"}, external_name=sentinel.external_name,
            notifications=[sentinel.notification],
            on_failure=sentinel.on_failure,
            stack_timeout=sentinel.stack_timeout
        )
        self.actions = StackActions(self.stack)
        self.stack_group_config = {}
        self.template = Template(
            "fixtures/templates", self.stack.template_handler_config,
            self.stack.sceptre_user_data, self.stack_group_config,
            self.actions.connection_manager, self.stack.s3_details
        )
        self.stack._template = self.template

    def teardown_method(self, test_method):
        self.patcher_connection_manager.stop()

    def test_stack_name(self):
        response = self.actions.stack_name(False)
        assert response == sentinel.external_name

#    Fails with TypeError: must be str, not _SentinelObject
#    def test_stack_name_p_opt(self):
#        response = self.actions.stack_name(True)
#        assert response.endswith(sentinel.external_name)

    @patch("sceptre.plan.actions.StackActions._describe_stack_resource_drifts")
    @patch("sceptre.plan.actions.StackActions._describe_stack_drift_detection_status")
    @patch("sceptre.plan.actions.StackActions._detect_stack_drift")
    def test_detect_stack_drift(
        self,
        mock_detect_stack_drift,
        mock_describe_stack_drift_detection_status,
        mock_describe_stack_resource_drifts
    ):
        mock_detect_stack_drift.return_value = {
            "StackDriftDetectionId": "3fb76910-f660-11eb-80ac-0246f7a6da62"
        }
        mock_describe_stack_drift_detection_status.side_effect = [
            {
                "StackId": "fake-stack-id",
                "StackDriftDetectionId": "3fb76910-f660-11eb-80ac-0246f7a6da62",
                "DetectionStatus": "DETECTION_IN_PROGRESS",
                "DetectionStatusReason": "User Initiated"
            },
            {
                "StackId": "fake-stack-id",
                "StackDriftDetectionId": "3fb76910-f660-11eb-80ac-0246f7a6da62",
                "StackDriftStatus": "IN_SYNC",
                "DetectionStatus": "DETECTION_COMPLETE",
                "DriftedStackResourceCount": 0
            }
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
                    "StackResourceDriftStatus": "IN_SYNC"
                }
            ]
        }

        mock_describe_stack_resource_drifts.return_value = expected_drifts
        expected_response = (sentinel.external_name, expected_drifts)

        response = self.actions.detect_stack_drift()

        assert response == expected_response
