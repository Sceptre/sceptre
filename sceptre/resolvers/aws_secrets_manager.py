# -*- coding: utf-8 -*-

import boto3
import json

from botocore.exceptions import ClientError
from sceptre.resolvers import Resolver


class AwsSecretsManager(Resolver):
    """
    Resolves an AWS Secret Mananger secret's value and even a JSON key subset of that value.

    :param secret_id: The Amazon Resource Name (ARN) or name of the secret.
    :type secret_id: str
    :param secret_string: The secret's string type. Either SecretBinary or SecretString.
    :type secret_string: str
    :param secret_value_key: The JSON key name of the secret's value to get.
    :type secret_value_key: str
    :returns: Secret value.
    :rtype: str
    """

    def __init__(self, *args, **kwargs):
        super(AwsSecretsManager, self).__init__(*args, **kwargs)

    def resolve(self):
        """
        Retrieves the contents of the encrypted fields SecretString or SecretBinary from the
        specified version of a secret, whichever contains content.
        Requires IAM permissions:
        * secretsmanager:GetSecretValue
        * kms:Decrypt - required only if you use a customer-managed AWS KMS key to encrypt the
          secret. You do not need this permission to use the account's default AWS managed CMK
          for Secrets Manager.

        :returns: Value of the secret.
        :rtype: str
        """
        secret_id, secret_string, secret_value_key = (self.argument.split("::") + [None] * 3)[:3]
        client = boto3.client('secretsmanager')
        try:
            secret_value_response = client.get_secret_value(
                SecretId=secret_id
            )
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                print("The requested secret " + secret_id + " was not found")
            elif e.response['Error']['Code'] == 'InvalidRequestException':
                print("The request was invalid due to:", e)
            elif e.response['Error']['Code'] == 'InvalidParameterException':
                print("The request had invalid params:", e)
        else:
            secret_value_json = json.loads(secret_value_response[secret_string])
            secret_value = (secret_value_json[secret_value_key] if secret_value_key
                            else secret_value_json)
            return secret_value
