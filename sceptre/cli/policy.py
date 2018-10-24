import click

from sceptre.cli.helpers import catch_exceptions, get_stack_or_stack_group
from sceptre.plan.plan import SceptrePlan


@click.command(name="set-policy")
@click.argument("path")
@click.argument("policy-file", required=False)
@click.option(
    "-b", "--built-in", type=click.Choice(["deny-all", "allow-all"]),
    help="Specify a built in stack policy."
)
@click.pass_context
@catch_exceptions
def set_policy_command(ctx, path, policy_file, built_in):
    """
    Sets stack policy.

    Sets a specific stack policy for either a file or using a built-in policy.
    """
    stack, _ = get_stack_or_stack_group(ctx, path)

    if built_in == 'deny-all':
        action = 'lock'
        plan = SceptrePlan(path, action, stack)
        plan.execute()
    elif built_in == 'allow-all':
        action = 'unlock'
        plan = SceptrePlan(path, action, stack)
        plan.execute()
    else:
        action = 'set_policy'
        plan = SceptrePlan(path, action, stack)
        plan.execute(policy_file)
