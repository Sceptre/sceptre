# -*- coding: utf-8 -*-
"""
sceptre.connection_manager

This module implements a ConnectionManager class, which simplifies and manages
Boto3 calls.
"""

import functools
import logging
import os
import random
import threading
import time
import warnings
from typing import Optional, Dict, Tuple, Any

import boto3
import deprecation
from botocore.credentials import Credentials
from botocore.exceptions import ClientError

from sceptre.exceptions import InvalidAWSCredentialsError, RetryLimitExceededError
from sceptre.helpers import mask_key, create_deprecated_alias_property


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
            "Exceeded request limit {0} times. Aborting.".format(max_retries)
        )

    return decorated


class ConnectionManager(object):
    """
    The Connection Manager is used to create boto3 clients for
    the various AWS services that Sceptre needs to interact with.

    :param profile: The AWS credentials profile that should be used.
    :param sceptre_role: The sceptre_role that should be assumed in the account.
    :param stack_name: The CloudFormation stack name for this connection.
    :param region: The region to use.
    :param sceptre_role_session_duration: The duration to assume the specified sceptre_role per session.
    """

    # STACK_DEFAULT is a sentinel value meaning "default to the stack's configuration". This is in
    # contrast with passing None, which would mean "use no value".
    STACK_DEFAULT = "[STACK DEFAULT]"

    _session_lock = threading.Lock()
    _client_lock = threading.Lock()
    _boto_sessions = {}
    _clients = {}
    _stack_keys = {}

    iam_role = create_deprecated_alias_property(
        "iam_role", "sceptre_role", "4.0.0", "5.0.0"
    )
    sceptre_role_session_duration = 0
    iam_role_session_duration = create_deprecated_alias_property(
        "iam_role_session_duration", "sceptre_role_session_duration", "4.0.0", "5.0.0"
    )

    def __init__(
        self,
        region: str,
        profile: Optional[str] = None,
        stack_name: Optional[str] = None,
        sceptre_role: Optional[str] = None,
        sceptre_role_session_duration: Optional[int] = None,
        *,
        session_class=boto3.Session,
        get_envs_func=lambda: os.environ,
    ):
        self.logger = logging.getLogger(__name__)

        self.region = region
        self.profile = profile
        self.stack_name = stack_name
        self.sceptre_role = sceptre_role
        self.sceptre_role_session_duration = sceptre_role_session_duration

        if stack_name:
            self._stack_keys[stack_name] = (region, profile, sceptre_role)

        self._session_class = session_class
        self._get_envs = get_envs_func

    def __repr__(self):
        return (
            "sceptre.connection_manager.ConnectionManager(region='{0}', "
            "profile='{1}', stack_name='{2}', sceptre_role='{3}', sceptre_role_session_duration='{4}')".format(
                self.region,
                self.profile,
                self.stack_name,
                self.sceptre_role,
                self.sceptre_role_session_duration,
            )
        )

    def get_session(
        self,
        profile: Optional[str] = STACK_DEFAULT,
        region: Optional[str] = STACK_DEFAULT,
        sceptre_role: Optional[str] = STACK_DEFAULT,
        *,
        iam_role: Optional[str] = STACK_DEFAULT,
    ) -> boto3.Session:
        """
        Returns a boto3 session for the targeted profile, region, and sceptre_role.

        For each of profile, region, and sceptre_role, these values will default to the ConnectionManager's
        configured default values (which correspond to the Stack's configuration). These values can
        be overridden, however, by passing them explicitly.

        :param profile: The name of the AWS Profile as configured in the local environment. Passing
            None will result in no profile being specified. Defaults to the ConnectionManager's
            configured profile (if there is one).
        :param region: The AWS Region the session should be configured with. Defaults to the
            ConnectionManager's configured region.
        :param sceptre_role: The IAM role ARN that is assumed using STS to create the session. Passing
            None will result in no IAM role being assumed. Defaults to the ConnectionManager's
            configured sceptre_role (if there is one).
        :param iam_role: An alias for sceptre_role; Deprecated in v4.0.0 and will be removed in
            v5.0.0.

        :returns: The Boto3 session.
        :raises: botocore.exceptions.ClientError
        """
        profile, region, sceptre_role = self._determine_session_args(
            profile, region, sceptre_role, iam_role
        )

        return self._get_session(profile, region, sceptre_role)

    def _determine_session_args(
        self, profile: str, region: str, sceptre_role: str, iam_role: str
    ) -> Tuple[str, str, str]:
        profile = self.profile if profile == self.STACK_DEFAULT else profile
        region = self.region if region == self.STACK_DEFAULT else region
        sceptre_role = self._coalesce_sceptre_role(iam_role, sceptre_role)
        sceptre_role = (
            self.sceptre_role if sceptre_role == self.STACK_DEFAULT else sceptre_role
        )
        # For historical reasons, if all three values are "None", that means we default to the
        # Stack's configuration.
        if (profile, region, sceptre_role) == (None, None, None):
            profile, region, sceptre_role = self.profile, self.region, self.sceptre_role

        return profile, region, sceptre_role

    def _emit_iam_role_deprecation_warning(self):
        warnings.warn(
            deprecation.DeprecatedWarning(
                "The iam_role parameter", "4.0.0", "5.0.0", "Use sceptre_role instead"
            ),
            DeprecationWarning,
            stacklevel=3,
        )

    def create_session_environment_variables(
        self,
        profile: Optional[str] = STACK_DEFAULT,
        region: Optional[str] = STACK_DEFAULT,
        sceptre_role: Optional[str] = STACK_DEFAULT,
        include_system_envs: bool = True,
    ) -> Dict[str, str]:
        """Creates the standard AWS environment variables that would need to be passed to a
        subprocess in a hook, resolver, or template handler and allow that subprocess to work with
        the currently configured session.

        The environment variables returned by this method should be everything needed for
        subprocesses to properly interact with AWS using the ConnectionManager's configurations for
        profile, sceptre_role, and region. By default, they include the other process environment
        variables, such as PATH and any others. If you do not want the other environment variables,
        you can toggle these off via include_system_envs=False.

        | Notes on including system envs:
        |   * The AWS_DEFAULT_REGION, AWS_REGION, AWS_ACCESS_KEY_ID, and AWS_SECRET_ACCESS_KEY
        |     environment variables (if they are set in the Sceptre process) will be overwritten in
        |     the returned dict with the correct values from the newly created Session.
        |   * If the AWS_SESSION_TOKEN environment variable is currently set for the process, this
        |     will be overwritten with the new session's token (if there is one) or removed from the
        |     returned environment variables dict (if the new session doesn't have a token).

        :param profile: The name of the AWS Profile as configured in the local environment. Passing
            None will result in no profile being specified. Defaults to the ConnectionManager's
            configured profile (if there is one).
        :param region: The AWS Region the session should be configured with. Defaults to the
            ConnectionManager's configured region.
        :param sceptre_role: The IAM role ARN that is assumed using STS to create the session. Passing
            None will result in no IAM role being assumed. Defaults to the ConnectionManager's
            configured sceptre_role (if there is one).
        :param include_system_envs: If True, will return a dict with all the system environment
            variables included. This is useful for creating a complete dict of environment variables
            to pass to a subprocess. If set to False, this method will ONLY return the relevant AWS
            environment variables. Defaults to True.

        :returns: A dict of environment variables with the appropriate credentials available for use.
        """
        session = self.get_session(profile, region, sceptre_role)
        # Set aws environment variables specific to whatever AWS configuration has been set on the
        # stack's connection manager.
        credentials: Credentials = session.get_credentials()
        envs = dict(**self._get_envs()) if include_system_envs else {}

        if include_system_envs:
            # We don't want a profile specified, since that could interfere with the credentials we're
            # about to set. Even if we're using a profile, the credentials will already reflect that
            # profile's configurations.
            envs.pop("AWS_PROFILE", None)

        envs.update(
            AWS_ACCESS_KEY_ID=credentials.access_key,
            AWS_SECRET_ACCESS_KEY=credentials.secret_key,
            # Most AWS SDKs use AWS_DEFAULT_REGION for the region; some use AWS_REGION
            AWS_DEFAULT_REGION=session.region_name,
            AWS_REGION=session.region_name,
        )

        if credentials.token:
            envs["AWS_SESSION_TOKEN"] = credentials.token
        # There might not be a session token, so if there isn't one, make sure it doesn't exist in
        # the envs being passed to the subprocess
        elif include_system_envs:
            envs.pop("AWS_SESSION_TOKEN", None)

        return envs

    def _get_session(
        self,
        profile: Optional[str],
        region: Optional[str],
        sceptre_role: Optional[str],
        *,
        iam_role: Optional[str] = None,
    ) -> boto3.Session:
        if iam_role is not None:
            self._emit_iam_role_deprecation_warning()
            sceptre_role = iam_role

        with self._session_lock:
            self.logger.debug("Getting Boto3 session")
            key = (region, profile, sceptre_role)

            if self._boto_sessions.get(key) is None:
                self.logger.debug("No Boto3 session found, creating one...")
                self.logger.debug("Using cli credentials...")
                environ = self._get_envs()
                # Credentials from env take priority over profile
                config = {
                    "profile_name": profile,
                    "region_name": region,
                    "aws_access_key_id": environ.get("AWS_ACCESS_KEY_ID"),
                    "aws_secret_access_key": environ.get("AWS_SECRET_ACCESS_KEY"),
                    "aws_session_token": environ.get("AWS_SESSION_TOKEN"),
                }

                session = self._session_class(**config)
                self._boto_sessions[key] = session

                if session.get_credentials() is None:
                    raise InvalidAWSCredentialsError(
                        "Session credentials were not found. Profile: {0}. Region: {1}.".format(
                            config["profile_name"], config["region_name"]
                        )
                    )

                if sceptre_role:
                    sts_client = session.client("sts")
                    # maximum session name length is 64 chars. 56 + "-session" = 64
                    session_name = f'{sceptre_role.split("/")[-1][:56]}-session'
                    assume_role_kwargs = {
                        "RoleArn": sceptre_role,
                        "RoleSessionName": session_name,
                    }
                    if self.sceptre_role_session_duration:
                        assume_role_kwargs["DurationSeconds"] = (
                            self.sceptre_role_session_duration
                        )
                    sts_response = sts_client.assume_role(**assume_role_kwargs)

                    credentials = sts_response["Credentials"]
                    session = self._session_class(
                        aws_access_key_id=credentials["AccessKeyId"],
                        aws_secret_access_key=credentials["SecretAccessKey"],
                        aws_session_token=credentials["SessionToken"],
                        region_name=region,
                    )

                    if session.get_credentials() is None:
                        raise InvalidAWSCredentialsError(
                            "Session credentials were not found. Role: {0}. Region: {1}.".format(
                                sceptre_role, region
                            )
                        )

                    self._boto_sessions[key] = session

                self.logger.debug(
                    "Using credential set from %s: %s",
                    session.get_credentials().method,
                    {
                        "AccessKeyId": mask_key(session.get_credentials().access_key),
                        "SecretAccessKey": mask_key(
                            session.get_credentials().secret_key
                        ),
                        "Region": session.region_name,
                    },
                )

                self.logger.debug("Boto3 session created")

            return self._boto_sessions[key]

    def _get_client(self, service, region, profile, stack_name, sceptre_role):
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
            key = (service, region, profile, stack_name, sceptre_role)
            if self._clients.get(key) is None:
                self.logger.debug("No %s client found, creating one...", service)
                self._clients[key] = self._get_session(
                    profile, region, sceptre_role
                ).client(service)

            return self._clients[key]

    @_retry_boto_call
    def call(
        self,
        service: str,
        command: str,
        kwargs: Dict[str, Any] = None,
        profile: Optional[str] = STACK_DEFAULT,
        region: Optional[str] = STACK_DEFAULT,
        stack_name: Optional[str] = None,
        sceptre_role: Optional[str] = STACK_DEFAULT,
        *,
        iam_role: Optional[str] = STACK_DEFAULT,
    ):
        """
        Makes a thread-safe Boto3 client call.

        Equivalent to ``boto3.client(<service>).<command>(**kwargs)``.

        | Note regarding the profile, region, and sceptre_role parameters:
        |    We will interpret each parameter individually this way:
        |      * If the value passed is the STACK_DEFAULT constant, we'll assume it to mean we ought
        |        to use the target stack's value of that parameter.
        |      * If the value passed is None, we will interpret that as an explicit request to nullify
        |        the target stack's setting. Note: While this is valid for profile and sceptre_role,
        |        it will likely blow up if doing this for region, since AWS almost always requires that.
        |      * Otherwise, any value that has been specified will override the target stack's
        |        configuration, regardless of what has been passed for other parameters.
        |      * In the case that `None` has been specified for all parameters, that will be
        |        interpreted as using the target stack's values for all three, falling back to the
        |        current stack.

        :param service: The Boto3 service to return a client for.
        :param command: The Boto3 command to call.
        :param kwargs: The keyword arguments to supply to <command>.
        :param profile: The profile to use when invoking the command; Defaults to the stack's configuration
        :param region: The region to use when invoking the command; Default's to the stack's configuration
        :param stack_name: The name of the stack whose configuration to use. Defaults to the current stack
        :param sceptre_role: The IAM Role ARN to assume in order to invoke the command; Defaults to
            the stack's configuration.
        :param iam_role: DEPRECATED. Use sceptre_role instead.
        :returns: The response from the Boto3 call.
        """
        # If stack_name has been specified and we've already cached the region/profile/role
        # configured for that stack, the "defaults" we'll use will be those of that stack rather then
        # the defaults for the current ConnectionManager instance.
        #
        # stack_name is not used often and only really makes sense when we are acting inside Stack A
        # but needing to interact with Stack B using Stack B's configurations. This is mostly only
        # done when we're getting Stack B's outputs to resolve for Stack A's configuration.
        if stack_name and stack_name in self._stack_keys:
            stack_region, stack_profile, stack_sceptre_role = self._stack_keys[
                stack_name
            ]
            sceptre_role = self._coalesce_sceptre_role(iam_role, sceptre_role)
            # For historical/legacy purposes, if `None` is explicitly passed for all three parameters,
            # this will be interpreted to mean we're going to use the profile/region/role configuration
            # of the stack name. This could potentially interfere with an explicit attempt to nullify
            # a setting; However, in that case, we'd need to be setting the region to None... which
            # is unlikely, since that is a required stack configuration. This is the way this
            # function has always operated, so to change this behavior could break or cause
            # unexpected behavior elsewhere.
            if (region, profile, sceptre_role) == (None, None, None):
                region, profile, sceptre_role = (
                    stack_region,
                    stack_profile,
                    stack_sceptre_role,
                )
            # In every other circumstance, we will interpret each parameter individually according
            # to the way described in the docstring.
            else:
                region = stack_region if region == self.STACK_DEFAULT else region
                profile = stack_profile if profile == self.STACK_DEFAULT else profile
                sceptre_role = (
                    stack_sceptre_role
                    if sceptre_role == self.STACK_DEFAULT
                    else sceptre_role
                )
        # In most cases, we won't be targeting another stack's configurations. Instead, we'll want
        # to be using the configurations of the CURRENT stack.
        else:
            profile, region, sceptre_role = self._determine_session_args(
                profile, region, sceptre_role, iam_role
            )

        if kwargs is None:  # pragma: no cover
            kwargs = {}

        client = self._get_client(service, region, profile, stack_name, sceptre_role)
        return getattr(client, command)(**kwargs)

    def _coalesce_sceptre_role(self, iam_role: str, sceptre_role: str) -> str:
        """Evaluates the iam_role and sceptre_role parameters as passed to determine which value to
        use.
        """
        if sceptre_role == self.STACK_DEFAULT and iam_role != self.STACK_DEFAULT:
            self._emit_iam_role_deprecation_warning()
            sceptre_role = iam_role
        return sceptre_role
