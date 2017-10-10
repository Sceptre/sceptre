import click

from sceptre.cli.helpers import catch_exceptions, write
from sceptre.cli.helpers import simplify_change_set_description


@click.group(name="describe")
def describe_group():
    """
    Commands for describing attributes of stacks.
    """
    pass


@describe_group.command(name="change-set")
@click.argument("path")
@click.argument("change-set-name")
@click.option("-v", "--verbose", is_flag=True)
@click.pass_context
@catch_exceptions
def describe_change_set(ctx, path, change_set_name, verbose):
    """
    Describes the change set.

    """
    stack = ctx.obj["config_reader"].construct_stack(path)
    description = stack.describe_change_set(change_set_name)
    if not verbose:
        description = simplify_change_set_description(description)
    write(description, ctx.obj["output_format"])


@describe_group.command(name="policy")
@click.argument("path")
@click.pass_context
@catch_exceptions
def describe_policy(ctx, path):
    """
    Displays the stack policy used.

    """
    stack = ctx.obj["config_reader"].construct_stack(path)
    response = stack.get_policy()
    write(response.get('StackPolicyBody', {}))
