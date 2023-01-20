# -*- coding: utf-8 -*-

import pytest

from os.path import join, sep
from datetime import datetime, timezone, timedelta

from sceptre.exceptions import PathConversionError
from sceptre.helpers import get_external_stack_name
from sceptre.helpers import normalise_path
from sceptre.helpers import sceptreise_path
from sceptre.helpers import extract_datetime_from_aws_response_headers, gen_repr


class SomeClass(object):
    def __init__(self, str_attr: str, int_attr: int):
        self.str_attr = str_attr
        self.int_attr = int_attr


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
        path = normalise_path("valid\\path")
        assert path == join("valid", "path")

    def test_normalise_path_with_leading_slash(self):
        path = normalise_path("/this/is/valid")
        assert path == join("{}this".format(sep), "is", "valid")

    def test_normalise_path_with_leading_backslash(self):
        path = normalise_path("\\this\\path\\is\\valid")
        assert path == join("{}this".format(sep), "path", "is", "valid")

    def test_normalise_path_with_trailing_slash(self):
        with pytest.raises(PathConversionError):
            normalise_path("this/path/is/invalid/")

    def test_normalise_path_with_trailing_backslash(self):
        with pytest.raises(PathConversionError):
            normalise_path("this\\path\\is\\invalid\\")

    def test_sceptreise_path_with_valid_path(self):
        path = "dev/app/stack"
        assert sceptreise_path(path) == path

    def test_sceptreise_path_with_windows_path(self):
        windows_path = "dev\\app\\stack"
        assert sceptreise_path(windows_path) == "dev/app/stack"

    def test_sceptreise_path_with_trailing_slash(self):
        with pytest.raises(PathConversionError):
            sceptreise_path("this/path/is/invalid/")

    def test_sceptreise_path_with_trailing_backslash(self):
        with pytest.raises(PathConversionError):
            sceptreise_path("this\\path\\is\\invalid\\")

    def test_get_response_datetime__response_is_valid__returns_datetime(self):
        resp = {
            "ResponseMetadata": {
                "HTTPHeaders": {"date": "Wed, 16 Oct 2019 07:28:00 GMT"}
            }
        }
        assert extract_datetime_from_aws_response_headers(resp) == datetime(
            2019, 10, 16, 7, 28, tzinfo=timezone.utc
        )

    def test_get_response_datetime__response_has_offset__returns_datetime(self):
        resp = {
            "ResponseMetadata": {
                "HTTPHeaders": {"date": "Wed, 16 Oct 2019 07:28:00 +0400"}
            }
        }
        offset = timezone(timedelta(hours=4))
        assert extract_datetime_from_aws_response_headers(resp) == datetime(
            2019, 10, 16, 7, 28, tzinfo=offset
        )

    def test_get_response_datetime__date_string_is_invalid__returns_none(self):
        resp = {"ResponseMetadata": {"HTTPHeaders": {"date": "garbage"}}}
        assert extract_datetime_from_aws_response_headers(resp) is None

    def test_get_response_datetime__response_is_empty__returns_none(self):
        assert extract_datetime_from_aws_response_headers({}) is None

    def test_get_response_datetime__response_is_none__returns_none(self):
        assert extract_datetime_from_aws_response_headers(None) is None

    def test_repr__one_attr__no_commas(self):
        i = SomeClass("a", 2)
        assert gen_repr(i, attributes=["str_attr"]) == "SomeClass(str_attr='a')"

    def test_repr__two_attrs__correct_order(self):
        i = SomeClass("b", 6)
        assert (
            gen_repr(i, attributes=["int_attr", "str_attr"])
            == "SomeClass(int_attr=6, str_attr='b')"
        )

    def test_repr__override_label__correct_name(self):
        i = SomeClass("q", 123)
        assert gen_repr(i, class_label="My.Class") == "My.Class()"
