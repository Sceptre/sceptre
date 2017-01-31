from behave import *
import subprocess
import boto3
import os
import time


@given("a stack update has failed into update rollback failed")
def step_impl(context):
    client = boto3.client("cloudformation")

    template_folder = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "templates"
    )

    vpc_stack_name = "{0}-{1}-vpc".format(
        context.project_code, context.environment_path_a
    )
    sg_stack_name = "{0}-{1}-security-group".format(
        context.project_code, context.environment_path_a
    )

    vpc_description = client.describe_stacks(StackName=vpc_stack_name)
    sg_description = client.describe_stacks(StackName=sg_stack_name)

    vpc_id = [
        output["OutputValue"]
        for output in vpc_description["Stacks"][0]["Outputs"]
        if output["OutputKey"] == "VpcId"
    ][0]
    sg_id = [
        output["OutputValue"]
        for output in sg_description["Stacks"][0]["Outputs"]
        if output["OutputKey"] == "SecurityGroupId"
    ][0]

    ec2_client = boto3.resource("ec2")

    # Stack updates fail if the update adds a rule to a security group which
    # pushes the total number of rules over 50.
    # Remove the original rule, so an update stack creates a new rule, rather
    # than updating this one in place.
    ec2_client.SecurityGroup(sg_id).revoke_ingress(
        IpProtocol="tcp",
        FromPort=80,
        ToPort=80,
        CidrIp="0.0.0.0/0"
    )

    # Add 50 new rules.
    for i in range(50):
        ec2_client.SecurityGroup(sg_id).authorize_ingress(
          IpProtocol="tcp",
          FromPort=80,
          ToPort=80,
          CidrIp="10.0.%i.0/24" % i
        )

    with open(os.path.join(template_folder, "security_group.json"), "r") as f:
        sg_template = f.read()

    client.update_stack(
        StackName=sg_stack_name,
        TemplateBody=sg_template,
        Parameters=[
            {
                "ParameterKey": "WhitelistIpParam",
                "ParameterValue": "10.0.50.0/24",
            },
            {
                "ParameterKey": "VpcId",
                "ParameterValue": vpc_id,
            }
        ]
    )

    def is_sg_stack_status_update_rollback_failed():
        response = client.describe_stacks(StackName=sg_stack_name)
        return response["Stacks"][0]["StackStatus"] == "UPDATE_ROLLBACK_FAILED"

    i = 0
    while not is_sg_stack_status_update_rollback_failed():
        print("waiting for update rollback to fail... {0}".format(
            str(i * 5)
        ))
        time.sleep(5)
        i += 1


@when("we continue update rollback")
def step_impl(context):
    subprocess.call(
        [
            "sceptre",
            "continue-update-rollback",
            "test-env/a",
            "security-group"
        ]
    )


@then("the stack changes status")
def step_impl(context):
    client = boto3.client("cloudformation")
    sg_stack_name = "{0}-{1}-security-group".format(
        context.project_code, context.environment_path_a
    )
    time.sleep(10)

    def is_sg_stack_status_update_rollback_failed():
        response = client.describe_stacks(StackName=sg_stack_name)
        return response["Stacks"][0]["StackStatus"] == "UPDATE_ROLLBACK_FAILED"

    i = 0
    while is_sg_stack_status_update_rollback_failed():
        print("waiting for stack status to change... {0}".format(
            str(i * 5)
        ))
        time.sleep(5)
        i += 1

    j = 0
    while not is_sg_stack_status_update_rollback_failed():
        print("waiting for status to revert to rollback failed... {0}".format(
            str(j * 5)
        ))
        time.sleep(5)
        j += 1
