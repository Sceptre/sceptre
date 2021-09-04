import contextlib
import json
import sys
from datetime import datetime
from io import StringIO
from pathlib import Path

import cfn_flip
import click
from deepdiff import DeepDiff

from sceptre.cli.helpers import catch_exceptions
from sceptre.context import SceptreContext
from sceptre.plan.plan import SceptrePlan
from sceptre.plan.stack_differ import StackDiff, StackConfiguration


@contextlib.contextmanager
def nullcontext(enter_result=None):
    yield enter_result


@click.command(name="diff", short_help="Prints the template.")
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
@click.argument("path")
@click.pass_context
@catch_exceptions
def diff_command(ctx, path, full_templates, output_file):
    """

    :param path: Path to execute the command on.
    :type path: str
    """
    context = SceptreContext(
        command_path=path,
        project_path=ctx.obj.get("project_path"),
        user_variables=ctx.obj.get("user_variables"),
        options=ctx.obj.get("options"),
        output_format=ctx.obj.get("output_format"),
        ignore_dependencies=ctx.obj.get("ignore_dependencies")
    )

    plan = SceptrePlan(context)
    responses = plan.diff()

    if output_file:
        path = Path(output_file)
        path.parent.mkdir(parents=True, exist_ok=True)
        context = path.open(mode='wt')
    else:
        context = nullcontext(sys.stdout)
    with context as stream:
        for stack_diff in responses.values():
            output_diff_results(stack_diff, full_templates, stream)


STAR_BAR = '*' * 80
LINE_BAR = '-' * 80


deepdiff_json_defaults = {
    datetime.date: lambda x: x.isoformat(),
    StackConfiguration: lambda x: x._asdict()
}


def output_diff_results(
    diff: StackDiff,
    print_full_template: bool,
    output_stream: StringIO
):
    def print(text):
        click.echo(text, file=output_stream)

    stack_name, template_diff, config_diff = diff
    if not len(template_diff) and not len(config_diff):
        print(f"No difference to deployed stack {stack_name}")
        return

    print(STAR_BAR)
    print(f"--> Difference detected for stack {stack_name}!")

    if len(config_diff):
        print(LINE_BAR)
        if config_diff.t1 is None:
            print("Current stack doesn't exist")
        else:
            print('Config difference:')
            print(config_diff.to_json(default_mapping=deepdiff_json_defaults, indent=4, ))

    else:
        print("No config difference")

    if len(template_diff):
        print(LINE_BAR)
        print("Template difference:")
        print(template_diff.to_json(default_mapping=deepdiff_json_defaults, indent=4,))
        if print_full_template:
            deployed, generated = dump_dict(diff.t1), dump_dict(diff.t2)
            print(LINE_BAR)
            print(f'Deployed template:\n{LINE_BAR}\n{deployed}')
            print(LINE_BAR)
            print(f'New Template:\n{LINE_BAR}\n{generated}')
    else:
        print("No template difference")

    print(STAR_BAR)


@click.pass_context
def dump_dict(ctx: click.Context, template: dict) -> str:
    output_format = ctx.obj.get('output_format', 'yaml')

    if output_format == 'json':
        # There's not really a viable way to dump a template as "text" -> YAML is very readable
        dumper = cfn_flip.dump_json
    else:
        dumper = cfn_flip.dump_yaml

    return dumper(template)


@click.pass_context
def dump_diff(ctx: click.Context, diff: DeepDiff) -> str:
    jsonified = diff.to_json(default_mapping=deepdiff_json_defaults, indent=4)
    if ctx.obj.get('output_format', 'yaml') == 'json':
        return jsonified

    loaded = json.loads(jsonified)
    return cfn_flip.dump_yaml(loaded)
