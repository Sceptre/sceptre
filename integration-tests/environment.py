import os
import time
import uuid
import yaml

import boto3

def before_all(context):
    context.cloudformation = boto3.resource('cloudformation')
    context.client = boto3.client("cloudformation")
    context.sceptre_dir = os.path.join(
        os.getcwd(), "integration-tests", "sceptre-project"
    )
    context.default_environment = "default"


def before_scenario(context, scenario):
    context.error = None
    context.response = None
