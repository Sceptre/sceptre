import click

from sceptre.context import SceptreContext
from sceptre.cli.helpers import catch_exceptions, write
from sceptre.config.reader import ConfigReader

@click.command(name="diff", short_help="Show diffs.")
@click.argument("path")
@click.pass_context
@catch_exceptions
def diff_command(ctx, path):
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

    for stack in list(stacks):
        diffs = stack.diff()
        if diffs:
            message = "\
Differences between running stack {} and \
generated template:\n\
{}".format(stack.external_name, diffs)
        else:
            message = "No diffs"

        write(message, context.output_format)
