import difflib
from io import StringIO
from itertools import chain
from typing import TextIO
from unittest.mock import Mock

import cfn_flip
import pytest

from sceptre.diffing.diff_writer import DiffWriter
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
            'Config difference:',
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
            'Template difference:',
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
            'Config difference:',
            '',
            self.diff_output,
            DiffWriter.LINE_BAR,
            'Template difference:',
            '',
            self.diff_output
        )


class TestDeepDiffWriter:
    def test_has_config_difference__config_difference_is_present__returns_true(self):
        assert False

    def test_has_config_difference__config_difference_is_absent__returns_false(self):
        assert False

    def test_has_template_difference__template_difference_is_present__returns_true(self):
        assert False

    def test_has_template_difference__template_difference_is_absent__returns_false(self):
        assert False

    def test_dump_diff__output_format_is_json__outputs_to_json(self):
        assert False

    def test_dump_diff__output_format_is_yaml__outputs_to_yaml(self):
        assert False

    def test_dump_diff__output_format_is_text__outputs_to_yaml(self):
        assert False


class TestDiffLibWriter:
    def test_has_config_difference__config_difference_is_present__returns_true(self):
        assert False

    def test_has_config_difference__config_difference_is_absent__returns_false(self):
        assert False

    def test_has_template_difference__template_difference_is_present__returns_true(self):
        assert False

    def test_has_template_difference__template_difference_is_absent__returns_false(self):
        assert False

    def test_dump_diff__returns_joined_list(self):
        assert False
