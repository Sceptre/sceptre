from uuid import uuid1

import click

from sceptre.context import SceptreContext
from sceptre.cli.helpers import catch_exceptions, confirmation
from sceptre.cli.helpers import write, stack_status_exit_code
from sceptre.cli.helpers import simplify_change_set_description
from sceptre.stack_status import StackChangeSetStatus
from sceptre.plan.plan import SceptrePlan


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

    :param path: Path to execute the command on.
    :type path: str
    :param change_set: Whether a change set should be created.
    :type change_set: bool
    :param verbose: A flag to print a verbose output.
    :type verbose: bool
    :param yes: A flag to answer 'yes' to all CLI questions.
    :type yes: bool
    """

    context = SceptreContext(
        command_path=path,
        project_path=ctx.obj.get("project_path"),
        user_variables=ctx.obj.get("user_variables"),
        options=ctx.obj.get("options"),
        output_format=ctx.obj.get("output_format"),
        ignore_dependencies=ctx.obj.get("ignore_dependencies")
    )

    plan = SceptrePlan(context)

    if change_set:
        change_set_name = "-".join(["change-set", uuid1().hex])
        plan.create_change_set(change_set_name)
        try:
            # Wait for change set to be created
            status = plan.wait_for_cs_completion(change_set_name)

            # Exit if change set fails to create
            if status != StackChangeSetStatus.READY:
                exit(1)

            # Describe changes
            description = plan.describe_change_set(change_set_name)
            if not verbose:
                description = simplify_change_set_description(description)
            write(description, context.output_format)

            # Execute change set if happy with changes
            if yes or click.confirm("Proceed with stack update?"):
                plan.execute_change_set(change_set_name)
        finally:
            # Clean up by deleting change set
            plan.delete_change_set(change_set_name)
    else:
        confirmation("update", yes, command_path=path)
        responses = plan.update()
        exit(stack_status_exit_code(responses.values()))
