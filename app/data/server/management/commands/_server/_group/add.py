from systems.command import types, mixins


class AddCommand(
    mixins.op.AddMixin,
    types.ServerGroupActionCommand
):
    def get_description(self, overview):
        if overview:
            return """add environment groups to servers

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam 
pulvinar nisl ac magna ultricies dignissim. Praesent eu feugiat 
elit. Cras porta magna vel blandit euismod.
"""
        else:
            return """add environment groups to servers
                      
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
        self.parse_server_reference()
        self.parse_server_groups(False)

    def exec(self):
        self.set_server_scope()

        def add_groups(server, state):
            self.exec_add_related(
                self._server_group, 
                server, 'groups', 
                self.server_group_names
            )
        self.run_list(self.servers, add_groups)
