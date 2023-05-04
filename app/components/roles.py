from systems.commands import profile


class ProfileComponent(profile.BaseProfileComponent):

    def priority(self):
        return 5

    def run(self, name, help):
        if not help:
            self.command.error(f"Role {name} help string must be provided")

        self.exec('template generate',
            module_name = self.profile.module.instance.name,
            module_template = 'user/role',
            template_fields = {
                'name': name.replace('_', '-'),
                'help': help.capitalize()
            }
        )
