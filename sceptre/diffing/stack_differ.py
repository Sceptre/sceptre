import difflib
from abc import abstractmethod
from typing import NamedTuple, Dict, List, Optional, Callable, Tuple, Generic, TypeVar, Any

import cfn_flip
import dictdiffer
import yaml
import deepdiff

from sceptre.exceptions import StackDoesNotExistError
from sceptre.plan.actions import StackActions
from sceptre.resolvers import Resolver
from sceptre.stack import Stack

DiffType = TypeVar('DiffType')


class StackConfiguration(NamedTuple):
    stack_name: str
    parameters: Dict[str, str]
    stack_tags: Dict[str, str]
    notifications: List[str]
    role_arn: Optional[str]


class StackDiff(NamedTuple):
    stack_name: str
    template_diff: DiffType
    config_diff: DiffType
    is_deployed: bool
    generated_config: StackConfiguration
    generated_template: str


class StackDiffer(Generic[DiffType]):

    def diff(self, stack_actions: StackActions) -> StackDiff:
        generated_config = self._create_generated_config(stack_actions.stack)
        deployed_config = self._create_deployed_stack_config(stack_actions)
        is_stack_deployed = bool(deployed_config)

        generated_template = self._generate_template(stack_actions)
        deployed_template = self._get_deployed_template(stack_actions)

        template_diff = self.compare_templates(deployed_template, generated_template)
        config_diff = self.compare_stack_configurations(deployed_config, generated_config)

        return StackDiff(
            stack_actions.stack.external_name,
            template_diff,
            config_diff,
            is_stack_deployed,
            generated_config,
            generated_template
        )

    def _generate_template(self, stack_actions: StackActions) -> str:
        return stack_actions.generate()

    def _create_generated_config(self, stack: Stack) -> StackConfiguration:
        parameters = self._extract_parameters_dict(stack)
        stack_configuration = StackConfiguration(
            stack_name=stack.external_name,
            parameters=parameters,
            stack_tags=stack.tags,
            notifications=stack.notifications,
            role_arn=stack.role_arn
        )

        return stack_configuration

    def _extract_parameters_dict(self, stack: Stack):
        parameters = {}
        # parameters is a ResolvableProperty, but the underlying, pre-resolved parameters are
        # stored in _parameters. We might not actually be able to resolve values, such as in the
        # case where it attempts to get a value from a stack that doesn't exist yet. Therefore, this
        # resolves the values individually, where they CAN be resolved, and otherwise makes an
        # alternative placeholder value
        for key, value in stack._parameters.items():
            if isinstance(value, Resolver):
                # There might be some resolvers that we can still resolve values for.
                try:
                    value_to_use = value.resolve()
                except StackDoesNotExistError:
                    # In the end, this value likely won't matter, because if the stack this one is
                    # dependent upon doesn't exist, this one most likely won't exist either, so
                    # when deployed version is compared to this one, it will indicate we're creating
                    # a new stack where one doesn't exist. The only place this value would be shown
                    # is where the current stack DOES exist, but a new dependency is added that does
                    # not exist yet. In which case, it will show the most usable output we can
                    # provide right now.
                    value_to_use = f'!{type(value).__name__}'
                    if value.argument is not None:
                        value_to_use += f': {value.argument}'
            else:
                value_to_use = value
            parameters[key] = value_to_use

        return parameters

    def _create_deployed_stack_config(self, stack_actions: StackActions) -> Optional[StackConfiguration]:
        description = stack_actions.describe()
        if description is None:
            return None

        stacks = description['Stacks']
        for stack in stacks:
            return StackConfiguration(
                parameters={
                    param['ParameterKey']: param.get('ResolvedValue', param['ParameterValue'])
                    for param
                    in stack.get('Parameters', [])
                },
                stack_tags={
                    tag['Key']: tag['Value']
                    for tag in stack['Tags']
                },
                stack_name=stack['StackName'],
                notifications=stack['NotificationARNs'],
                role_arn=stack.get('RoleARN')
            )

    def _get_deployed_template(self, stack_actions: StackActions) -> str:
        template_string = stack_actions.fetch_remote_template()

        if template_string is None:
            return '{}'

        return template_string

    @abstractmethod
    def compare_templates(
        self,
        deployed: str,
        generated: str,
    ) -> DiffType:
        """Implement this method to return the diff for the templates"""

    @abstractmethod
    def compare_stack_configurations(
        self,
        deployed: Optional[StackConfiguration],
        generated: StackConfiguration,
    ) -> DiffType:
        """Implement this method to return the diff for the Stack Configurations"""


class DeepDiffStackDiffer(StackDiffer):
    VERBOSITY_LEVEL_TO_INDICATE_CHANGED_VALUES = 2

    def __init__(
        self,
        *,
        universal_template_loader: Callable[[str], Tuple[dict, str]] = cfn_flip.load
    ):
        self.load_template = universal_template_loader

    def compare_stack_configurations(
        self,
        deployed: Optional[StackConfiguration],
        generated: StackConfiguration,
    ) -> deepdiff.DeepDiff:
        return deepdiff.DeepDiff(
            deployed,
            generated,
            verbose_level=self.VERBOSITY_LEVEL_TO_INDICATE_CHANGED_VALUES
        )

    def compare_templates(self, deployed: str, generated: str,) -> deepdiff.DeepDiff:
        deployed_dict, original_format = self.load_template(deployed)
        generated_dict, original_format = self.load_template(generated)

        return deepdiff.DeepDiff(
            deployed_dict,
            generated_dict,
            verbose_level=self.VERBOSITY_LEVEL_TO_INDICATE_CHANGED_VALUES
        )


class DifflibStackDiffer(StackDiffer):
    def __init__(
        self,
        *,
        serializer: Callable[[dict], str] = yaml.dump,
    ):
        super().__init__()
        self.serialize = serializer

    def compare_stack_configurations(
        self,
        deployed: Optional[StackConfiguration],
        generated: StackConfiguration,
    ) -> List[str]:
        deployed_string = self.serialize(deployed._asdict())
        generated_string = self.serialize(generated._asdict())
        diff_lines = difflib.unified_diff(
            deployed_string.splitlines(),
            generated_string.splitlines(),
            fromfile="deployed",
            tofile="generated",
            lineterm=""
        )
        return list(diff_lines)

    def compare_templates(
        self,
        deployed: str,
        generated: str,
    ) -> List[str]:
        diff_lines = difflib.unified_diff(
            deployed.splitlines(),
            generated.splitlines(),
            fromfile="deployed",
            tofile="generated",
            lineterm=""
        )
        return list(diff_lines)
