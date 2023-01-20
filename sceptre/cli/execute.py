import click

from typing import Optional
from sceptre.context import SceptreContext
from sceptre.cli.helpers import catch_exceptions, confirmation
from sceptre.plan.plan import SceptrePlan


@click.command(name="execute")
@click.argument("path")
@click.argument("change-set-name")
@click.option("-y", "--yes", is_flag=True, help="Assume yes to all questions.")
@click.option(
    "--disable-rollback/--enable-rollback",
    default=None,
    help="Disable or enable the cloudformation automatic rollback",
)
@click.pass_context
@catch_exceptions
def execute_command(ctx, path, change_set_name, yes, disable_rollback: Optional[bool]):
    """
    Executes a Change Set.
    \f

    :param path: Path to execute the command on.
    :type path: str
    :param change_set_name: Change Set to use.
    :type change_set_name: str
    :param yes: A flag to answer 'yes' too all CLI questions.
    :type yes: bool
    """
    context = SceptreContext(
        command_path=path,
        command_params=ctx.params,
        project_path=ctx.obj.get("project_path"),
        user_variables=ctx.obj.get("user_variables"),
        options=ctx.obj.get("options"),
        ignore_dependencies=ctx.obj.get("ignore_dependencies"),
    )

    plan = SceptrePlan(context)
    confirmation(
        plan.execute_change_set.__name__,
        yes,
        change_set=change_set_name,
        command_path=path,
    )
    plan.execute_change_set(change_set_name)
