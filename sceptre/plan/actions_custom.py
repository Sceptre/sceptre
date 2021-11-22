# -*- coding: utf-8 -*-

"""
sceptre.plan.actions_custom

Custom code that is inherited in SceptrePlan.
"""

import time
from sceptre.hooks import add_stack_hooks


class StackActionsCustom(object):

    @add_stack_hooks
    def stack_name(self, print_name):
        """
        Returns the Stack's stack name.

        :param print_name: Also print the internal stack name.
        :type print_name: bool
        :returns: The Stack's stack name (external_name).
        :rtype: str
        """
        return_value = self.stack.external_name

        if print_name:
            return_value = self.name + ": " + return_value

        return return_value

    @add_stack_hooks
    def detect_stack_drift(self):
        """
        Detects stack drift for a running stack.

        :returns: The stack drift.
        :rtype: Tuple[str, Union[str, dict]]
        """
        response = self._detect_stack_drift()

        detection_id = response["StackDriftDetectionId"]
        status = self._wait_for_drift(detection_id)

        if status == "DETECTION_COMPLETE":
            response = self._describe_stack_resource_drifts()
            return_value = (self.stack.external_name, response)
        else:
            return_value = (self.stack.external_name, status)

        return return_value

    def _wait_for_drift(self, detection_id):
        """
        Waits for drift detection to complete.

        :param detection_id: The drift detection ID.
        :type detection_id: str

        :returns: The drift status.
        :rtype: str
        """
        timeout = 300
        elapsed = 0

        while True:
            if elapsed >= timeout:
                return "TIMED_OUT"

            self.logger.debug("%s - Waiting for drift detection", self.stack.name)
            response = self._describe_stack_drift_detection_status(detection_id)

            status = response["DetectionStatus"]
            self._print_drift_status(response)

            if status == "DETECTION_IN_PROGRESS":
                time.sleep(10)
                elapsed += 10
            else:
                return status

    def _print_drift_status(self, response):
        """
        Print the drift status while waiting for
        drift detection to complete.
        """
        keys = [
            "StackDriftDetectionId",
            "DetectionStatus",
            "DetectionStatusReason",
            "StackDriftStatus"
        ]

        for key in keys:
            if key in response:
                self.logger.debug(
                    "%s - %s - %s",
                    self.stack.name,
                    key, response[key]
                )

    def _detect_stack_drift(self):
        """
        Run detect_stack_drift.
        """
        self.logger.debug("%s - Detecting Stack Drift", self.stack.name)

        return self.connection_manager.call(
            service="cloudformation",
            command="detect_stack_drift",
            kwargs={
                "StackName": self.stack.external_name
            }
        )

    def _describe_stack_drift_detection_status(self, detection_id):
        """
        Run describe_stack_drift_detection_status.
        """
        self.logger.debug("%s - Detecting Stack Drift Detection Status", self.stack.name)

        return self.connection_manager.call(
            service="cloudformation",
            command="describe_stack_drift_detection_status",
            kwargs={
                "StackDriftDetectionId": detection_id
            }
        )

    def _describe_stack_resource_drifts(self):
        """
        Detects stack resource_drifts for a running stack.
        """
        self.logger.debug("%s - Detecting Stack Drift", self.stack.name)

        return self.connection_manager.call(
            service="cloudformation",
            command="describe_stack_resource_drifts",
            kwargs={
                "StackName": self.stack.external_name
            }
        )
