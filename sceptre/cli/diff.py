import io
import sys
from logging import getLogger
from typing import Dict, TextIO, Type, List, Iterable

import click
from click import Context

from sceptre.cli.helpers import catch_exceptions
from sceptre.context import SceptreContext
from sceptre.diffing.diff_writer import DeepDiffWriter, DiffLibWriter, DiffWriter
from sceptre.diffing.stack_differ import DeepDiffStackDiffer, DifflibStackDiffer, StackDiff, StackDiffer
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
    '-s',
    '--show-no-echo',
    is_flag=True,
    help='If set, will display the unmasked values of NoEcho parameters generated LOCALLY (NoEcho '
         'parameters for deployed stacks will always be masked when retrieved from CloudFormation.). '
         'If not set (the default), parameters identified as NoEcho on the local template will be '
         'masked when presented in the diff.'
)
@click.argument('path')
@click.pass_context
@catch_exceptions
def diff_command(ctx: Context, differ: str, show_no_echo: bool, path: str):
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
        stack_differ = DeepDiffStackDiffer(show_no_echo)
        writer_class = DeepDiffWriter
    elif differ == 'difflib':
        stack_differ = DifflibStackDiffer(show_no_echo)
        writer_class = DiffLibWriter
    else:
        raise ValueError(f"Unexpected differ type: {differ}")

    diffs: Dict[Stack, StackDiff] = plan.diff(stack_differ)
    num_stacks_with_diff = output_diffs(diffs.values(), writer_class, sys.stdout, output_format)

    if num_stacks_with_diff:
        logger.warning(
            f"{num_stacks_with_diff} stacks with differences detected."
        )


def output_diffs(
    diffs: Iterable[StackDiff],
    writer_class: Type[DiffWriter],
    output_buffer: TextIO,
    output_format: str,
) -> int:
    """Outputs the diff results to the output_buffer.

    :param diffs: The differences computed
    :param writer_class: The DiffWriter class to be instantiated for each StackDiff
    :param output_buffer: The buffer to write the diff results to
    :param output_format: The format to output the results in
    :return: The number of stacks that had a difference
    """

    line_buffer = io.StringIO()

    num_stacks_with_diff = 0

    for stack_diff in diffs:
        writer = writer_class(stack_diff, line_buffer, output_format)
        writer.write()
        if writer.has_difference:
            num_stacks_with_diff += 1

    output_buffer_with_normalized_bar_lengths(line_buffer, output_buffer)
    return num_stacks_with_diff


def output_buffer_with_normalized_bar_lengths(buffer: io.StringIO, output_stream: TextIO):
    """Takes the output from a buffer and ensures that the star and line bars are the same length
    across the entire buffer and that their length is the full width of longest line.

    :param buffer: The input stream to normalize bar lengths for
    :param output_stream: The stream to output the normalized buffer into
    """
    buffer.seek(0)
    max_length = len(max(buffer, key=len))
    buffer.seek(0)
    full_length_star_bar = '*' * max_length
    full_length_line_bar = '-' * max_length
    for line in buffer:
        if DiffWriter.STAR_BAR in line:
            line = line.replace(DiffWriter.STAR_BAR, full_length_star_bar)
        if DiffWriter.LINE_BAR in line:
            line = line.replace(DiffWriter.LINE_BAR, full_length_line_bar)
        output_stream.write(line)
