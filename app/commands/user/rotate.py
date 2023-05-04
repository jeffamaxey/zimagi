from django.conf import settings

from systems.commands.index import Command


class Rotate(Command('user.rotate')):

    def exec(self):
        user = self.user if self.user_name else self.active_user
        token = self._user.generate_token()

        user.set_password(token)
        user.save()

        self.silent_data('name', user.name)
        self.data(f"User {user.name} token:", token, 'token')

    def postprocess(self, response):
        host = self.get_host()
        if host and host.user == response['name']:
            self.save_host(token = response['token'])
