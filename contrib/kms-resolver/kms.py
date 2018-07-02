from sceptre.resolvers import Resolver
import base64


class KMS(Resolver):
    """
    Resolver for KMS. Resolves data stored in KMS from a Ciphertext.

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
