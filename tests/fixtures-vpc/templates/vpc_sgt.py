# -*- coding: utf-8 -*-

from troposphere import Template, Parameter, Ref, Output

from troposphere.ec2 import VPC, InternetGateway, VPCGatewayAttachment


class VpcTemplate(object):

    def __init__(self):
        self.template = Template()

        self.add_parameters()

        self.add_vpc()
        self.add_igw()

        self.add_outputs()

    def add_parameters(self):
        t = self.template

        self.cidr_block_param = t.add_parameter(Parameter(
            "CidrBlock",
            Type="String",
            Default="10.0.0.0/16",
        ))

    def add_vpc(self):
        t = self.template

        self.vpc = t.add_resource(VPC(
            "VirtualPrivateCloud",
            CidrBlock=Ref(self.cidr_block_param),
            InstanceTenancy="default",
            EnableDnsSupport=True,
            EnableDnsHostnames=True,
        ))

    def add_igw(self):
        t = self.template

        self.igw = t.add_resource(InternetGateway(
            "InternetGateway",
        ))

        t.add_resource(VPCGatewayAttachment(
            "IGWAttachment",
            VpcId=Ref(self.vpc),
            InternetGatewayId=Ref(self.igw),
        ))

    def add_outputs(self):
        t = self.template

        t.add_output(Output(
            "VpcId",
            Description="New VPC ID",
            Value=Ref(self.vpc)
        ))


def sceptre_handler(sceptre_user_data):
    vpc = VpcTemplate()
    return vpc.template.to_json()
