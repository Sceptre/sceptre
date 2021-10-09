import difflib
import json
from typing import Union, Optional
from unittest.mock import Mock, PropertyMock, ANY

import cfn_flip
import pytest
import yaml

from sceptre.diffing.stack_differ import (
    StackDiffer,
    StackConfiguration,
    DiffType,
    DeepDiffStackDiffer,
    DifflibStackDiffer
)
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
        self.stack_status = 'CREATE_COMPLETE'

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
                    'StackStatus': self.stack_status,
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

    @pytest.mark.parametrize(
        'status',
        [
            pytest.param(status)
            for status in [
                'CREATE_FAILED',
                'ROLLBACK_COMPLETE',
                'DELETE_COMPLETE',
            ]
        ]
    )
    def test_diff__non_deployed_stack_status__compares_none_to_generated_config(self, status):
        self.stack_status = status
        self.differ.diff(self.actions)

        self.command_capturer.compare_stack_configurations.assert_called_with(
            None,
            self.expected_generated_config
        )

    @pytest.mark.parametrize(
        'status',
        [
            pytest.param(status)
            for status in [
                'CREATE_FAILED',
                'ROLLBACK_COMPLETE',
                'DELETE_COMPLETE',
            ]
        ]
    )
    def test_diff__non_deployed_stack_status__compares_empty_dict_string_to_generated_template(self, status):
        self.stack_status = status
        self.differ.diff(self.actions)
        self.command_capturer.compare_templates.assert_called_with(
            '{}',
            self.actions.generate.return_value
        )


class TestDeepDiffStackDiffer:

    def setup_method(self, method):
        self.differ = DeepDiffStackDiffer()

        self.config1 = StackConfiguration(
            stack_name='stack',
            parameters={'pk1': 'pv1'},
            stack_tags={'tk1': 'tv1'},
            notifications=['notification'],
            role_arn=None
        )

        self.config2 = StackConfiguration(
            stack_name='stack',
            parameters={'pk1': 'pv1', 'pk2': 'pv2'},
            stack_tags={'tk1': 'tv1'},
            notifications=['notification'],
            role_arn='new_role'
        )

        self.template_dict_1 = {
            'AWSTemplateFormat': '2010-09-09',
            'Description': 'deployed',
            'Parameters': {'pk1': 'pv1'},
            'Resources': {}
        }
        self.template_dict_2 = {
            'AWSTemplateFormat': '2010-09-09',
            'Description': 'deployed',
            'Parameters': {'pk1': 'pv1'},
            'Resources': {
                'MyBucket': {
                    'Type': 'AWS::S3::Bucket',
                    'Properties': {
                        'BucketName': 'test'
                    }
                }
            }
        }

    def test_compare_stack_configurations__returns_deepdiff_of_deployed_and_generated(self):
        comparison = self.differ.compare_stack_configurations(self.config1, self.config2)
        assert comparison.t1 == self.config1
        assert comparison.t2 == self.config2

    def test_compare_stack_configurations__returned_deepdiff_has_verbosity_of_2(self):
        comparison = self.differ.compare_stack_configurations(self.config1, self.config2)
        assert comparison.verbose_level == 2

    def test_compare_stack_configurations__deployed_is_none__returns_deepdiff_with_none_for_t1(self):
        comparison = self.differ.compare_stack_configurations(None, self.config2)
        assert comparison.t1 is None

    @pytest.mark.parametrize(
        't1_serializer, t2_serializer',
        [
            pytest.param(json.dumps, json.dumps, id='templates are json'),
            pytest.param(yaml.dump, yaml.dump, id='templates are yaml'),
            pytest.param(json.dumps, yaml.dump, id="templates are mixed formats"),
        ]
    )
    def test_compare_templates__templates_are_json__returns_deepdiff_of_dicts(
        self,
        t1_serializer,
        t2_serializer
    ):
        template1, template2 = t1_serializer(self.template_dict_1), t2_serializer(self.template_dict_2)
        comparison = self.differ.compare_templates(template1, template2)
        assert comparison.t1 == self.template_dict_1
        assert comparison.t2 == self.template_dict_2

    def test_compare_templates__templates_are_yaml_with_intrinsic_functions__returns_deepdiff_of_dicts(self):
        template = """
            Resources:
              MyBucket:
                Type: AWS::S3::Bucket
                Properties:
                  BucketName: !Ref MyParam
        """
        comparison = self.differ.compare_templates(template, template)

        expected = cfn_flip.load_yaml(template)
        assert (comparison.t1, comparison.t2) == (expected, expected)

    def test_compare_templates__deployed_is_empty_dict_string__returns_deepdiff_with_empty_dict_for_t1(self):
        template = json.dumps(self.template_dict_1)
        comparison = self.differ.compare_templates('{}', template)
        assert comparison.t1 == {}


class TestDifflibStackDiffer:

    def setup_method(self, method):
        self.serialize = cfn_flip.dump_yaml
        self.differ = DifflibStackDiffer()
        self.config1 = StackConfiguration(
            stack_name='stack',
            parameters={'pk1': 'pv1'},
            stack_tags={'tk1': 'tv1'},
            notifications=['notification'],
            role_arn=None
        )

        self.config2 = StackConfiguration(
            stack_name='stack',
            parameters={'pk1': 'pv1', 'pk2': 'pv2'},
            stack_tags={'tk1': 'tv1'},
            notifications=['notification'],
            role_arn='new_role'
        )

        self.template_dict_1 = {
            'AWSTemplateFormat': '2010-09-09',
            'Description': 'deployed',
            'Parameters': {'pk1': 'pv1'},
            'Resources': {}
        }
        self.template_dict_2 = {
            'AWSTemplateFormat': '2010-09-09',
            'Description': 'deployed',
            'Parameters': {'pk1': 'pv1'},
            'Resources': {
                'MyBucket': {
                    'Type': 'AWS::S3::Bucket',
                    'Properties': {
                        'BucketName': 'test'
                    }
                }
            }
        }

    def create_expected_diff(self, first, second):
        deployed_dict, deployed_format = cfn_flip.load(first)
        generated_dict, generated_format = cfn_flip.load(second)
        dumpers = {
            'json': cfn_flip.dump_json,
            'yaml': cfn_flip.dump_yaml
        }
        first_reformatted = dumpers[generated_format](deployed_dict)
        second_reformatted = dumpers[generated_format](generated_dict)
        first_list, second_list = first_reformatted.splitlines(), second_reformatted.splitlines()
        return list(difflib.unified_diff(
            first_list,
            second_list,
            fromfile='deployed',
            tofile='generated',
            lineterm=''
        ))

    def test_compare_stack_configurations__returns_diff_of_deployed_and_generated_when_converted_to_dicts(self):
        comparison = self.differ.compare_stack_configurations(self.config1, self.config2)
        expected_config_1 = self.serialize(self.config1._asdict())
        expected_config_2 = self.serialize(self.config2._asdict())
        expected = self.create_expected_diff(expected_config_1, expected_config_2)

        assert comparison == expected

    def test_compare_stack_configurations__deployed_is_none__returns_diff_with_none(self):
        comparison = self.differ.compare_stack_configurations(None, self.config2)
        expected = self.create_expected_diff(self.serialize({}), self.serialize(self.config2._asdict()))
        assert comparison == expected

    @pytest.mark.parametrize(
        'serializer',
        [
            pytest.param(json.dumps, id='templates are json'),
            pytest.param(yaml.dump, id='templates are yaml'),
        ]
    )
    def test_compare_templates__templates_are_json__returns_deepdiff_of_dicts(
        self,
        serializer,
    ):
        template1, template2 = serializer(self.template_dict_1), serializer(self.template_dict_2)
        comparison = self.differ.compare_templates(template1, template2)
        expected = self.create_expected_diff(template1, template2)
        assert comparison == expected

    def test_compare_templates__deployed_is_empty_dict_string__returns_diff_with_empty_string(self):
        template = json.dumps(self.template_dict_1)
        comparison = self.differ.compare_templates('{}', template)
        expected = self.create_expected_diff('{}', template)
        assert comparison == expected

    def test_compare_templates__json_template__only_indentation_diff__returns_no_diff(self):
        template1 = json.dumps(self.template_dict_1, indent=2)
        template2 = json.dumps(self.template_dict_1, indent=4)
        comparison = self.differ.compare_templates(template1, template2)
        assert len(comparison) == 0

    def test_compare_templates__yaml_template__only_indentation_diff__returns_no_diff(self):
        template1 = yaml.dump(self.template_dict_1, indent=2)
        template2 = yaml.dump(self.template_dict_1, indent=4)
        comparison = self.differ.compare_templates(template1, template2)
        assert len(comparison) == 0

    def test_compare_templates__opposite_template_types_but_identical_template__returns_no_diff(self):
        template1 = json.dumps(self.template_dict_1)
        template2 = yaml.dump(self.template_dict_1)
        comparison = self.differ.compare_templates(template1, template2)
        assert len(comparison) == 0
