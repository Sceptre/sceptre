# -*- coding: utf-8 -*-

from troposphere import Template, Parameter, Ref, Output

from troposphere.ec2 import VPC, InternetGateway, VPCGatewayAttachment

t = Template()

cidr_block_param = t.add_parameter(Parameter(
    "CidrBlock",
    Type="String",
    Default="10.0.0.0/16",
))

vpc = t.add_resource(VPC(
    "VirtualPrivateCloud",
    CidrBlock=Ref(cidr_block_param),
    InstanceTenancy="default",
    EnableDnsSupport=True,
    EnableDnsHostnames=True,
))

igw = t.add_resource(InternetGateway(
    "InternetGateway",
))

igw_attachment = t.add_resource(VPCGatewayAttachment(
    "IGWAttachment",
    VpcId=Ref(vpc),
    InternetGatewayId=Ref(igw),
))

vpc_id_output = t.add_output(Output(
    "VpcId",
    Description="New VPC ID",
    Value=Ref(vpc)
))
