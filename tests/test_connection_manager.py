# -*- coding: utf-8 -*-

import os
import pytest
from unittest.mock import Mock, MagicMock, patch, sentinel, ANY
from moto import mock_s3

from boto3.session import Session
from botocore.exceptions import ClientError, UnknownServiceError

from sceptre.connection_manager import ConnectionManager, _retry_boto_call
from sceptre.exceptions import RetryLimitExceededError, InvalidAWSCredentialsError


class TestConnectionManager(object):
    def setup_method(self, test_method):
        self.stack_name = None
        self.profile = None
        self.iam_role = None
        self.iam_role_session_duration = 3600
        self.region = "eu-west-1"

        ConnectionManager._boto_sessions = {}
        ConnectionManager._clients = {}
        ConnectionManager._stack_keys = {}

        # Temporary workaround for https://github.com/spulec/moto/issues/1924
        os.environ.setdefault("AWS_ACCESS_KEY_ID", "sceptre_test_key_id")
        os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "sceptre_test_access_key")

        self.connection_manager = ConnectionManager(
            region=self.region,
            stack_name=self.stack_name,
            profile=self.profile,
            iam_role=self.iam_role,
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
            iam_role="iam_role",
            iam_role_session_duration=21600,
        )

        assert connection_manager.stack_name == "stack"
        assert connection_manager.profile == "profile"
        assert connection_manager.iam_role == "iam_role"
        assert connection_manager.iam_role_session_duration == 21600
        assert connection_manager.region == self.region
        assert connection_manager._boto_sessions == {}
        assert connection_manager._clients == {}
        assert connection_manager._stack_keys == {
            "stack": (self.region, "profile", "iam_role")
        }

    def test_repr(self):
        self.connection_manager.stack_name = "stack"
        self.connection_manager.profile = "profile"
        self.connection_manager.region = "region"
        self.connection_manager.iam_role = "iam_role"
        response = self.connection_manager.__repr__()
        assert (
            response == "sceptre.connection_manager.ConnectionManager("
            "region='region', profile='profile', stack_name='stack', "
            "iam_role='iam_role', iam_role_session_duration='None')"
        )

    def test_repr_with_iam_role_session_duration(self):
        self.connection_manager.stack_name = "stack"
        self.connection_manager.profile = "profile"
        self.connection_manager.region = "region"
        self.connection_manager.iam_role = "iam_role"
        self.connection_manager.iam_role_session_duration = 21600
        response = self.connection_manager.__repr__()
        assert (
            response == "sceptre.connection_manager.ConnectionManager("
            "region='region', profile='profile', stack_name='stack', "
            "iam_role='iam_role', iam_role_session_duration='21600')"
        )

    def test_boto_session_with_cache(self):
        self.connection_manager._boto_sessions["test"] = sentinel.boto_session

        boto_session = self.connection_manager._boto_sessions["test"]
        assert boto_session == sentinel.boto_session

    @patch("sceptre.connection_manager.boto3.session.Session")
    def test_boto_session_with_no_profile(self, mock_Session):
        self.connection_manager._boto_sessions = {}
        self.connection_manager.profile = None

        boto_session = self.connection_manager._get_session(
            self.connection_manager.profile, self.region, self.iam_role
        )

        assert boto_session.isinstance(mock_Session)
        mock_Session.assert_called_once_with(
            profile_name=None,
            region_name="eu-west-1",
            aws_access_key_id=ANY,
            aws_secret_access_key=ANY,
            aws_session_token=ANY,
        )

    @patch("sceptre.connection_manager.boto3.session.Session")
    def test_boto_session_with_profile(self, mock_Session):
        self.connection_manager._boto_sessions = {}
        self.connection_manager.profile = "profile"

        boto_session = self.connection_manager._get_session(
            self.connection_manager.profile, self.region, self.iam_role
        )

        assert boto_session.isinstance(mock_Session)
        mock_Session.assert_called_once_with(
            profile_name="profile",
            region_name="eu-west-1",
            aws_access_key_id=ANY,
            aws_secret_access_key=ANY,
            aws_session_token=ANY,
        )

    @patch("sceptre.connection_manager.boto3.session.Session")
    def test_boto_session_with_no_iam_role(self, mock_Session):
        self.connection_manager._boto_sessions = {}
        self.connection_manager.iam_role = None

        boto_session = self.connection_manager._get_session(
            self.profile, self.region, self.connection_manager.iam_role
        )

        assert boto_session.isinstance(mock_Session)
        mock_Session.assert_called_once_with(
            profile_name=None,
            region_name="eu-west-1",
            aws_access_key_id=ANY,
            aws_secret_access_key=ANY,
            aws_session_token=ANY,
        )

        boto_session.client().assume_role.assert_not_called()

    @patch("sceptre.connection_manager.boto3.session.Session")
    def test_boto_session_with_iam_role(self, mock_Session):
        self.connection_manager._boto_sessions = {}
        self.connection_manager.iam_role = "iam_role"

        boto_session = self.connection_manager._get_session(
            self.profile, self.region, self.connection_manager.iam_role
        )

        assert boto_session.isinstance(mock_Session)
        mock_Session.assert_any_call(
            profile_name=None,
            region_name="eu-west-1",
            aws_access_key_id=ANY,
            aws_secret_access_key=ANY,
            aws_session_token=ANY,
        )

        boto_session.client().assume_role.assert_called_once_with(
            RoleArn=self.connection_manager.iam_role,
            RoleSessionName="{0}-session".format(
                self.connection_manager.iam_role.split("/")[-1]
            ),
        )

        credentials = boto_session.client().assume_role()["Credentials"]

        mock_Session.assert_any_call(
            region_name="eu-west-1",
            aws_access_key_id=credentials["AccessKeyId"],
            aws_secret_access_key=credentials["SecretAccessKey"],
            aws_session_token=credentials["SessionToken"],
        )

    @patch("sceptre.connection_manager.boto3.session.Session")
    def test_boto_session_with_iam_role_session_duration(self, mock_Session):
        self.connection_manager._boto_sessions = {}
        self.connection_manager.iam_role = "iam_role"
        self.connection_manager.iam_role_session_duration = 21600

        boto_session = self.connection_manager._get_session(
            self.profile, self.region, self.connection_manager.iam_role
        )

        boto_session.client().assume_role.assert_called_once_with(
            RoleArn=self.connection_manager.iam_role,
            RoleSessionName="{0}-session".format(
                self.connection_manager.iam_role.split("/")[-1]
            ),
            DurationSeconds=21600,
        )

    @patch("sceptre.connection_manager.boto3.session.Session")
    def test_boto_session_with_iam_role_returning_empty_credentials(self, mock_Session):
        self.connection_manager._boto_sessions = {}
        self.connection_manager.iam_role = "iam_role"

        mock_Session.return_value.get_credentials.side_effect = [
            MagicMock(),
            None,
            MagicMock(),
            MagicMock(),
            MagicMock(),
        ]

        with pytest.raises(InvalidAWSCredentialsError):
            self.connection_manager._get_session(
                self.profile, self.region, self.connection_manager.iam_role
            )

    @patch("sceptre.connection_manager.boto3.session.Session")
    def test_two_boto_sessions(self, mock_Session):
        self.connection_manager._boto_sessions = {
            "one": mock_Session,
            "two": mock_Session,
        }

        boto_session_1 = self.connection_manager._boto_sessions["one"]
        boto_session_2 = self.connection_manager._boto_sessions["two"]
        assert boto_session_1 == boto_session_2

    @patch("sceptre.connection_manager.boto3.session.Session.get_credentials")
    def test_get_client_with_no_pre_existing_clients(self, mock_get_credentials):
        service = "s3"
        region = "eu-west-1"
        profile = None
        iam_role = None
        stack = self.stack_name

        client = self.connection_manager._get_client(
            service, region, profile, stack, iam_role
        )
        expected_client = Session().client(service)
        assert str(type(client)) == str(type(expected_client))

    @patch("sceptre.connection_manager.boto3.session.Session.get_credentials")
    def test_get_client_with_invalid_client_type(self, mock_get_credentials):
        service = "invalid_type"
        region = "eu-west-1"
        iam_role = None
        profile = None
        stack = self.stack_name

        with pytest.raises(UnknownServiceError):
            self.connection_manager._get_client(
                service, region, profile, stack, iam_role
            )

    @patch("sceptre.connection_manager.boto3.session.Session.get_credentials")
    def test_get_client_with_exisiting_client(self, mock_get_credentials):
        service = "cloudformation"
        region = "eu-west-1"
        iam_role = None
        profile = None
        stack = self.stack_name

        client_1 = self.connection_manager._get_client(
            service, region, profile, stack, iam_role
        )
        client_2 = self.connection_manager._get_client(
            service, region, profile, stack, iam_role
        )
        assert client_1 == client_2

    @patch("sceptre.connection_manager.boto3.session.Session.get_credentials")
    def test_get_client_with_exisiting_client_and_profile_none(
        self, mock_get_credentials
    ):
        service = "cloudformation"
        region = "eu-west-1"
        iam_role = None
        profile = None
        stack = self.stack_name

        self.connection_manager.profile = None
        client_1 = self.connection_manager._get_client(
            service, region, profile, stack, iam_role
        )
        client_2 = self.connection_manager._get_client(
            service, region, profile, stack, iam_role
        )
        assert client_1 == client_2

    @mock_s3
    def test_call_with_valid_service_and_call(self):
        service = "s3"
        command = "list_buckets"

        return_value = self.connection_manager.call(service, command, {})
        assert return_value["ResponseMetadata"]["HTTPStatusCode"] == 200

    @mock_s3
    def test_call_with_valid_service_and_stack_name_call(self):
        service = "s3"
        command = "list_buckets"

        connection_manager = ConnectionManager(region=self.region, stack_name="stack")

        return_value = connection_manager.call(service, command, {}, stack_name="stack")
        assert return_value["ResponseMetadata"]["HTTPStatusCode"] == 200


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
