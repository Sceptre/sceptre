import difflib
import logging
from abc import abstractmethod
from typing import (
    NamedTuple,
    Dict,
    List,
    Optional,
    Callable,
    Tuple,
    Generic,
    TypeVar,
    Union,
)

import cfn_flip
import deepdiff
import yaml
from cfn_tools import ODict
from yaml import Dumper

from sceptre.exceptions import SceptreException
from sceptre.plan.actions import StackActions
from sceptre.stack import Stack

from botocore.exceptions import ClientError

DiffType = TypeVar("DiffType")

logger = logging.getLogger(__name__)


class StackConfiguration(NamedTuple):
    """A data container to represent the comparable parts of a Stack."""

    stack_name: str
    parameters: Dict[str, Union[str, List[str]]]
    stack_tags: Dict[str, str]
    notifications: List[str]
    cloudformation_service_role: Optional[str]


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


def repr_str(dumper: Dumper, data: str) -> str:
    """A YAML Representer that handles strings, breaking multi-line strings into something a lot
    more readable in the yaml output. This is useful for representing long, multiline strings in
    templates or in stack parameters.

    :param dumper: The Dumper that is being used to serialize this object
    :param data: The string to serialize
    :return: The represented string
    """
    if "\n" in data:
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    return dumper.represent_str(data)


def repr_odict(dumper: Dumper, data: ODict) -> str:
    """A YAML Representer for cfn-flip's ODict objects.

    ODicts are a variation on OrderedDicts for that library. Since the Diff command makes extensive
    use of ODicts, they can end up in diff output and the PyYaml library doesn't otherwise calls the
    dicts like !!ODict, which looks weird. We can just treat them like normal dicts when we serialize
    them, though.

    :param dumper: The Dumper that is being used to serialize this object
    :param data: The ODict object to serialize
    :return: The serialized ODict
    """
    return dumper.represent_dict(data)


yaml.add_representer(str, repr_str)
yaml.add_representer(ODict, repr_odict)


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
        "CREATE_FAILED",
        "ROLLBACK_COMPLETE",
        "DELETE_COMPLETE",
    ]

    NO_ECHO_REPLACEMENT = "****"

    def __init__(self, show_no_echo=False):
        """Initializes the StackDiffer.

        :param show_no_echo: If True, local parameters passed that the template says are NoEcho
            parameters will be displayed; Otherwise, they will be masked in the diff.
        """
        self.show_no_echo = show_no_echo

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
        deployed_template = self._get_deployed_template(
            stack_actions, is_stack_deployed
        )

        self._handle_special_parameter_situations(
            stack_actions, generated_config, deployed_config
        )

        template_diff = self.compare_templates(deployed_template, generated_template)
        config_diff = self.compare_stack_configurations(
            deployed_config, generated_config
        )

        return StackDiff(
            stack_actions.stack.external_name,
            template_diff,
            config_diff,
            is_stack_deployed,
            generated_config,
            generated_template,
        )

    def _create_generated_config(self, stack: Stack) -> StackConfiguration:
        parameters = self._extract_parameters_from_generated_stack(stack)
        stack_configuration = StackConfiguration(
            stack_name=stack.external_name,
            parameters=parameters,
            stack_tags=stack.tags,
            notifications=stack.notifications,
            cloudformation_service_role=stack.cloudformation_service_role,
        )

        return stack_configuration

    def _extract_parameters_from_generated_stack(self, stack: Stack) -> dict:
        """Extracts a usable dict of parameters from the stack, performing some minor transformations
        to match the what CloudFormation does on its end.

        :param stack: The stack to extract the parameters from
        :return: A dictionary of stack parameters to be compared.
        """
        formatted_parameters = {}
        for key, value in stack.parameters.items():
            # When boto3 receives "None" for a cloudformation parameter, it treats it as if the
            # value is not passed at all. To be consistent in our diffing, we need to skip Nones
            # altogether.
            if value is None:
                continue

            try:
                if isinstance(value, list):
                    value = ",".join(item.rstrip("\n") for item in value)
                formatted_parameters[key] = value.rstrip("\n")
            # Other unexpected data can get through and this would blow up the differ
            # and lead to quite confusing exceptions being raised. This check here could
            # be removed in a future version of Sceptre if the reader class did sanity checking.
            except AttributeError:
                raise SceptreException(
                    f"Parameter '{key}' whose value is {value} "
                    f"is of type {type(value)} and not expected here"
                )

        return formatted_parameters

    def _create_deployed_stack_config(
        self, stack_actions: StackActions
    ) -> Optional[StackConfiguration]:
        try:
            description = stack_actions.describe()
        except ClientError as err:
            # This means the stack has not been deployed yet
            if err.response["Error"]["Message"].endswith("does not exist"):
                return None

        stacks = description["Stacks"]
        for stack in stacks:
            if stack["StackStatus"] in self.STACK_STATUSES_INDICATING_NOT_DEPLOYED:
                return None
            return StackConfiguration(
                parameters={
                    param["ParameterKey"]: param["ParameterValue"]
                    for param in stack.get("Parameters", [])
                },
                stack_tags={tag["Key"]: tag["Value"] for tag in stack["Tags"]},
                stack_name=stack["StackName"],
                notifications=stack["NotificationARNs"],
                cloudformation_service_role=stack.get("RoleARN"),
            )

    def _handle_special_parameter_situations(
        self,
        stack_actions: StackActions,
        generated_config: StackConfiguration,
        deployed_config: StackConfiguration,
    ):
        deployed_template_summary = stack_actions.fetch_remote_template_summary()
        generated_template_summary = stack_actions.fetch_local_template_summary()

        if deployed_config is not None:
            # Trailing linebreaks sometimes get removed by CloudFormation in certain circumstances
            # and can sometimes come from using the !file_contents resolver, but ultimately they
            # shouldn't affect the diff. We'll ignore all trailing linebreaks.
            self._remove_terminating_linebreaks_from_deployed_parameters(
                deployed_template_summary, deployed_config
            )

            # If the parameter is not passed by Sceptre and the value on the deployed parameter is
            # the default value, we'll actually remove it from the deployed parameters list so it
            # doesn't show up as a false positive.
            self._remove_deployed_default_parameters_that_arent_passed(
                deployed_template_summary, generated_config, deployed_config
            )

        if not self.show_no_echo:
            # We don't actually want to show parameters Sceptre is passing that the local template
            # marks as NoEcho parameters (unless show_no_echo is set to true). Therefore those
            # parameter values will be masked.
            self._mask_no_echo_parameters(generated_template_summary, generated_config)

    def _remove_terminating_linebreaks_from_deployed_parameters(
        self, template_summary: Optional[dict], deployed_config: StackConfiguration
    ):
        if template_summary is None:
            return

        parameter_types = {
            parameter["ParameterKey"]: parameter["ParameterType"]
            for parameter in template_summary["Parameters"]
        }

        for key, value in deployed_config.parameters.items():
            parameter_type = parameter_types[key]
            if parameter_type == "CommaDelimitedList":
                # If it's a list of strings, remove trailing linebreaks for each item
                value = ",".join([item.rstrip("\n") for item in value.split(",")])

            deployed_config.parameters[key] = value.rstrip("\n")

    def _remove_deployed_default_parameters_that_arent_passed(
        self,
        template_summary: dict,
        generated_config: StackConfiguration,
        deployed_config: StackConfiguration,
    ):
        deployed_config_default_map = self._get_parameter_default_map(template_summary)
        for parameter_key, default_value in deployed_config_default_map.items():
            # If the generated config defines that parameter, leave that in the deployed config
            # so we can see the diff.
            if parameter_key in generated_config.parameters:
                continue

            # But if the stack config is relying on the template's default value for this parameter,
            # remove that parameter from the deployed config... but only if its value is set to the
            # default value. If we don't do this, it will show up as a difference when it isn't.
            if deployed_config.parameters[parameter_key] == default_value:
                del deployed_config.parameters[parameter_key]

    def _get_parameter_default_map(self, template_summary: dict) -> Dict[str, str]:
        if template_summary is None:
            return {}

        parameters = template_summary["Parameters"]
        default_map = {}

        for parameter in parameters:
            key = parameter["ParameterKey"]
            value = self._handle_default_value(parameter)
            if value is not None:
                default_map[key] = value

        return default_map

    def _handle_default_value(self, parameter):
        default_value = parameter.get("DefaultValue")
        param_type = parameter["ParameterType"]

        if default_value is None:
            return None

        if parameter.get("NoEcho"):
            default_value = "****"
        elif "List" in param_type:
            # Eliminate whitespace around commas
            default_value = ",".join(
                value.strip() for value in default_value.split(",")
            )

        return default_value

    def _mask_no_echo_parameters(
        self, template_summary: dict, generated_config: StackConfiguration
    ):
        parameters = template_summary["Parameters"]

        for parameter in parameters:
            key = parameter["ParameterKey"]
            if parameter.get("NoEcho") and key in generated_config.parameters:
                generated_config.parameters[key] = self.NO_ECHO_REPLACEMENT

    def _generate_template(self, stack_actions: StackActions) -> str:
        return stack_actions.dump_template()

    def _get_deployed_template(
        self, stack_actions: StackActions, is_deployed: bool
    ) -> str:
        if is_deployed:
            return stack_actions.fetch_remote_template() or "{}"
        else:
            return "{}"

    @abstractmethod
    def compare_templates(self, deployed: str, generated: str) -> DiffType:
        """Implement this method to return the diff for the templates

        :param deployed: The stack template as it has been deployed
        :param generated: The stack template as it exists locally within Sceptre
        :return: The generated diff between the two
        """

    @abstractmethod
    def compare_stack_configurations(
        self, deployed: Optional[StackConfiguration], generated: StackConfiguration
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
        show_no_echo=False,
        *,
        universal_template_loader: Callable[[str], Tuple[dict, str]] = cfn_flip.load,
    ):
        """Initializes a DeepDiffStackDiffer.

        :param show_no_echo: If True, local parameters passed that the template says are NoEcho
            parameters will be displayed; Otherwise, they will be masked in the diff.
        :param universal_template_loader: This should be a callable that can load either a json or
            yaml string and return a tuple where the first element is the loaded template and the
            second element is the template format (either "json" or "yaml")
        """
        super().__init__(show_no_echo)
        self.load_template = universal_template_loader

    def compare_stack_configurations(
        self,
        deployed: Optional[StackConfiguration],
        generated: StackConfiguration,
    ) -> deepdiff.DeepDiff:
        return deepdiff.DeepDiff(
            deployed,
            generated,
            verbose_level=self.VERBOSITY_LEVEL_TO_INDICATE_CHANGED_VALUES,
        )

    def compare_templates(self, deployed: str, generated: str) -> deepdiff.DeepDiff:
        # We don't actually care about the original formats here, since we only care about the
        # template VALUES.
        deployed_dict, _ = self.load_template(deployed)
        generated_dict, _ = self.load_template(generated)

        return deepdiff.DeepDiff(
            deployed_dict,
            generated_dict,
            verbose_level=self.VERBOSITY_LEVEL_TO_INDICATE_CHANGED_VALUES,
        )


class DifflibStackDiffer(StackDiffer[List[str]]):
    """A StackDiffer that uses difflib to produce a diff between the stack as it exists on AWS and
    the stack as it exists locally within Sceptre.

    Because difflib generates diffs off of lists of strings, both StackConfigurations and
    """

    def __init__(
        self,
        show_no_echo=False,
        *,
        universal_template_loader: Callable[[str], Tuple[dict, str]] = cfn_flip.load,
    ):
        """Initializes a DifflibStackDiffer.

        :param show_no_echo: If True, local parameters passed that the template says are NoEcho
            parameters will be displayed; Otherwise, they will be masked in the diff.
        :param universal_template_loader: This should be a callable that can load either a json or
            yaml string and return a tuple where the first element is the loaded template and the
            second element is the template format (either "json" or "yaml")
        """
        super().__init__(show_no_echo)
        self.load_template = universal_template_loader

    def compare_stack_configurations(
        self,
        deployed: Optional[StackConfiguration],
        generated: StackConfiguration,
    ) -> List[str]:
        if deployed is None:
            comparable_deployed = None
        else:
            comparable_deployed = self._make_stack_configuration_comparable(deployed)

        comparable_generated = self._make_stack_configuration_comparable(generated)
        deployed_string = cfn_flip.dump_yaml(comparable_deployed)
        generated_string = cfn_flip.dump_yaml(comparable_generated)
        return self._make_string_diff(deployed_string, generated_string)

    def _make_stack_configuration_comparable(
        self, config: Optional[StackConfiguration]
    ):
        as_dict = dict(config._asdict())
        return {
            key: value
            for key, value in as_dict.items()
            # stack_name isn't always going to be the same, otherwise we wouldn't be comparing them.
            # It's more confusing to have it in the diff output than to just remove it.
            if value not in (None, [], {}) and key != "stack_name"
        }

    def compare_templates(
        self,
        deployed: str,
        generated: str,
    ) -> List[str]:
        # Sometimes there might only be simple whitespace differences... which difflib will show but
        # are actually insignificant and "false positives". Also, it's POSSIBLE that the template
        # format might have changed, even if all the VALUES have stayed the same, so we'll read both
        # templates into dicts (regardless of their format) and we'll output both to the format of
        # the local template using identical serialization settings. This will truly enable comparison
        # of the actual values rather than other things that don't actually make a difference to
        # CloudFormation. If only the format/meaningless whitespace has changed, this will result in
        # there being no diff.
        deployed_dict, _ = self.load_template(deployed)
        generated_dict, generated_format = self.load_template(generated)
        dumpers = {"json": cfn_flip.dump_json, "yaml": cfn_flip.dump_yaml}
        deployed_reformatted = dumpers[generated_format](deployed_dict)
        generated_reformatted = dumpers[generated_format](generated_dict)

        return self._make_string_diff(deployed_reformatted, generated_reformatted)

    def _make_string_diff(self, deployed: str, generated: str) -> List[str]:
        diff_lines = difflib.unified_diff(
            deployed.splitlines(),
            generated.splitlines(),
            fromfile="deployed",
            tofile="generated",
            lineterm="",
        )
        return list(diff_lines)
