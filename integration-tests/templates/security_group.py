# -*- coding: utf-8 -*-

from troposphere import Template, Parameter, Ref, Output
from troposphere.ec2 import SecurityGroup, SecurityGroupRule


class SecurityGroupTemplate(object):

    def __init__(self):
        self.template = Template()

        self.add_parameters()
        self.add_security_group()
        self.add_outputs()

    def add_parameters(self):
        t = self.template
        self.whitelist_ip_param = t.add_parameter(Parameter(
            "WhitelistIpParam",
            Type="String"
        ))
        self.vpc_id_param = t.add_parameter(Parameter(
            "VpcId",
            Type="String",
        ))

    def add_security_group(self):
        t = self.template

        self.security_group = t.add_resource(SecurityGroup(
            "SecurityGroup",
            GroupDescription="Security Group",
            SecurityGroupIngress=[
                SecurityGroupRule(
                    IpProtocol="tcp",
                    FromPort="80",
                    ToPort="80",
                    CidrIp=Ref(self.whitelist_ip_param)
                )
            ],
            VpcId=Ref(self.vpc_id_param),
        ))

    def add_outputs(self):
        t = self.template

        t.add_output(Output(
            "SecurityGroupId",
            Description="Security Group Id",
            Value=Ref(self.security_group)
        ))


def sceptre_handler(sceptre_user_data):
    return SecurityGroupTemplate().template.to_json()
