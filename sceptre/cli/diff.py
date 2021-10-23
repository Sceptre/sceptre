import io
import sys
from logging import getLogger
from typing import Dict, TextIO

import click
import yaml
from click import Context
from yaml import Dumper

from sceptre.cli.helpers import catch_exceptions
from sceptre.context import SceptreContext
from sceptre.diffing.diff_writer import DeepDiffWriter, DiffLibWriter, DiffWriter
from sceptre.diffing.stack_differ import DeepDiffStackDiffer, DifflibStackDiffer, StackDiff
from sceptre.plan.plan import SceptrePlan
from sceptre.stack import Stack

logger = getLogger(__name__)


@click.command(name="diff", short_help="Compares deployed infrastructure with current configurations")
@click.option(
    '-t',
    '--type',
    'differ',
    type=click.Choice(['deepdiff', 'difflib']),
    default='deepdiff',
    help='The type of differ to use. Use "deepdiff" for recursive key/value comparison. "difflib" '
         'produces a more traditional "diff" result. Defaults to deepdiff.'
)
@click.option(
    '--nonzero',
    is_flag=True,
    help="If set to True, this will return a nonzero exit code if there is any difference. Defaults"
         "to False, meaning this command only returns a nonzero if there are errors."
)
@click.argument('path')
@click.pass_context
@catch_exceptions
def diff_command(ctx: Context, differ: str, nonzero: bool, path):
    """Indicates the difference between the currently DEPLOYED stacks in the command path and
    the stacks configured in Sceptre right now. This command will compare both the templates as well
    as the subset of stack configurations that can be compared.

    Note: Some settings (such as sceptre_user_data) are not available in a CloudFormation stack
    description, so the diff will not be indicated. Currently compared stack configurations are:

    \b
      * parameters
      * notifications
      * role_arn
      * stack_tags
    """
    context = SceptreContext(
        command_path=path,
        project_path=ctx.obj.get("project_path"),
        user_variables=ctx.obj.get("user_variables"),
        options=ctx.obj.get("options"),
        ignore_dependencies=ctx.obj.get("ignore_dependencies"),
        output_format=ctx.obj.get('output_format'),
        no_colour=ctx.obj.get('no_colour')
    )
    output_format = context.output_format
    plan = SceptrePlan(context)

    if differ == "deepdiff":
        stack_differ = DeepDiffStackDiffer()
        writer_class = DeepDiffWriter
    elif differ == 'difflib':
        stack_differ = DifflibStackDiffer()
        writer_class = DiffLibWriter
    else:
        raise ValueError(f"Unexpected differ type: {differ}")

    # Setup proper multi-line string representation for yaml output
    yaml.add_representer(str, repr_str)

    diffs: Dict[Stack, StackDiff] = plan.diff(stack_differ)
    line_buffer = io.StringIO()
    differences = 0

    for stack_diff in diffs.values():
        writer = writer_class(stack_diff, line_buffer, output_format)
        writer.write()
        if writer.has_difference:
            differences += 1

    line_buffer.seek(0)
    output_buffer_with_normalized_bar_lengths(line_buffer, sys.stdout)
    if nonzero and differences:
        logger.warning(
            "A difference was detected. Exiting with the number of stacks with differences as the "
            "exit code."
        )
        exit(differences)


def output_buffer_with_normalized_bar_lengths(buffer: TextIO, output_stream: TextIO):
    lines = buffer.readlines()
    max_length = len(max(lines, key=len))
    full_length_star_bar = '*' * max_length
    full_length_line_bar = '-' * max_length
    for line in lines:
        if DiffWriter.STAR_BAR in line:
            line = line.replace(DiffWriter.STAR_BAR, full_length_star_bar)
        if DiffWriter.LINE_BAR in line:
            line = line.replace(DiffWriter.LINE_BAR, full_length_line_bar)
        output_stream.write(line)


def repr_str(dumper: Dumper, data):
    if '\n' in data:
        return dumper.represent_scalar(u'tag:yaml.org,2002:str', data, style='|')
    return dumper.represent_str(data)

