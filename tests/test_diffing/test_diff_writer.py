class TestDiffWriter:

    def test_write__no_difference__writes_no_difference(self):
        assert False

    def test_write__new_stack__writes_new_stack_config_and_template(self):
        assert False

    def test_write__only_config_is_different__writes_config_difference(self):
        assert False

    def test_write__only_template_is_different__writes_template_difference(self):
        assert False

    def test_write__config_and_template_are_different__writes_both_differences(self):
        assert False


class TestDeepDiffWriter:
    def test_has_config_difference__config_difference_is_present__returns_true(self):
        assert False

    def test_has_config_difference__config_difference_is_absent__returns_false(self):
        assert False

    def test_has_template_difference__template_difference_is_present__returns_true(self):
        assert False

    def test_has_template_difference__template_difference_is_absent__returns_false(self):
        assert False

    def test_dump_diff__output_format_is_json__outputs_to_json(self):
        assert False

    def test_dump_diff__output_format_is_yaml__outputs_to_yaml(self):
        assert False

    def test_dump_diff__output_format_is_text__outputs_to_yaml(self):
        assert False


class TestDiffLibWriter:
    def test_has_config_difference__config_difference_is_present__returns_true(self):
        assert False

    def test_has_config_difference__config_difference_is_absent__returns_false(self):
        assert False

    def test_has_template_difference__template_difference_is_present__returns_true(self):
        assert False

    def test_has_template_difference__template_difference_is_absent__returns_false(self):
        assert False

    def test_dump_diff__returns_joined_list(self):
        assert False
