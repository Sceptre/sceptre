# -*- coding: utf-8 -*-
import pytest
from mock import Mock, patch, sentinel, MagicMock
from moto import mock_s3

import sceptre.connection_manager
from sceptre.connection_manager import ConnectionManager
from boto3.session import Session
import botocore


def test_connection_manager_returns_ConnectionManager(fixtures_dir):
    cm = sceptre.connection_manager.connection_manager(
        fixtures_dir, "account/environment/region"
    )
    assert type(cm) == ConnectionManager


def test_connection_manager_memoizes(fixtures_dir):
    cm_a = sceptre.connection_manager.connection_manager(
        fixtures_dir, "account/environment/region"
    )
    cm_b = sceptre.connection_manager.connection_manager(
        fixtures_dir, "account/environment/region"
    )
    assert id(cm_a) == id(cm_b)


class TestConnectionManager(object):

    def setup_method(self, test_method):
        self.iam_role = None
        self.region = "eu-west-1"

        self.connection_manager = ConnectionManager(
            region=self.region, iam_role=self.iam_role
        )

    def test_connection_manager_initialised_with_all_parameters(self):
        connection_manager = ConnectionManager(
            region=self.region, iam_role=self.iam_role
        )
        assert connection_manager.iam_role == self.iam_role
        assert connection_manager.region == self.region
        assert connection_manager._boto_session is None
        assert connection_manager.clients == {}

    def test_connection_manager_initialised_with_no_optional_parameters(self):
        connection_manager = ConnectionManager(region=sentinel.region)

        assert connection_manager.iam_role is None
        assert connection_manager.region == sentinel.region
        assert connection_manager._boto_session is None
        assert connection_manager.clients == {}

    def test_repr(self):
        self.connection_manager.iam_role = "role"
        self.connection_manager.region = "region"
        response = self.connection_manager.__repr__()
        assert response == "sceptre.connection_manager.ConnectionManager(" \
            "region='region', iam_role='role')"

    def test_boto_session_with_cache(self):
        self.connection_manager._boto_session = sentinel.boto_session
        assert self.connection_manager.boto_session == sentinel.boto_session

    @patch("sceptre.connection_manager.boto3.session.Session")
    def test_boto_session_with_no_iam_role_and_no_cache(self, mock_Session):
        mock_Session = MagicMock(name='Session', return_value=sentinel.session)
        mock_Session.get_credentials.access_key.return_value = \
            sentinel.access_key
        mock_Session.get_credentials.secret_key.return_value = \
            sentinel.secret_key
        mock_Session.get_credentials.method.return_value = \
            sentinel.method

        self.connection_manager._boto_session = None
        self.connection_manager.iam_role = None

        boto_session = self.connection_manager.boto_session
        assert boto_session.isinstance(mock_Session(
            region_name="eu-west-1"
        ))
        mock_Session.assert_called_once_with(
            region_name="eu-west-1"
        )

    @patch("sceptre.connection_manager.boto3.session.Session")
    @patch("sceptre.connection_manager.boto3.client")
    def test_boto_session_with_iam_role_and_no_cache(
            self, mock_client, mock_Session
    ):
        mock_Session.return_value = sentinel.session
        self.connection_manager.iam_role = "non-default"
        mock_credentials = {
            "Credentials": {
                "AccessKeyId": "id",
                "SecretAccessKey": "key",
                "SessionToken": "token"
            }
        }
        mock_sts_client = Mock()
        mock_sts_client.assume_role.return_value = mock_credentials
        mock_client.return_value = mock_sts_client

        boto_session = self.connection_manager.boto_session

        assert boto_session == sentinel.session
        mock_Session.assert_called_once_with(
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
        with pytest.raises(botocore.exceptions.UnknownServiceError):
            self.connection_manager._get_client(service)

    @patch("sceptre.connection_manager.boto3.session.Session.get_credentials")
    def test_get_client_with_exisiting_client(self, mock_get_credentials):
        service = "cloudformation"
        client_1 = self.connection_manager._get_client(service)
        client_2 = self.connection_manager._get_client(service)
        assert client_1 == client_2

    @mock_s3
    def test_call_with_valid_service_and_call(self):
        service = 's3'
        command = 'list_buckets'

        return_value = self.connection_manager.call(service, command, {})
        assert return_value['ResponseMetadata']['HTTPStatusCode'] == 200
