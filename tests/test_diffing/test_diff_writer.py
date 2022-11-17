import difflib
from copy import deepcopy
from io import StringIO
from typing import TextIO
from unittest.mock import Mock

import cfn_flip
import pytest
import yaml
from deepdiff import DeepDiff

from sceptre.diffing.diff_writer import DiffWriter, DeepDiffWriter, deepdiff_json_defaults, DiffLibWriter
from sceptre.diffing.stack_differ import StackDiff, DiffType, StackConfiguration


class ImplementedDiffWriter(DiffWriter):

    def __init__(
        self,
        stack_diff: StackDiff,
        output_stream: TextIO,
        output_format: str,
        capturing_mock: Mock
    ):
        super().__init__(stack_diff, output_stream, output_format)
        self.capturing_mock = capturing_mock

    def dump_diff(self, diff: DiffType) -> str:
        return self.capturing_mock.dump_diff(diff)

    @property
    def has_config_difference(self) -> bool:
        return self.capturing_mock.has_config_difference

    @property
    def has_template_difference(self) -> bool:
        return self.capturing_mock.has_template_difference


class TestDiffWriter:

    def setup_method(self, method):
        self.diff_output = 'diff'
        self.capturing_mock = Mock(**{
            'dump_diff.return_value': self.diff_output
        })
        self.stack_name = 'stack'
        self.template_diff = Mock()
        self.config_diff = Mock()
        self.is_deployed = True
        self.generated_template = 'my template'
        self.output_format = 'yaml'

        self.output_stream = StringIO()

        self.diff_detected_message = f'--> Difference detected for stack {self.stack_name}!'

    @property
    def generated_config(self):
        return StackConfiguration(
            stack_name=self.stack_name,
            parameters={},
            stack_tags={},
            notifications=[],
            role_arn=None
        )

    @property
    def diff(self):
        return StackDiff(
            self.stack_name,
            self.template_diff,
            self.config_diff,
            self.is_deployed,
            self.generated_config,
            self.generated_template
        )

    @property
    def writer(self):
        return ImplementedDiffWriter(
            self.diff,
            self.output_stream,
            self.output_format,
            self.capturing_mock
        )

    def assert_expected_output(self, *expected_segments):
        expected_segments = [f'{line}\n' for line in expected_segments]
        joined = ''.join(expected_segments)
        expected_split_lines = joined.splitlines()

        received_lines = self.output_stream.getvalue().splitlines()
        diff = list(difflib.unified_diff(
            received_lines,
            expected_split_lines,
            fromfile='actual',
            tofile='expected'
        ))
        assert not diff, '\n'.join(diff)

    def test_write__no_difference__writes_no_difference(self):
        self.capturing_mock.has_config_difference = False
        self.capturing_mock.has_template_difference = False

        self.writer.write()

        self.assert_expected_output(
            DiffWriter.STAR_BAR,
            f'No difference to deployed stack {self.stack_name}'
        )

    @pytest.mark.parametrize(
        'output_format, config_serializer',
        [
            pytest.param('yaml', cfn_flip.dump_yaml, id='output format is yaml'),
            pytest.param('json', cfn_flip.dump_json, id='output format is json'),
            pytest.param('text', cfn_flip.dump_yaml, id='output format is text')
        ]
    )
    def test_write__new_stack__writes_new_stack_config_and_template(self, output_format, config_serializer):
        self.is_deployed = False
        self.output_format = output_format

        self.writer.write()

        self.assert_expected_output(
            DiffWriter.STAR_BAR,
            self.diff_detected_message,
            'This stack is not deployed yet!',
            DiffWriter.LINE_BAR,
            'New Config:',
            '',
            config_serializer(dict(self.generated_config._asdict())),
            DiffWriter.LINE_BAR,
            'New Template:',
            '',
            self.generated_template
        )

    def test_write__only_config_is_different__writes_config_difference(self):
        self.capturing_mock.has_config_difference = True
        self.capturing_mock.has_template_difference = False

        self.writer.write()

        self.assert_expected_output(
            DiffWriter.STAR_BAR,
            self.diff_detected_message,
            DiffWriter.LINE_BAR,
            f'Config difference for {self.stack_name}:',
            '',
            self.diff_output,
            DiffWriter.LINE_BAR,
            'No template difference'
        )

    def test_write__only_template_is_different__writes_template_difference(self):
        self.capturing_mock.has_config_difference = False
        self.capturing_mock.has_template_difference = True

        self.writer.write()

        self.assert_expected_output(
            DiffWriter.STAR_BAR,
            self.diff_detected_message,
            DiffWriter.LINE_BAR,
            'No stack config difference',
            DiffWriter.LINE_BAR,
            f'Template difference for {self.stack_name}:',
            '',
            self.diff_output
        )

    def test_write__config_and_template_are_different__writes_both_differences(self):
        self.capturing_mock.has_config_difference = True
        self.capturing_mock.has_template_difference = True

        self.writer.write()

        self.assert_expected_output(
            DiffWriter.STAR_BAR,
            self.diff_detected_message,
            DiffWriter.LINE_BAR,
            f'Config difference for {self.stack_name}:',
            '',
            self.diff_output,
            DiffWriter.LINE_BAR,
            f'Template difference for {self.stack_name}:',
            '',
            self.diff_output
        )


class TestDeepDiffWriter:
    def setup_method(self, method):
        self.stack_name = 'stack'

        self.is_deployed = True
        self.output_format = 'yaml'

        self.output_stream = StringIO()

        self.config1 = StackConfiguration(
            stack_name=self.stack_name,
            parameters={},
            stack_tags={},
            notifications=[],
            role_arn=None
        )

        self.config2 = deepcopy(self.config1)

        self.template1 = 'template'
        self.template2 = 'template'

    @property
    def template_diff(self):
        return DeepDiff(self.template1, self.template2)

    @property
    def config_diff(self):
        return DeepDiff(self.config1, self.config2)

    @property
    def diff(self):
        return StackDiff(
            self.stack_name,
            self.template_diff,
            self.config_diff,
            self.is_deployed,
            self.config1,
            self.template1
        )

    @property
    def writer(self):
        return DeepDiffWriter(
            self.diff,
            self.output_stream,
            self.output_format,
        )

    def test_has_config_difference__config_difference_is_present__returns_true(self):
        self.config2.parameters['new_key'] = 'new value'
        assert self.writer.has_config_difference

    def test_has_config_difference__config_difference_is_absent__returns_false(self):
        assert self.writer.has_config_difference is False

    def test_has_template_difference__template_difference_is_present__returns_true(self):
        self.template2 = 'new'
        assert self.writer.has_template_difference

    def test_has_template_difference__template_difference_is_absent__returns_false(self):
        assert self.writer.has_template_difference is False

    def test_dump_diff__output_format_is_json__outputs_to_json(self):
        self.output_format = 'json'
        self.config2.parameters['new_key'] = 'new value'

        result = self.writer.dump_diff(self.config_diff)
        expected = self.config_diff.to_json(indent=4, default_mapping=deepdiff_json_defaults)
        assert result == expected

    def test_dump_diff__output_format_is_yaml__outputs_to_yaml(self):
        self.output_format = 'yaml'
        self.config2.parameters['new_key'] = 'new value'

        result = self.writer.dump_diff(self.config_diff)
        expected_dict = self.config_diff.to_dict()
        expected_yaml = yaml.dump(expected_dict, indent=4)
        assert result == expected_yaml

    def test_dump_diff__output_format_is_text__outputs_to_yaml(self):
        self.output_format = 'text'
        self.config2.parameters['new_key'] = 'new value'

        result = self.writer.dump_diff(self.config_diff)
        expected_dict = self.config_diff.to_dict()
        expected_yaml = yaml.dump(expected_dict, indent=4)
        assert result == expected_yaml

    def test_dump_diff__output_format_is_yaml__diff_has_multiline_strings__strips_out_extra_spaces(self):
        self.config1.parameters['long_param'] = 'here \nis \nmy \nlong \nstring'
        self.config2.parameters['long_param'] = 'here \nis \nmy \nother \nlong \nstring'

        dumped = self.writer.dump_diff(self.config_diff)
        loaded = yaml.safe_load(dumped)
        assert ' ' not in loaded['values_changed']["root.parameters['long_param']"]['new_value']
        assert ' ' not in loaded['values_changed']["root.parameters['long_param']"]['old_value']
        expected_diff = '\n'.join(
            difflib.unified_diff(
                self.config1.parameters['long_param'].splitlines(),
                self.config2.parameters['long_param'].splitlines(),
                lineterm=''
            )
        ).replace(' \n', '\n')
        assert expected_diff == loaded['values_changed']["root.parameters['long_param']"]['diff']


class TestDiffLibWriter:
    def setup_method(self, method):
        self.stack_name = 'stack'

        self.is_deployed = True
        self.output_format = 'yaml'

        self.output_stream = StringIO()

        self.config1 = StackConfiguration(
            stack_name=self.stack_name,
            parameters={},
            stack_tags={},
            notifications=[],
            role_arn=None
        )

        self.config2 = deepcopy(self.config1)

        self.template1 = 'template'
        self.template2 = 'template'

    @property
    def template_diff(self):
        return list(difflib.unified_diff(self.template1, self.template2))

    @property
    def config_diff(self):
        config_1 = yaml.dump(dict(self.config1._asdict())).splitlines()
        config_2 = yaml.dump(dict(self.config2._asdict())).splitlines()
        return list(difflib.unified_diff(config_1, config_2))

    @property
    def diff(self):
        return StackDiff(
            self.stack_name,
            self.template_diff,
            self.config_diff,
            self.is_deployed,
            self.config1,
            self.template1
        )

    @property
    def writer(self):
        return DiffLibWriter(
            self.diff,
            self.output_stream,
            self.output_format,
        )

    def test_has_config_difference__config_difference_is_present__returns_true(self):
        self.config2.parameters['new_key'] = 'new value'
        assert self.writer.has_config_difference

    def test_has_config_difference__config_difference_is_absent__returns_false(self):
        assert self.writer.has_config_difference is False

    def test_has_template_difference__template_difference_is_present__returns_true(self):
        self.template2 = 'new'
        assert self.writer.has_template_difference

    def test_has_template_difference__template_difference_is_absent__returns_false(self):
        assert self.writer.has_template_difference is False

    def test_dump_diff__returns_joined_list(self):
        result = self.writer.dump_diff(self.diff.config_diff)
        expected = '\n'.join(self.diff.config_diff)
        assert result == expected
