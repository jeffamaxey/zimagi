from systems.commands.index import Command


class Pull(Command('db.pull')):

    def exec(self):
        self.silent_data('db', self.db.save(self.db_packages, encrypted = False))

    def postprocess(self, response):
        self.db.load(response['db'], encrypted = False)
        self.success(
            f'Database packages {",".join(self.db_packages)} successfully pulled'
        )
