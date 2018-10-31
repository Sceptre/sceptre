import click

from sceptre.cli.helpers import (
            catch_exceptions,
            get_stack_or_stack_group,
            simplify_change_set_description,
            write
            )
from sceptre.plan.plan import SceptrePlan


@click.group(name="describe")
@click.pass_context
def describe_group(ctx):
    """
    Commands for describing attributes of stacks.
    """
    pass


@describe_group.command(name="change-set")
@click.argument("path")
@click.argument("change-set-name")
@click.option(
    "-v", "--verbose", is_flag=True, help="Display verbose output."
)
@click.pass_context
@catch_exceptions
def describe_change_set(ctx, path, change_set_name, verbose):
    """
    Describes the change set.

    """
    stack, _ = get_stack_or_stack_group(ctx, path)
    action = 'describe_change_set'
    plan = SceptrePlan(path, action, stack)
    description = plan.execute(change_set_name)
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
    stack, _ = get_stack_or_stack_group(ctx, path)
    action = 'get_policy'
    plan = SceptrePlan(path, action, stack)
    response = plan.execute()
    write(response.get('StackPolicyBody', {}))
