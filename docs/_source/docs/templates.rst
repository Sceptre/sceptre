Templates
=========

Sceptre uses CloudFormation Templates to launch AWS Stacks. Templates must be
stored in a directory named ``templates/``, in the same directory as the
``config/`` directory:

.. code-block:: text

   .
   ├── config
   │   └── dev
   │       ├── config.yaml
   │       └── vpc.yaml
   └── templates
       └── vpc.py

CloudFormation
--------------

Templates with ``.json`` or ``.yaml`` extensions are treated as CloudFormation
Templates. They are read in and used without modification.

Jinja
-----

Templates with ``.j2`` extensions are treated as Jinja2 Templates.
These are rendered and should create a raw JSON or YAML CloudFormation
Template. Sceptre User Data is accessible within Templates as
``sceptre_user_data``. For example ``{{ sceptre_user_data.some_variable }}``.
``sceptre_user_data`` accesses the ``sceptre_user_data`` key in the Stack
Config file.


Example
~~~~~~~

While rendering templates with Jinja2, some characters aren't supported by AWS. A workaround for this is to use Jinja to replace `-`, `.` and `_` with other characters to ensure that we produce a valid template. With this we had some plasticity to the template and it becomes easier to add/remove entries on a particular stack.

With this templating some problems will arise, such empty strings as parameters. In the following example you can find a work around for this issues.

This represents a stack to deploy route53 records, it's only showing CNAME and ALIAS records to not get too large.

Stack:

.. code-block:: yaml

    template
      path: templates/dns-extras.j2
      type: file
    dependencies:
    - prod/route53/domain-zone.yaml
    parameters:
      DomainName: "example.com"!stack_output prod/route53/example-com-zone.yaml::FullDomainName
      Zone: !stack_output prod/route53/example-com-zone.yaml::HostedZoneID
    sceptre_user_data:
      CNAMErecords:
        - record: "example01"
          address: "example01.otherdomain.com."
          ttl: 600
        - record: "example02"
          address: "example01.otherdomain.com."
          ttl: 600
      ALIASrecords:
        - record: ""
          hostedzoneid: "ZYOURZONEIDDDD"
          dnsnamealias: "ELB07-Sites-000000000.us-east-1.elb.amazonaws.com"
          ttl: 600
        - record: "www"
          hostedzoneid: "Z32O12XQLNTSW2"
          dnsnamealias: "ELB07-Sit es-000000000.us-east-1.elb.amazonaws.com"
          ttl: 600


Template `dns-extras.j2`:

.. code-block:: jinja

    AWSTemplateFormatVersion: '2010-09-09'
    Description: 'Add Route53 - CNAME and ALIAS records'
    Parameters:
      DomainName:
        Type: String
        Default: example.net
      Zone:
        Type: String
      {% if sceptre_user_data.CNAMErecords is defined %}{% for rule in sceptre_user_data.CNAMErecords %}
      {{ rule.record |replace("-","d")|replace("_","s")|replace('.',"p")}}cnamerecord:
        Type: String
        Default: "{{rule.record}}"{% endfor %}{% endif %}
      {% if sceptre_user_data.ALIASrecords is defined %}{% for rule in sceptre_user_data.ALIASrecords %}
      {{ rule.record |replace("-","d")|replace("_","s")|replace('.',"p")}}aliasrecord:
        Type: String
        Default: "{{rule.record}}"
      {{ rule.record |replace("-","d")|replace("_","s")|replace('.',"p")}}aliasvalue:
        Type: String
        Default: "{{rule.dnsnamealias}}"
      {{ rule.record |replace("-","d")|replace("_","s")|replace('.',"p")}}aliaszoneid:
        Type: String
        Default: "{{rule.hostedzoneid}}"
      {% endfor %}{% endif %}
    Resources:
    {% if sceptre_user_data.CNAMErecords is defined %}{% for rule in sceptre_user_data.CNAMErecords %}add{{ rule.record |    replace("-","d")|replace("_","s")|replace('.',"p")}}cnamerecord:
        {% set record = rule.record %}
        Type: 'AWS::Route53::RecordSet'
        Properties:
          Name: !Join
            - ""
            - [ !Sub '${ {{ rule.record |replace("-","d")|replace("_","s")|replace('.',"p")}}cnamerecord }','.', !Ref DomainName, '.']
          HostedZoneId: !Sub '${Zone}'
          Type: CNAME
          TTL: {{ rule.ttl }}
          ResourceRecords:
            - {{ rule.address }}
      {% endfor %}{% endif %}
        {% if sceptre_user_data.ALIASrecords is defined %}{% for rule in sceptre_user_data.ALIASrecords %}
      {% set entry = rule.record |replace("-","d")|replace("_","s")|replace('.',"p")%}add{{entry}}aliasrecord:
        Type: AWS::Route53::RecordSet
        Properties:
          {% if rule.record == "" %}
          Name: !Ref DomainName
          {% else %}
          Name: !Join
            - ""
            - [ !Sub '${ {{ rule.record |replace("-","d")|replace("_","s")|replace('.',"p")}}aliasrecord }','.', !Ref DomainName, '.']
          {% endif %}
          Type: A
          HostedZoneId: !Ref Zone
          AliasTarget:
            DNSName: "{{ rule.dnsnamealias }}"
            HostedZoneId: "{{ rule.hostedzoneid }}"
      {% endfor %}{% endif %}
    Outputs:
      {% if sceptre_user_data.CNAMErecords is defined %}{% for rule in sceptre_user_data.CNAMErecords %}add{{ rule.record |    replace("-","d")|replace("_","s")|replace('.',"p")}}cnamerecord:
        Value: !Ref 'add{{ rule.record |replace("-","d")|replace("_","s")|replace('.',"p")}}cnamerecord'
        Description: '{{ rule.address }}'
      {% endfor %}{% endif %}
      {% if sceptre_user_data.ALIASrecords is defined %}{% for rule in sceptre_user_data.ALIASrecords %}add{{ rule.record |    replace("-","d")|replace("_","s")|replace('.',"p")}}aliasrecord:
        Value: !Ref 'add{{ rule.record |replace("-","d")|replace("_","s")|replace('.',"p")}}aliasrecord'
        Description: '{{ rule.dnsnamealias }}'
      {% endfor %}{% endif %}
      StackName:
        Description: 'Stack name.'
        Value: !Sub '${AWS::StackName}'
        Export:
          Name: !Sub '${AWS::StackName}'


Python
------

Templates with a ``.py`` extension are treated as Python Templates. They should
implement a function named ``sceptre_handler(sceptre_user_data)`` which returns
the CloudFormation Template as a ``string``. Sceptre User Data is passed to
this function as an argument. If Sceptre User Data is not defined in the Stack
Config file, Sceptre passes an empty ``dict``.

Example
~~~~~~~

Troposphere
^^^^^^^^^^^

This example is using `troposphere`_
to generate CloudFormation Template as a `json` string.

.. code-block:: python

    from troposphere import Template
    from troposphere.ec2 import VPC

    def vpc(sceptre_user_data):
        """AWS VPC CloudFormationTemplate"""
        template = Template()
        template.add_resource(VPC(
                "VirtualPrivateCloud",
                CidrBlock=sceptre_user_data["cidr_block"]
            ))
        return template.to_yaml()

    def sceptre_handler(sceptre_user_data):
        return vpc(sceptre_user_data)

.. note::
  To generate templates using Troposphere you must install the
  Troposphere library by running ``pip install sceptre[troposphere]``

.. _troposphere: https://github.com/cloudtools/troposphere/

AWS CDK
^^^^^^^

This example generates a cloudformation template from `AWS CDK`_ code.

Stack `dev/S3CdkStack.yaml`:

.. code-block:: yaml

  template_path: templates/S3Cdk.py
  sceptre_user_data:
    bucket_name: my-bucket
    aws_profile: {{ var.profile }} 

..

Template `templates/S3Cdk.py`:

.. code-block:: python

  import yaml
  import aws_cdk
  import subprocess
  import os
  from constructs import Construct
  from sceptre import exceptions
 
  class CdkStack(aws_cdk.Stack):
      '''
      Stack to perform the following:
  
      - Create an S3 Bucket
      - Deploy an 'object-key.txt' file to the bucket
  
      Notes:
      - 'sceptre_user_data' must contain the following keys:
          - 'bucket_name' - The name for the S3 Bucket
          - 'aws_profile' - The name of the AWS profile used for publishing the CDK assets
      '''
  
      def __init__(self, scope: Construct, construct_id: str, sceptre_user_data, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
  
        bucket_name = sceptre_user_data['bucket_name']
        s3_bucket = aws_cdk.aws_s3.Bucket(self, 'S3Bucket',
                                          bucket_name=bucket_name)
  
        aws_cdk.aws_s3_deployment.BucketDeployment(self,
                                                   'S3Deployment',
                                                   sources=[aws_cdk.aws_s3_deployment.Source.data(
                                                     'object-key.txt', 'hello, world!')],
                                                   destination_bucket=s3_bucket)
  
  def sceptre_handler(sceptre_user_data: dict) -> str:

    # Synthesize App
    app = aws_cdk.App()
    stack_name = 'CDKStack'
    CdkStack(app, stack_name, sceptre_user_data)
    app_synth = app.synth()

    # Publish CDK Assets
    asset_artifacts = None

    for artifacts in app_synth.artifacts:
      if isinstance(artifacts, aws_cdk.cx_api.AssetManifestArtifact):
        asset_artifacts = artifacts
        break
    if asset_artifacts is None:
      raise exceptions.SceptreException('Asset manifest artifact not found')

    # https://github.com/aws/aws-cdk/tree/main/packages/cdk-assets
    os.environ['AWS_PROFILE'] = sceptre_user_data['AwsProfile']
    cdk_assets_result = subprocess.run(f'npx cdk-assets publish --path {asset_artifacts.file}', shell=True)
    cdk_assets_result.check_returncode()

    # Return synthesized template
    template = app_synth.get_stack_by_name(stack_name).template
    return yaml.safe_dump(template)

.. _AWS_CDK: https://github.com/aws/aws-cdk


Generate cloudformation:

``sceptre generate dev/S3CdkStack.yaml``

.. code-block:: yaml

  Parameters:
    BootstrapVersion:
      Default: /cdk-bootstrap/hnb659fds/version
      Description: Version of the CDK Bootstrap resources in this environment, automatically
        retrieved from SSM Parameter Store. [cdk:skip]
      Type: AWS::SSM::Parameter::Value<String>
  Resources:
    CustomCDKBucketDeployment8693BB64968944B69AAFB0CC9EB8756C81C01536:
      DependsOn:
      - CustomCDKBucketDeployment8693BB64968944B69AAFB0CC9EB8756CServiceRoleDefaultPolicy88902FDF
      - CustomCDKBucketDeployment8693BB64968944B69AAFB0CC9EB8756CServiceRole89A01265
      Properties:
        Code:
          S3Bucket:
            Fn::Sub: cdk-hnb659fds-assets-${AWS::AccountId}-${AWS::Region}
          S3Key: 2bc265c5e0569aeb24a6349c15bd54e76e845892376515e036627ab0cc70bb64.zip
        Handler: index.handler
        Layers:
        - Ref: S3DeploymentAwsCliLayer8AAFE44F
        Role:
          Fn::GetAtt:
          - CustomCDKBucketDeployment8693BB64968944B69AAFB0CC9EB8756CServiceRole89A01265
          - Arn
        Runtime: python3.9
        Timeout: 900
      Type: AWS::Lambda::Function
    CustomCDKBucketDeployment8693BB64968944B69AAFB0CC9EB8756CServiceRole89A01265:
      Properties:
        AssumeRolePolicyDocument:
          Statement:
          - Action: sts:AssumeRole
            Effect: Allow
          Principal:
              Service: lambda.amazonaws.com
          Version: '2012-10-17'
        ManagedPolicyArns:
        - Fn::Join:
          - ''
          - - 'arn:'
            - Ref: AWS::Partition
            - :iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
      Type: AWS::IAM::Role
    CustomCDKBucketDeployment8693BB64968944B69AAFB0CC9EB8756CServiceRoleDefaultPolicy88902FDF:
      Properties:
        PolicyDocument:
          Statement:
          - Action:
            - s3:GetObject*
            - s3:GetBucket*
            - s3:List*
            Effect: Allow
            Resource:
            - Fn::Join:
              - ''
              - - 'arn:'
                - Ref: AWS::Partition
                - ':s3:::'
                - Fn::Sub: cdk-hnb659fds-assets-${AWS::AccountId}-${AWS::Region}
            - Fn::Join:
              - ''
              - - 'arn:'
                - Ref: AWS::Partition
                - ':s3:::'
                - Fn::Sub: cdk-hnb659fds-assets-${AWS::AccountId}-${AWS::Region}
                - /*
          - Action:
            - s3:GetObject*
            - s3:GetBucket*
            - s3:List*
            - s3:DeleteObject*
            - s3:PutObject
            - s3:PutObjectLegalHold
            - s3:PutObjectRetention
            - s3:PutObjectTagging
            - s3:PutObjectVersionTagging
            - s3:Abort*
            Effect: Allow
            Resource:
            - Fn::GetAtt:
              - S3Bucket07682993
              - Arn
            - Fn::Join:
              - ''
              - - Fn::GetAtt:
                  - S3Bucket07682993
                  - Arn
                - /*
          Version: '2012-10-17'
        PolicyName: CustomCDKBucketDeployment8693BB64968944B69AAFB0CC9EB8756CServiceRoleDefaultPolicy88902FDF
        Roles:
        - Ref: CustomCDKBucketDeployment8693BB64968944B69AAFB0CC9EB8756CServiceRole89A01265
      Type: AWS::IAM::Policy
    S3Bucket07682993:
      DeletionPolicy: Retain
      Properties:
        BucketName: my-bucket
        Tags:
        - Key: aws-cdk:cr-owned:d7218acd
          Value: 'true'
      Type: AWS::S3::Bucket
      UpdateReplacePolicy: Retain
    S3DeploymentAwsCliLayer8AAFE44F:
      Properties:
        Content:
          S3Bucket:
            Fn::Sub: cdk-hnb659fds-assets-${AWS::AccountId}-${AWS::Region}
          S3Key: 5d8d1d0aacea23824c62f362e1e3c14b7dd14a31c71b53bfae4d14a6373c5510.zip
        Description: /opt/awscli/aws
      Type: AWS::Lambda::LayerVersion
    S3DeploymentCustomResource4ADB55A7:
      DeletionPolicy: Delete
      Properties:
        DestinationBucketName:
          Ref: S3Bucket07682993
        Prune: true
        ServiceToken:
          Fn::GetAtt:
          - CustomCDKBucketDeployment8693BB64968944B69AAFB0CC9EB8756C81C01536
          - Arn
        SourceBucketNames:
        - Fn::Sub: cdk-hnb659fds-assets-${AWS::AccountId}-${AWS::Region}
        SourceMarkers:
        - {}
        SourceObjectKeys:
        - a930df18abdf36e70748ff3d515e4d72dfd16dbde04204905b9bc2edc2874a2e.zip
      Type: Custom::CDKBucketDeployment
      UpdateReplacePolicy: Delete
  Rules:
    CheckBootstrapVersion:
      Assertions:
      - Assert:
          Fn::Not:
          - Fn::Contains:
            - - '1'
              - '2'
              - '3'
              - '4'
              - '5'
            - Ref: BootstrapVersion
        AssertDescription: CDK bootstrap stack version 6 required. Please run 'cdk bootstrap'
          with a recent version of the CDK CLI.

..
