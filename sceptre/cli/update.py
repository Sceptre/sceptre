from uuid import uuid1

import click

from sceptre.cli.helpers import catch_exceptions, confirmation
from sceptre.cli.helpers import write, get_stack_or_env
from sceptre.cli.helpers import simplify_change_set_description
from sceptre.stack_status import StackStatus, StackChangeSetStatus


@click.command(name="update")
@click.argument("path")
@click.option(
    "-c", "--change-set", is_flag=True,
    help="Create a change set before updating."
)
@click.option(
    "-v", "--verbose", is_flag=True, help="Display verbose output."
)
@click.option(
    "-y", "--yes", is_flag=True, help="Assume yes to all questions."
)
@click.pass_context
@catch_exceptions
def update_command(ctx, path, change_set, verbose, yes):
    """
    Update a stack.

    Updates a stack for a given config PATH. Or perform an update via
    change-set when the change-set flag is set.
    """

    stack, _ = get_stack_or_env(ctx, path)
    if change_set:
        change_set_name = "-".join(["change-set", uuid1().hex])
        stack.create_change_set(change_set_name)
        try:
            # Wait for change set to be created
            status = stack.wait_for_cs_completion(change_set_name)

            # Exit if change set fails to create
            if status != StackChangeSetStatus.READY:
                exit(1)

            # Describe changes
            description = stack.describe_change_set(change_set_name)
            if not verbose:
                description = simplify_change_set_description(description)
            write(description, ctx.obj["output_format"])

            # Execute change set if happy with changes
            if yes or click.confirm("Proceed with stack update?"):
                stack.execute_change_set(change_set_name)
        finally:
            # Clean up by deleting change set
            stack.delete_change_set(change_set_name)
    else:
        confirmation("update", yes, stack=path)
        response = stack.update()
        if response != StackStatus.COMPLETE:
            exit(1)
