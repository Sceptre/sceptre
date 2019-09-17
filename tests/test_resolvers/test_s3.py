# -*- coding: utf-8 -*-
import io

import pytest
from mock import MagicMock

from sceptre.connection_manager import ConnectionManager
from sceptre.exceptions import SceptreException
from sceptre.resolvers.s3 import S3
from sceptre.stack import Stack


class TestS3Resolver(object):

    def test_resolver(self):
        stack = MagicMock(spec=Stack)
        stack.dependencies = []
        stack.project_code = "project-code"

        stack._connection_manager = MagicMock(spec=ConnectionManager)
        stack.connection_manager.call.return_value = {
            "Body": io.BytesIO(b"Stuff is working")
        }

        s3_resolver = S3(
            "my-fancy-bucket/account/vpc.yaml", stack
        )
        s3_resolver.setup()

        result = s3_resolver.resolve()

        stack.connection_manager.call.assert_called_once_with(
            service="s3",
            command="get_object",
            kwargs={
                "Bucket": "my-fancy-bucket",
                "Key": "account/vpc.yaml"
            }
        )
        assert result == b"Stuff is working"

    def test_invalid_response_reraises_exception(self):
        stack = MagicMock(spec=Stack)
        stack.dependencies = []
        stack.project_code = "project-code"

        stack._connection_manager = MagicMock(spec=ConnectionManager)
        stack.connection_manager.call.side_effect = SceptreException("BOOM!")

        s3_resolver = S3(
            "my-fancy-bucket/account/vpc.yaml", stack
        )
        s3_resolver.setup()

        with pytest.raises(SceptreException) as e:
            s3_resolver.resolve()

        assert str(e.value) == "BOOM!"
