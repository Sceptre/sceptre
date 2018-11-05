import click

from sceptre.context import SceptreContext
from sceptre.cli.helpers import catch_exceptions
from sceptre.cli.helpers import confirmation
from sceptre.cli.helpers import stack_status_exit_code
from sceptre.plan.plan import SceptrePlan


@click.command(name="launch")
@click.argument("path")
@click.option(
    "-y", "--yes", is_flag=True, help="Assume yes to all questions."
)
@click.pass_context
@catch_exceptions
def launch_command(ctx, path, yes):
    """
    Launch a stack or stack_group.

    Launch a stack or stack_group for a given config PATH.
    """
    context = SceptreContext(
                command_path=path,
                project_path=ctx.obj.get("project_path"),
                user_variables=ctx.obj.get("user_variables"),
                options=ctx.obj.get("options")
            )

    plan = SceptrePlan(context)

    if len(plan.stack_group.stacks) == 1:
        confirmation(plan.launch.__name__, yes, stack=path)
        plan.launch()
        exit(stack_status_exit_code(plan))
    else:
        confirmation(plan.launch.__name__, yes, stack_group=path)
        plan.launch()
        exit(stack_status_exit_code(plan))
