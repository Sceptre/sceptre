from abc import abstractmethod
from typing import NamedTuple, Dict, List, Optional, Callable, Tuple, Generic, TypeVar, Any

import cfn_flip

from sceptre.exceptions import StackDoesNotExistError
from sceptre.plan.actions import StackActions
from sceptre.resolvers import Resolver
from sceptre.stack import Stack

DiffType = TypeVar('DiffType')


class StackDiff(NamedTuple):
    stack_name: str
    template_diff: Any
    config_diff: Any


class StackConfiguration(NamedTuple):
    name: str
    parameters: Dict[str, str]
    tags: Dict[str, str]
    notification_arns: List[str]
    role_arn: Optional[str]


class StackDiffer(Generic[DiffType]):
    def __init__(
        self,
        *,
        universal_template_loader: Callable[[str], Tuple[dict, str]] = cfn_flip.load
    ):
        self.load_template = universal_template_loader

    def diff(self, stack_actions: StackActions) -> StackDiff:
        generated_config = self._create_generated_config(stack_actions.stack)
        deployed_config = self._create_deployed_stack_config(stack_actions)

        generated_template = self._generate_template(stack_actions)
        deployed_template = self._get_deployed_template(stack_actions)

        template_diff = self.compare_templates(generated_template, deployed_template)
        config_diff = self.compare_stack_configurations(generated_config, deployed_config)

        return StackDiff(stack_actions.stack.external_name, template_diff, config_diff)

    def _generate_template(self, stack_actions: StackActions) -> dict:
        generated_template_string = stack_actions.generate()
        template_as_dict, template_format = self.load_template(generated_template_string)
        return template_as_dict

    def _create_generated_config(self, stack: Stack) -> StackConfiguration:
        parameters = self._extract_parameters_dict(stack)
        stack_configuration = StackConfiguration(
            name=stack.external_name,
            parameters=parameters,
            tags=stack.tags,
            notification_arns=stack.notifications,
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
                tags={
                    tag['Key']: tag['Value']
                    for tag in stack['Tags']
                },
                name=stack['StackName'],
                notification_arns=stack['NotificationARNs'],
                role_arn=stack.get('RoleARN')
            )

    def _get_deployed_template(self, stack_actions: StackActions) -> dict:
        template_string = stack_actions.fetch_remote_template()
        if template_string is None:
            return {}
        template_dict, template_format = self.load_template(template_string)
        return template_dict

    @abstractmethod
    def compare_templates(
        self,
        generated: dict,
        deployed: dict
    ) -> DiffType:
        """Implement this method to return the diff for the templates"""

    @abstractmethod
    def compare_stack_configurations(
        self,
        generated: StackConfiguration,
        deployed: Optional[StackConfiguration]
    ) -> DiffType:
        """Implement this method to return the diff for the Stack Configurations"""
