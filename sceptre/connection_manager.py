# -*- coding: utf-8 -*-

"""
sceptre.connection_manager

This module implements a ConnectionManager class, which simplifies and  manages
Boto3 calls.
"""


import logging
import threading

import boto3

import config
from .helpers import _memoize
from .helpers import mask_key
from .helpers import exponential_backoff


@_memoize
def connection_manager(sceptre_dir, environment_path, user_variables=None):
    """
    Returns the ConnectionManager for the environment ``environment_path``.

    :param sceptre_dir: The absolute path to the Sceptre directory.
    :type sceptre_dir: str
    :param environment_path: Path to the environment
    :type environment_path: str
    :returns: The ConnectionManager for the environment
    :rtype: sceptre.connection_manager.ConnectionManager
    """
    user_variables = user_variables if user_variables is not None else {}
    env_config = config.environment(
        sceptre_dir, environment_path, user_variables
    )
    return ConnectionManager(
        region=env_config["region"],
        iam_role=env_config.get("iam_role")
    )


class ConnectionManager(object):
    """
    The Connection Manager should be used to create boto3 clients for
    the various AWS services that we need to interact with.

    :param iam_role: The iam_role that should be assumed in the account.
    :type iam_role: str
    :param region: The region to use.
    :type region: str
    """

    _session_lock = threading.Lock()
    _client_lock = threading.Lock()

    def __init__(self, region, iam_role=None):
        self.logger = logging.getLogger(__name__)

        self.region = region
        self.iam_role = iam_role
        self._boto_session = None

        self.clients = {}

    def __repr__(self):
        return (
            "sceptre.connection_manager.ConnectionManager(region='{0}', "
            "iam_role='{1}')".format(self.region, self.iam_role)
        )

    @property
    def boto_session(self):
        """
        Returns a boto session in the target account.

        If an ``iam_role`` is specified in ConnectionManager's initialiser,
        then STS is used to assume the specified IAM role in the account and
        uses temporary credentials to create the boto session. If ``iam_role``
        is not specified, the default AWS credentials are used to create the
        boto session.

        :returns: The Boto3 session.
        :rtype: boto3.session.Session
        :raises: botocore.exceptions.ClientError
        """
        with self._session_lock:
            self.logger.debug("Getting Boto3 session")

            if self._boto_session is None:
                self.logger.debug("No Boto3 session found, creating one...")
                if self.iam_role:
                    self.logger.debug("Assuming role '%s'...", self.iam_role)
                    sts_client = boto3.client("sts")
                    sts_response = sts_client.assume_role(
                        RoleArn=self.iam_role,
                        RoleSessionName="{0}-session".format(
                            self.iam_role.split("/")[-1]
                        )
                    )
                    credentials = sts_response["Credentials"]
                    self._boto_session = boto3.session.Session(
                        aws_access_key_id=credentials["AccessKeyId"],
                        aws_secret_access_key=credentials["SecretAccessKey"],
                        aws_session_token=credentials["SessionToken"],
                        region_name=self.region
                    )
                    self.logger.debug(
                        "Using temporary credential set: %s",
                        {
                            "AccessKeyId": mask_key(
                                credentials["AccessKeyId"]
                            ),
                            "SecretAccessKey": mask_key(
                                credentials["SecretAccessKey"]
                            )
                        }
                    )
                else:
                    self.logger.debug("Using cli credentials...")
                    self._boto_session = boto3.session.Session(
                        region_name=self.region
                    )
                    self.logger.debug(
                        "Using credential set from %s: %s",
                        self._boto_session.get_credentials().method,
                        {
                            "AccessKeyId": mask_key(
                                self._boto_session.get_credentials().access_key
                            ),
                            "SecretAccessKey": mask_key(
                                self._boto_session.get_credentials().secret_key
                            ),
                            "Region": self._boto_session.region_name
                        }
                    )

                self.logger.debug("Boto3 session created")

            return self._boto_session

    def _get_client(self, service):
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
            if self.clients.get(service) is None:
                self.logger.debug(
                    "No %s client found, creating one...", service
                )
                self.clients[service] = self.boto_session.client(service)
            return self.clients[service]

    @exponential_backoff
    def call(self, service, command, kwargs=None):
        """
        Makes a threadsafe Boto3 client call.

        Equivalent to boto3.client(<service>).<command>(**kwargs).

        :param service: The Boto3 service to return a client for.
        :type service: str
        :param command: The Boto3 command to call.
        :type command: str
        :param kwargs: The keyword arguments to supply to <command>.
        :type kwargs: dict
        :returns: The response from the Boto3 call.
        :rtype: dict
        """
        if kwargs is None:  # pragma: no cover
            kwargs = {}
        client = self._get_client(service)
        return getattr(client, command)(**kwargs)
