function(StackParameters, SceptreUserData)
  {
    Parameters: {
      Input: {
        Type: 'String',
      },
    },
    Resources: {
      WaitConditionHandle: {
        Type: 'AWS::CloudFormation::WaitConditionHandle',
        Properties: {
            Input: StackParameters.Input
        },
      },
    },
    Outputs: {
      Output: {
        Value: {
          Ref: 'Input',
        },
      },
    },
  }
