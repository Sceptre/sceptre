# -*- coding: utf-8 -*-

from sceptre.hooks import Hook
from sceptre.exceptions import InvalidHookArgumentValueError
from sceptre.exceptions import InvalidHookArgumentTypeError


class ASGScheduledActions(Hook):
    """
    A command to resume or suspend autoscaling group scheduled actions. This is
    useful as schedule actions must be suspended when updating stacks with
    on autoscaling groups.
    """

    def __init__(self, *args, **kwargs):
        super(ASGScheduledActions, self).__init__(*args, **kwargs)

    def run(self):
        """
        Either suspends or resumes any scheduled actions on all autoscaling
        groups with in the current stack.
        """
        if not isinstance(self.argument, basestring):
            raise InvalidHookArgumentTypeError(
                'The argument "{0}" is the wrong type - asg_scheduled_actions '
                'hooks require arguments of type string.'.format(self.argument)
            )
        if self.argument not in ["resume", "suspend"]:
            raise InvalidHookArgumentValueError(
                'The argument "{0}" is invalid - valid arguments for '
                'asg_scheduled_actions hooks are "resume" or "suspend".'
                .format(self.argument)
            )

        self.argument += "_processes"

        autoscaling_group_names = self._find_autoscaling_groups()
        for autoscaling_group in autoscaling_group_names:
            self.connection_manager.call(
                service="autoscaling",
                command=self.argument,
                kwargs={
                    "AutoScalingGroupName": autoscaling_group,
                    "ScalingProcesses": [
                        "ScheduledActions"
                    ]
                }
            )

    def _get_stack_resources(self):
        """
        Retrieves all resources in stack.
        :return: list
        """
        full_stack_name = "-".join([
            self.environment_config["project_code"],
            self.environment_config.environment_path,
            self.stack_config.name
        ]).replace("/", "-")
        response = self.connection_manager.call(
            service="cloudformation",
            command="describe_stack_resources",
            kwargs={"StackName": full_stack_name}
        )
        return response.get("StackResources", [])

    def _find_autoscaling_groups(self):
        """
        Retrieves all the autoscaling groups
        :return: list [str]
        """
        asg_names = []
        resources = self._get_stack_resources()
        resource_type = "AWS::AutoScaling::AutoScalingGroup"
        for resource in resources:
            if resource.get("ResourceType", False) == resource_type:
                    asg_names.append(resource["PhysicalResourceId"])

        return asg_names
