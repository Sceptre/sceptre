import os
import time
import uuid
import yaml
import boto3


def before_all(context):
    context.uuid = uuid.uuid1().hex
    context.project_code = "sceptre-integration-tests-{0}".format(
        context.uuid
    )
    context.bucket_name = "sceptre-integration-tests-templates"

    if not os.environ.get("CIRCLECI"):
        context.bucket_name = context.bucket_name + "-" + str(context.uuid)

    context.sceptre_dir = os.path.join(
        os.getcwd(), "integration-tests", "sceptre-project"
    )
    update_config(context)
    context.cloudformation = boto3.resource('cloudformation')
    context.client = boto3.client("cloudformation")


def before_scenario(context, scenario):
    context.error = None
    context.response = None
    context.output = None


def update_config(context):
    config_path = os.path.join(
        context.sceptre_dir, "config", "config.yaml"
    )
    with open(config_path) as config_file:
        env_config = yaml.safe_load(config_file)

    env_config["template_bucket_name"] = context.bucket_name
    env_config["project_code"] = context.project_code

    with open(config_path, 'w') as config_file:
        yaml.safe_dump(env_config, config_file, default_flow_style=False)


def after_all(context):
    response = context.client.describe_stacks()
    for stack in response["Stacks"]:
        time.sleep(2)
        if stack["StackName"].startswith(context.project_code):
            context.client.delete_stack(
                StackName=stack["StackName"]
            )
    context.project_code = "sceptre-integration-tests"
    context.bucket_name = "sceptre-integration-tests-templates"
    update_config(context)
