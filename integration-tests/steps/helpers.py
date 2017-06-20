import os
import time

from behave import *
import boto3


@then('the user is told {message}')
def step_impl(context, message):
    if message == "stack does not exist":
        assert context.error.endswith("does not exist")
