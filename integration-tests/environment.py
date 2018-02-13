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

    sts = boto3.client("sts")
    account_number = sts.get_caller_identity()['Account']
    context.bucket_name = "sceptre-integration-tests-templates-{}".format(
        account_number
    )

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


def get_integration_test_bucket_name():
    bucket_prefix = "sceptre-integration-tests-templates"

    if os.environ.get("CIRCLECI"):
        return bucket_prefix

    s3 = boto3.client('s3')

    existing_buckets = [
        bucket['Name'] for bucket in s3.list_buckets()['Buckets']
        if bucket['Name'].startswith(bucket_prefix)
    ]

    if existing_buckets:
        return existing_buckets[0]

    iam = boto3.client("iam")
    account_aliases = iam.list_account_aliases()['AccountAliases']
    if account_aliases:
        account_alias = account_aliases[0]
        return '{}-{}'.format(
            bucket_prefix[:62 - len(account_alias)],
            account_alias
        )

    sts = boto3.client("sts")
    account_number = sts.get_caller_identity()['Account']
    return '{}-{}'.format(bucket_prefix, account_number)
