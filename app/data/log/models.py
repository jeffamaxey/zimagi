from django.utils.timezone import now

from systems.models.index import Model, ModelFacade


class LogFacade(ModelFacade('log')):

    def get_field_message_render_display(self, instance, value, short):
        from systems.commands import messages

        display = []
        for record in instance.messages.all().order_by('created'):
            msg = messages.AppMessage.get(record.data, decrypt = False)
            display.append(msg.format(True))

        return "\n".join(display) + "\n"


class Log(Model('log')):

    STATUS_QUEUED = 'queued'
    STATUS_RUNNING = 'running'
    STATUS_SUCCESS = 'success'
    STATUS_FAILED = 'failed'
    STATUS_ABORTED = 'aborted'
    STATUS_UNTRACKED = 'untracked'


    def save(self, *args, **kwargs):
        if not self.name:
            self.name = "{}{}x".format(
                now().strftime("%Y%m%d%H%M%S"),
                self.facade.generate_token(5)
            )
        super().save(*args, **kwargs)


    def success(self):
        return self.status == self.STATUS_SUCCESS

    def failed(self):
        return self.status == self.STATUS_FAILED

    def aborted(self):
        return self.status == self.STATUS_ABORTED

    def running(self):
        return self.status == self.STATUS_RUNNING

    def queued(self):
        return self.status == self.STATUS_QUEUED

    def untracked(self):
        return self.status == self.STATUS_UNTRACKED


    def set_status(self, status):
        if isinstance(status, bool):
            self.status = self.STATUS_SUCCESS if status else self.STATUS_FAILED
        else:
            self.status = status


class LogMessage(Model('log_message')):

    def __str__(self):
        return "{} ({})".format(self.log.command, self.data)
