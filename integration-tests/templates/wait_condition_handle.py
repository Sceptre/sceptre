from troposphere import GetAtt, Output, Parameter, Ref, Template
from troposphere.cloudformation import WaitConditionHandle


class WaitConditionHandleTemplate(object):

    def __init__(self):
        self.template = Template()

        self.add_rule()

    def add_rule(self):
        t = self.template

        self.rule = t.add_resource(WaitConditionHandle(
            "WaitConditionHandle"
        ))


def sceptre_handler(sceptre_user_data):
    return WaitConditionHandleTemplate().template.to_json()
