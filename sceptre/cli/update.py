from uuid import uuid1

import click

from typing import Optional
from sceptre.context import SceptreContext
from sceptre.cli.helpers import catch_exceptions, confirmation
from sceptre.cli.helpers import write, stack_status_exit_code
from sceptre.cli.helpers import simplify_change_set_description
from sceptre.stack_status import StackChangeSetStatus
from sceptre.plan.plan import SceptrePlan


@click.command(name="update", short_help="Update a stack.")
@click.argument("path")
@click.option(
    "-c", "--change-set", is_flag=True, help="Create a change set before updating."
)
@click.option("-v", "--verbose", is_flag=True, help="Display verbose output.")
@click.option("-y", "--yes", is_flag=True, help="Assume yes to all questions.")
@click.option(
    "--disable-rollback/--enable-rollback",
    default=None,
    help="Disable or enable the cloudformation automatic rollback",
)
@click.pass_context
@catch_exceptions
def update_command(
    ctx, path, change_set, verbose, yes, disable_rollback: Optional[bool]
):
    """
    Updates a stack for a given config PATH. Or perform an update via
    change-set when the change-set flag is set.
    \f

    :param path: Path to execute the command on.
    :type path: str
    :param change_set: Whether a change set should be created.
    :type change_set: bool
    :param verbose: A flag to print a verbose output.
    :type verbose: bool
    :param yes: A flag to answer 'yes' to all CLI questions.
    :type yes: bool
    :param disable_rollback: A flag to disable cloudformation rollback.
    """

    context = SceptreContext(
        command_path=path,
        command_params=ctx.params,
        project_path=ctx.obj.get("project_path"),
        user_variables=ctx.obj.get("user_variables"),
        options=ctx.obj.get("options"),
        output_format=ctx.obj.get("output_format"),
        ignore_dependencies=ctx.obj.get("ignore_dependencies"),
    )

    plan = SceptrePlan(context)

    if change_set:
        change_set_name = "-".join(["change-set", uuid1().hex])
        plan.create_change_set(change_set_name)
        try:
            # Wait for change set to be created
            statuses = plan.wait_for_cs_completion(change_set_name)

            at_least_one_ready = False

            for status in statuses.values():
                # Exit if change set fails to create
                if status not in (
                    StackChangeSetStatus.READY,
                    StackChangeSetStatus.NO_CHANGES,
                ):
                    write("Failed to create change set", context.output_format)
                    exit(1)

                if status == StackChangeSetStatus.READY:
                    at_least_one_ready = True

            # If none are ready, and we haven't exited, there are no changes
            if not at_least_one_ready:
                write("No changes detected", context.output_format)
                exit(0)

            # Describe changes
            descriptions = plan.describe_change_set(change_set_name)
            for stack, description in descriptions.items():
                # No need to print if there are no changes
                if statuses[stack] == StackChangeSetStatus.NO_CHANGES:
                    continue

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
