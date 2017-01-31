# -*- coding: utf-8 -*-

from troposphere import Template, Ref, Output

from troposphere.ec2 import VPC, InternetGateway, VPCGatewayAttachment


def sceptre_handler(sceptre_user_data):

    t = Template()

    vpc = t.add_resource(VPC(
        "VirtualPrivateCloud",
        CidrBlock=sceptre_user_data["cidr_block"],
        InstanceTenancy="default",
        EnableDnsSupport=True,
        EnableDnsHostnames=True,
    ))

    igw = t.add_resource(InternetGateway(
        "InternetGateway",
    ))

    t.add_resource(VPCGatewayAttachment(
        "IGWAttachment",
        VpcId=Ref(vpc),
        InternetGatewayId=Ref(igw),
    ))

    t.add_output(Output(
        "VpcId",
        Description="New VPC ID",
        Value=Ref(vpc)
    ))

    return t.to_json()
