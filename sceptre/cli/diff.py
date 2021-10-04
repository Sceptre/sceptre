import sys
from typing import Dict

import click
from click import Context

from sceptre.cli.helpers import catch_exceptions
from sceptre.context import SceptreContext
from sceptre.diffing.diff_writer import DeepDiffWriter, DiffLibWriter
from sceptre.diffing.stack_differ import DeepDiffStackDiffer, DifflibStackDiffer, StackDiff
from sceptre.plan.plan import SceptrePlan
from sceptre.stack import Stack


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
@click.argument('path')
@click.pass_context
@catch_exceptions
def diff_command(ctx: Context, differ: str, path):
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

    diffs: Dict[Stack, StackDiff] = plan.diff(stack_differ)

    for stack_diff in diffs.values():
        writer = writer_class(stack_diff, sys.stdout, output_format)
        writer.write()
