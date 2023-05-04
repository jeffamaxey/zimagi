from django.conf import settings
from celery import Celery
from celery.signals import celeryd_init, before_task_publish, worker_shutting_down
from kombu import Queue

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings.full")


@celeryd_init.connect
def capture_service_name(sender, instance, **kwargs):
    os.environ['ZIMAGI_CELERY_NAME'] = sender

@before_task_publish.connect
def task_sent_handler(sender, headers = None, body = None, **kwargs):
    from systems.commands.action import ActionCommand
    command = ActionCommand('worker')

    if queue := next(
        (
            entity.name
            for entity in kwargs['declare']
            if isinstance(entity, Queue)
        ),
        None,
    ):
        worker = command.get_provider('worker', settings.WORKER_PROVIDER,
            worker_type = queue,
            command_name = body[0][0],
            command_options = body[1]
        )
        worker.ensure()

@worker_shutting_down.connect
def cleanup_worker_manager(*args, **kwargs):
    if manager:
        manager.terminate()


manager = None
app = Celery('Zimagi', task_cls='systems.celery.task:CommandTask')
app.config_from_object('django.conf:settings', namespace = 'CELERY')
app.set_default()


if os.environ.get('ZIMAGI_BOOTSTRAP_DJANGO', None):
    import django
    django.setup()
    app.autodiscover_tasks(force = True)

if os.environ.get('ZIMAGI_WORKER_EXEC', None):
    from systems.celery.worker import start_worker_manager
    manager = start_worker_manager(app)
