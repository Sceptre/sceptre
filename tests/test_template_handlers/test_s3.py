# -*- coding: utf-8 -*-
import io

import pytest
from mock import MagicMock

from sceptre.connection_manager import ConnectionManager
from sceptre.exceptions import SceptreException
from sceptre.template_handlers.s3 import S3


class TestS3(object):

    def test_template_handler(self):
        connection_manager = MagicMock(spec=ConnectionManager)
        connection_manager.call.return_value = {
            "Body": io.BytesIO(b"Stuff is working")
        }
        template_handler = S3(
            name="vpc",
            arguments={"path": "my-fancy-bucket/account/vpc.yaml"},
            connection_manager=connection_manager
        )
        result = template_handler.handle()

        connection_manager.call.assert_called_once_with(
            service="s3",
            command="get_object",
            kwargs={
                "Bucket": "my-fancy-bucket",
                "Key": "account/vpc.yaml"
            }
        )
        assert result == b"Stuff is working"

    def test_invalid_response_reraises_exception(self):
        connection_manager = MagicMock(spec=ConnectionManager)
        connection_manager.call.side_effect = SceptreException("BOOM!")

        template_handler = S3(
            name="vpc",
            arguments={"path": "my-fancy-bucket/account/vpc.yaml"},
            connection_manager=connection_manager
        )

        with pytest.raises(SceptreException) as e:
            template_handler.handle()

        assert str(e.value) == "BOOM!"
