import io
import sys
from logging import getLogger
from typing import Dict, TextIO, Type

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
    '--nonzero',
    is_flag=True,
    help="If this flag is passed, this will return the number of stacks with a difference as the "
         "exit code. Otherwise, this will always return a 0 exit code except in the case of errors."
)
@click.argument('path')
@click.pass_context
@catch_exceptions
def diff_command(ctx: Context, differ: str, nonzero: bool, path: str):
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

    num_stacks_with_diff = run_diff(plan, stack_differ, writer_class, sys.stdout, output_format)

    if nonzero and num_stacks_with_diff:
        logger.warning(
            "A difference was detected. Exiting with the number of stacks with differences as the "
            "exit code."
        )
        exit(num_stacks_with_diff)


def run_diff(
    plan: SceptrePlan,
    stack_differ: StackDiffer,
    writer_class: Type[DiffWriter],
    output_buffer: TextIO,
    output_format: str,
) -> int:
    """Runs the action of the diff command, outputting the results to the output_buffer.

    :param plan: The SceptrePlan used to run the diff command across all stacks
    :param stack_differ: The StackDiffer used by the diff command
    :param writer_class: The DiffWriter class to be instantiated for each StackDiff
    :param output_buffer: The buffer to write the diff results to
    :param output_format: The format to output the results in
    :return: The number of stacks that had a difference
    """
    diffs: Dict[Stack, StackDiff] = plan.diff(stack_differ)
    line_buffer = io.StringIO()

    num_stacks_with_diff = 0

    for stack_diff in diffs.values():
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
