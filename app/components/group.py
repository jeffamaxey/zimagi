from systems.commands import profile
from utility.data import ensure_list


class ProfileComponent(profile.BaseProfileComponent):

    def priority(self):
        return 1


    def run(self, name, children):
        if children and isinstance(children, dict):
            for child, grandchildren in children.items():
                self.run(child, grandchildren)

            children = list(children.keys())

        self.exec('group children',
            group_name = name,
            group_names = [] if not children else ensure_list(children)
        )

    def describe(self, instance):
        return self.get_names(instance.group_relation)

    def destroy(self, name, children):
        if children:
            if isinstance(children, dict):
                for child, grandchildren in children.items():
                    self.destroy(child, grandchildren)
            elif isinstance(children, (list, tuple, str)):
                for child in ensure_list(children):
                    self.destroy(child, None)

        self.exec('group remove',
            group_name = name,
            force = True
        )
