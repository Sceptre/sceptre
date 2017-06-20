from behave import *
import json
import time
import os
import boto3
from botocore.exceptions import ClientError, WaiterError
from sceptre.environment import Environment


@given('the policy for stack "{stack_name}" is {state}')
def step_impl(context, stack_name, state):
    full_name = "-".join(
        ["sceptre-integration-tests", context.default_environment, stack_name]
    )
    context.client.set_stack_policy(
        StackName=full_name,
        StackPolicyBody=generate_stack_policy(state)
    )


@when('the user unlocks stack "{stack_name}"')
def step_impl(context, stack_name):
    env = Environment(context.sceptre_dir, context.default_environment)
    try:
        env.stacks[stack_name].unlock()
    except ClientError as e:
        context.error = e.response['Error']['Message']
    else:
        raise e


@when('the user locks stack "{stack_name}"')
def step_impl(context, stack_name):
    env = Environment(context.sceptre_dir, context.default_environment)
    try:
        env.stacks[stack_name].lock()
    except ClientError as e:
        context.error = e.response['Error']['Message']
    else:
        raise e


@then('the policy for stack "{stack_name}" is {state}')
def step_impl(context, stack_name, state):
    full_name = "-".join(
        ["sceptre-integration-tests", context.default_environment, stack_name]
    )
    policy = get_stack_policy(context, full_name)
    print(policy)

    if state == 'not set':
        assert (policy is None)


def get_stack_policy(context, stack_name):
    try:
        response = context.client.get_stack_policy(
            StackName=stack_name
        )
    except ClientError as e:
        if e.response['Error']['Code'] == 'ValidationError' \
          and e.response['Error']['Message'].endswith("does not exist"):
            return None
        else:
            raise e
    return response.get("StackPolicyBody")


def generate_stack_policy(policy_type):
    data = ''
    if policy_type == 'allow all':
        data = {
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": "Update:*",
                    "Principal": "*",
                    "Resource": "*"
                }
             ]
        }
    elif policy_type == 'deny all':
        data = {
            "Statement": [
                {
                    "Effect": "Deny",
                    "Action": "Update:*",
                    "Principal": "*",
                    "Resource": "*"
                }
             ]
        }

    return json.dumps(data, sort_keys=True, indent=4, separators=(',', ': '))
