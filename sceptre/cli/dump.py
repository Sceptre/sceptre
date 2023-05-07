import logging
import click

from pathlib import Path

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
@click.option(
    "--to-file", is_flag=True, help="If True, also dump the template to a local file."
)
@click.pass_context
@catch_exceptions
def dump_config(ctx, to_file, path):
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

    output_format = "json" if context.output_format == "json" else "yaml"

    for stack, config in responses.items():
        stack_name = stack.external_name

        if to_file:
            file_path = Path(".dump") / stack_name / f"config.{output_format}"
            logger.info(f"{stack_name} dumping to {file_path}")
            write(config, output_format, no_colour=True, file_path=file_path)
            logger.info(f"{stack_name} dump to {file_path} complete.")

        else:
            write(config, output_format, no_colour=True)


@dump_group.command(name="template")
@click.argument("path")
@click.option(
    "-n",
    "--no-placeholders",
    is_flag=True,
    help="If True, no placeholder values will be supplied for resolvers that cannot be resolved.",
)
@click.option(
    "--to-file", is_flag=True, help="If True, also dump the template to a local file."
)
@click.pass_context
@catch_exceptions
def dump_template(ctx, to_file, no_placeholders, path):
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
        responses = plan.dump_template()

    output_format = "json" if context.output_format == "json" else "yaml"

    for stack, template in responses.items():
        stack_name = stack.external_name

        if to_file:
            file_path = Path(".dump") / stack_name / f"template.{output_format}"
            logger.info(f"{stack_name} dumping template to {file_path}")
            write(template, output_format, no_colour=True, file_path=file_path)
            logger.info(f"{stack_name} dump to {file_path} complete.")

        else:
            write(template, output_format, no_colour=True)


@dump_group.command(name="all")
@click.argument("path")
@click.option(
    "-n",
    "--no-placeholders",
    is_flag=True,
    help="If True, no placeholder values will be supplied for resolvers that cannot be resolved.",
)
@click.option(
    "--to-file", is_flag=True, help="If True, also dump the template to a local file."
)
@click.pass_context
@catch_exceptions
def dump_all(ctx, to_file, no_placeholders, path):
    """
    Dumps both the rendered (post-Jinja) Stack Configs and the template used for stack in PATH.
    \f

    :param path: Path to execute the command on.
    :type path: str
    """
    ctx.invoke(dump_config, to_file=to_file, path=path)
    ctx.invoke(
        dump_template, to_file=to_file, no_placeholders=no_placeholders, path=path
    )
