import logging
from typing import List

import click
from click import Context
from colorama import Fore, Style

from sceptre.cli.helpers import catch_exceptions, confirmation, stack_status_exit_code
from sceptre.context import SceptreContext
from sceptre.exceptions import DependencyDoesNotExistError
from sceptre.plan.plan import SceptrePlan
from sceptre.stack import Stack
from sceptre.stack_status import StackStatus

logger = logging.getLogger(__name__)


@click.command(name="launch", short_help="Launch a Stack or StackGroup.")
@click.argument("path")
@click.option("-y", "--yes", is_flag=True, help="Assume yes to all questions.")
@click.option(
    "-p",
    "--prune",
    is_flag=True,
    help="If set, will delete all stacks in the command path marked as obsolete."
)
@click.pass_context
@catch_exceptions
def launch_command(ctx: Context, path: str, yes: bool, prune: bool):
    """
    Launch a Stack or StackGroup for a given config PATH. This command is intended as a catch-all
    command that will apply any changes from Stack Configs indicated via the path.

    \b
    * Any Stacks that do not exist will be created
    * Any stacks that already exist will be updated (if there are any changes)
    * If any stacks are marked with "ignore: True", those stacks will neither be created nor updated
    * If any stacks are marked with "obsolete: True", those stacks will neither be created nor updated.
      Furthermore, if the "-p"/"--prune" flag is used, these stacks will be deleted prior to any
      other launch commands
    """
    context = SceptreContext(
        command_path=path,
        project_path=ctx.obj.get("project_path"),
        user_variables=ctx.obj.get("user_variables"),
        options=ctx.obj.get("options"),
        ignore_dependencies=ctx.obj.get("ignore_dependencies")
    )
    launcher = Launcher(context)
    exit_code = launcher.launch(yes, prune)
    exit(exit_code)


class Launcher:
    """Launcher is a utility to coordinate the flow of launching.

    :param context: The Sceptre context to use for launching
    :param plan_factory: A callable with the signature of (SceptreContext) -> SceptrePlan
    """
    def __init__(self, context: SceptreContext, plan_factory=SceptrePlan):
        self._context = context
        self._make_plan = plan_factory

    def launch(self, yes: bool, prune: bool) -> int:
        deploy_plan = self._create_deploy_plan()
        stacks_to_skip = self._get_stacks_to_skip(deploy_plan, prune)
        stacks_to_prune = self._get_stacks_to_prune(deploy_plan, prune)

        self._exclude_stacks_from_plan(deploy_plan, *stacks_to_skip, *stacks_to_prune)
        self._validate_launch_for_missing_dependencies(deploy_plan, prune)
        self._print_skips(stacks_to_skip)
        self._print_deletions(stacks_to_prune)
        self._confirm_launch(yes)

        code = self._prune(stacks_to_prune)
        code = code or self._deploy(deploy_plan)
        return code

    def _create_deploy_plan(self) -> SceptrePlan:
        plan = self._make_plan(self._context)
        # The plan must be resolved so we can modify launch order and items before executing it
        plan.resolve(plan.launch.__name__)
        return plan

    def _get_stacks_to_skip(self, deploy_plan: SceptrePlan, prune: bool) -> List[Stack]:
        return [stack for stack in deploy_plan if stack.ignore or (stack.obsolete and not prune)]

    def _get_stacks_to_prune(self, deploy_plan: SceptrePlan, prune: bool) -> List[Stack]:
        return [stack for stack in deploy_plan if prune and stack.obsolete]

    def _exclude_stacks_from_plan(self, deployment_plan: SceptrePlan, *stacks: Stack):
        for stack in stacks:
            deployment_plan.remove_stack_from_plan(stack)

    def _validate_launch_for_missing_dependencies(self, deploy_plan: SceptrePlan, prune: bool):
        validated_stacks = set()
        skipped_dependencies = set()

        def validate_stack_dependencies(stack: Stack):
            if stack in validated_stacks:
                # In order to avoid unnecessary recursions on stacks already evaluated, we'll return
                # early if we've already evaluated the stack without issue.
                return
            if prune and stack.obsolete:
                raise DependencyDoesNotExistError(
                    f"Launch plan with option depends on stack {stack.name} that is marked as obsolete. "
                    f"This plan cannot be launched with the --prune option. Only obsolete stacks can "
                    f"depend upon obsolete stacks when pruning."
                )
            for dependency in stack.dependencies:
                if dependency.ignore or dependency.obsolete:
                    skipped_dependencies.add(dependency)
                validate_stack_dependencies(dependency)
            validated_stacks.add(stack)

        for stack in deploy_plan:
            validate_stack_dependencies(stack)

        message = (
            "WARNING: Launch plan depends on the following ignored and/or obsolete stacks. Sceptre "
            "will attempt to continue with launch, but it may fail if any Stack Configs require "
            "certain resources or outputs that don't currently exist."
        )
        self._print_stacks_with_message(list(skipped_dependencies), message)

    def _print_skips(self, stacks_to_skip: List[Stack]):
        skip_message = "During launch, the following stacks will be skipped, neither created nor updated:"
        self._print_stacks_with_message(stacks_to_skip, skip_message)

    def _print_stacks_with_message(self, stacks: List[Stack], message: str):
        if not len(stacks):
            return

        message = f'* {message}\n'
        for stack in stacks:
            message += f"{Fore.YELLOW}{stack.name}{Style.RESET_ALL}\n"

        click.echo(message)

    def _print_deletions(self, stacks_to_prune: List[Stack]):
        delete_message = "During launch, the following stacks will be will be deleted, if they exist:"
        self._print_stacks_with_message(stacks_to_prune, delete_message)

    def _confirm_launch(self, yes: bool):
        confirmation("launch", yes, command_path=self._context.command_path)

    def _prune(self, stacks_to_prune: List[Stack]) -> int:
        if len(stacks_to_prune) == 0:
            return 0

        delete_plan = self._create_prune_plan(stacks_to_prune)
        result = delete_plan.delete()
        exit_code = stack_status_exit_code(result.values())
        if exit_code != 0:
            failed_stacks = [s for s in result.keys() if result[s] != StackStatus.COMPLETE]
            self._print_stacks_with_message(
                failed_stacks,
                "Stack deletion failed, so could not proceed with launch. Failed Stacks:"
            )
        return exit_code

    def _create_prune_plan(self, stacks_to_prune: List[Stack]) -> SceptrePlan:
        # We need a new context for deletion
        delete_context = self._context.clone()
        delete_context.full_scan = True  # full_scan lets us pull all stacks in root directory
        delete_context.ignore_dependencies = True  # we ONLY care about deleting the command stacks
        deletion_plan = self._make_plan(delete_context)
        # We're overriding the command_stacks so we target only those stacks that have been marked
        # with obsolete: True
        deletion_plan.command_stacks = set(stacks_to_prune)
        return deletion_plan

    def _deploy(self, deploy_plan: SceptrePlan) -> int:
        result = deploy_plan.launch()
        exit_code = stack_status_exit_code(result.values())
        return exit_code
