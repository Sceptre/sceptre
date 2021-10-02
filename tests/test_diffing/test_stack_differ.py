from typing import Union, Optional
from unittest.mock import Mock, PropertyMock, ANY

import pytest

from sceptre.diffing.stack_differ import StackDiffer, StackConfiguration, DiffType
from sceptre.exceptions import StackDoesNotExistError
from sceptre.plan.actions import StackActions
from sceptre.resolvers import Resolver
from sceptre.stack import Stack


class ResolvableResolver(Resolver):
    RESOLVED_VALUE = "I'm resolved!"

    def resolve(self):
        return self.RESOLVED_VALUE


class UnresolvableResolver(Resolver):

    def resolve(self):
        raise StackDoesNotExistError()


class ImplementedStackDiffer(StackDiffer):

    def __init__(self, command_capturer: Mock):
        self.command_capturer = command_capturer

    def compare_templates(self, deployed: str, generated: str) -> DiffType:
        return self.command_capturer.compare_templates(deployed, generated)

    def compare_stack_configurations(
        self,
        deployed: Optional[StackConfiguration],
        generated: StackConfiguration
    ) -> DiffType:
        return self.command_capturer.compare_stack_configurations(deployed, generated)


class TestStackDiffer:

    def setup_method(self, method):
        self.name = 'my/stack'
        self.external_name = "full-stack-name"
        self.role_arn = 'role_arn'
        self.parameters = {
            'param': 'some_value'
        }
        self.tags = {
            'tag_name': 'tag_value'
        }
        self.notifications = [
            'notification_arn1'
        ]
        self.stack: Union[Stack, Mock] = Mock(
            spec=Stack,
            external_name=self.external_name,
            _parameters=self.parameters,
            role_arn=self.role_arn,
            tags=self.tags,
            notifications=self.notifications
        )
        self.stack.name = self.name
        self.parameters_property = PropertyMock(return_value=self.parameters)
        type(self.stack).parameters = self.parameters_property
        self.actions: Union[StackActions, Mock] = Mock(
            **{
                'spec': StackActions,
                'stack': self.stack,
                'describe.side_effect': self.describe_stack
            }
        )
        self.deployed_parameters = dict(self.parameters)
        self.deployed_tags = dict(self.tags)
        self.deployed_notification_arns = list(self.notifications)
        self.deployed_role_arn = self.role_arn

        self.command_capturer = Mock()
        self.differ = ImplementedStackDiffer(self.command_capturer)

    def describe_stack(self):
        return {
            'Stacks': [
                {
                    'StackName': self.stack.external_name,
                    'Parameters': [
                        {
                            'ParameterKey': key,
                            'ParameterValue': value,
                        }
                        for key, value in self.deployed_parameters.items()
                    ],
                    'StackStatus': 'CREATE_COMPLETE',
                    'NotificationARNs': self.deployed_notification_arns,
                    'RoleARN': self.deployed_role_arn,
                    'Tags': [
                        {
                            'Key': key,
                            'Value': value
                        }
                        for key, value in self.deployed_tags.items()
                    ],
                },
            ],
        }

    @property
    def expected_generated_config(self):
        return StackConfiguration(
            stack_name=self.external_name,
            parameters=self.parameters,
            stack_tags=self.tags,
            notifications=self.notifications,
            role_arn=self.role_arn
        )

    @property
    def expected_deployed_config(self):
        return StackConfiguration(
            stack_name=self.external_name,
            parameters=self.deployed_parameters,
            stack_tags=self.deployed_tags,
            notifications=self.deployed_notification_arns,
            role_arn=self.deployed_role_arn
        )

    def test_diff__compares_deployed_template_to_generated_template(self):
        self.differ.diff(self.actions)

        self.command_capturer.compare_templates.assert_called_with(
            self.actions.fetch_remote_template.return_value,
            self.actions.generate.return_value
        )

    def test_diff__template_diff_is_value_returned_by_implemented_differ(self):
        diff = self.differ.diff(self.actions)

        assert diff.template_diff == self.command_capturer.compare_templates.return_value

    def test_diff__compares_deployed_stack_config_to_generated_stack_config(self):
        self.deployed_parameters['new'] = 'value'

        self.differ.diff(self.actions)

        self.command_capturer.compare_stack_configurations.assert_called_with(
            self.expected_deployed_config,
            self.expected_generated_config
        )

    def test_diff__config_diff_is_value_returned_by_implemented_differ(self):
        diff = self.differ.diff(self.actions)

        assert diff.config_diff == self.command_capturer.compare_stack_configurations.return_value

    def test_diff__returned_diff_has_stack_name_of_external_name(self):
        diff = self.differ.diff(self.actions)
        assert diff.stack_name == self.external_name

    def test_diff__resolver_in_parameters__cannot_be_resolved__uses_resolvable_value(self):
        self.parameters_property.side_effect = StackDoesNotExistError()
        self.parameters.update(
            resolvable=ResolvableResolver(),
        )
        self.differ.diff(self.actions)
        expected_generated_config = self.expected_generated_config
        expected_generated_config.parameters['resolvable'] = ResolvableResolver.RESOLVED_VALUE

        self.command_capturer.compare_stack_configurations.assert_called_with(
            ANY,
            expected_generated_config
        )

    @pytest.mark.parametrize(
        'argument, resolved_value',
        [
            pytest.param('arg', '!UnresolvableResolver: arg', id='has argument'),
            pytest.param(
                {'test': 'this'},
                '!UnresolvableResolver: {\'test\': \'this\'}',
                id='has dict argument'
            ),
            pytest.param(None, '!UnresolvableResolver', id='no argument')
        ]
    )
    def test_diff__resolver_in_parameters__resolver_raises_stack_does_not_exist_error__uses_replacement_value(
        self,
        argument,
        resolved_value
    ):
        self.parameters_property.side_effect = StackDoesNotExistError()
        self.parameters.update(
            unresolvable=UnresolvableResolver(argument),
        )
        self.differ.diff(self.actions)
        expected_generated_config = self.expected_generated_config
        expected_generated_config.parameters['unresolvable'] = resolved_value
        self.command_capturer.compare_stack_configurations.assert_called_with(
            ANY,
            expected_generated_config
        )

    def test_diff__returns_generated_config(self):
        diff = self.differ.diff(self.actions)
        assert diff.generated_config == self.expected_generated_config

    def test_diff__returns_generated_template(self):
        diff = self.differ.diff(self.actions)
        assert diff.generated_template == self.actions.generate.return_value

    def test_diff__deployed_stack_exists__returns_is_deployed_as_true(self):
        diff = self.differ.diff(self.actions)
        assert diff.is_deployed is True

    def test_diff__deployed_stack_does_not_exist__returns_is_deployed_as_false(self):
        self.actions.describe.return_value = self.actions.describe.side_effect = None
        diff = self.differ.diff(self.actions)
        assert diff.is_deployed is False

    def test_diff__deployed_stack_does_not_exist__compares_none_to_generated_config(self):
        self.actions.describe.return_value = self.actions.describe.side_effect = None
        self.differ.diff(self.actions)

        self.command_capturer.compare_stack_configurations.assert_called_with(
            None,
            self.expected_generated_config
        )

    def test_diff__deployed_stack_does_not_exist__compares_empty_dict_string_to_generated_template(self):
        self.actions.fetch_remote_template.return_value = None
        self.differ.diff(self.actions)

        self.command_capturer.compare_templates.assert_called_with(
            '{}',
            self.actions.generate.return_value
        )
