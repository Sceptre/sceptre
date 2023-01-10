import click

from sceptre.context import SceptreContext
from sceptre.cli.helpers import catch_exceptions
from sceptre.plan.plan import SceptrePlan


@click.command(name="set-policy", short_help="Sets Stack policy.")
@click.argument("path")
@click.argument("policy-file", required=False)
@click.option(
    "-b",
    "--built-in",
    type=click.Choice(["deny-all", "allow-all"]),
    help="Specify a built in stack policy.",
)
@click.pass_context
@catch_exceptions
def set_policy_command(ctx, path, policy_file, built_in):
    """
    Sets a specific Stack policy for either a file or using a built-in policy.
    \f

    :param path: Path to execute the command on.
    :type path: str
    :param policy_file: path to the AWS Policy file to use.
    :type policy_file: str
    :param built_in: the name of the built-in policy file to use.
    :type built_in: str
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

    if built_in == "deny-all":
        plan.lock()
    elif built_in == "allow-all":
        plan.unlock()
    else:
        plan.set_policy(policy_file)
