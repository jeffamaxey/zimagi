from systems.commands.index import Command


class Get(Command('log.get')):

    def exec(self):
        self.table([
            [self.key_color("Log key"), self.value_color(self.log_name)],
            [self.key_color("Command"), self.value_color(self.log.command)],
            [self.key_color("Status"), self.log.status],
            [self.key_color("User"), self.log.user.name],
            [self.key_color("Scheduled"), self.log.scheduled],
            [self.key_color("Started"), self.format_time(self.log.created)],
            [self.key_color("Last Updated"), self.format_time(self.log.updated)]
        ], 'data')

        parameter_table = [[self.key_color("Parameter"), self.key_color("Value")]]
        parameter_table.extend(
            [self.key_color(name), value]
            for name, value in self.log.config.items()
        )
        self.table(parameter_table, 'parameters')

        self.info("\nCommand Messages:\n")

        if self.log.running():
            log = self.log
            created = log.created

            while self.connected():
                for record in log.messages.filter(created__gt = created).order_by('created'):
                    self.message(self.create_message(record.data, decrypt = False), log = False)
                    created = record.created

                log = self._log.retrieve(self.log_name)
                if not log.running():
                    if log.success():
                        self.success(f"Command '{log.command}' completed successfully")
                    else:
                        self.warning(f"Command '{log.command}' completed with errors")
                    break

                self.sleep(self.poll_interval)
        else:
            for record in self.log.messages.all().order_by('created'):
                self.message(self.create_message(record.data, decrypt = False), log = False)
