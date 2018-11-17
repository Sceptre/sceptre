import click

from sceptre.context import SceptreContext
from sceptre.cli.helpers import catch_exceptions, confirmation
from sceptre.plan.plan import SceptrePlan


@click.command(name="execute")
@click.argument("path")
@click.argument("change-set-name", required=False)
@click.option(
    "-y", "--yes", is_flag=True, help="Assume yes to all questions."
)
@click.pass_context
@catch_exceptions
def execute_command(ctx, path, change_set_name, yes):
    """
    Executes a Change Set.

    :param path: Path to execute the command on.
    :type path: str
    :param change_set_name: Change Set to use.
    :type change_set_name: str
    :param yes: A flag to answer 'yes' too all CLI questions.
    :type yes: str
    """
    context = SceptreContext(
        command_path=path,
        project_path=ctx.obj.get("project_path"),
        user_variables=ctx.obj.get("user_variables"),
        options=ctx.obj.get("options")
    )

    plan = SceptrePlan(context)
    confirmation(
        plan.execute_change_set.__name__,
        yes,
        change_set=change_set_name,
        command_path=path
    )
    plan.execute_change_set(change_set_name)
