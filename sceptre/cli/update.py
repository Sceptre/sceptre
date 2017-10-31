from uuid import uuid1

import click

from helpers import catch_exceptions, get_stack, write
from helpers import change_set, simplify_change_set_description
from sceptre.stack_status import StackStatus, StackChangeSetStatus


@click.command(name="update")
@click.argument("path")
@click.option("-c", "--change-set", "change_set_flag", is_flag=True)
@click.option("-v", "--verbose", is_flag=True)
@click.pass_context
@catch_exceptions
def update(ctx, path, change_set_flag, verbose):
    """
    Update a stack.

    Updates a stack for a given config PATH. Or perform an update via
    change-set when the change-set flag is set.
    """
    stack = get_stack(ctx, path)
    if change_set_flag:
        change_set_name = "-".join(["change-set", uuid1().hex])
        with change_set(stack, change_set_name):
            status = stack.wait_for_cs_completion(change_set_name)
            description = stack.describe_change_set(change_set_name)
            if not verbose:
                description = simplify_change_set_description(description)
            write(description, ctx.obj["output_format"])
            if status != StackChangeSetStatus.READY:
                exit(1)
            if click.confirm("Proceed with stack update?"):
                stack.execute_change_set(change_set_name)
    else:
        response = stack.update()
        if response != StackStatus.COMPLETE:
            exit(1)
