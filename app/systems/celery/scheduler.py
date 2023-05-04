from celery import schedules
from celery import beat
from django.conf import settings
from django_celery_beat.clockedschedule import clocked
from django_celery_beat.schedulers import DatabaseScheduler, ModelEntry

from data.schedule.models import (
    ScheduledTaskChanges,
    ScheduledTask,
    TaskInterval,
    TaskCrontab,
    TaskDatetime
)
from utility.mutex import check_mutex, MutexError, MutexTimeoutError

import heapq
import re
import time
import random
import logging


logger = logging.getLogger(__name__)


class ScheduleEntry(ModelEntry):

    model_schedules = (
        (schedules.schedule, TaskInterval, 'interval'),
        (schedules.crontab, TaskCrontab, 'crontab'),
        (clocked, TaskDatetime, 'clocked')
    )

    @classmethod
    def from_entry(cls, name, app = None, **entry):
        return cls(ScheduledTask._default_manager.update_or_create(
            name = name, defaults = cls._unpack_fields(**entry),
        ), app = app)


class CeleryScheduler(DatabaseScheduler):

    Entry = ScheduleEntry
    Model = ScheduledTask
    Changes = ScheduledTaskChanges

    lock_id = 'zimagi-scheduler'


    def tick(self, event_t = beat.event_t, min = min, heappop = heapq.heappop, heappush = heapq.heappush):
        try:
            time.sleep(random.randrange(10))
            with check_mutex(self.lock_id):
                super().tick(
                    event_t = event_t,
                    min = min,
                    heappop = heappop,
                    heappush = heappush
                )
        except MutexError:
            logger.warning(f"Scheduler could not obtain lock for {self.lock_id}")

        except MutexTimeoutError:
            logger.warning("Scheduler sync completed but the lock timed out")


    def apply_async(self, entry, producer = None, advance = True, **kwargs):
        if entry.task == 'zimagi.command.exec':
            if 'worker_type' not in entry.kwargs or not entry.kwargs['worker_type']:
                command = settings.MANAGER.index.find_command(re.split(r'\s+', entry.args[0]))
                entry.kwargs['worker_type'] = command.spec.get('worker_type', 'default')

            entry.options['queue'] = entry.kwargs['worker_type']

        return super().apply_async(entry, producer, advance, **kwargs)
