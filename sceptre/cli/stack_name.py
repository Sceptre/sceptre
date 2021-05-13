import click

from sceptre.context import SceptreContext
from sceptre.cli.helpers import catch_exceptions
from sceptre.config.reader import ConfigReader

@click.command(name="stack_name", short_help="Emit the stack name.")
@click.argument("path")
@click.pass_context
@catch_exceptions
def stack_name_command(ctx, path):
    """
    Emit the stack name.

    :param path: The path to launch. Can be a Stack or StackGroup.
    :type path: str
    """
    context = SceptreContext(
        command_path=path,
        project_path=ctx.obj.get("project_path"),
        user_variables=ctx.obj.get("user_variables"),
        options=ctx.obj.get("options"),
        ignore_dependencies=ctx.obj.get("ignore_dependencies")
    )

    stacks, _ = ConfigReader(context).construct_stacks()

    print(path, "contains these stacks:")

    while len(stacks):
        print(stacks.pop().external_name)
