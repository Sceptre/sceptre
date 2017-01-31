import os
import time

from behave import *
import boto3


@given("a stack exists")
def step_impl(context):
    """
    Create a stack containing a wait condition handle resource.
    """
    template_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "templates",
        "wait_condition_handle.json"
    )
    stack_name = "{0}-{1}-wait-condition-handle".format(
        context.project_code, context.environment_path_a
    )
    create_stack(template_path, stack_name)


@given("a vpc stack exists")
def step_impl(context):
    """
    Create a stack containing a VPC resource.
    """
    template_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "templates",
        "vpc.json"
    )
    stack_name = "{0}-{1}-vpc".format(
        context.project_code, context.environment_path_a
    )
    create_stack(template_path, stack_name)


@given("multiple stacks exist")
def step_impl(context):
    """
    Create stacks containing a VPC and a Security Group respectively.
    """
    vpc_template_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "templates",
        "vpc.json"
    )
    vpc_stack_name = "{0}-{1}-vpc".format(
        context.project_code, context.environment_path_a
    )
    response = create_stack(vpc_template_path, vpc_stack_name)

    vpc_id = [
        output["OutputValue"] for output in response["Stacks"][0]["Outputs"]
        if output["OutputKey"] == "VpcId"
    ][0]

    sg_template_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "templates",
        "security_group.json"
    )
    sg_a_stack_name = "{0}-{1}-security-group".format(
        context.project_code, context.environment_path_a
    )
    sg_parameters = [
        {
            "ParameterKey": "VpcId",
            "ParameterValue": vpc_id,
        },
        {
            "ParameterKey": "WhitelistIpParam",
            "ParameterValue": "0.0.0.0/0",
        }
    ]
    create_stack(sg_template_path, sg_a_stack_name, sg_parameters)

    sg_b_stack_name = "{0}-{1}-security-group".format(
        context.project_code, context.environment_path_b
    )
    create_stack(sg_template_path, sg_b_stack_name, sg_parameters)


@given("stacks capable of getting to update rollback failed exist")
def step_impl(context):
    """
    Create stacks capable of getting to the update rollback failed status.
    Currently, this consists of a VPC and a Security Group.
    """
    vpc_template_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "templates",
        "vpc.json"
    )
    vpc_stack_name = "{0}-{1}-vpc".format(
        context.project_code, context.environment_path_a
    )
    response = create_stack(vpc_template_path, vpc_stack_name)

    vpc_id = [
        output["OutputValue"] for output in response["Stacks"][0]["Outputs"]
        if output["OutputKey"] == "VpcId"
    ][0]

    sg_template_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "templates",
        "security_group.json"
    )
    sg_stack_name = "{0}-{1}-security-group".format(
        context.project_code, context.environment_path_a
    )
    sg_parameters = [
        {
            "ParameterKey": "VpcId",
            "ParameterValue": vpc_id,
        },
        {
            "ParameterKey": "WhitelistIpParam",
            "ParameterValue": "0.0.0.0/0",
        }
    ]
    create_stack(sg_template_path, sg_stack_name, sg_parameters)


def create_stack(template_path, stack_name, parameters=[]):
    """
    Run boto3.client("cloudformation").create_stack().

    :param template_path: The path to the CloudFormation template to create \
    the stack with.
    :type template_path: string
    :param stack_name: The name to give the stack.
    :type stack_name: string
    :param parameters: A list of parameters to supply to the stack.
    :type parameters: list
    :returns: dict
    """
    client = boto3.client("cloudformation")
    with open(template_path, "r") as f:
        template = f.read()

    client.create_stack(
        StackName=stack_name,
        TemplateBody=template,
        Parameters=parameters
    )
    wait_for_stack_create(stack_name)

    response = client.describe_stacks(StackName=stack_name)
    return response


def wait_for_stack_create(stack_name):
    """
    Wait for the stack with name <stack_name> change its status to
    CREATE_COMPLETE.

    :param stack_name: The name of the stack to wait for.
    :type stack_name: string
    """
    client = boto3.client("cloudformation")

    def is_stack_creating():
        response = client.describe_stacks(StackName=stack_name)
        return response["Stacks"][0]["StackStatus"] != "CREATE_COMPLETE"

    i = 0
    while is_stack_creating():
        print("waiting for stack to be created... {0}s elapsed".format(
            str(i * 5)
        ))
        time.sleep(5)
        i += 1
