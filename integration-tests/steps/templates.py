from behave import *
import os
import imp
import yaml
from sceptre.environment import Environment


@given('the template for stack "{stack_name}" is {template_name}')
def step_impl(context, stack_name, template_name):
    config_path = os.path.join(
        context.sceptre_dir, "config",
        context.default_environment, stack_name + ".yaml"
    )
    template_path = os.path.join("templates", template_name)
    with open(config_path) as config_file:
        stack_config = yaml.safe_load(config_file)

    stack_config["template_path"] = template_path

    with open(config_path, 'w') as config_file:
        yaml.safe_dump(stack_config, config_file, default_flow_style=False)


@when('the user validates the template for stack "{stack_name}"')
def step_impl(context, stack_name):
    env = Environment(context.sceptre_dir, context.default_environment)
    try:
        context.response = env.stacks[stack_name].validate_template()
    except ClientError as e:
        context.error = e.response['Error']['Message']


@when('the user generates the template for stack {stack_name}')
def step_impl(context, stack_name):
    env = Environment(context.sceptre_dir, context.default_environment)
    try:
        context.output = env.stacks[stack_name].template.body
    except Exception as e:
        context.error = e


@then('the output is the same as the contents of {filename} template')
def step_impl(context, filename):
    filepath = os.path.join(
        context.sceptre_dir, "templates", filename
    )
    with open(filepath) as template:
        body = template.read()

    assert body == context.output


@then('the output is the same as the string returned by {filename}')
def step_impl(context, filename):
    filepath = os.path.join(
        context.sceptre_dir, "templates", filename
    )

    module = imp.load_source("template", filepath)
    body = module.sceptre_handler({})
    assert body == context.output
