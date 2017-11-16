# -*- coding: utf-8 -*-

from datetime import datetime
from dateutil import tz

import pytest
from mock import Mock, patch, sentinel
from moto import mock_s3
from freezegun import freeze_time

from boto3.session import Session
from botocore.exceptions import ClientError, UnknownServiceError

from sceptre.connection_manager import ConnectionManager, _retry_boto_call
from sceptre.exceptions import RetryLimitExceededError


class TestConnectionManager(object):

    def setup_method(self, test_method):
        self.iam_role = None
        self.profile = None
        self.region = "eu-west-1"

        self.connection_manager = ConnectionManager(
            region=self.region,
            iam_role=self.iam_role,
            profile=self.profile
        )

    def test_connection_manager_initialised_with_all_parameters(self):
        connection_manager = ConnectionManager(
            region=self.region,
            iam_role="role",
            profile="profile"
        )
        assert connection_manager.iam_role == "role"
        assert connection_manager.profile == "profile"
        assert connection_manager.region == self.region
        assert connection_manager._boto_session is None
        assert connection_manager.clients == {}

    def test_connection_manager_initialised_with_no_optional_parameters(self):
        connection_manager = ConnectionManager(region=sentinel.region)

        assert connection_manager.iam_role is None
        assert connection_manager.profile is None
        assert connection_manager.region == sentinel.region
        assert connection_manager._boto_session is None
        assert connection_manager.clients == {}

    def test_repr(self):
        self.connection_manager.iam_role = "role"
        self.connection_manager.profile = "profile"
        self.connection_manager.region = "region"
        response = self.connection_manager.__repr__()
        assert response == "sceptre.connection_manager.ConnectionManager(" \
            "region='region', iam_role='role', profile='profile')"

    def test_boto_session_with_cache(self):
        self.connection_manager._boto_session = sentinel.boto_session
        assert self.connection_manager.boto_session == sentinel.boto_session

    @patch("sceptre.connection_manager.boto3.session.Session")
    def test_boto_session_with_no_iam_role_and_no_profile(
            self, mock_Session
    ):
        self.connection_manager._boto_session = None
        self.connection_manager.iam_role = None
        self.connection_manager.profile = None

        boto_session = self.connection_manager.boto_session
        assert boto_session.isinstance(mock_Session)
        mock_Session.assert_called_once_with(
            region_name="eu-west-1",
            profile_name=None
        )

    @patch("sceptre.connection_manager.boto3.session.Session")
    def test_boto_session_with_no_iam_role_and_profile(self, mock_Session):
        self.connection_manager._boto_session = None
        self.connection_manager.iam_role = None
        self.connection_manager.profile = "profile"

        boto_session = self.connection_manager.boto_session
        assert boto_session.isinstance(mock_Session)
        mock_Session.assert_called_once_with(
            region_name="eu-west-1",
            profile_name="profile"
        )

    @patch("sceptre.connection_manager.boto3.session.Session")
    def test_boto_session_with_iam_role_and_no_profile(self, mock_Session):
        self.connection_manager._boto_session = None
        self.connection_manager.iam_role = "non-default"
        self.connection_manager.profile = None

        mock_credentials = {
            "Credentials": {
                "AccessKeyId": "id",
                "SecretAccessKey": "key",
                "SessionToken": "token",
                "Expiration": datetime(2020, 1, 1)
            }
        }

        mock_Session.return_value.client.return_value.\
            assume_role.return_value = mock_credentials

        boto_session = self.connection_manager.boto_session
        assert boto_session.isinstance(mock_Session)

        mock_Session.assert_any_call(
            profile_name=None,
            region_name=self.region
        )
        mock_Session.assert_any_call(
            aws_access_key_id="id",
            aws_secret_access_key="key",
            aws_session_token="token",
            region_name=self.region
        )

    @patch("sceptre.connection_manager.boto3.session.Session")
    def test_boto_session_with_iam_role_and_profile(self, mock_Session):
        self.connection_manager._boto_session = None
        self.connection_manager.iam_role = "non-default"
        self.connection_manager.profile = "profile"

        mock_credentials = {
            "Credentials": {
                "AccessKeyId": "id",
                "SecretAccessKey": "key",
                "SessionToken": "token",
                "Expiration": datetime(2020, 1, 1)
            }
        }

        mock_Session.return_value.client.return_value. \
            assume_role.return_value = mock_credentials

        boto_session = self.connection_manager.boto_session
        assert boto_session.isinstance(mock_Session)

        mock_Session.assert_any_call(
            profile_name="profile",
            region_name=self.region
        )
        mock_Session.assert_any_call(
            aws_access_key_id="id",
            aws_secret_access_key="key",
            aws_session_token="token",
            region_name=self.region
        )

    @patch("sceptre.connection_manager.boto3.session.Session")
    def test_two_boto_sessions(self, mock_Session):
        self.connection_manager._boto_session = None
        boto_session_1 = self.connection_manager.boto_session
        boto_session_2 = self.connection_manager.boto_session
        assert boto_session_1 == boto_session_2

    @patch("sceptre.connection_manager.boto3.session.Session.get_credentials")
    def test_get_client_with_no_pre_existing_clients(
        self, mock_get_credentials
    ):
        service = "s3"

        client = self.connection_manager._get_client(service)
        expected_client = Session().client(service)
        assert str(type(client)) == str(type(expected_client))

    @patch("sceptre.connection_manager.boto3.session.Session.get_credentials")
    def test_get_client_with_invalid_client_type(self, mock_get_credentials):
        service = "invalid_type"
        with pytest.raises(UnknownServiceError):
            self.connection_manager._get_client(service)

    @patch("sceptre.connection_manager.boto3.session.Session.get_credentials")
    def test_get_client_with_exisiting_client(self, mock_get_credentials):
        service = "cloudformation"
        client_1 = self.connection_manager._get_client(service)
        client_2 = self.connection_manager._get_client(service)
        assert client_1 == client_2

    @patch("sceptre.connection_manager.boto3.session.Session.get_credentials")
    def test_get_client_with_exisiting_client_and_iam_role_none(
            self, mock_get_credentials
    ):
        service = "cloudformation"
        self.connection_manager._iam_role = None
        client_1 = self.connection_manager._get_client(service)
        client_2 = self.connection_manager._get_client(service)
        assert client_1 == client_2

    def test_clear_session_cache_if_expired_with_no_iam_role(self):
        self.connection_manager.iam_role = None
        self.connection_manager._boto_session_expiration = sentinel.expiration
        self.connection_manager.clients = sentinel.clients
        self.connection_manager._boto_session = sentinel.boto_session
        self.connection_manager._clear_session_cache_if_expired()
        assert self.connection_manager.clients == sentinel.clients
        assert self.connection_manager._boto_session == sentinel.boto_session

    @freeze_time("2000-01-30")
    def test_clear_session_cache_if_expired_with_future_date(self):
        self.connection_manager.iam_role = "iam_role"
        future_date = datetime(2015, 1, 30, tzinfo=tz.tzutc())
        self.connection_manager._boto_session_expiration = future_date
        self.connection_manager.clients = sentinel.clients
        self.connection_manager._boto_session = sentinel.boto_session
        self.connection_manager._clear_session_cache_if_expired()
        assert self.connection_manager.clients == sentinel.clients
        assert self.connection_manager._boto_session == sentinel.boto_session

    @freeze_time("2015-01-30")
    def test_clear_session_cache_if_expired_with_expired_date(self):
        self.connection_manager.iam_role = "iam_role"
        past_date = datetime(2000, 1, 30, tzinfo=tz.tzutc())
        self.connection_manager._boto_session_expiration = past_date

        self.connection_manager.clients = sentinel.clients
        self.connection_manager._boto_session = sentinel.boto_session

        self.connection_manager._clear_session_cache_if_expired()
        assert self.connection_manager.clients == {}
        assert self.connection_manager._boto_session is None

    @mock_s3
    def test_call_with_valid_service_and_call(self):
        service = 's3'
        command = 'list_buckets'

        return_value = self.connection_manager.call(service, command, {})
        assert return_value['ResponseMetadata']['HTTPStatusCode'] == 200


class TestRetry():

    def test_retry_boto_call_returns_response_correctly(self):
        def func(*args, **kwargs):
            return sentinel.response

        response = _retry_boto_call(func)()

        assert response == sentinel.response

    @patch("sceptre.connection_manager.time.sleep")
    def test_retry_boto_call_pauses_when_request_limit_hit(
            self, mock_sleep
    ):
        mock_func = Mock()
        mock_func.side_effect = [
            ClientError(
                {
                    "Error": {
                        "Code": "Throttling",
                        "Message": "Request limit hit"
                    }
                },
                sentinel.operation
            ),
            sentinel.response
        ]
        # The attribute function.__name__ is required by the decorator @wraps.
        mock_func.__name__ = "mock_func"

        _retry_boto_call(mock_func)()
        mock_sleep.assert_called_once_with(1)

    def test_retry_boto_call_raises_non_throttling_error(self):
        mock_func = Mock()
        mock_func.side_effect = ClientError(
            {
                "Error": {
                    "Code": 500,
                    "Message": "Boom!"
                }
            },
            sentinel.operation
        )
        # The attribute function.__name__ is required by the decorator @wraps.
        mock_func.__name__ = "mock_func"

        with pytest.raises(ClientError) as e:
            _retry_boto_call(mock_func)()
        assert e.value.response["Error"]["Code"] == 500
        assert e.value.response["Error"]["Message"] == "Boom!"

    @patch("sceptre.connection_manager.time.sleep")
    def test_retry_boto_call_raises_retry_limit_exceeded_exception(
            self, mock_sleep
    ):
        mock_func = Mock()
        mock_func.side_effect = ClientError(
            {
                "Error": {
                    "Code": "Throttling",
                    "Message": "Request limit hit"
                }
            },
            sentinel.operation
        )
        # The attribute function.__name__ is required by the decorator @wraps.
        mock_func.__name__ = "mock_func"

        with pytest.raises(RetryLimitExceededError):
            _retry_boto_call(mock_func)()
