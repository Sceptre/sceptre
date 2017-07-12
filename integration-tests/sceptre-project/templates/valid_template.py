import json


def sceptre_handler(scepter_user_data):
    template = {
      "Resources": {
        "WaitConditionHandle": {
          "Type": "AWS::CloudFormation::WaitConditionHandle",
          "Properties": {}
        }
      }
    }
    return json.dumps(template)
