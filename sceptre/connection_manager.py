# -*- coding: utf-8 -*-

"""
sceptre.connection_manager

This module implements a ConnectionManager class, which simplifies and manages
Boto3 calls.
"""

import functools
import logging
import random
import threading
import time
import boto3

from os import environ
from botocore.exceptions import ClientError

from sceptre.helpers import mask_key
from sceptre.exceptions import InvalidAWSCredentialsError, RetryLimitExceededError


def _retry_boto_call(func):
    """
    Retries a Boto3 call up to 30 times if request rate limits are hit.

    Between each try we wait a random amount with a max of that time being 45 seconds.
    Specifically we are picking number between a ceiling (delay_cap) of 45 seconds and the last
    delay multiplied by 2.5, rounding to two decimal places.  You can read more
    here: https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/
    If rate limits are hit 30 times, _retry_boto_call raises a
    sceptre.exceptions.RetryLimitExceededException.

    :param func: A function that uses boto calls
    :type func: function
    :returns: The decorated function.
    :rtype: function
    :raises: sceptre.exceptions.RetryLimitExceededException
    """
    logger = logging.getLogger(__name__)

    @functools.wraps(func)
    def decorated(*args, **kwargs):
        max_retries = 30
        attempts = 1
        mdelay = 1
        delay_cap = 45
        while attempts < max_retries:
            try:
                return func(*args, **kwargs)
            except ClientError as e:
                if e.response["Error"]["Code"] == "Throttling":
                    logger.error("Request limit exceeded, pausing {}...".format(mdelay))
                    time.sleep(mdelay)

                    # Using De-correlated Jitter Algorithm
                    # We are picking number between a ceiling (delay_cap) of 45 seconds and the
                    # last delay multiplied by 2.5, rounding to two decimal places.
                    mdelay = min(delay_cap, round((random.uniform(1, mdelay * 2.5)), 2))

                    attempts += 1
                else:
                    raise
        raise RetryLimitExceededError(
            "Exceeded request limit {0} times. Aborting.".format(
                max_retries
            )
        )

    return decorated


class ConnectionManager(object):
    """
    The Connection Manager is used to create boto3 clients for
    the various AWS services that Sceptre needs to interact with.

    :param profile: The AWS credentials profile that should be used.
    :type profile: str
    :param iam_role: The iam_role that should be assumed in the account.
    :type iam_role: str
    :param stack_name: The CloudFormation stack name for this connection.
    :type stack_name: str
    :param region: The region to use.
    :type region: str
    """

    _session_lock = threading.Lock()
    _client_lock = threading.Lock()
    _boto_sessions = {}
    _clients = {}
    _stack_keys = {}

    def __init__(self, region, profile=None, stack_name=None, iam_role=None):
        self.logger = logging.getLogger(__name__)

        self.region = region
        self.profile = profile
        self.stack_name = stack_name
        self.iam_role = iam_role

        if stack_name:
            self._stack_keys[stack_name] = (region, profile, iam_role)

    def __repr__(self):
        return (
            "sceptre.connection_manager.ConnectionManager(region='{0}', "
            "profile='{1}', stack_name='{2}', iam_role='{3}')".format(
                self.region, self.profile, self.stack_name, self.iam_role
            )
        )

    def _get_session(self, profile, region, iam_role):
        """
        Returns a boto session in the target account.

        If a ``profile`` is specified in ConnectionManager's initialiser,
        then the profile is used to generate temporary credentials to create
        the Boto session. If ``profile`` is not specified then the default
        profile is assumed to create the boto session.

        :returns: The Boto3 session.
        :rtype: boto3.session.Session
        :raises: botocore.exceptions.ClientError
        """
        with self._session_lock:
            self.logger.debug("Getting Boto3 session")
            key = (region, profile, iam_role)

            if self._boto_sessions.get(key) is None:
                self.logger.debug("No Boto3 session found, creating one...")
                self.logger.debug("Using cli credentials...")

                # Credentials from env take priority over profile
                config = {
                    "profile_name": profile,
                    "region_name": region,
                    "aws_access_key_id": environ.get("AWS_ACCESS_KEY_ID"),
                    "aws_secret_access_key": environ.get("AWS_SECRET_ACCESS_KEY"),
                    "aws_session_token": environ.get("AWS_SESSION_TOKEN")
                }

                session = boto3.session.Session(**config)
                self._boto_sessions[key] = session

                if session.get_credentials() is None:
                    raise InvalidAWSCredentialsError(
                        "Session credentials were not found. Profile: {0}. Region: {1}.".format(
                            config["profile_name"], config["region_name"]
                        )
                    )

                if iam_role:
                    sts_client = session.client("sts")
                    sts_response = sts_client.assume_role(
                        RoleArn=iam_role,
                        RoleSessionName="{0}-session".format(
                            iam_role.split("/")[-1]
                        )
                    )

                    credentials = sts_response["Credentials"]
                    session = boto3.session.Session(
                        aws_access_key_id=credentials["AccessKeyId"],
                        aws_secret_access_key=credentials["SecretAccessKey"],
                        aws_session_token=credentials["SessionToken"],
                        region_name=region
                    )

                    if session.get_credentials() is None:
                        raise InvalidAWSCredentialsError(
                            "Session credentials were not found. Role: {0}. Region: {1}.".format(
                                iam_role, region
                            )
                        )

                    self._boto_sessions[key] = session

                self.logger.debug(
                    "Using credential set from %s: %s",
                    session.get_credentials().method,
                    {
                        "AccessKeyId": mask_key(
                            session.get_credentials().access_key
                        ),
                        "SecretAccessKey": mask_key(
                            session.get_credentials().secret_key
                        ),
                        "Region": session.region_name
                    }
                )

                self.logger.debug("Boto3 session created")

            return self._boto_sessions[key]

    def _get_client(self, service, region, profile, stack_name, iam_role):
        """
        Returns the Boto3 client associated with <service>.

        Equivalent to calling Boto3.client(<service>). Gets the client using
        ``boto_session``.

        :param service: The Boto3 service to return a client for.
        :type service: str
        :returns: The Boto3 client.
        :rtype: boto3.client.Client
        """
        with self._client_lock:
            key = (service, region, profile, stack_name, iam_role)
            if self._clients.get(key) is None:
                self.logger.debug(
                    "No %s client found, creating one...", service
                )
                self._clients[key] = self._get_session(
                    profile, region, iam_role
                ).client(service)

            return self._clients[key]

    @_retry_boto_call
    def call(
        self, service, command, kwargs=None, profile=None, region=None,
        stack_name=None, iam_role=None
    ):
        """
        Makes a thread-safe Boto3 client call.

        Equivalent to ``boto3.client(<service>).<command>(**kwargs)``.

        :param service: The Boto3 service to return a client for.
        :type service: str
        :param command: The Boto3 command to call.
        :type command: str
        :param kwargs: The keyword arguments to supply to <command>.
        :type kwargs: dict
        :returns: The response from the Boto3 call.
        :rtype: dict
        """
        if region is None and profile is None and iam_role is None:
            if stack_name and stack_name in self._stack_keys:
                region, profile, iam_role = self._stack_keys[stack_name]
            else:
                region = self.region
                profile = self.profile
                iam_role = self.iam_role

        if kwargs is None:  # pragma: no cover
            kwargs = {}

        client = self._get_client(service, region, profile, stack_name, iam_role)
        return getattr(client, command)(**kwargs)
