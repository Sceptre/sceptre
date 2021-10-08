import difflib
from abc import abstractmethod
from typing import NamedTuple, Dict, List, Optional, Callable, Tuple, Generic, TypeVar

import cfn_flip
import deepdiff

from sceptre.exceptions import StackDoesNotExistError
from sceptre.plan.actions import StackActions
from sceptre.resolvers import Resolver
from sceptre.stack import Stack

DiffType = TypeVar('DiffType')


class StackConfiguration(NamedTuple):
    """A data container to represent the comparable parts of a Stack."""
    stack_name: str
    parameters: Dict[str, str]
    stack_tags: Dict[str, str]
    notifications: List[str]
    role_arn: Optional[str]


class StackDiff(NamedTuple):
    """A data container to represent the full difference between a deployed stack and the stack as
    it exists locally within Sceptre.
    """
    stack_name: str
    template_diff: DiffType
    config_diff: DiffType
    is_deployed: bool
    generated_config: StackConfiguration
    generated_template: str


class StackDiffer(Generic[DiffType]):
    """A utility for producing a StackDiff that indicates the full difference between a given stack
    as it is currently DEPLOYED on CloudFormation and the stack as it exists in the local Sceptre
    configurations.

    This utility compares both the stack configuration (specifically those attributes that CAN be
    compared) as well as the stack template.

    As an abstract base class, the two comparison methods need to be implemented so that the
    StackDiff can be generated.
    """

    STACK_STATUSES_INDICATING_NOT_DEPLOYED = [
        'CREATE_FAILED',
        'ROLLBACK_COMPLETE',
        'DELETE_COMPLETE',
    ]

    def diff(self, stack_actions: StackActions) -> StackDiff:
        """Produces a StackDiff between the currently deployed stack (if it exists) and the stack
        as it exists locally in Sceptre.

        :param stack_actions: The StackActions object to use for generating and fetching templates
            as well as providing other details about the stack.
        :return: The StackDiff that expresses the difference.
        """
        generated_config = self._create_generated_config(stack_actions.stack)
        deployed_config = self._create_deployed_stack_config(stack_actions)
        is_stack_deployed = bool(deployed_config)

        generated_template = self._generate_template(stack_actions)
        deployed_template = self._get_deployed_template(stack_actions, is_stack_deployed)

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

    def _extract_parameters_dict(self, stack: Stack) -> dict:
        """Extracts a USABLE dict of parameters from the stack.

        Because stack parameters often contain resolvers referencing stacks that might not exist yet
        (such as when producing a diff on a yet-to-be-deployed stack), we cannot always resolve the
        stack parameters. Therefore, we need to resolve them (if possible) and fall back to a
        different representation of that resolver, if necessary.

        :param stack: The stack to extract the parameters from
        :return: A dictionary of stack parameters to be compared.
        """
        parameters = {}
        # parameters is a ResolvableProperty, but the underlying, pre-resolved parameters are
        # stored in _parameters. We might not actually be able to resolve values, such as in the
        # case where it attempts to get a value from a stack that doesn't exist yet.
        for key, value in stack._parameters.items():
            if isinstance(value, Resolver):
                # There might be some resolvers that we can still resolve values for.
                try:
                    value_to_use = value.resolve()
                except Exception:
                    # We catch any errors out of the resolver, since that usually indicates the stack
                    # doesn't exist yet. In the end, this value likely won't matter, because if the
                    # stack this one is dependent upon doesn't exist, this one most likely won't
                    # exist either, so when deployed version is compared to this one, it will
                    # indicate we're creating a new stack where one doesn't exist. The only place
                    # this value would be shown is where the current stack DOES exist, but a new
                    # dependency is added that does not exist yet. In which case, it will show the
                    # most usable output we can provide right now.
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
            # This means the stack has not been deployed yet
            return None

        stacks = description['Stacks']
        for stack in stacks:
            if stack['StackStatus'] in self.STACK_STATUSES_INDICATING_NOT_DEPLOYED:
                return None
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

    def _get_deployed_template(self, stack_actions: StackActions, is_deployed: bool) -> str:
        if is_deployed:
            return stack_actions.fetch_remote_template() or '{}'
        else:
            return '{}'

    @abstractmethod
    def compare_templates(
        self,
        deployed: str,
        generated: str,
    ) -> DiffType:
        """Implement this method to return the diff for the templates

        :param deployed: The stack template as it has been deployed
        :param generated: The stack template as it exists locally within Sceptre
        :return: The generated diff between the two
        """

    @abstractmethod
    def compare_stack_configurations(
        self,
        deployed: Optional[StackConfiguration],
        generated: StackConfiguration,
    ) -> DiffType:
        """Implement this method to return the diff for the stack configurations.

        :param deployed: The StackConfiguration as it has been deployed. This MIGHT be None, if the
            stack has not been deployed.
        :param generated: The StackConfiguration as it exists locally within Sceptre
        :return: The generated diff between the two
        """


class DeepDiffStackDiffer(StackDiffer[deepdiff.DeepDiff]):
    """A StackDiffer that relies upon the DeepDiff library to produce the difference between the
    stack as it has been deployed onto CloudFormation and as it exists locally within Sceptre.

    This differ relies upon a recursive key/value comparison of Python data structures, indicating
    specific keys or values that have been added, removed, or altered between the two. Templates
    are read in as dictionaries and compared this way, so json or yaml formatting changes will not
    be reflected, only changes in value.
    """
    VERBOSITY_LEVEL_TO_INDICATE_CHANGED_VALUES = 2

    def __init__(
        self,
        *,
        universal_template_loader: Callable[[str], Tuple[dict, str]] = cfn_flip.load
    ):
        """Initializes a DeepDiffStackDiffer.

        :param universal_template_loader: This should be a callable that can load either a json or
            yaml string and return a tuple where the first element is the loaded template and the
            second element is the template format (either "json" or "yaml")
        """
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
        # We don't actually care about the original formats here, since we only care about the
        # template VALUES.
        deployed_dict, _ = self.load_template(deployed)
        generated_dict, _ = self.load_template(generated)

        return deepdiff.DeepDiff(
            deployed_dict,
            generated_dict,
            verbose_level=self.VERBOSITY_LEVEL_TO_INDICATE_CHANGED_VALUES
        )


class DifflibStackDiffer(StackDiffer[List[str]]):
    """A StackDiffer that uses difflib to produce a diff between the stack as it exists on AWS and
    the stack as it exists locally within Sceptre.

    Because difflib generates diffs off of lists of strings, both StackConfigurations and
    """
    def __init__(
        self,
        *,
        universal_template_loader: Callable[[str], Tuple[dict, str]] = cfn_flip.load
    ):
        """Initializes a DifflibStackDiffer.

        :param universal_template_loader: This should be a callable that can load either a json or
            yaml string and return a tuple where the first element is the loaded template and the
            second element is the template format (either "json" or "yaml")
        """
        super().__init__()
        self.load_template = universal_template_loader

    def compare_stack_configurations(
        self,
        deployed: Optional[StackConfiguration],
        generated: StackConfiguration,
    ) -> List[str]:
        deployed_dict = deployed._asdict() if deployed else {}
        deployed_string = cfn_flip.dump_yaml(deployed_dict)
        generated_string = cfn_flip.dump_yaml(generated._asdict())
        return self._make_string_diff(
            deployed_string,
            generated_string
        )

    def compare_templates(
        self,
        deployed: str,
        generated: str,
    ) -> List[str]:
        # Sometimes there might only be simple whitespace differences... which difflib will show but
        # are actually insignificant and "false positives". Also, CloudFormation has a habit of
        # returning dictionaries when we get the "Original" template. We can't know the original
        # format for these, so we load them and dump them uniformly again. This will eliminate minor
        # whitespace changes.
        deployed_dict, _ = self.load_template(deployed)
        generated_dict, generated_format = self.load_template(generated)
        dumpers = {
            'json': cfn_flip.dump_json,
            'yaml': cfn_flip.dump_yaml
        }
        # We always prefer the generated format, because often CloudFormation will send back a
        # dictionary for the template and it is not clear what the original format was. By preferring
        # the generated format, we assume that we haven't switched between yaml and json. But if we
        # did, we'd still would only be comparing the the values and not the actual formatting, so
        # this is a better diff anyway.
        deployed_reformatted = dumpers[generated_format](deployed_dict)
        generated_reformatted = dumpers[generated_format](generated_dict)

        return self._make_string_diff(deployed_reformatted, generated_reformatted)

    def _make_string_diff(self, deployed: str, generated: str) -> List[str]:
        diff_lines = difflib.unified_diff(
            deployed.splitlines(),
            generated.splitlines(),
            fromfile="deployed",
            tofile="generated",
            lineterm=""
        )
        return list(diff_lines)
