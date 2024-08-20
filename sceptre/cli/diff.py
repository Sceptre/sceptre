import io
import sys
from logging import getLogger
from typing import Dict, TextIO, Type, Iterable

import click
from click import Context

from sceptre.cli.helpers import catch_exceptions
from sceptre.context import SceptreContext
from sceptre.diffing.diff_writer import (
    DeepDiffWriter,
    DiffLibWriter,
    ColouredDiffLibWriter,
    DiffWriter,
)
from sceptre.diffing.stack_differ import (
    DeepDiffStackDiffer,
    DifflibStackDiffer,
    StackDiff,
)
from sceptre.helpers import null_context
from sceptre.plan.plan import SceptrePlan
from sceptre.resolvers.placeholders import use_resolver_placeholders_on_error
from sceptre.stack import Stack

logger = getLogger(__name__)


@click.command(
    name="diff",
    short_help="Compares deployed infrastructure with current configurations",
)
@click.option(
    "-t",
    "--type",
    "differ",
    type=click.Choice(["deepdiff", "difflib"]),
    default="deepdiff",
    help='The type of differ to use. Use "deepdiff" for recursive key/value comparison. "difflib" '
    'produces a more traditional "diff" result. Defaults to deepdiff.',
)
@click.option(
    "-s",
    "--show-no-echo",
    is_flag=True,
    help="If set, will display the unmasked values of NoEcho parameters generated LOCALLY (NoEcho "
    "parameters for deployed stacks will always be masked when retrieved from CloudFormation.). "
    "If not set (the default), parameters identified as NoEcho on the local template will be "
    "masked when presented in the diff.",
)
@click.option(
    "-n",
    "--no-placeholders",
    is_flag=True,
    help="If set, no placeholder values will be supplied for resolvers that cannot be resolved.",
)
@click.option(
    "-a",
    "--all",
    "all_",
    is_flag=True,
    help=(
        "If set, will perform diffing on ALL stacks, including ignored and obsolete ones; Otherwise, "
        "it will diff only stacks that would be created or updated when running the launch command."
    ),
)
@click.argument("path")
@click.pass_context
@catch_exceptions
def diff_command(
    ctx: Context,
    differ: str,
    show_no_echo: bool,
    no_placeholders: bool,
    all_: bool,
    path: str,
):
    """Indicates the difference between the currently DEPLOYED stacks in the command path and
    the stacks configured in Sceptre right now. This command will compare both the templates as well
    as the subset of stack configurations that can be compared. By default, only stacks that would
    be launched via the launch command will be diffed, but you can diff ALL stacks relevant to the
    passed command path if you pass the --all flag.

    Some settings (such as sceptre_user_data) are not available in a CloudFormation stack
    description, so the diff will not be indicated. Currently compared stack configurations are:

    \b
      * parameters
      * notifications
      * cloudformation_service_role
      * stack_tags

    Important: There are resolvers (notably !stack_output) that rely on other stacks
    to be already deployed when they are resolved. When producing a diff on Stack Configs that have
    such resolvers that point to non-deployed stacks, this presents a challenge, since this means
    those resolvers cannot be resolved. This particularly applies to stack parameters and when a
    stack's template uses sceptre_user_data with resolvers in it. In order to continue to be useful
    when producing a diff in these conditions, this command will do the following:

    1. If the resolver CAN be resolved, it will be resolved and the resolved value will be in the
    diff results.
    2. If the resolver CANNOT be resolved, it will be replaced with a string that represents the
    resolver and its arguments. For example: !stack_output my_stack.yaml::MyOutput will resolve in
    the parameters to "{ !StackOutput(my_stack.yaml::MyOutput) }".

    Particularly in cases where the replaced value doesn't work in the template as the template logic
    requires and causes an error, there is nothing further Sceptre can do and diffing will fail.
    """
    no_colour = ctx.obj.get("no_colour")

    context = SceptreContext(
        command_path=path,
        command_params=ctx.params,
        project_path=ctx.obj.get("project_path"),
        user_variables=ctx.obj.get("user_variables"),
        options=ctx.obj.get("options"),
        ignore_dependencies=ctx.obj.get("ignore_dependencies"),
        output_format=ctx.obj.get("output_format"),
        no_colour=no_colour,
    )
    output_format = context.output_format
    plan = SceptrePlan(context)
    if not all_:
        filter_plan_for_launchable(plan)

    if differ == "deepdiff":
        stack_differ = DeepDiffStackDiffer(show_no_echo)
        writer_class = DeepDiffWriter
    elif differ == "difflib":
        stack_differ = DifflibStackDiffer(show_no_echo)
        writer_class = DiffLibWriter if no_colour else ColouredDiffLibWriter
    else:
        raise ValueError(f"Unexpected differ type: {differ}")

    execution_context = (
        null_context() if no_placeholders else use_resolver_placeholders_on_error()
    )
    with execution_context:
        diffs: Dict[Stack, StackDiff] = plan.diff(stack_differ)

    num_stacks_with_diff = output_diffs(
        diffs.values(), writer_class, sys.stdout, output_format
    )

    if num_stacks_with_diff:
        logger.warning(f"{num_stacks_with_diff} stacks with differences detected.")


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


def output_buffer_with_normalized_bar_lengths(
    buffer: io.StringIO, output_stream: TextIO
):
    """Takes the output from a buffer and ensures that the star and line bars are the same length
    across the entire buffer and that their length is the full width of longest line.

    :param buffer: The input stream to normalize bar lengths for
    :param output_stream: The stream to output the normalized buffer into
    """
    buffer.seek(0)
    max_length = len(max(buffer, key=len))
    buffer.seek(0)
    full_length_star_bar = "*" * max_length
    full_length_tilde_bar = "~" * max_length
    for line in buffer:
        if DiffWriter.STAR_BAR in line:
            line = line.replace(DiffWriter.STAR_BAR, full_length_star_bar)
        if DiffWriter.TILDE_BAR in line:
            line = line.replace(DiffWriter.TILDE_BAR, full_length_tilde_bar)
        output_stream.write(line)


def filter_plan_for_launchable(plan: SceptrePlan):
    plan.resolve(plan.diff.__name__)
    plan.filter(lambda stack: not stack.ignore and not stack.obsolete)
