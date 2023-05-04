from systems.commands.index import Command


class Push(Command('db.push')):

    def preprocess(self, options):
        options['db'] = self.db.save(self.db_packages, encrypted = False)

    def exec(self):
        self.db.load(self.options.get('db'), encrypted = False)
        self.success(
            f'Database packages {",".join(self.db_packages)} successfully pushed'
        )
