import os
import time
import uuid
import yaml

import boto3


def before_all(context):
    """
    before_all is an Behave environmental control. This function is run before
    the integration tests start. It appends a UUID to the project_code that
    is used by Sceptre when creating resources. This ensures that the
    integration tests can be run in parallel without stack name clashes.
    """
    build_uuid = uuid.uuid1().hex
    context.sceptre_dir = os.path.dirname(__file__)
    context.environment_path_a = "test-env-a"
    context.environment_path_b = "test-env-b"
    context.project_code = "sceptre-integration-tests-{0}".format(
        build_uuid
    )
    print("The UUID for this build is '{0}'.".format(build_uuid))

    config_file = os.path.abspath(os.path.join(
        os.path.dirname(__file__),
        "config",
        "config.yaml"
    ))

    with open(config_file, "r") as f:
        config = yaml.load(f)
    config["project_code"] = context.project_code
    with open(config_file, "w") as f:
        yaml.dump(config, f, default_flow_style=False)


def after_all(context):
    """
    after_all is an Behave environmental control. This function is run after
    the integration tests end. It changes the project code stored at
    `sceptre/integration-tests/config.yaml` is returned to its
    non-UUID-appended value.
    """
    config_file = os.path.abspath(os.path.join(
        os.path.dirname(__file__),
        "config",
        "config.yaml"
    ))
    with open(config_file, "r+") as f:
        config = yaml.load(f)
    config["project_code"] = "sceptre-integration-tests"
    with open(config_file, "w") as f:
        yaml.dump(config, f, default_flow_style=False)


def before_feature(context, feature):
    """
    Delete any stacks remaining from the previous feature.
    """
    delete_all_integration_test_stacks(context.project_code)


def after_feature(context, feature):
    """
    Delete any stacks remaining after a feature.
    """
    delete_all_integration_test_stacks(context.project_code)


def after_scenario(context, scenario):
    """
    Perform additional cleanup after certain scenarios.
    """
    clean_vpc_scenario_names = [
        "check sceptre updates a stack",
        "check sceptre creates change set"
    ]
    if scenario.name in clean_vpc_scenario_names:
        clean_vpc_yaml()


def delete_all_integration_test_stacks(project_code):
    """
    Deletes all stacks whose names contain `project_code`. Waits for the stack
    deletes to complete.
    """
    client = boto3.client("cloudformation")

    def get_integration_tests_stack_names():
        """
        returns a list of stack names of currently running stacks whose names
        contain "integration-tests"
        """
        response = client.describe_stacks()
        integraion_test_stacks = [
            stack["StackName"] for stack in response["Stacks"]
            if project_code in stack["StackName"]
        ]
        return integraion_test_stacks

    i = 0
    existing_stack_names = get_integration_tests_stack_names()

    while existing_stack_names:
        for stack in existing_stack_names:
            client.delete_stack(StackName=stack)
        print(
            "waiting for stack to be deleted... {0}s "
            "elapsed".format(str(i * 5))
        )
        existing_stack_names = get_integration_tests_stack_names()
        time.sleep(5)
        i += 1


def clean_vpc_yaml():
    """
    Certain scenarios require a stack update. This is done by changing a value
    in the vpc stack's config file. clean_vpc_yaml returns the value to its
    default value.
    """
    vpc_config_file = os.path.abspath(os.path.join(
        os.path.dirname(__file__),
        "config",
        "test-env",
        "a",
        "vpc.yaml"
    ))
    with open(vpc_config_file, "r+") as f:
        config = f.read()
    config = config.replace("updated_vpc.py", "vpc.py")
    with open(vpc_config_file, "w") as f:
        f.write(config)
