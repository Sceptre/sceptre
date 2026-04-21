# -*- coding: utf-8 -*-
import warnings
import pytest

from collections import defaultdict
from datetime import datetime, timezone
from typing import Union
from unittest.mock import Mock, patch, sentinel, create_autospec
from deprecation import fail_if_not_removed
from freezegun import freeze_time

from boto3.session import Session
from botocore.exceptions import ClientError

from sceptre.connection_manager import (
    ConnectionManager,
    _retry_boto_call,
)
from sceptre.exceptions import RetryLimitExceededError, InvalidAWSCredentialsError


class TestConnectionManager(object):
    def setup_method(self, test_method):
        self.stack_name = None
        self.profile = None
        self.sceptre_role = None
        self.sceptre_role_session_duration = 3600
        self.region = "eu-west-1"

        self.environment_variables = {
            "AWS_ACCESS_KEY_ID": "sceptre_test_key_id",
            "AWS_SECRET_ACCESS_KEY": "sceptre_test_access_key",
        }
        self.session_class = create_autospec(Session)
        self.mock_session: Union[Mock, Session] = self.session_class.return_value

        ConnectionManager._boto_sessions = {}
        ConnectionManager._boto_session_expirations = {}
        ConnectionManager._clients = {}
        ConnectionManager._stack_keys = {}

        self.connection_manager = ConnectionManager(
            region=self.region,
            stack_name=self.stack_name,
            profile=self.profile,
            sceptre_role=self.sceptre_role,
            session_class=self.session_class,
            get_envs_func=lambda: self.environment_variables,
        )

    def test_connection_manager_initialised_with_no_optional_parameters(self):
        connection_manager = ConnectionManager(region=sentinel.region)

        assert connection_manager.stack_name is None
        assert connection_manager.profile is None
        assert connection_manager.region == sentinel.region
        assert connection_manager._boto_sessions == {}
        assert connection_manager._clients == {}
        assert connection_manager._stack_keys == {}

    def test_connection_manager_initialised_with_all_parameters(self):
        connection_manager = ConnectionManager(
            region=self.region,
            stack_name="stack",
            profile="profile",
            sceptre_role="sceptre_role",
            sceptre_role_session_duration=21600,
        )

        assert connection_manager.stack_name == "stack"
        assert connection_manager.profile == "profile"
        assert connection_manager.sceptre_role == "sceptre_role"
        assert connection_manager.sceptre_role_session_duration == 21600
        assert connection_manager.region == self.region
        assert connection_manager._boto_sessions == {}
        assert connection_manager._clients == {}
        assert connection_manager._stack_keys == {
            "stack": (self.region, "profile", "sceptre_role")
        }

    def test_repr(self):
        self.connection_manager.stack_name = "stack"
        self.connection_manager.profile = "profile"
        self.connection_manager.region = "region"
        self.connection_manager.sceptre_role = "sceptre_role"
        response = self.connection_manager.__repr__()
        assert (
            response == "sceptre.connection_manager.ConnectionManager("
            "region='region', profile='profile', stack_name='stack', "
            "sceptre_role='sceptre_role', sceptre_role_session_duration='None')"
        )

    def test_repr_with_sceptre_role_session_duration(self):
        self.connection_manager.stack_name = "stack"
        self.connection_manager.profile = "profile"
        self.connection_manager.region = "region"
        self.connection_manager.sceptre_role = "sceptre_role"
        self.connection_manager.sceptre_role_session_duration = 21600
        response = self.connection_manager.__repr__()
        assert (
            response == "sceptre.connection_manager.ConnectionManager("
            "region='region', profile='profile', stack_name='stack', "
            "sceptre_role='sceptre_role', sceptre_role_session_duration='21600')"
        )

    def test_boto_session_with_cache(self):
        self.connection_manager._boto_sessions["test"] = sentinel.boto_session

        boto_session = self.connection_manager._boto_sessions["test"]
        assert boto_session == sentinel.boto_session

    def test__get_session__no_args__no_defaults__makes_boto_session_with_defaults(self):
        self.connection_manager.profile = None
        self.connection_manager.sceptre_role = None

        boto_session = self.connection_manager.get_session()

        self.session_class.assert_called_once_with(
            profile_name=None,
            region_name=self.region,
            aws_access_key_id=self.environment_variables["AWS_ACCESS_KEY_ID"],
            aws_secret_access_key=self.environment_variables["AWS_SECRET_ACCESS_KEY"],
            aws_session_token=None,
        )
        assert boto_session == self.mock_session

    def test_get_session__no_args__connection_manager_has_profile__uses_profile(self):
        self.connection_manager.profile = "fancy"
        self.connection_manager.sceptre_role = None

        boto_session = self.connection_manager.get_session()

        self.session_class.assert_called_once_with(
            profile_name="fancy",
            region_name=self.region,
            aws_access_key_id=self.environment_variables["AWS_ACCESS_KEY_ID"],
            aws_secret_access_key=self.environment_variables["AWS_SECRET_ACCESS_KEY"],
            aws_session_token=None,
        )
        assert boto_session == self.mock_session

    def test_get_session___profile_specified__makes_boto_session_with_passed_profile(
        self,
    ):
        self.connection_manager.profile = None

        boto_session = self.connection_manager.get_session(profile="fancy")

        self.session_class.assert_called_once_with(
            profile_name="fancy",
            region_name=self.region,
            aws_access_key_id=self.environment_variables["AWS_ACCESS_KEY_ID"],
            aws_secret_access_key=self.environment_variables["AWS_SECRET_ACCESS_KEY"],
            aws_session_token=None,
        )
        assert boto_session == self.mock_session

    def test_get_session__none_for_profile_passed__connection_manager_has_default_profile__uses_no_profile(
        self,
    ):
        self.connection_manager.profile = "default profile"

        boto_session = self.connection_manager.get_session(profile=None)

        self.session_class.assert_called_once_with(
            profile_name=None,
            region_name=self.region,
            aws_access_key_id=self.environment_variables["AWS_ACCESS_KEY_ID"],
            aws_secret_access_key=self.environment_variables["AWS_SECRET_ACCESS_KEY"],
            aws_session_token=None,
        )
        assert boto_session == self.mock_session

    def test_get_session__no_sceptre_role_passed__no_sceptre_role_on_connection_manager__does_not_assume_role(
        self,
    ):
        self.connection_manager.sceptre_role = None

        self.connection_manager.get_session()
        self.mock_session.client.assert_not_called()

    def test_get_session__none_passed_for_sceptre_role__sceptre_role_on_connection_manager__does_not_assume_role(
        self,
    ):
        self.connection_manager.sceptre_role = (
            "arn:aws:iam::123456:role/my-path/other-role"
        )
        self.connection_manager.get_session(sceptre_role=None)

        self.mock_session.client.assert_not_called()

    @pytest.mark.parametrize(
        "connection_manager,arg",
        [
            pytest.param(
                "arn:aws:iam::123456:role/my-path/my-role",
                ConnectionManager.STACK_DEFAULT,
                id="role on connection manager",
            ),
            pytest.param(
                "arn:aws:iam::123456:role/my-path/other-role",
                "arn:aws:iam::123456:role/my-path/my-role",
                id="overrides connection manager",
            ),
        ],
    )
    def test_get_session__sceptre_role__assumes_that_role(
        self, connection_manager, arg
    ):
        self.connection_manager.sceptre_role = connection_manager

        kwargs = {}
        if arg != self.connection_manager.STACK_DEFAULT:
            kwargs["sceptre_role"] = arg

        self.connection_manager.get_session(**kwargs)

        self.mock_session.client.assert_called_once_with("sts")
        expected_role = (
            arg if arg != self.connection_manager.STACK_DEFAULT else connection_manager
        )
        self.mock_session.client.return_value.assume_role.assert_called_once_with(
            RoleArn=expected_role, RoleSessionName="my-role-session"
        )

        credentials = self.mock_session.client.return_value.assume_role()["Credentials"]

        self.session_class.assert_any_call(
            region_name=self.region,
            aws_access_key_id=credentials["AccessKeyId"],
            aws_secret_access_key=credentials["SecretAccessKey"],
            aws_session_token=credentials["SessionToken"],
        )

    def test_get_session__sceptre_role_and_session_duration_on_connection_manager__uses_session_duration(
        self,
    ):
        self.connection_manager.sceptre_role = "sceptre_role"
        self.connection_manager.sceptre_role_session_duration = 21600

        self.connection_manager.get_session()

        self.mock_session.client.return_value.assume_role.assert_called_once_with(
            RoleArn=self.connection_manager.sceptre_role,
            RoleSessionName="{0}-session".format(
                self.connection_manager.sceptre_role.split("/")[-1]
            ),
            DurationSeconds=21600,
        )

    def test_get_session__with_sceptre_role__returning_empty_credentials__raises_invalid_aws_credentials_error(
        self,
    ):
        self.connection_manager._boto_sessions = {}
        self.connection_manager.sceptre_role = "sceptre_role"

        self.mock_session.get_credentials.return_value = None

        with pytest.raises(InvalidAWSCredentialsError):
            self.connection_manager.get_session(
                self.profile, self.region, self.connection_manager.sceptre_role
            )

    def test_get_client_with_no_pre_existing_clients(self):
        service = "s3"
        region = "eu-west-1"
        profile = None
        sceptre_role = None
        stack = self.stack_name

        client = self.connection_manager._get_client(
            service, region, profile, stack, sceptre_role
        )
        expected_client = self.mock_session.client.return_value
        assert client == expected_client
        self.mock_session.client.assert_any_call(service)

    def test_get_client_with_existing_client(self):
        service = "cloudformation"
        region = "eu-west-1"
        sceptre_role = None
        profile = None
        stack = self.stack_name

        client_1 = self.connection_manager._get_client(
            service, region, profile, stack, sceptre_role
        )
        client_2 = self.connection_manager._get_client(
            service, region, profile, stack, sceptre_role
        )
        assert client_1 == client_2
        assert self.mock_session.client.call_count == 1

    @patch("sceptre.connection_manager.boto3.session.Session.get_credentials")
    def test_get_client_with_existing_client_and_profile_none(
        self, mock_get_credentials
    ):
        service = "cloudformation"
        region = "eu-west-1"
        sceptre_role = None
        profile = None
        stack = self.stack_name

        self.connection_manager.profile = None
        client_1 = self.connection_manager._get_client(
            service, region, profile, stack, sceptre_role
        )
        client_2 = self.connection_manager._get_client(
            service, region, profile, stack, sceptre_role
        )
        assert client_1 == client_2

    # ------------------------------------------------------------------
    # STS session expiry tests
    #
    # Background: AWS STS credentials obtained via assume_role carry a
    # maximum lifetime (default 1 hour, up to 12 hours).  Before this
    # fix, Sceptre cached the boto3 session indefinitely, which meant
    # any deployment running longer than the credential lifetime would
    # fail with an authentication error when the next AWS call was made
    # on the expired session.  The tests below demonstrate both the
    # previous flaw (expired-credential scenarios that formerly succeeded
    # only because the stale cached value was blindly returned) and the
    # corrected behaviour (the cache is evicted and a fresh session is
    # obtained via a new assume_role call).
    # ------------------------------------------------------------------

    @freeze_time("2024-01-01 12:00:00")
    def test_get_session__sts_credentials_not_yet_expired__reuses_cached_session(self):
        """A session whose STS expiration is in the future must be reused
        without triggering a new assume_role call."""
        region = self.region
        profile = None
        sceptre_role = "arn:aws:iam::123456:role/my-role"
        key = (region, profile, sceptre_role)
        # Expiration is 1 hour after the frozen "now" (2024-01-01 13:00 UTC)
        future_expiration = datetime(2024, 1, 1, 13, 0, 0, tzinfo=timezone.utc)

        self.connection_manager._boto_sessions[key] = sentinel.existing_session
        self.connection_manager._boto_session_expirations[key] = future_expiration

        session = self.connection_manager._get_session(profile, region, sceptre_role)

        assert session is sentinel.existing_session
        # Session class must NOT have been called — no new session was created.
        self.session_class.assert_not_called()

    @freeze_time("2024-01-01 12:00:00")
    def test_get_session__sts_credentials_expired__evicts_and_recreates_session(self):
        """A session whose STS expiration is in the past must be evicted from
        the cache and a new session created via a fresh assume_role call.

        This test demonstrates the previous flaw: before the fix, the stale
        cached session would have been returned directly, causing subsequent
        AWS calls to fail with an authentication error.
        """
        region = self.region
        profile = None
        sceptre_role = "arn:aws:iam::123456:role/my-role"
        key = (region, profile, sceptre_role)
        # Expiration was 1 hour before the frozen "now" (2024-01-01 11:00 UTC)
        past_expiration = datetime(2024, 1, 1, 11, 0, 0, tzinfo=timezone.utc)
        new_expiration = datetime(2024, 1, 1, 13, 0, 0, tzinfo=timezone.utc)

        # Prime the cache with a stale entry (simulates the pre-fix state)
        self.connection_manager._boto_sessions[key] = sentinel.stale_session
        self.connection_manager._boto_session_expirations[key] = past_expiration

        # Configure assume_role to return fresh credentials for the new session
        sts_client_mock = self.mock_session.client.return_value
        sts_client_mock.assume_role.return_value = {
            "Credentials": {
                "AccessKeyId": "new_id",
                "SecretAccessKey": "new_key",
                "SessionToken": "new_token",
                "Expiration": new_expiration,
            }
        }

        new_session = self.connection_manager._get_session(
            profile, region, sceptre_role
        )

        # The stale session must have been replaced with a fresh one
        assert new_session is not sentinel.stale_session
        # The refreshed expiration must be persisted for future expiry checks
        assert self.connection_manager._boto_session_expirations[key] == new_expiration

    @freeze_time("2024-01-01 12:00:00")
    def test_get_session__sts_expiration_stored_when_role_assumed(self):
        """After a successful assume_role the ``Expiration`` timestamp is
        stored in ``_boto_session_expirations`` so that future calls to
        ``_get_session`` and ``_get_client`` can detect and handle expiry."""
        region = self.region
        profile = None
        sceptre_role = "arn:aws:iam::123456:role/my-role"
        key = (region, profile, sceptre_role)
        expiration = datetime(2024, 1, 1, 13, 0, 0, tzinfo=timezone.utc)

        sts_client_mock = self.mock_session.client.return_value
        sts_client_mock.assume_role.return_value = {
            "Credentials": {
                "AccessKeyId": "id",
                "SecretAccessKey": "key",
                "SessionToken": "token",
                "Expiration": expiration,
            }
        }

        self.connection_manager._get_session(profile, region, sceptre_role)

        assert self.connection_manager._boto_session_expirations.get(key) == expiration

    def test_get_session__no_sceptre_role__no_expiration_stored(self):
        """Without a ``sceptre_role`` no STS assume_role call is made and
        therefore no expiration entry is stored in
        ``_boto_session_expirations``."""
        region = self.region
        profile = None
        sceptre_role = None

        self.connection_manager._get_session(profile, region, sceptre_role)

        assert self.connection_manager._boto_session_expirations == {}

    @freeze_time("2024-01-01 12:00:00")
    def test_get_client__underlying_session_expired__evicts_client_and_creates_new(
        self,
    ):
        """If the STS session backing a cached client has expired, the cached
        client must be evicted and a new one created from a refreshed session.

        This test demonstrates the previous flaw: before the fix, the stale
        client (backed by expired credentials) would have been returned and any
        subsequent AWS call with it would have received an authentication error.
        """
        service = "cloudformation"
        region = self.region
        profile = None
        sceptre_role = "arn:aws:iam::123456:role/my-role"
        stack = None
        client_key = (service, region, profile, stack, sceptre_role)
        session_key = (region, profile, sceptre_role)
        # Expiration 1 hour before frozen "now" — the session is expired
        past_expiration = datetime(2024, 1, 1, 11, 0, 0, tzinfo=timezone.utc)
        new_expiration = datetime(2024, 1, 1, 13, 0, 0, tzinfo=timezone.utc)

        # Prime the client cache with a stale client (simulates the pre-fix state)
        stale_client = Mock(name="stale_client")
        self.connection_manager._clients[client_key] = stale_client
        # Record an expired STS timestamp for the underlying session
        self.connection_manager._boto_session_expirations[session_key] = past_expiration

        # Configure assume_role so the session refresh succeeds
        sts_client_mock = self.mock_session.client.return_value
        sts_client_mock.assume_role.return_value = {
            "Credentials": {
                "AccessKeyId": "new_id",
                "SecretAccessKey": "new_key",
                "SessionToken": "new_token",
                "Expiration": new_expiration,
            }
        }

        new_client = self.connection_manager._get_client(
            service, region, profile, stack, sceptre_role
        )

        # The stale client must have been replaced with a new one
        assert new_client is not stale_client

    @freeze_time("2024-01-01 12:00:00")
    def test_get_client__underlying_session_not_expired__reuses_cached_client(self):
        """If the STS session is still valid the cached client must be returned
        as-is, without creating a new session or a new client."""
        service = "cloudformation"
        region = self.region
        profile = None
        sceptre_role = "arn:aws:iam::123456:role/my-role"
        stack = None
        client_key = (service, region, profile, stack, sceptre_role)
        session_key = (region, profile, sceptre_role)
        # Expiration 1 hour after frozen "now" — the session is still valid
        future_expiration = datetime(2024, 1, 1, 13, 0, 0, tzinfo=timezone.utc)

        cached_client = Mock(name="cached_client")
        self.connection_manager._clients[client_key] = cached_client
        self.connection_manager._boto_session_expirations[session_key] = (
            future_expiration
        )

        result = self.connection_manager._get_client(
            service, region, profile, stack, sceptre_role
        )

        assert result is cached_client
        # No new session or client must have been created
        self.session_class.assert_not_called()

    def test_call__profile_region_and_role_are_stack_default__uses_instance_settings(
        self,
    ):
        service = "s3"
        command = "list_buckets"
        instance_profile = "profile"
        instance_role = "role"
        stack_name = None
        self.set_connection_manager_vars(instance_profile, self.region, instance_role)
        expected_client = self.set_up_expected_client(
            service, stack_name, instance_profile, self.region, instance_role
        )

        self.connection_manager.call(service, command)
        expected_client.list_buckets.assert_any_call()

    def set_connection_manager_vars(self, profile, region, sceptre_role):
        self.connection_manager.region = region
        self.connection_manager.profile = profile
        self.connection_manager.sceptre_role = sceptre_role

    def set_up_expected_client(
        self, service, stack_name, profile, region, sceptre_role
    ):
        self.connection_manager._clients = clients = defaultdict(Mock)
        clients[(service, region, profile, stack_name, sceptre_role)] = expected = Mock(
            name="expected"
        )
        return expected

    def set_target_stack_settings(self, stack_name, profile, region, role):
        self.connection_manager._stack_keys = settings = defaultdict(
            lambda: ("wrong", "wrong", "wrong")
        )
        settings[stack_name] = (region, profile, role)

    def test_call__profile_region_set__role_is_stack_default__uses_instance_role(self):
        service = "s3"
        command = "list_buckets"
        instance_profile = "profile"
        instance_role = "role"
        stack_name = None
        self.set_connection_manager_vars(instance_profile, self.region, instance_role)

        expected_profile = "new profile"
        expected_region = "us-west-800"
        expected_client = self.set_up_expected_client(
            service, stack_name, expected_profile, expected_region, instance_role
        )

        self.connection_manager.call(
            service, command, profile=expected_profile, region=expected_region
        )
        expected_client.list_buckets.assert_any_call()

    def test_call__profile_region_set__role_is_none__nullifies_role(self):
        service = "s3"
        command = "list_buckets"
        instance_profile = "profile"
        instance_role = "role"
        stack_name = None
        self.set_connection_manager_vars(instance_profile, self.region, instance_role)

        expected_profile = "new profile"
        expected_region = "us-west-800"
        expected_role = None
        expected_client = self.set_up_expected_client(
            service, stack_name, expected_profile, expected_region, expected_role
        )

        self.connection_manager.call(
            service,
            command,
            profile=expected_profile,
            region=expected_region,
            sceptre_role=expected_role,
        )
        expected_client.list_buckets.assert_any_call()

    def test_call__stack_name_set_and_cached__profile_region_and_role_are_stack_default__uses_target_stack_settings(
        self,
    ):
        service = "s3"
        command = "list_buckets"
        instance_profile = "profile"
        instance_role = "role"
        stack_name = "target"
        self.set_connection_manager_vars(instance_profile, self.region, instance_role)

        target_profile = "new profile"
        target_region = "us-west-800"
        target_role = "roley role"
        self.set_target_stack_settings(
            stack_name, target_profile, target_region, target_role
        )
        expected_client = self.set_up_expected_client(
            service, stack_name, target_profile, target_region, target_role
        )

        self.connection_manager.call(
            service,
            command,
            stack_name=stack_name,
        )
        expected_client.list_buckets.assert_any_call()

    def test_call__stack_name_set_not_cached__profile_region_and_role_are_stack_default__uses_target_stack_settings(
        self,
    ):
        service = "s3"
        command = "list_buckets"
        instance_profile = "profile"
        instance_role = "role"
        stack_name = "target"
        self.set_connection_manager_vars(instance_profile, self.region, instance_role)

        expected_client = self.set_up_expected_client(
            service, stack_name, instance_profile, self.region, instance_role
        )

        self.connection_manager.call(
            service,
            command,
            stack_name=stack_name,
        )
        expected_client.list_buckets.assert_any_call()

    def test_call__stack_name_set_and_cached__profile_region_and_role_are_none__uses_current_stack_settings(
        self,
    ):
        service = "s3"
        command = "list_buckets"
        instance_profile = "profile"
        instance_role = "role"
        stack_name = "target"
        self.set_connection_manager_vars(instance_profile, self.region, instance_role)

        target_profile = "new profile"
        target_region = "us-west-800"
        target_role = "roley role"
        self.set_target_stack_settings(
            stack_name, target_profile, target_region, target_role
        )
        expected_client = self.set_up_expected_client(
            service, stack_name, target_profile, target_region, target_role
        )

        self.connection_manager.call(
            service,
            command,
            stack_name=stack_name,
            profile=None,
            region=None,
            sceptre_role=None,
        )
        expected_client.list_buckets.assert_any_call()

    def test_call__stack_name_set_not_cached__profile_region_and_role_are_none__uses_current_stack_settings(
        self,
    ):
        service = "s3"
        command = "list_buckets"
        instance_profile = "profile"
        instance_role = "role"
        stack_name = "target"
        self.set_connection_manager_vars(instance_profile, self.region, instance_role)

        expected_client = self.set_up_expected_client(
            service, stack_name, instance_profile, self.region, instance_role
        )

        self.connection_manager.call(
            service,
            command,
            stack_name=stack_name,
            profile=None,
            region=None,
            sceptre_role=None,
        )
        expected_client.list_buckets.assert_any_call()

    def test_call__stack_name_set_and_cached__profile_and_region_are_stack_default_and_role_is_none__nullifies_role(
        self,
    ):
        service = "s3"
        command = "list_buckets"
        instance_profile = "profile"
        instance_role = "role"
        stack_name = "target"
        self.set_connection_manager_vars(instance_profile, self.region, instance_role)

        target_profile = "new profile"
        target_region = "us-west-800"
        target_role = "roley role"
        self.set_target_stack_settings(
            stack_name, target_profile, target_region, target_role
        )

        expected_client = self.set_up_expected_client(
            service, stack_name, target_profile, target_region, None
        )

        self.connection_manager.call(
            service,
            command,
            stack_name=stack_name,
            sceptre_role=None,
        )
        expected_client.list_buckets.assert_any_call()

    def test_call__stack_name_set_not_cached__profile_and_region_are_stack_default_and_role_is_none__nullifies_role(
        self,
    ):
        service = "s3"
        command = "list_buckets"
        instance_profile = "profile"
        instance_role = "role"
        stack_name = "target"
        self.set_connection_manager_vars(instance_profile, self.region, instance_role)

        expected_client = self.set_up_expected_client(
            service, stack_name, instance_profile, self.region, None
        )

        self.connection_manager.call(
            service,
            command,
            stack_name=stack_name,
            sceptre_role=None,
        )
        expected_client.list_buckets.assert_any_call()

    def test_call__invoked_with_iam_role_kwarg__emits_deprecation_warning(self):
        service = "s3"
        command = "list_buckets"
        instance_profile = "profile"
        instance_role = "role"
        stack_name = None
        self.set_connection_manager_vars(instance_profile, self.region, instance_role)
        self.set_up_expected_client(
            service, stack_name, instance_profile, self.region, instance_role
        )

        with warnings.catch_warnings(record=True) as recorded:
            self.connection_manager.call(service, command, iam_role="new role")

        assert len(recorded) == 1
        assert issubclass(recorded[0].category, DeprecationWarning)

    def test_call__stack_name_set_and_cached__invoked_with_iam_role_kwarg__emits_deprecation_warning(
        self,
    ):
        service = "s3"
        command = "list_buckets"
        instance_profile = "profile"
        instance_role = "role"
        stack_name = "target"
        self.set_connection_manager_vars(instance_profile, self.region, instance_role)

        target_profile = "new profile"
        target_region = "us-west-800"
        target_role = "roley role"
        self.set_target_stack_settings(
            stack_name, target_profile, target_region, target_role
        )
        self.set_up_expected_client(
            service, stack_name, target_profile, target_region, target_role
        )
        with warnings.catch_warnings(record=True) as recorded:
            self.connection_manager.call(
                service,
                command,
                stack_name=stack_name,
                profile=None,
                region=None,
                iam_role=None,
            )

        assert len(recorded) == 1
        assert issubclass(recorded[0].category, DeprecationWarning)

    def test_call__stack_name_set_not_cached__invoked_with_iam_role_kwarg__emits_deprecation_warning(
        self,
    ):
        service = "s3"
        command = "list_buckets"
        instance_profile = "profile"
        instance_role = "role"
        stack_name = "target"
        self.set_connection_manager_vars(instance_profile, self.region, instance_role)

        self.set_up_expected_client(
            service, stack_name, instance_profile, self.region, instance_role
        )
        with warnings.catch_warnings(record=True) as recorded:
            self.connection_manager.call(
                service,
                command,
                stack_name=stack_name,
                profile=None,
                region=None,
                iam_role=None,
            )

        assert len(recorded) == 1
        assert issubclass(recorded[0].category, DeprecationWarning)

    def test_call__invoked_with_iam_role__uses_that_as_sceptre_role(self):
        service = "s3"
        command = "list_buckets"
        instance_profile = "profile"
        instance_role = "role"
        stack_name = None
        expected_role = "new role"
        self.set_connection_manager_vars(instance_profile, self.region, instance_role)
        expected_client = self.set_up_expected_client(
            service, stack_name, instance_profile, self.region, expected_role
        )

        with warnings.catch_warnings():
            self.connection_manager.call(service, command, iam_role=expected_role)

        expected_client.list_buckets.assert_any_call()

    def test_call__stack_name_set_and_cached__invoked_with_iam_role__uses_that_as_sceptre_role(
        self,
    ):
        service = "s3"
        command = "list_buckets"
        instance_profile = "profile"
        instance_role = "role"
        stack_name = "target"
        self.set_connection_manager_vars(instance_profile, self.region, instance_role)

        target_profile = "new profile"
        target_region = "us-west-800"
        target_role = "roley role"
        self.set_target_stack_settings(
            stack_name, target_profile, target_region, target_role
        )

        expected_role = "new role"
        expected_client = self.set_up_expected_client(
            service, stack_name, target_profile, target_region, expected_role
        )

        with warnings.catch_warnings():
            self.connection_manager.call(
                service,
                command,
                stack_name=stack_name,
                iam_role=expected_role,
            )
        expected_client.list_buckets.assert_any_call()

    def test_call__stack_name_set_not_cached__invoked_with_iam_role__uses_that_as_sceptre_role(
        self,
    ):
        service = "s3"
        command = "list_buckets"
        instance_profile = "profile"
        instance_role = "role"
        stack_name = "target"
        self.set_connection_manager_vars(instance_profile, self.region, instance_role)

        expected_role = "new role"
        expected_client = self.set_up_expected_client(
            service, stack_name, instance_profile, self.region, expected_role
        )

        with warnings.catch_warnings():
            self.connection_manager.call(
                service,
                command,
                stack_name=stack_name,
                iam_role=expected_role,
            )
        expected_client.list_buckets.assert_any_call()

    def test_create_session_environment_variables__no_token__returns_envs_dict(self):
        self.mock_session.configure_mock(
            **{
                "region_name": "us-west-2",
                "get_credentials.return_value.access_key": "new_access_key",
                "get_credentials.return_value.secret_key": "new_secret_key",
                "get_credentials.return_value.token": None,
            }
        )

        result = self.connection_manager.create_session_environment_variables()
        expected = {
            "AWS_ACCESS_KEY_ID": "new_access_key",
            "AWS_SECRET_ACCESS_KEY": "new_secret_key",
            "AWS_DEFAULT_REGION": "us-west-2",
            "AWS_REGION": "us-west-2",
        }
        assert expected == result

    def test_create_session_environment_variables__has_session_token__returns_envs_dict_with_token(
        self,
    ):
        self.mock_session.configure_mock(
            **{
                "region_name": "us-west-2",
                "get_credentials.return_value.access_key": "new_access_key",
                "get_credentials.return_value.secret_key": "new_secret_key",
                "get_credentials.return_value.token": "my token",
            }
        )

        result = self.connection_manager.create_session_environment_variables()
        expected = {
            "AWS_ACCESS_KEY_ID": "new_access_key",
            "AWS_SECRET_ACCESS_KEY": "new_secret_key",
            "AWS_DEFAULT_REGION": "us-west-2",
            "AWS_REGION": "us-west-2",
            "AWS_SESSION_TOKEN": "my token",
        }
        assert expected == result

    def test_create_session_environment_variables__include_system_envs_true__adds_envs_removing_profile_and_token(
        self,
    ):
        self.environment_variables.update(
            AWS_PROFILE="my_profile",  # We expect this popped out
            AWS_SESSION_TOKEN="my token",  # This should be removed if there's no token
            OTHER="value-blah-blah",  # we expect this to be in dictionary coming out,
        )

        self.mock_session.configure_mock(
            **{
                "region_name": "us-west-2",
                "get_credentials.return_value.access_key": "new_access_key",
                "get_credentials.return_value.secret_key": "new_secret_key",
                "get_credentials.return_value.token": None,
            }
        )

        result = self.connection_manager.create_session_environment_variables(
            include_system_envs=True
        )
        expected = {
            "AWS_ACCESS_KEY_ID": "new_access_key",
            "AWS_SECRET_ACCESS_KEY": "new_secret_key",
            "AWS_DEFAULT_REGION": "us-west-2",
            "AWS_REGION": "us-west-2",
            "OTHER": "value-blah-blah",
        }
        assert expected == result

    def test_create_session_environment_variables__include_system_envs_false__does_not_add_system_envs(
        self,
    ):
        self.environment_variables.update(
            AWS_PROFILE="my_profile",  # We expect this popped out
            AWS_SESSION_TOKEN="my token",  # This should be removed if there's no token
            OTHER="value-blah-blah",  # we expect this to be in dictionary coming out,
        )

        self.mock_session.configure_mock(
            **{
                "region_name": "us-west-2",
                "get_credentials.return_value.access_key": "new_access_key",
                "get_credentials.return_value.secret_key": "new_secret_key",
                "get_credentials.return_value.token": None,
            }
        )

        result = self.connection_manager.create_session_environment_variables(
            include_system_envs=False
        )
        expected = {
            "AWS_ACCESS_KEY_ID": "new_access_key",
            "AWS_SECRET_ACCESS_KEY": "new_secret_key",
            "AWS_DEFAULT_REGION": "us-west-2",
            "AWS_REGION": "us-west-2",
        }
        assert expected == result

    @fail_if_not_removed
    def test_iam_role__is_removed_on_removal_version(self):
        self.connection_manager.iam_role

    @fail_if_not_removed
    def test_iam_role_session_duration__is_removed_on_removal_version(self):
        self.connection_manager.iam_role_session_duration

    def test_init__iam_role_fields_resolve_to_sceptre_role_fields(self):
        connection_manager = ConnectionManager(
            region="us-west-2",
            sceptre_role="sceptre_role",
            sceptre_role_session_duration=123456,
        )
        assert connection_manager.iam_role == "sceptre_role"
        assert connection_manager.iam_role_session_duration == 123456

    # ------------------------------------------------------------------
    # Reactive ExpiredToken retry tests
    #
    # Background: The proactive eviction mechanism (checking
    # _boto_session_expirations before returning a cached client) only covers
    # sessions created via assume_role (sceptre_role).  For all other
    # credential sources — e.g. env-var tokens injected by Jenkins — the
    # expiration is never stored, so the proactive check is a no-op.
    #
    # The reactive retry in call() catches ExpiredToken / ExpiredTokenException
    # ClientErrors, evicts the stale client and session, and retries the call
    # once with a freshly-created client.  These tests exercise that path.
    # ------------------------------------------------------------------

    def test_call__expired_token_error__evicts_and_retries_successfully(self):
        """When the first API call returns an ``ExpiredToken`` ClientError,
        call() must evict the stale client & session then retry and return the
        successful response from the second attempt."""
        service = "cloudformation"
        command = "describe_stacks"
        self.connection_manager.region = self.region
        self.connection_manager.profile = None
        self.connection_manager.sceptre_role = None

        stale_client = Mock(name="stale_client")
        expired_error = ClientError(
            {"Error": {"Code": "ExpiredToken", "Message": "Token expired"}},
            "DescribeStacks",
        )
        fresh_response = {"Stacks": []}
        stale_client.describe_stacks.side_effect = [expired_error]

        fresh_client = Mock(name="fresh_client")
        fresh_client.describe_stacks.return_value = fresh_response

        client_key = (service, self.region, None, None, None)
        self.connection_manager._clients[client_key] = stale_client

        # The fresh session returns fresh_client when .client() is called
        self.mock_session.client.return_value = fresh_client

        result = self.connection_manager.call(service, command)

        assert result == fresh_response
        # The stale client must have been evicted
        assert self.connection_manager._clients.get(client_key) is not stale_client

    def test_call__expired_token_exception__evicts_and_retries_successfully(self):
        """``ExpiredTokenException`` (returned by STS and some other services)
        must trigger the same evict-and-retry path as ``ExpiredToken``."""
        service = "sts"
        command = "get_caller_identity"
        self.connection_manager.region = self.region
        self.connection_manager.profile = None
        self.connection_manager.sceptre_role = None

        stale_client = Mock(name="stale_client")
        expired_error = ClientError(
            {
                "Error": {
                    "Code": "ExpiredTokenException",
                    "Message": "Token is expired",
                }
            },
            "GetCallerIdentity",
        )
        fresh_response = {"UserId": "AIDA...", "Account": "123456789012", "Arn": "..."}
        stale_client.get_caller_identity.side_effect = [expired_error]

        fresh_client = Mock(name="fresh_client")
        fresh_client.get_caller_identity.return_value = fresh_response

        client_key = (service, self.region, None, None, None)
        self.connection_manager._clients[client_key] = stale_client

        self.mock_session.client.return_value = fresh_client

        result = self.connection_manager.call(service, command)

        assert result == fresh_response
        assert self.connection_manager._clients.get(client_key) is not stale_client

    def test_call__expired_token__non_sceptre_role__evicts_base_session(self):
        """Without a sceptre_role (env-var credentials only), an ``ExpiredToken``
        error must still evict the cached session so that the retry creates a
        fresh session reading current environment variables."""
        service = "cloudformation"
        command = "describe_stacks"
        self.connection_manager.region = self.region
        self.connection_manager.profile = None
        self.connection_manager.sceptre_role = None

        session_key = (self.region, None, None)
        client_key = (service, self.region, None, None, None)

        stale_session = Mock(name="stale_session")
        stale_client = Mock(name="stale_client")
        stale_client.describe_stacks.side_effect = ClientError(
            {"Error": {"Code": "ExpiredToken", "Message": "Token expired"}},
            "DescribeStacks",
        )
        self.connection_manager._boto_sessions[session_key] = stale_session
        self.connection_manager._clients[client_key] = stale_client

        fresh_client = Mock(name="fresh_client")
        fresh_client.describe_stacks.return_value = {"Stacks": []}
        self.mock_session.client.return_value = fresh_client

        self.connection_manager.call(service, command)

        # The stale session must have been evicted
        assert (
            self.connection_manager._boto_sessions.get(session_key) is not stale_session
        )

    def test_call__non_expiry_client_error__not_retried(self):
        """A ClientError that is NOT an expiry error must propagate immediately
        without triggering the evict-and-retry path."""
        service = "cloudformation"
        command = "describe_stacks"
        self.connection_manager.region = self.region
        self.connection_manager.profile = None
        self.connection_manager.sceptre_role = None

        other_error = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "Access denied"}},
            "DescribeStacks",
        )
        client = Mock(name="client")
        client.describe_stacks.side_effect = other_error

        client_key = (service, self.region, None, None, None)
        self.connection_manager._clients[client_key] = client

        with pytest.raises(ClientError) as exc_info:
            self.connection_manager.call(service, command)

        assert exc_info.value.response["Error"]["Code"] == "AccessDenied"
        # Called exactly once — no retry
        client.describe_stacks.assert_called_once()


class TestRetry:
    def test_retry_boto_call_returns_response_correctly(self):
        def func(*args, **kwargs):
            return sentinel.response

        response = _retry_boto_call(func)()

        assert response == sentinel.response

    @patch("sceptre.connection_manager.time.sleep")
    def test_retry_boto_call_pauses_when_request_limit_hit(self, mock_sleep):
        mock_func = Mock()
        mock_func.side_effect = [
            ClientError(
                {"Error": {"Code": "Throttling", "Message": "Request limit hit"}},
                sentinel.operation,
            ),
            sentinel.response,
        ]
        # The attribute function.__name__ is required by the decorator @wraps.
        mock_func.__name__ = "mock_func"

        _retry_boto_call(mock_func)()
        mock_sleep.assert_called_once_with(1)

    def test_retry_boto_call_raises_non_throttling_error(self):
        mock_func = Mock()
        mock_func.side_effect = ClientError(
            {"Error": {"Code": 500, "Message": "Boom!"}}, sentinel.operation
        )
        # The attribute function.__name__ is required by the decorator @wraps.
        mock_func.__name__ = "mock_func"

        with pytest.raises(ClientError) as e:
            _retry_boto_call(mock_func)()
        assert e.value.response["Error"]["Code"] == 500
        assert e.value.response["Error"]["Message"] == "Boom!"

    @patch("sceptre.connection_manager.time.sleep")
    def test_retry_boto_call_raises_retry_limit_exceeded_exception(self, mock_sleep):
        mock_func = Mock()
        mock_func.side_effect = ClientError(
            {"Error": {"Code": "Throttling", "Message": "Request limit hit"}},
            sentinel.operation,
        )
        # The attribute function.__name__ is required by the decorator @wraps.
        mock_func.__name__ = "mock_func"

        with pytest.raises(RetryLimitExceededError):
            _retry_boto_call(mock_func)()
