import click

from sceptre.cli.helpers import catch_exceptions, get_stack


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
    stack = get_stack(ctx, path)

    if built_in == 'deny-all':
        stack.lock()
    elif built_in == 'allow-all':
        stack.unlock()
    else:
        stack.set_policy(policy_file)
