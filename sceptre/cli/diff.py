import click

from sceptre.context import SceptreContext
from sceptre.cli.helpers import catch_exceptions
from sceptre.plan.plan import SceptrePlan
from sceptre.cli.helpers import stack_status_exit_code


@click.command(
    name="diff", short_help="Creates a diff between local and CloudFormation templates.")
@click.argument("path")
@click.pass_context
@catch_exceptions
def diff_command(ctx, path):
    context = SceptreContext(
        command_path=path,
        project_path=ctx.obj.get("project_path"),
        user_variables=ctx.obj.get("user_variables"),
        options=ctx.obj.get("options"),
        ignore_dependencies=ctx.obj.get("ignore_dependencies")
    )

    plan = SceptrePlan(context)
    response = plan.diff()

    exit(stack_status_exit_code(response.values()))
