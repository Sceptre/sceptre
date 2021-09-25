import json
from pathlib import Path
from typing import TextIO

import click
import yaml
from click import Context

from sceptre.cli import catch_exceptions
from sceptre.context import SceptreContext
from sceptre.diffing.diff_writer import DeepDiffWriter, DictDifferWriter, DiffLibWriter
from sceptre.diffing.stack_differ import DeepDiffStackDiffer, StackDiff, DictDifferStackDiffer, DifflibStackDiffer
from sceptre.plan.plan import SceptrePlan


@click.command(name="diff", short_help="Compares deployed infrastructure with current configurations")
@click.option(
    '-f',
    '--full-templates',
    is_flag=True,
    help=(
        "If there is a difference between deployed and generated, it will print the full generated "
        "template if this is set to True"
    )
)
@click.option(
    '-o',
    '--output-file',
    type=click.Path(file_okay=True, dir_okay=False, resolve_path=True),
    help=(
        "If specified, the filepath that diff results will be printed to; "
        "Otherwise they will streamed to stdout."
    )
)
@click.option(
    '-D',
    '--differ',
    type=click.Choice(['deepdiff', 'dictdiffer', 'difflib']),
    default='deepdiff'
)
@click.argument('path')
@click.pass_context
@catch_exceptions
def diff_command(ctx: Context, full_templates: bool, output_file: str, differ: str, path):
    """This command is designed to indicate what the difference between the currently DEPLOYED
    stack templates at the indicated command_path and the stack templates generated off of the
    current templates and configurations.
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
    elif differ == 'dictdiffer':
        stack_differ = DictDifferStackDiffer()
        writer_class = DictDifferWriter
    elif differ == 'difflib':
        serializer = json.dumps if output_format == 'json' else yaml.dump
        stack_differ = DifflibStackDiffer(serializer=serializer)
        writer_class = DiffLibWriter
    else:
        raise ValueError(f"Unexpected differ type: {differ}")

    diffs = plan.diff(stack_differ)

    if output_file:
        path = Path(output_file)
        path.parent.mkdir(parents=True, exist_ok=True)
        context = path.open(mode='wt')
    else:
        context = nullcontext(sys.stdout)

    writer_class = FullTemplateDiffWriter if full_templates else DiffWriter
    output_format = OutputFormat[kwargs.get('output', 'yaml')]
    with context as stream:
        for stack_diff in diffs:
            writer = writer_class(stack_diff, stream, output_format)
            writer.write()


