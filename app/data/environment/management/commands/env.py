
from django.core.management.base import CommandError

from systems.command import ComplexCommand
from data.environment.management.commands import _env as env


class Command(ComplexCommand):

    def get_priority(self):
        return 5

    def get_command_name(self):
        return 'env'

    def get_description(self, overview):
        if overview:
            return """manage cluster environments

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam 
pulvinar nisl ac magna ultricies dignissim. Praesent eu feugiat 
elit. Cras porta magna vel blandit euismod.
"""
        else:
            return """manage cluster environments
                      
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

    
    def get_subcommands(self):
        return (
            ('list', env.ListCommand),
            ('add', env.AddCommand),
            ('rm', env.RemoveCommand),
            ('clear', env.ClearCommand),
            ('get', env.GetCommand),
            ('set', env.SetCommand)
        )
