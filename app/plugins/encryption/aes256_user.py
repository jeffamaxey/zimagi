from systems.plugins.index import BaseProvider
from systems.encryption.cipher import EncryptionError


class Provider(BaseProvider('encryption', 'aes256_user')):

    def initialize(self, options):
        if options.get('user', None):
            user_facade = self.manager.index.get_facade_index()['user']
            if user := user_facade.retrieve(options['user']):
                options['key'] = user.encryption_key
            else:
                raise EncryptionError(f"User {options['user']} does not exist")
