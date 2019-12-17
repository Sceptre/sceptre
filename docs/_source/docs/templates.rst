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

    template_path: dns-extras.j2
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

.. code-block:: yaml

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

.. _troposphere: https://github.com/cloudtools/troposphere/
