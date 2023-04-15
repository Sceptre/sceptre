import logging
import click

from sceptre.context import SceptreContext
from sceptre.cli.helpers import catch_exceptions, write
from sceptre.plan.plan import SceptrePlan
from sceptre.helpers import null_context
from sceptre.resolvers.placeholders import use_resolver_placeholders_on_error

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


@dump_group.command(name="template")
@click.argument("path")
@click.option(
    "-n",
    "--no-placeholders",
    is_flag=True,
    help="If True, no placeholder values will be supplied for resolvers that cannot be resolved.",
)
@click.pass_context
@catch_exceptions
def dump_template(ctx, no_placeholders, path):
    """
    Prints the template used for stack in PATH.
    \f

    :param path: Path to execute the command on.
    :type path: str
    """
    context = SceptreContext(
        command_path=path,
        command_params=ctx.params,
        project_path=ctx.obj.get("project_path"),
        user_variables=ctx.obj.get("user_variables"),
        options=ctx.obj.get("options"),
        output_format=ctx.obj.get("output_format"),
        ignore_dependencies=ctx.obj.get("ignore_dependencies"),
    )

    plan = SceptrePlan(context)

    execution_context = (
        null_context() if no_placeholders else use_resolver_placeholders_on_error()
    )
    with execution_context:
        responses = plan.generate()

    output = [template for template in responses.values()]
    write(output, context.output_format)
