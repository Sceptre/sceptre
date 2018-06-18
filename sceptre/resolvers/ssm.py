from sceptre.resolvers import Resolver


class SSM(Resolver):
    """
    Resolver for SSM. Resolves the value stored in the parameter store.

    Add a value to the SSM parameter store:
    > aws ssm put-parameter --name <parameter prefix>/<parameter name> \
    >   --value <parameter value> --key-id <kms key id> --type "SecureString"

    :param argument: The SSM parameter
    :type argument: str

    """

    def __init__(self, *args, **kwargs):
        super(SSM, self).__init__(*args, **kwargs)

    def resolve(self):
        """
        Retrieves the parameter value from SSM Parameter Store.

        :returns: parameter value
        :rtype: str
        """
        decoded_value = None
        if self.argument:
            param = self.argument
            ssm_client = self.connection_manager.boto_session.client('ssm')
            meta = ssm_client.get_parameter(Name=param, WithDecryption=True)
            decoded_value = meta['Parameter']['Value']
        return decoded_value
