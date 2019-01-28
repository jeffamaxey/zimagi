from settings import Roles
from systems.command import types, mixins


class ListCommand(
    mixins.op.ListMixin,
    types.ServerActionCommand
):
    def groups_allowed(self):
        return False # Server access model

    def get_description(self, overview):
        if overview:
            return """list servers in current environment

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam 
pulvinar nisl ac magna ultricies dignissim. Praesent eu feugiat 
elit. Cras porta magna vel blandit euismod.
"""
        else:
            return """list servers in current environment
                      
Etiam mattis iaculis felis eu pharetra. Nulla facilisi. 
Duis placerat pulvinar urna et elementum. Mauris enim risus, 
mattis vel risus quis, imperdiet convallis felis. Donec iaculis 
tristique diam eget rutrum.

Etiam sit amet mollis lacus. Nulla pretium, neque id porta feugiat, 
erat sapien sollicitudin tellus, vel fermentum quam purus non sem. 
Mauris venenatis eleifend nulla, ac facilisis nulla efficitur sed. 
Etiam a ipsum odio. Curabitur magna mi, ornare sit amet nulla at, 
scelerisque tristique leo. Curabitur ut faucibus leo, non tincidunt 
velit. Aenean sit amet consequat mauris.
"""
    def parse(self):
        self.parse_network_name('--network')
        self.parse_server_reference(True)

    def exec(self):
        def process(op, info, key_index):
            if op == 'label':
                info.extend(['state', 'groups'])
            else:
                server = self.get_instance(self._server, info[key_index])
                info.append(server.state)
                info.append("\n".join(server.groups.values_list('name', flat = True)))

        self.exec_processed_list(self._server, process,
            'name',
            'type',
            'subnet__network__name',
            'subnet__name',
            'ip',
            'user',
            name__in = [ server.name for server in self.servers ]
        )
