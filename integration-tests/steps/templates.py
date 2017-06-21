from behave import *
import json
from botocore.exceptions import ClientError, WaiterError
from sceptre.environment import Environment


@when('the user validates the template for stack "{stack_name}"')
def step_impl(context, stack_name):
    env = Environment(context.sceptre_dir, context.default_environment)
    try:
        context.response = env.stacks[stack_name].validate_template()
        print(str(context.response))
    except ClientError as e:
        context.error = e.response['Error']['Message']
        print(str(context.error))
