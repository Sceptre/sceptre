from behave import *
import subprocess
import boto3
import os


@when("we run lock stack")
def step_impl(context):
    subprocess.call([
        "sceptre", "lock-stack", "test-env/a", "wait-condition-handle"
    ])


@then("the stack is locked")
def step_impl(context):
    client = boto3.client("cloudformation")
    response = client.get_stack_policy(
        StackName="{0}-{1}-wait-condition-handle".format(
            context.project_code, context.environment_path_a
        )
    )
    lock_policy_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__)
        ))),
        "sceptre",
        "stack_policies",
        "lock.json"
    )
    assert response["StackPolicyBody"] == open(lock_policy_path, "r").read()


@when("we run unlock stack")
def step_impl(context):
    subprocess.call([
        "sceptre", "unlock-stack", "test-env/a", "wait-condition-handle"
    ])


@then("the stack is unlocked")
def step_impl(context):
    client = boto3.client("cloudformation")
    response = client.get_stack_policy(
        StackName="{0}-{1}-wait-condition-handle".format(
            context.project_code, context.environment_path_a
        )
    )
    unlock_policy_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__)
        ))),
        "sceptre",
        "stack_policies",
        "unlock.json"
    )
    assert response["StackPolicyBody"] == open(unlock_policy_path, "r").read()
