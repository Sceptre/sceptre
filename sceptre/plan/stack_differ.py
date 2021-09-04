import botocore
from botocore.exceptions import ClientError
from cfn_tools import dump_json
from deepdiff import DeepDiff
import cfn_flip

from sceptre.connection_manager import ConnectionManager
from sceptre.exceptions import StackDoesNotExistError
from sceptre.resolvers import Resolver
from sceptre.stack import Stack
from typing import NamedTuple, Dict, List, Optional


class StackDiff(NamedTuple):
    stack_name: str
    template_diff: DeepDiff
    config_diff: DeepDiff


class StackConfiguration(NamedTuple):
    parameters: Dict[str, str]
    tags: Dict[str, str]
    name: str
    notification_arns: List[str]


class StackDiffer:
    def __init__(self, stack: Stack, connection_manager: ConnectionManager):
        self.stack = stack
        self.connection_manager = connection_manager

    @property
    def template(self):
        return self.stack.template.body

    @property
    def external_name(self):
        return self.stack.external_name

    @property
    def tags(self):
        return self.stack.tags

    @property
    def notifications(self):
        return self.stack.notifications

    def diff(self) -> StackDiff:
        generated_config = self._create_generated_config()
        deployed_config = self._create_deployed_stack_config()
        deployed_stack_template = self._get_deployed_template()

        template_diff = self._compare_templates(deployed_stack_template)
        config_diff = self._compare_configs(generated_config, deployed_config)

        return StackDiff(self.external_name, template_diff, config_diff)

    def _create_generated_config(self):
        parameters = self._extract_parameters_dict()
        stack_configuration = StackConfiguration(
            parameters=parameters,
            tags=self.tags,
            name=self.external_name,
            notification_arns=self.notifications
        )

        return stack_configuration

    def _extract_parameters_dict(self):
        parameters = {}
        # parameters is a ResolvableProperty, but the underlying, pre-resolved parameters are
        # stored in _parameters. We might not actually be able to resolve values, such as in the
        # case where it attempts to get a value from a stack that doesn't exist yet. Therefore, this
        # Resolves the values individually, where they CAN be resolved, and otherwise makes an
        # alternative placeholder value
        for key, value in self.stack._parameters.items():
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
                    value_to_use = f'!{type(value).__name__}: {value.argument}'
            else:
                value_to_use = value
            parameters[key] = value_to_use

        return parameters

    def _create_deployed_stack_config(self) -> Optional[StackConfiguration]:
        try:
            description = self.connection_manager.call(
                service="cloudformation",
                command="describe_stacks",
                kwargs={"StackName": self.stack.external_name}
            )
        except botocore.exceptions.ClientError as e:
            if e.response["Error"]["Message"].endswith("does not exist"):
                return
            raise

        return self._map_stack_description_to_stack_configuration(
            description
        )

    def _get_deployed_template(self) -> str:
        try:
            template = self.connection_manager.call(
                service='cloudformation',
                command='get_template',
                kwargs={'StackName': self.external_name, 'TemplateStage': 'Original'}
            )
            template_body = template['TemplateBody']
            # Sometimes boto return a string, sometimes a dictionary
            if not isinstance(template_body, str):
                template_body = dump_json(template_body)
            return template_body
        except ClientError as ex:
            if ex.response['Error']['Code'] == 'ValidationError':
                # Template doesn't exist
                return '{}'
            raise

    def _map_stack_description_to_stack_configuration(self, description):
        stacks = description['Stacks']
        for stack in stacks:
            return StackConfiguration(
                parameters={
                    param['ParameterKey']: param['ParameterValue']
                    for param in stack.get('Parameters', [])
                },
                tags={
                    tag['Key']: tag['Value']
                    for tag in stack['Tags']
                },
                name=stack['StackName'],
                notification_arns=stack['NotificationARNs']
            )

    def _compare_templates(self, deployed_template: str) -> DeepDiff:
        """Compares the generated templates to the deployed templates using DeepDiff.

        Returns:
            A dictionary where the keys are the stack names and the values are DeepDiff objects
        """
        generated_dict, _ = cfn_flip.load(self.template)
        deployed_dict, _ = cfn_flip.load(deployed_template)
        return DeepDiff(
            deployed_dict,
            generated_dict,
            verbose_level=2
        )

    def _compare_configs(self,
        generated_config: StackConfiguration,
        deployed_config: StackConfiguration
    ):
        return DeepDiff(
            deployed_config,
            generated_config,
            verbose_level=2
        )
