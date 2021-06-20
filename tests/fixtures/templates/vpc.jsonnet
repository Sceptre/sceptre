function(StackParameters, SceptreUserData) {
  Parameters: {
    CidrBlock: {
      Default: '10.0.0.0/16',
      Type: 'String',
    },
  },
  Resources: {
    VPC: {
      Type: 'AWS::EC2::VPC',
      Properties: {
        EnableDnsHostnames: StackParameters.EnableDnsHostnames,
        CidrBlock: SceptreUserData.VpcId,
        Tags: StackParameters.Tags,
      },
      AdditionalProperties: StackParameters.AdditionalProperties,
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
