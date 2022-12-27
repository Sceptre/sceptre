import click
from colorama import Fore, Style

from sceptre.cli.helpers import catch_exceptions, stack_status_exit_code
from sceptre.context import SceptreContext
from sceptre.exceptions import CannotPruneStackError
from sceptre.plan.plan import SceptrePlan
from sceptre.stack import Stack

PATH_FOR_WHOLE_PROJECT = "."


@click.command(name="prune", short_help="Deletes all obsolete stacks in the project")
@click.option("-y", "--yes", is_flag=True, help="Assume yes to all questions.")
@click.argument("path", default=PATH_FOR_WHOLE_PROJECT)
@click.pass_context
@catch_exceptions
def prune_command(ctx, yes: bool, path):
    """
    This command deletes all obsolete stacks in the project. Only obsolete stacks can be deleted
    via prune; If any non-obsolete stacks depend on obsolete stacks, an error will be
    raised and this command will fail.
    """
    context = SceptreContext(
        command_path=path,
        command_params=ctx.params,
        project_path=ctx.obj.get("project_path"),
        user_variables=ctx.obj.get("user_variables"),
        options=ctx.obj.get("options"),
        ignore_dependencies=ctx.obj.get("ignore_dependencies"),
        full_scan=True,
    )
    pruner = Pruner(context)
    pruner.print_operations()
    if not yes and pruner.prune_count > 0:
        pruner.confirm()

    code = pruner.prune()
    exit(code)


class Pruner:
    """Pruner is a utility to coordinate the flow of deleting all stacks in the project that
    are marked "obsolete".

    Note: The command_path on the passed context will be ignored; This command operates on the
    entire project rather than on any particular command path.

    :param context: The Sceptre context to use for pruning
    :param plan_factory: A callable with the signature of (SceptreContext) -> SceptrePlan
    """

    def __init__(self, context: SceptreContext, plan_factory=SceptrePlan):
        self._context = context
        self._make_plan = plan_factory

        self._plan = None

    def confirm(self):
        self._confirm_prune()

    def print_operations(self):
        plan = self._create_plan()

        if not self._plan_has_obsolete_stacks(plan):
            self._print_no_obsolete_stacks()
            return

        self._print_stacks_to_be_deleted(plan)

    @property
    def prune_count(self) -> 0:
        plan = self._create_plan()
        if self._plan_has_obsolete_stacks(plan):
            return len(list(plan))
        return 0

    def prune(self) -> int:
        plan = self._create_plan()

        if not self._plan_has_obsolete_stacks(plan):
            return 0

        if not self._context.ignore_dependencies:
            self._validate_plan_for_dependencies_on_obsolete_stacks(plan)

        code = self._prune(plan)
        return code

    def _create_plan(self):
        if not self._plan:
            context = self._context.clone()
            context.full_scan = True
            plan = self._make_plan(self._context)
            if context.command_path == PATH_FOR_WHOLE_PROJECT:
                stacks = plan.graph
            else:
                stacks = plan.command_stacks

            plan.command_stacks = {stack for stack in stacks if stack.obsolete}
            self._resolve_plan(plan)
            self._plan = plan
        return self._plan

    def _plan_has_obsolete_stacks(self, plan: SceptrePlan):
        return len(plan.command_stacks) > 0

    def _print_no_obsolete_stacks(self):
        click.echo(
            "* There are no stacks marked obsolete, so there is nothing to prune."
        )

    def _resolve_plan(self, plan: SceptrePlan):
        if len(plan.command_stacks) > 0:
            # Prune is actually a particular kind of filtered deletion, so we use delete as the actual
            # resolved command.
            plan.resolve(plan.delete.__name__, reverse=True)

    def _validate_plan_for_dependencies_on_obsolete_stacks(self, plan: SceptrePlan):
        def check_for_non_obsolete_dependencies(stack: Stack):
            # If we've already established it as an obsolete stack to delete, we're good.
            if stack in plan.command_stacks:
                return

            # This check shouldn't be necessary, but we're just double-checking that it is indeed
            # not obsolete.
            if stack.obsolete:
                return

            # Theoretically, we've already gathered up ALL obsolete stacks as command stacks. If
            # we've hit this line, there's a problem. Now we just need to know what caused it. This
            # block climbs down the dependency graph to see which obsolete stack caused this stack
            # to be included in the plan.
            for dependency in stack.dependencies:
                if dependency.obsolete:
                    raise CannotPruneStackError(
                        f"Cannot prune obsolete stack {dependency.name} because stack {stack.name} "
                        f"depends on it but is not obsolete."
                    )

            # If we get to this point, it means this stack isn't obsolete and none of its dependencies
            # are either. That only happens it depends on another non-obsolete stack that depends on
            # an obsolete stack. As a result, we're not going to blow up here and instead will
            # continue iterating on the plan and will raise the error on a stack that directly
            # depends on the obsolete stack.
            return

        for stack in plan:
            check_for_non_obsolete_dependencies(stack)

    def _print_stacks_to_be_deleted(self, plan: SceptrePlan):
        delete_msg = (
            "* The following obsolete stacks will be deleted (if they exist on AWS):\n"
        )

        stacks_list = ""
        for stack in plan:
            # It's possible there could be stacks in the plan that aren't obsolete because those
            # stacks depend on obsolete stacks. They won't pass validation, but that's not the
            # point of this method. We'll just skip those here and fail validation later.
            if not stack.obsolete:
                continue
            stacks_list += "{}{}{}\n".format(Fore.YELLOW, stack.name, Style.RESET_ALL)

        click.echo(delete_msg + stacks_list)

    def _confirm_prune(self):
        click.confirm("Do you want to delete these stacks?", abort=True)

    def _prune(self, plan: SceptrePlan):
        responses = plan.delete()
        return stack_status_exit_code(responses.values())
