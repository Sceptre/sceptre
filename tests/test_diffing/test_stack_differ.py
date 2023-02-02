import difflib
import json
from collections import defaultdict
from copy import deepcopy
from typing import Union, Optional
from unittest.mock import Mock, PropertyMock

import cfn_flip
import pytest
import yaml

from sceptre.diffing.stack_differ import (
    StackDiffer,
    StackConfiguration,
    DiffType,
    DeepDiffStackDiffer,
    DifflibStackDiffer,
)
from sceptre.plan.actions import StackActions
from sceptre.stack import Stack


class ImplementedStackDiffer(StackDiffer):
    def __init__(self, command_capturer: Mock):
        super().__init__()
        self.command_capturer = command_capturer

    def compare_templates(self, deployed: str, generated: str) -> DiffType:
        return self.command_capturer.compare_templates(deployed, generated)

    def compare_stack_configurations(
        self, deployed: Optional[StackConfiguration], generated: StackConfiguration
    ) -> DiffType:
        return self.command_capturer.compare_stack_configurations(deployed, generated)


class TestStackDiffer:
    def setup_method(self, method):
        self.name = "my/stack"
        self.external_name = "full-stack-name"
        self.cloudformation_service_role = "cloudformation_service_role"
        self.parameters_on_stack_config = {"param": "some_value"}
        self.tags = {"tag_name": "tag_value"}
        self.notifications = ["notification_arn1"]
        self.sceptre_user_data = {}

        self.deployed_parameters = deepcopy(self.parameters_on_stack_config)
        self.deployed_parameter_defaults = {}
        self.deployed_no_echo_parameters = []
        self.deployed_parameter_types = defaultdict(lambda: "String")
        self.local_no_echo_parameters = []
        self.deployed_tags = dict(self.tags)
        self.deployed_notification_arns = list(self.notifications)
        self.deployed_cloudformation_service_role = self.cloudformation_service_role

        self.command_capturer = Mock()
        self.differ = ImplementedStackDiffer(self.command_capturer)
        self.stack_status = "CREATE_COMPLETE"

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
                cloudformation_service_role=self.cloudformation_service_role,
                tags=self.tags,
                notifications=self.notifications,
                __sceptre_user_data=self.sceptre_user_data,
            )
            self._stack.name = self.name
            type(self._stack).parameters = PropertyMock(
                side_effect=lambda: self.parameters_on_stack
            )
        return self._stack

    @property
    def actions(self) -> Union[StackActions, Mock]:
        if not self._actions:
            self._actions = Mock(
                **{
                    "spec": StackActions,
                    "stack": self.stack,
                    "describe.side_effect": self.describe_stack,
                    "fetch_remote_template_summary.side_effect": self.get_remote_template_summary,
                    "fetch_local_template_summary.side_effect": self.get_local_template_summary,
                }
            )
        return self._actions

    def describe_stack(self):
        return {
            "Stacks": [
                {
                    "StackName": self.stack.external_name,
                    "Parameters": [
                        {
                            "ParameterKey": key,
                            "ParameterValue": value,
                            "ResolvedValue": "I'm resolved and don't matter for the diff!",
                        }
                        for key, value in self.deployed_parameters.items()
                    ],
                    "StackStatus": self.stack_status,
                    "NotificationARNs": self.deployed_notification_arns,
                    "RoleARN": self.deployed_cloudformation_service_role,
                    "Tags": [
                        {"Key": key, "Value": value}
                        for key, value in self.deployed_tags.items()
                    ],
                },
            ],
        }

    def get_remote_template_summary(self):
        params = []
        for param, value in self.deployed_parameters.items():
            entry = {
                "ParameterKey": param,
                "ParameterType": self.deployed_parameter_types[param],
            }
            if param in self.deployed_parameter_defaults:
                default_value = self.deployed_parameter_defaults[param]
                if "List" in entry["ParameterType"]:
                    default_value = ", ".join(
                        val.strip() for val in default_value.split(",")
                    )
                entry["DefaultValue"] = default_value
            if param in self.deployed_no_echo_parameters:
                entry["NoEcho"] = True

            params.append(entry)

        return {"Parameters": params}

    def get_local_template_summary(self):
        params = []
        for param, value in self.parameters_on_stack.items():
            entry = {"ParameterKey": param}
            if param in self.local_no_echo_parameters:
                entry["NoEcho"] = True
            params.append(entry)

        return {"Parameters": params}

    @property
    def expected_generated_config(self):
        return StackConfiguration(
            stack_name=self.external_name,
            parameters=self.parameters_on_stack_config,
            stack_tags=deepcopy(self.tags),
            notifications=deepcopy(self.notifications),
            cloudformation_service_role=self.cloudformation_service_role,
        )

    @property
    def expected_deployed_config(self):
        return StackConfiguration(
            stack_name=self.external_name,
            parameters=self.deployed_parameters,
            stack_tags=deepcopy(self.deployed_tags),
            notifications=deepcopy(self.deployed_notification_arns),
            cloudformation_service_role=self.deployed_cloudformation_service_role,
        )

    def test_diff__compares_deployed_template_to_generated_template(self):
        self.differ.diff(self.actions)

        self.command_capturer.compare_templates.assert_called_with(
            self.actions.fetch_remote_template.return_value,
            self.actions.generate.return_value,
        )

    def test_diff__template_diff_is_value_returned_by_implemented_differ(self):
        diff = self.differ.diff(self.actions)

        assert (
            diff.template_diff == self.command_capturer.compare_templates.return_value
        )

    def test_diff__compares_deployed_stack_config_to_generated_stack_config(self):
        self.deployed_parameters["new"] = "value"

        self.differ.diff(self.actions)

        self.command_capturer.compare_stack_configurations.assert_called_with(
            self.expected_deployed_config, self.expected_generated_config
        )

    def test_diff__config_diff_is_value_returned_by_implemented_differ(self):
        diff = self.differ.diff(self.actions)

        assert (
            diff.config_diff
            == self.command_capturer.compare_stack_configurations.return_value
        )

    def test_diff__returned_diff_has_stack_name_of_external_name(self):
        diff = self.differ.diff(self.actions)
        assert diff.stack_name == self.external_name

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

    def test_diff__deployed_stack_does_not_exist__compares_none_to_generated_config(
        self,
    ):
        self.actions.describe.return_value = self.actions.describe.side_effect = None
        self.differ.diff(self.actions)

        self.command_capturer.compare_stack_configurations.assert_called_with(
            None, self.expected_generated_config
        )

    def test_diff__deployed_stack_does_not_exist__compares_empty_dict_string_to_generated_template(
        self,
    ):
        self.actions.fetch_remote_template.return_value = None
        self.differ.diff(self.actions)

        self.command_capturer.compare_templates.assert_called_with(
            "{}", self.actions.generate.return_value
        )

    @pytest.mark.parametrize(
        "status",
        [
            pytest.param(status)
            for status in [
                "CREATE_FAILED",
                "ROLLBACK_COMPLETE",
                "DELETE_COMPLETE",
            ]
        ],
    )
    def test_diff__non_deployed_stack_status__compares_none_to_generated_config(
        self, status
    ):
        self.stack_status = status
        self.differ.diff(self.actions)

        self.command_capturer.compare_stack_configurations.assert_called_with(
            None, self.expected_generated_config
        )

    @pytest.mark.parametrize(
        "status",
        [
            pytest.param(status)
            for status in [
                "CREATE_FAILED",
                "ROLLBACK_COMPLETE",
                "DELETE_COMPLETE",
            ]
        ],
    )
    def test_diff__non_deployed_stack_status__compares_empty_dict_string_to_generated_template(
        self, status
    ):
        self.stack_status = status
        self.differ.diff(self.actions)
        self.command_capturer.compare_templates.assert_called_with(
            "{}", self.actions.generate.return_value
        )

    def test_diff__deployed_stack_has_default_values__doesnt_pass_parameter__compares_identical_configs(
        self,
    ):
        self.deployed_parameters["new"] = "default value"
        self.deployed_parameter_defaults["new"] = "default value"
        self.differ.diff(self.actions)
        self.command_capturer.compare_stack_configurations.assert_called_with(
            self.expected_generated_config, self.expected_generated_config
        )

    def test_diff__deployed_stack_has_list_default_parameter__doesnt_pass_parameter__compares_identical_configs(
        self,
    ):
        self.deployed_parameters["new"] = "first,second,third"
        self.deployed_parameter_defaults["new"] = "first, second, third"
        self.deployed_parameter_types["new"] = "CommaDelimitedList"
        self.differ.diff(self.actions)

        self.command_capturer.compare_stack_configurations.assert_called_with(
            self.expected_generated_config, self.expected_generated_config
        )

    def test_diff__deployed_stack_has_default_values__passes_the_parameter__compares_identical_configs(
        self,
    ):
        self.deployed_parameters["new"] = "default value"
        self.deployed_parameter_defaults["new"] = "default value"
        self.parameters_on_stack_config["new"] = "default value"
        self.differ.diff(self.actions)
        self.command_capturer.compare_stack_configurations.assert_called_with(
            self.expected_generated_config, self.expected_generated_config
        )

    def test_diff__deployed_stack_has_default_values__passes_different_value__compares_different_configs(
        self,
    ):
        self.deployed_parameters["new"] = "default value"
        self.deployed_parameter_defaults["new"] = "default value"
        self.parameters_on_stack_config["new"] = "custom value"
        self.differ.diff(self.actions)
        self.command_capturer.compare_stack_configurations.assert_called_with(
            self.expected_deployed_config, self.expected_generated_config
        )

    def test_diff__stack_exists_with_same_config_but_template_does_not__compares_identical_configs(
        self,
    ):
        self.actions.fetch_remote_template_summary.side_effect = None
        self.actions.fetch_remote_template_summary.return_value = None
        self.actions.fetch_remote_template.return_value = None
        self.differ.diff(self.actions)
        self.command_capturer.compare_stack_configurations.assert_called_with(
            self.expected_generated_config, self.expected_generated_config
        )

    def test_diff__deployed_parameter_has_linebreak_but_otherwise_no_difference__compares_identical_configs(
        self,
    ):
        self.deployed_parameters["param"] = self.deployed_parameters["param"] + "\n"
        self.differ.diff(self.actions)
        self.command_capturer.compare_stack_configurations.assert_called_with(
            self.expected_generated_config, self.expected_generated_config
        )

    def test_diff__parameter_has_identical_string_linebreak__compares_identical_configs(
        self,
    ):
        self.deployed_parameters["param"] = self.deployed_parameters["param"] + "\n"
        self.parameters_on_stack_config["param"] = (
            self.parameters_on_stack_config["param"] + "\n"
        )

        self.differ.diff(self.actions)
        generated_config = deepcopy(self.expected_generated_config._asdict())
        generated_parameters = generated_config.pop("parameters")
        expected_config = StackConfiguration(
            parameters={
                key: value.rstrip("\n") for key, value in generated_parameters.items()
            },
            **generated_config,
        )

        self.command_capturer.compare_stack_configurations.assert_called_with(
            expected_config, expected_config
        )

    def test_diff__parameter_has_identical_list_linebreaks__compares_identical_configs(
        self,
    ):
        self.deployed_parameter_types["param"] = "CommaDelimitedList"
        self.deployed_parameters["param"] = "testing\n,this\n,out\n"
        self.parameters_on_stack_config["param"] = ["testing\n", "this\n", "out\n"]

        self.differ.diff(self.actions)
        generated_config = deepcopy(self.expected_generated_config._asdict())
        generated_parameters = generated_config.pop("parameters")
        generated_parameters["param"] = "testing,this,out"
        expected_config = StackConfiguration(
            parameters=generated_parameters,
            **generated_config,
        )

        self.command_capturer.compare_stack_configurations.assert_called_with(
            expected_config, expected_config
        )

    def test_diff__no_echo_default_parameter__generated_stack_doesnt_pass_parameter__compares_identical_configs(
        self,
    ):
        self.deployed_parameters["new"] = "****"
        self.deployed_parameter_defaults["new"] = "default value"
        self.deployed_no_echo_parameters.append("new")
        self.differ.diff(self.actions)
        self.command_capturer.compare_stack_configurations.assert_called_with(
            self.expected_generated_config, self.expected_generated_config
        )

    def test_diff__generated_template_has_no_echo_parameter__masks_value(self):
        self.parameters_on_stack_config["hide_me"] = "don't look at me!"
        self.local_no_echo_parameters.append("hide_me")

        expected_generated_config = self.expected_generated_config
        expected_generated_config.parameters[
            "hide_me"
        ] = StackDiffer.NO_ECHO_REPLACEMENT

        self.differ.diff(self.actions)

        self.command_capturer.compare_stack_configurations.assert_called_with(
            self.expected_deployed_config,
            expected_generated_config,
        )

    def test_diff__generated_template_has_no_echo_parameter__show_no_echo__shows_value(
        self,
    ):
        self.parameters_on_stack_config["hide_me"] = "don't look at me!"
        self.local_no_echo_parameters.append("hide_me")
        self.differ.show_no_echo = True
        self.differ.diff(self.actions)

        self.command_capturer.compare_stack_configurations.assert_called_with(
            self.expected_deployed_config,
            self.expected_generated_config,
        )


class TestDeepDiffStackDiffer:
    def setup_method(self, method):
        self.differ = DeepDiffStackDiffer()

        self.config1 = StackConfiguration(
            stack_name="stack",
            parameters={"pk1": "pv1"},
            stack_tags={"tk1": "tv1"},
            notifications=["notification"],
            cloudformation_service_role=None,
        )

        self.config2 = StackConfiguration(
            stack_name="stack",
            parameters={"pk1": "pv1", "pk2": "pv2"},
            stack_tags={"tk1": "tv1"},
            notifications=["notification"],
            cloudformation_service_role="new_role",
        )

        self.template_dict_1 = {
            "AWSTemplateFormat": "2010-09-09",
            "Description": "deployed",
            "Parameters": {"pk1": "pv1"},
            "Resources": {},
        }
        self.template_dict_2 = {
            "AWSTemplateFormat": "2010-09-09",
            "Description": "deployed",
            "Parameters": {"pk1": "pv1"},
            "Resources": {
                "MyBucket": {
                    "Type": "AWS::S3::Bucket",
                    "Properties": {"BucketName": "test"},
                }
            },
        }

    def test_compare_stack_configurations__returns_deepdiff_of_deployed_and_generated(
        self,
    ):
        comparison = self.differ.compare_stack_configurations(
            self.config1, self.config2
        )
        assert comparison.t1 == self.config1
        assert comparison.t2 == self.config2

    def test_compare_stack_configurations__returned_deepdiff_has_verbosity_of_2(self):
        comparison = self.differ.compare_stack_configurations(
            self.config1, self.config2
        )
        assert comparison.verbose_level == 2

    def test_compare_stack_configurations__deployed_is_none__returns_deepdiff_with_none_for_t1(
        self,
    ):
        comparison = self.differ.compare_stack_configurations(None, self.config2)
        assert comparison.t1 is None

    @pytest.mark.parametrize(
        "t1_serializer, t2_serializer",
        [
            pytest.param(json.dumps, json.dumps, id="templates are json"),
            pytest.param(yaml.dump, yaml.dump, id="templates are yaml"),
            pytest.param(json.dumps, yaml.dump, id="templates are mixed formats"),
        ],
    )
    def test_compare_templates__templates_are_json__returns_deepdiff_of_dicts(
        self, t1_serializer, t2_serializer
    ):
        template1, template2 = t1_serializer(self.template_dict_1), t2_serializer(
            self.template_dict_2
        )
        comparison = self.differ.compare_templates(template1, template2)
        assert comparison.t1 == self.template_dict_1
        assert comparison.t2 == self.template_dict_2

    def test_compare_templates__templates_are_yaml_with_intrinsic_functions__returns_deepdiff_of_dicts(
        self,
    ):
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

    def test_compare_templates__deployed_is_empty_dict_string__returns_deepdiff_with_empty_dict_for_t1(
        self,
    ):
        template = json.dumps(self.template_dict_1)
        comparison = self.differ.compare_templates("{}", template)
        assert comparison.t1 == {}


class TestDifflibStackDiffer:
    def setup_method(self, method):
        self.serialize = cfn_flip.dump_yaml
        self.differ = DifflibStackDiffer()
        self.config1 = StackConfiguration(
            stack_name="stack",
            parameters={"pk1": "pv1"},
            stack_tags={"tk1": "tv1"},
            notifications=["notification"],
            cloudformation_service_role=None,
        )

        self.config2 = StackConfiguration(
            stack_name="stack",
            parameters={"pk1": "pv1", "pk2": "pv2"},
            stack_tags={"tk1": "tv1"},
            notifications=["notification"],
            cloudformation_service_role="new_role",
        )

        self.template_dict_1 = {
            "AWSTemplateFormat": "2010-09-09",
            "Description": "deployed",
            "Parameters": {"pk1": "pv1"},
            "Resources": {},
        }
        self.template_dict_2 = {
            "AWSTemplateFormat": "2010-09-09",
            "Description": "deployed",
            "Parameters": {"pk1": "pv1"},
            "Resources": {
                "MyBucket": {
                    "Type": "AWS::S3::Bucket",
                    "Properties": {"BucketName": "test"},
                }
            },
        }

    def create_expected_diff(self, first, second, already_formatted=False):
        if not already_formatted:
            deployed_dict, deployed_format = cfn_flip.load(first)
            generated_dict, generated_format = cfn_flip.load(second)
            dumpers = {"json": cfn_flip.dump_json, "yaml": cfn_flip.dump_yaml}
            first = dumpers[generated_format](deployed_dict)
            second = dumpers[generated_format](generated_dict)
        first_list, second_list = first.splitlines(), second.splitlines()
        return list(
            difflib.unified_diff(
                first_list,
                second_list,
                fromfile="deployed",
                tofile="generated",
                lineterm="",
            )
        )

    def test_compare_stack_configurations__returns_diff_of_deployed_and_generated_when_converted_to_dicts(
        self,
    ):
        comparison = self.differ.compare_stack_configurations(
            self.config1, self.config2
        )
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
            if value not in (None, [], {}) and key != "stack_name"
        }
        return without_empty_values

    def test_compare_stack_configurations__deployed_is_none__returns_diff_with_none(
        self,
    ):
        comparison = self.differ.compare_stack_configurations(None, self.config2)
        expected = self.create_expected_diff(
            self.serialize(None),
            self.serialize(self.make_config_comparable(self.config2)),
        )
        assert comparison == expected

    def test_compare_stack_configurations__deployed_is_none__all_configs_are_falsey__returns_diff_with_none(
        self,
    ):
        empty_config = StackConfiguration(
            stack_name="stack",
            parameters={},
            stack_tags={},
            notifications=[],
            cloudformation_service_role=None,
        )
        comparison = self.differ.compare_stack_configurations(None, empty_config)

        expected = self.create_expected_diff(
            self.serialize(None),
            self.serialize(self.make_config_comparable(empty_config)),
            already_formatted=True,
        )
        assert comparison == expected

    @pytest.mark.parametrize(
        "serializer",
        [
            pytest.param(json.dumps, id="templates are json"),
            pytest.param(yaml.dump, id="templates are yaml"),
        ],
    )
    def test_compare_templates__templates_are_json__returns_deepdiff_of_dicts(
        self,
        serializer,
    ):
        template1, template2 = serializer(self.template_dict_1), serializer(
            self.template_dict_2
        )
        comparison = self.differ.compare_templates(template1, template2)
        expected = self.create_expected_diff(template1, template2)
        assert comparison == expected

    def test_compare_templates__deployed_is_empty_dict_string__returns_diff_with_empty_string(
        self,
    ):
        template = json.dumps(self.template_dict_1)
        comparison = self.differ.compare_templates("{}", template)
        expected = self.create_expected_diff("{}", template)
        assert comparison == expected

    def test_compare_templates__json_template__only_indentation_diff__returns_no_diff(
        self,
    ):
        template1 = json.dumps(self.template_dict_1, indent=2)
        template2 = json.dumps(self.template_dict_1, indent=4)
        comparison = self.differ.compare_templates(template1, template2)
        assert len(comparison) == 0

    def test_compare_templates__yaml_template__only_indentation_diff__returns_no_diff(
        self,
    ):
        template1 = yaml.dump(self.template_dict_1, indent=2)
        template2 = yaml.dump(self.template_dict_1, indent=4)
        comparison = self.differ.compare_templates(template1, template2)
        assert len(comparison) == 0

    def test_compare_templates__opposite_template_types_but_identical_template__returns_no_diff(
        self,
    ):
        template1 = json.dumps(self.template_dict_1)
        template2 = yaml.dump(self.template_dict_1)
        comparison = self.differ.compare_templates(template1, template2)
        assert len(comparison) == 0
