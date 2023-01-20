import logging
import click

from sceptre.context import SceptreContext
from sceptre.cli.helpers import catch_exceptions, write
from sceptre.plan.plan import SceptrePlan

logger = logging.getLogger(__name__)


@click.group(name="dump")
def dump_group():
    """
    Commands for dumping attributes of stacks.
    """
    pass


@dump_group.command(name="config")
@click.argument("path")
@click.pass_context
@catch_exceptions
def dump_config(ctx, path):
    """
    Dump the rendered (post-Jinja) Stack Configs.
    \f

    :param path: Path to execute the command on or path to stack group
    """
    context = SceptreContext(
        command_path=path,
        command_params=ctx.params,
        project_path=ctx.obj.get("project_path"),
        user_variables=ctx.obj.get("user_variables"),
        output_format=ctx.obj.get("output_format"),
        options=ctx.obj.get("options"),
        ignore_dependencies=ctx.obj.get("ignore_dependencies"),
    )
    plan = SceptrePlan(context)
    responses = plan.dump_config()

    output = []
    for stack, config in responses.items():
        if config is None:
            logger.warning(f"{stack.external_name} does not exist")
        else:
            output.append({stack.external_name: config})

    output_format = "json" if context.output_format == "json" else "yaml"

    if len(output) == 1:
        write(output[0][stack.external_name], output_format)
    else:
        for config in output:
            write(config, output_format)
