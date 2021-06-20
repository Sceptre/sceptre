{
  Resources: {
    VPC: {
      Type: 'AWS::EC2::VPC',
      Properties: {
        EnableDnsHostnames: true,
        CidrBlock: '10.0.0.0/16',
      },
    },
  },
  Outputs: {
    VpcId: {
      Value: {
        Ref: 'VPC',
      },
    },
  },
}
