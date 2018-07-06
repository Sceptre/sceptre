from sceptre.resolvers import Resolver
import boto3

from dateutil import parser


class FetchAMI(Resolver):

    """
    Resolver for AMI.
    Fetches the correct AMI ID based on the type of AMI requested.
    :param argument: Type of AMI required.
    :type argument: str
    """

    def __init__(self, *args, **kwargs):
        super(FetchAMI, self).__init__(*args, **kwargs)

    @staticmethod
    def newest_image(list_of_images):
        """
        Sorts the AMIs in descending order and returns the latest one
        :returns: AMI ID from AWS CLI.
        :rtype: str 
	"""

        latest = None

        for image in list_of_images:
            if not latest:
                latest = image
                continue

            if parser.parse(image['CreationDate'])\
                    > parser.parse(latest['CreationDate']):
                latest = image

        return latest

    def resolve(self):
        """
        Retrieves AMI ID from AWS CLI.
        :returns: AMI ID from AWS CLI.
        :rtype: str
        """

        region = self.environment_config['region']
        ami_type = self.argument

        client = boto3.client('ec2', region_name=region)

        filters = [{
                'Name': 'description',
                'Values': ['Amazon Linux AMI*']
            }, {
                'Name': 'architecture',
                'Values': ['x86_64']
            }, {
                'Name': 'owner-alias',
                'Values': ['amazon']
            }, {
                'Name': 'owner-id',
                'Values': ['137112412989']
            }, {
                'Name': 'state',
                'Values': ['available']
            }, {
                'Name': 'hypervisor',
                'Values': ['xen']
            }, {
                'Name': 'image-type',
                'Values': ['machine']
            }]

        if ami_type == "HVM (SSD) EBS-Backed 64-bit":

            filters.extend([{
                'Name': 'name',
                'Values': ['amzn-ami-hvm-*']
            }, {
                'Name': 'root-device-type',
                'Values': ['ebs']
            }, {
                'Name': 'block-device-mapping.volume-type',
                'Values': ['gp2']
            }, {
                'Name': 'virtualization-type',
                'Values': ['hvm']
            }])

        elif ami_type == "HVM Instance Store 64-bit":

            filters.extend([{
                'Name': 'name',
                'Values': ['amzn-ami-hvm-*']
            }, {
                'Name': 'root-device-type',
                'Values': ['instance-store']
            }, {
                'Name': 'virtualization-type',
                'Values': ['hvm']
            }])

        elif ami_type == "PV EBS-Backed 64-bit":

            filters.extend([{
                'Name': 'name',
                'Values': ['amzn-ami-pv-*']
            }, {
                'Name': 'root-device-type',
                'Values': ['ebs']
            }, {
                'Name': 'virtualization-type',
                'Values': ['paravirtual']
            }])

        elif ami_type == "PV Instance Store 64-bit":

            filters.extend([{
                'Name': 'name',
                'Values': ['amzn-ami-pv-*']
            }, {
                'Name': 'root-device-type',
                'Values': ['instance-store']
            }, {
                'Name': 'virtualization-type',
                'Values': ['paravirtual']
            }])

        elif ami_type == "HVM (NAT) EBS-Backed 64-bit":

            filters.extend([{
                'Name': 'name',
                'Values': ['amzn-ami-vpc-nat-hvm-*']
            }, {
                'Name': 'root-device-ami_type',
                'Values': ['ebs']
            }, {
                'Name': 'virtualization-ami_type',
                'Values': ['hvm']
            }])

        response = client.describe_images(Owners=['amazon'], Filters=filters)

        if response['Images'] == []:
            return "n/a"
        else:
            source_image = self.newest_image(response['Images'])
            return source_image['ImageId']
