from smtplib import SMTPConnectError, SMTPServerDisconnected
from django.conf import settings
from django.core.mail import send_mail
from celery import Task
from celery.utils.log import get_task_logger

from systems.commands.action import ActionCommand
from utility.data import ensure_list


logger = get_task_logger(__name__)


class CommandTask(Task):

    def __init__(self):
        self.command = ActionCommand('celery')


    def exec_command(self, name, options):
        user = self.command._user.retrieve(options.pop('_user', settings.ADMIN_USER))
        self.command._user.set_active_user(user)

        self.command.exec_local(name, options,
            primary = True,
            task = self
        )


    def clean_interval_schedule(self):
        def run():
            interval_ids = list(self.command._scheduled_task.filter(interval_id__isnull = False).distinct().values_list('interval_id', flat=True))
            logger.debug("Interval IDs: {}".format(interval_ids))

            for record in self.command._task_interval.exclude(name__in = interval_ids):
                record.delete()
                logger.info("Deleted unused interval schedule: {}".format(record.get_id()))

        self.command.run_exclusive('zimagi-task-clean-interval', run,
            error_on_locked = True
        )


    def clean_crontab_schedule(self):
        def run():
            crontab_ids = list(self.command._scheduled_task.filter(crontab_id__isnull = False).distinct().values_list('crontab_id', flat=True))
            logger.debug("Crontab IDs: {}".format(crontab_ids))

            for record in self.command._task_crontab.exclude(name__in = crontab_ids):
                record.delete()
                logger.info("Deleted unused crontab schedule: {}".format(record.get_id()))

        self.command.run_exclusive('zimagi-task-clean-crontab', run,
            error_on_locked = True
        )


    def clean_datetime_schedule(self):
        def run():
            datetime_ids = list(self.command._scheduled_task.filter(clocked_id__isnull = False).distinct().values_list('clocked_id', flat=True))
            logger.debug("Datetime IDs: {}".format(datetime_ids))

            for record in self.command._task_datetime.exclude(name__in = datetime_ids):
                record.delete()
                logger.info("Deleted unused datetime schedule: {}".format(record.get_id()))

        self.command.run_exclusive('zimagi-task-clean-datetime', run,
            error_on_locked = True
        )


    def send_notification(self, recipient, subject, body):
        if not settings.EMAIL_HOST or not settings.EMAIL_HOST_USER:
            return
        try:
            html_body = body.replace("\n", '<br/>')
            html_body = html_body.replace(" ", '&nbsp;')
            html_body = f'<font face="Courier New, Courier, monospace">{html_body}</font>'

            send_mail(
                subject,
                body,
                settings.EMAIL_HOST_USER,
                ensure_list(recipient),
                html_message = html_body
            )
            logger.info(f"Notification message '{subject}' sent to: {recipient}")

        except SMTPConnectError as e:
            logger.error(f"Notification delivery failed: {e}")
            raise self.retry(exc = e)

        except SMTPServerDisconnected as e:
            logger.error(f"Notification service disconnected: {e}")
            raise self.retry(exc = e)

        except Exception as e:
            logger.error(f"Notification error: {e}")
            raise e
