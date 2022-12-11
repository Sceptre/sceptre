# -*- coding: utf-8 -*-

import pytest

from os.path import join, sep
from datetime import datetime

from sceptre.exceptions import PathConversionError
from sceptre.helpers import get_external_stack_name
from sceptre.helpers import normalise_path
from sceptre.helpers import sceptreise_path
from sceptre.helpers import get_response_datetime


class TestHelpers(object):

    def test_get_external_stack_name(self):
        result = get_external_stack_name("prj", "dev/ew1/jump-host")
        assert result == "prj-dev-ew1-jump-host"

    def test_normalise_path_with_valid_path(self):
        path = normalise_path("valid/path")
        assert path == join("valid", "path")

    def test_normalise_path_with_backslashes_in_path(self):
        path = normalise_path("valid\\path")
        assert path == join("valid", "path")

    def test_normalise_path_with_double_backslashes_in_path(self):
        path = normalise_path('valid\\path')
        assert path == join("valid", "path")

    def test_normalise_path_with_leading_slash(self):
        path = normalise_path("/this/is/valid")
        assert path == join("{}this".format(sep), "is", "valid")

    def test_normalise_path_with_leading_backslash(self):
        path = normalise_path('\\this\\path\\is\\valid')
        assert path == join("{}this".format(sep), "path", "is", "valid")

    def test_normalise_path_with_trailing_slash(self):
        with pytest.raises(PathConversionError):
            normalise_path(
                "this/path/is/invalid/"
            )

    def test_normalise_path_with_trailing_backslash(self):
        with pytest.raises(PathConversionError):
            normalise_path(
                'this\\path\\is\\invalid\\'
            )

    def test_sceptreise_path_with_valid_path(self):
        path = 'dev/app/stack'
        assert sceptreise_path(path) == path

    def test_sceptreise_path_with_windows_path(self):
        windows_path = 'dev\\app\\stack'
        assert sceptreise_path(windows_path) == 'dev/app/stack'

    def test_sceptreise_path_with_trailing_slash(self):
        with pytest.raises(PathConversionError):
            sceptreise_path(
                "this/path/is/invalid/"
            )

    def test_sceptreise_path_with_trailing_backslash(self):
        with pytest.raises(PathConversionError):
            sceptreise_path(
                'this\\path\\is\\invalid\\'
            )

    def test_get_response_datetime_valid(self):
        resp = {
            "ResponseMetadata": {
                "HTTPHeaders": {"date": "Wed, 16 Oct 2019 07:28:00 GMT"}
            }
        }
        assert get_response_datetime(resp) == datetime(2019, 10, 16, 7, 28)

    def test_get_response_datetime_invalid(self):
        resp = {
            "ResponseMetadata": {
                "HTTPHeaders": {"date": "garbage"}
            }
        }
        assert get_response_datetime(resp) is None

    def test_get_response_datetime_missing(self):
        assert get_response_datetime({}) is None

    def test_get_response_datetime_null(self):
        assert get_response_datetime(None) is None
