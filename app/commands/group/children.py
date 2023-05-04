from systems.commands.index import Command


class Children(Command('group.children')):

    def exec(self):
        self.exec_local('group save', {
            'group_name': self.group_name,
            'group_provider_name': self.group_provider_name,
            'verbosity': 0
        })
        parent = self._group.retrieve(self.group_name)
        for group in self.group_child_names:
            self._group.store(group,
                provider_type = parent.provider_type,
                parent = parent
            )
        self.success(f"Successfully saved group {parent.name}")
