import difflib
import json
from collections import defaultdict
from copy import deepcopy
from typing import Union, Optional
from unittest.mock import Mock, PropertyMock, ANY, DEFAULT

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

    def __init__(self, argument=None, stack=None):
        # we don't want to call super().__init__ since you can't deepcopy resolvers with locks in py36
        self.argument = argument

    def resolve(self):
        return self.RESOLVED_VALUE


class UnresolvableResolver(Resolver):
    def __init__(self, argument=None, stack=None):
        # we don't want to call super().__init__ since you can't deepcopy resolvers with locks in py36
        self.argument = argument

    def resolve(self):
        raise StackDoesNotExistError()


class ImplementedStackDiffer(StackDiffer):

    def __init__(self, command_capturer: Mock):
        super().__init__()
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
        self.parameters_on_stack_config = {
            'param': 'some_value'
        }
        self.tags = {
            'tag_name': 'tag_value'
        }
        self.notifications = [
            'notification_arn1'
        ]
        self.sceptre_user_data = {}

        self.deployed_parameters = deepcopy(self.parameters_on_stack_config)
        self.deployed_parameter_defaults = {}
        self.deployed_no_echo_parameters = []
        self.deployed_parameter_types = defaultdict(lambda: 'String')
        self.local_no_echo_parameters = []
        self.deployed_tags = dict(self.tags)
        self.deployed_notification_arns = list(self.notifications)
        self.deployed_role_arn = self.role_arn

        self.command_capturer = Mock()
        self.differ = ImplementedStackDiffer(self.command_capturer)
        self.stack_status = 'CREATE_COMPLETE'

        self._stack = None
        self._actions = None
        self._parameters = None

    @property
    def parameters_on_stack(self):
        if self._parameters is None:
            self._parameters = deepcopy(self.parameters_on_stack_config)
        return self._parameters

    @property
    def stack(self) -> Union[Stack, Mock]:
        if not self._stack:
            self._stack = Mock(
                spec=Stack,
                external_name=self.external_name,
                _parameters=self.parameters_on_stack,
                role_arn=self.role_arn,
                tags=self.tags,
                notifications=self.notifications,
                __sceptre_user_data=self.sceptre_user_data
            )
            self._stack.name = self.name
            type(self._stack).parameters = PropertyMock(side_effect=lambda: self.parameters_on_stack)
        return self._stack

    @property
    def actions(self) -> Union[StackActions, Mock]:
        if not self._actions:
            self._actions = Mock(
                **{
                    'spec': StackActions,
                    'stack': self.stack,
                    'describe.side_effect': self.describe_stack,
                    'fetch_remote_template_summary.side_effect': self.get_remote_template_summary,
                    'fetch_local_template_summary.side_effect': self.get_local_template_summary,
                }
            )
        return self._actions

    def describe_stack(self):
        return {
            'Stacks': [
                {
                    'StackName': self.stack.external_name,
                    'Parameters': [
                        {
                            'ParameterKey': key,
                            'ParameterValue': value,
                            'ResolvedValue': "I'm resolved and don't matter for the diff!"
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

    def get_remote_template_summary(self):
        params = []
        for param, value in self.deployed_parameters.items():
            entry = {
                'ParameterKey': param,
                'ParameterType': self.deployed_parameter_types[param]
            }
            if param in self.deployed_parameter_defaults:
                default_value = self.deployed_parameter_defaults[param]
                if 'List' in entry['ParameterType']:
                    default_value = ', '.join(val.strip() for val in default_value.split(','))
                entry['DefaultValue'] = default_value
            if param in self.deployed_no_echo_parameters:
                entry['NoEcho'] = True

            params.append(entry)

        return {
            'Parameters': params
        }

    def get_local_template_summary(self):
        params = []
        for param, value in self.parameters_on_stack.items():
            entry = {
                'ParameterKey': param
            }
            if param in self.local_no_echo_parameters:
                entry['NoEcho'] = True
            params.append(entry)

        return {
            'Parameters': params
        }

    @property
    def expected_generated_config(self):
        return StackConfiguration(
            stack_name=self.external_name,
            parameters=self.parameters_on_stack_config,
            stack_tags=deepcopy(self.tags),
            notifications=deepcopy(self.notifications),
            role_arn=self.role_arn
        )

    @property
    def expected_deployed_config(self):
        return StackConfiguration(
            stack_name=self.external_name,
            parameters=self.deployed_parameters,
            stack_tags=deepcopy(self.deployed_tags),
            notifications=deepcopy(self.deployed_notification_arns),
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

    def test_diff__resolver_in_parameters__can_be_resolved__uses_resolved_value(self):
        self.parameters_on_stack_config.update(
            resolvable=ResolvableResolver(),
        )
        self.differ.diff(self.actions)
        expected_generated_config = self.expected_generated_config
        expected_generated_config.parameters['resolvable'] = ResolvableResolver.RESOLVED_VALUE

        self.command_capturer.compare_stack_configurations.assert_called_with(
            ANY,
            expected_generated_config
        )

    def test_diff__list_of_resolvers_in_parameters__resolves_each_of_them(self):
        self.parameters_on_stack_config.update(
            list_of_resolvers=[
                ResolvableResolver(),
                ResolvableResolver()
            ]
        )
        self.differ.diff(self.actions)
        expected_generated_config = self.expected_generated_config
        expected_generated_config.parameters['list_of_resolvers'] = ','.join([
            ResolvableResolver.RESOLVED_VALUE,
            ResolvableResolver.RESOLVED_VALUE
        ])

        self.command_capturer.compare_stack_configurations.assert_called_with(
            ANY,
            expected_generated_config
        )

    @pytest.mark.parametrize(
        'argument, resolved_value',
        [
            pytest.param('arg', '{ !UnresolvableResolver(arg) }', id='has argument'),
            pytest.param(
                {'test': 'this'},
                '{ !UnresolvableResolver({\'test\': \'this\'}) }',
                id='has dict argument'
            ),
            pytest.param(None, '{ !UnresolvableResolver }', id='no argument')
        ]
    )
    def test_diff__resolver_in_parameters__resolver_raises_error__uses_replacement_value(
        self,
        argument,
        resolved_value
    ):
        self.parameters_on_stack_config.update(
            unresolvable=UnresolvableResolver(argument),
        )
        self.differ.diff(self.actions)
        expected_generated_config = self.expected_generated_config
        expected_generated_config.parameters['unresolvable'] = resolved_value
        self.command_capturer.compare_stack_configurations.assert_called_with(
            ANY,
            expected_generated_config
        )

    def test_diff__list_of_resolvers_in_parameters__some_cannot_be_resolved__uses_replacement_value(self):
        self.parameters_on_stack_config.update(
            list_of_resolvers=[
                ResolvableResolver(),
                UnresolvableResolver()
            ]
        )
        self.differ.diff(self.actions)
        expected_generated_config = self.expected_generated_config
        expected_generated_config.parameters['list_of_resolvers'] = ','.join([
            ResolvableResolver.RESOLVED_VALUE,
            '{ !UnresolvableResolver }'
        ])

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

    def test_diff__deployed_stack_has_default_values__doesnt_pass_parameter__compares_identical_configs(self):
        self.deployed_parameters['new'] = 'default value'
        self.deployed_parameter_defaults['new'] = 'default value'
        self.differ.diff(self.actions)
        self.command_capturer.compare_stack_configurations.assert_called_with(
            self.expected_generated_config,
            self.expected_generated_config
        )

    def test_diff__deployed_stack_has_list_default_parameter__doesnt_pass_parameter__compares_identical_configs(self):
        self.deployed_parameters['new'] = 'first,second,third'
        self.deployed_parameter_defaults['new'] = 'first, second, third'
        self.deployed_parameter_types['new'] = 'CommaDelimitedList'
        self.differ.diff(self.actions)

        self.command_capturer.compare_stack_configurations.assert_called_with(
            self.expected_generated_config,
            self.expected_generated_config
        )

    def test_diff__deployed_stack_has_default_values__passes_the_parameter__compares_identical_configs(self):
        self.deployed_parameters['new'] = 'default value'
        self.deployed_parameter_defaults['new'] = 'default value'
        self.parameters_on_stack_config['new'] = 'default value'
        self.differ.diff(self.actions)
        self.command_capturer.compare_stack_configurations.assert_called_with(
            self.expected_generated_config,
            self.expected_generated_config
        )

    def test_diff__deployed_stack_has_default_values__passes_different_value__compares_different_configs(self):
        self.deployed_parameters['new'] = 'default value'
        self.deployed_parameter_defaults['new'] = 'default value'
        self.parameters_on_stack_config['new'] = 'custom value'
        self.differ.diff(self.actions)
        self.command_capturer.compare_stack_configurations.assert_called_with(
            self.expected_deployed_config,
            self.expected_generated_config
        )

    def test_diff__stack_exists_with_same_config_but_template_does_not__compares_identical_configs(self):
        self.actions.fetch_remote_template_summary.side_effect = None
        self.actions.fetch_remote_template_summary.return_value = None
        self.actions.fetch_remote_template.return_value = None
        self.differ.diff(self.actions)
        self.command_capturer.compare_stack_configurations.assert_called_with(
            self.expected_generated_config,
            self.expected_generated_config
        )

    def test_diff__deployed_parameter_has_linebreak_but_otherwise_no_difference__compares_identical_configs(self):
        self.deployed_parameters['param'] = self.deployed_parameters['param'] + '\n'
        self.differ.diff(self.actions)
        self.command_capturer.compare_stack_configurations.assert_called_with(
            self.expected_generated_config,
            self.expected_generated_config
        )

    def test_diff__no_echo_default_parameter__generated_stack_doesnt_pass_parameter__compares_identical_configs(self):
        self.deployed_parameters['new'] = '****'
        self.deployed_parameter_defaults['new'] = 'default value'
        self.deployed_no_echo_parameters.append('new')
        self.differ.diff(self.actions)
        self.command_capturer.compare_stack_configurations.assert_called_with(
            self.expected_generated_config,
            self.expected_generated_config
        )

    def test_diff__generated_template_has_no_echo_parameter__masks_value(self):
        self.parameters_on_stack_config['hide_me'] = "don't look at me!"
        self.local_no_echo_parameters.append('hide_me')

        expected_generated_config = self.expected_generated_config
        expected_generated_config.parameters['hide_me'] = StackDiffer.NO_ECHO_REPLACEMENT

        self.differ.diff(self.actions)

        self.command_capturer.compare_stack_configurations.assert_called_with(
            self.expected_deployed_config,
            expected_generated_config,
        )

    def test_diff__generated_template_has_no_echo_parameter__show_no_echo__shows_value(self):
        self.parameters_on_stack_config['hide_me'] = "don't look at me!"
        self.local_no_echo_parameters.append('hide_me')
        self.differ.show_no_echo = True
        self.differ.diff(self.actions)

        self.command_capturer.compare_stack_configurations.assert_called_with(
            self.expected_deployed_config,
            self.expected_generated_config,
        )

    def test_diff__local_generation_raises_an_error__replaces_unresolvable_sceptre_user_data(self):
        has_raised = False

        def generate():
            nonlocal has_raised
            if not has_raised:
                has_raised = True
                raise ValueError()
            return DEFAULT

        unresolvable_mock = Mock(**{
            'spec': Resolver,
            'argument': 'test',
            'resolve.side_effect': RuntimeError()
        })
        self.sceptre_user_data.update(
            unresolvable=unresolvable_mock
        )
        self.actions.generate.side_effect = generate

        self.differ.diff(self.actions)

        assert self.sceptre_user_data['unresolvable'] == 'Mocktest'

    def test_diff__local_generation_raises_an_error__resolves_resolvable_sceptre_user_data(self):
        has_raised = False

        def generate():
            nonlocal has_raised
            if not has_raised:
                has_raised = True
                raise ValueError()
            return DEFAULT

        resolvable_mock = Mock(
            **{
                'spec': Resolver,
                'argument': 'test',
                'resolve.return_value': 'resolved'
            }
        )
        self.sceptre_user_data.update(
            resolvable=resolvable_mock
        )
        self.actions.generate.side_effect = generate

        self.differ.diff(self.actions)

        assert self.sceptre_user_data['resolvable'] == 'resolved'

    def test_diff__local_generation_raises_an_error__reattempts_generation(self):
        has_raised = False

        def generate():
            nonlocal has_raised
            if not has_raised:
                has_raised = True
                raise ValueError()
            return DEFAULT

        resolvable_mock = Mock(
            **{
                'spec': Resolver,
                'argument': 'test',
                'resolve.return_value': 'resolved'
            }
        )
        self.sceptre_user_data.update(
            resolvable=resolvable_mock
        )
        self.actions.generate.side_effect = generate

        self.differ.diff(self.actions)

        assert self.actions.generate.call_count == 2

    def test_diff__local_generation_raises_an_error_twice__raises_exception(self):
        resolvable_mock = Mock(
            **{
                'spec': Resolver,
                'argument': 'test',
                'resolve.return_value': 'resolved'
            }
        )
        self.sceptre_user_data.update(
            resolvable=resolvable_mock
        )
        self.actions.generate.side_effect = ValueError()

        with pytest.raises(ValueError):
            self.differ.diff(self.actions)

        assert self.actions.generate.call_count == 2


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

    def create_expected_diff(self, first, second, already_formatted=False):
        if not already_formatted:
            deployed_dict, deployed_format = cfn_flip.load(first)
            generated_dict, generated_format = cfn_flip.load(second)
            dumpers = {
                'json': cfn_flip.dump_json,
                'yaml': cfn_flip.dump_yaml
            }
            first = dumpers[generated_format](deployed_dict)
            second = dumpers[generated_format](generated_dict)
        first_list, second_list = first.splitlines(), second.splitlines()
        return list(difflib.unified_diff(
            first_list,
            second_list,
            fromfile='deployed',
            tofile='generated',
            lineterm=''
        ))

    def test_compare_stack_configurations__returns_diff_of_deployed_and_generated_when_converted_to_dicts(self):
        comparison = self.differ.compare_stack_configurations(self.config1, self.config2)
        expected_config_1_dict = self.make_config_comparable(self.config1)
        expected_config_2_dict = self.make_config_comparable(self.config2)
        expected_config_1 = self.serialize(expected_config_1_dict)
        expected_config_2 = self.serialize(expected_config_2_dict)
        expected = self.create_expected_diff(expected_config_1, expected_config_2)

        assert comparison == expected

    def make_config_comparable(self, config: StackConfiguration):
        config_dict = dict(config._asdict())
        without_empty_values = {
            key: value
            for key, value in config_dict.items()
            if value not in (None, [], {}) and key != 'stack_name'
        }
        return without_empty_values

    def test_compare_stack_configurations__deployed_is_none__returns_diff_with_none(self):
        comparison = self.differ.compare_stack_configurations(None, self.config2)
        expected = self.create_expected_diff(
            self.serialize(None),
            self.serialize(self.make_config_comparable(self.config2))
        )
        assert comparison == expected

    def test_compare_stack_configurations__deployed_is_none__all_configs_are_falsey__returns_diff_with_none(self):
        empty_config = StackConfiguration(
            stack_name='stack',
            parameters={},
            stack_tags={},
            notifications=[],
            role_arn=None
        )
        comparison = self.differ.compare_stack_configurations(None, empty_config)

        expected = self.create_expected_diff(
            self.serialize(None),
            self.serialize(self.make_config_comparable(empty_config)),
            already_formatted=True
        )
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
