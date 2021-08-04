import click

from sceptre.context import SceptreContext
from sceptre.cli.helpers import (
    catch_exceptions,
    write
)
from sceptre.plan.plan import SceptrePlan


@click.command(name="status", short_help="Print status of stack or stack_group.")
@click.argument("path")
@click.pass_context
@catch_exceptions
def status_command(ctx, path):
    """
    Prints the stack status or the status of the stacks within a
    stack_group for a given config PATH.
    \f

    :param path: Path to execute the command on.
    :type path: str
    """
    context = SceptreContext(
        command_path=path,
        project_path=ctx.obj.get("project_path"),
        user_variables=ctx.obj.get("user_variables"),
        options=ctx.obj.get("options"),
        no_colour=ctx.obj.get("no_colour"),
        output_format=ctx.obj.get("output_format"),
        ignore_dependencies=ctx.obj.get("ignore_dependencies")
    )

    plan = SceptrePlan(context)
    responses = plan.get_status()
    message = "\n".join("{}: {}".format(stack.name, status)
                        for stack, status in responses.items())
    write(message, no_colour=context.no_colour)
