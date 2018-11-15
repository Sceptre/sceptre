# -*- coding: utf-8 -*-

from sceptre.helpers import get_external_stack_name


class TestHelpers(object):

    def test_get_external_stack_name(self):
        result = get_external_stack_name("prj", "dev/ew1/jump-host")
        assert result == "prj-dev-ew1-jump-host"
