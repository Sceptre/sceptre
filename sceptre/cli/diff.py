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
        click.echo(f"Outputting diff file to {Path(output_file).absolute()}")
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
    print_full_templates: bool,
    output_stream: StringIO
):
    def output(text):
        click.echo(text, file=output_stream)

    stack_name, template_diff, config_diff = diff
    there_is_config_difference = len(config_diff)
    there_is_template_difference = len(template_diff)
    there_is_difference = any([there_is_config_difference, there_is_template_difference])

    stack_is_not_yet_deployed = config_diff.t1 is None

    if not there_is_difference:
        output(f"No difference to deployed stack {stack_name}")
        return

    output(STAR_BAR)
    output(f"--> Difference detected for stack {stack_name}!")

    if stack_is_not_yet_deployed:
        output("This stack is not deployed yet!")
        output(f'{LINE_BAR}\nNew config:')
        output(dump_stack_config(config_diff.t2))
        output(f'{LINE_BAR}\nNew template:')
        output(dump_dict(template_diff.t2))
        output(STAR_BAR)
        return

    if there_is_config_difference:
        output(LINE_BAR)
        output('Config difference:')
        output(dump_diff(config_diff))
    else:
        output("No config difference")

    if len(template_diff):
        output(LINE_BAR)
        output("Template difference:")
        output(dump_diff(template_diff))
        if print_full_templates:
            deployed, generated = dump_dict(template_diff.t1), dump_dict(template_diff.t2)
            output(LINE_BAR)
            output(f'Deployed template:\n{LINE_BAR}\n{deployed}')
            output(LINE_BAR)
            output(f'New Template:\n{LINE_BAR}\n{generated}')
    else:
        output("No template difference")

    output(STAR_BAR)


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


def dump_stack_config(stack_config: StackConfiguration) -> str:
    return dump_dict(stack_config._asdict())
