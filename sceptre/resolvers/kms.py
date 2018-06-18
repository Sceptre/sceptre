from sceptre.resolvers import Resolver
import base64


class KMS(Resolver):
    """
    Resolver for KMS. Resolves data stored in KMS from a Ciphertext.

    Encrypt data and get a Ciphertext:
    > aws kms --key-id <Kms Key Id> --plaintext <data> \
    >   --output text --query CiphertextBlob \
    >   AQICAHhZyEsV0yflwE0mpKvPz7/O/zc1epgIurV43wXF/qF6MwFQYwZq7TrvtQ2....

    :param argument: The Ciphertext from KMS.
    :type argument: str

    """

    def __init__(self, *args, **kwargs):
        super(KMS, self).__init__(*args, **kwargs)

    def resolve(self):
        """
        Retrieves data from KMS.

        :returns: Value from KMS.
        :rtype: str
        """
        decoded_value = None
        if self.argument:
            ciphertext = self.argument
            ciphertext_blob = base64.b64decode(ciphertext)
            kms_client = self.connection_manager.boto_session.client('kms')
            meta = kms_client.decrypt(CiphertextBlob=ciphertext_blob)
            binary_value = meta[u'Plaintext']
            decoded_value = binary_value.decode()
        return decoded_value
