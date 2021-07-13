# Generated by Django 3.2.5 on 2021-07-13 07:03

import data.schedule.models
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import django_celery_beat.models
import django_celery_beat.validators
import systems.models.fields
import timezone_field.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('user', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ScheduledTaskChanges',
            fields=[
                ('ident', models.SmallIntegerField(default=1, primary_key=True, serialize=False, unique=True)),
                ('last_update', models.DateTimeField()),
            ],
            options={
                'verbose_name': 'scheduled task change',
                'verbose_name_plural': 'scheduled task changes',
                'db_table': 'core_task_changes',
            },
        ),
        migrations.CreateModel(
            name='TaskCrontab',
            fields=[
                ('created', models.DateTimeField(editable=False, null=True)),
                ('updated', models.DateTimeField(editable=False, null=True)),
                ('id', models.CharField(editable=False, max_length=64, primary_key=True, serialize=False)),
                ('name', models.CharField(editable=False, max_length=256)),
                ('minute', models.CharField(default='*', help_text='Cron Minutes to Run. Use "*" for "all". (Example: "0,30")', max_length=240, validators=[django_celery_beat.validators.minute_validator], verbose_name='Minute(s)')),
                ('hour', models.CharField(default='*', help_text='Cron Hours to Run. Use "*" for "all". (Example: "8,20")', max_length=96, validators=[django_celery_beat.validators.hour_validator], verbose_name='Hour(s)')),
                ('day_of_week', models.CharField(default='*', help_text='Cron Days Of The Week to Run. Use "*" for "all". (Example: "0,5")', max_length=64, validators=[django_celery_beat.validators.day_of_week_validator], verbose_name='Day(s) Of The Week')),
                ('day_of_month', models.CharField(default='*', help_text='Cron Days Of The Month to Run. Use "*" for "all". (Example: "1,15")', max_length=124, validators=[django_celery_beat.validators.day_of_month_validator], verbose_name='Day(s) Of The Month')),
                ('month_of_year', models.CharField(default='*', help_text='Cron Months Of The Year to Run. Use "*" for "all". (Example: "0,6")', max_length=64, validators=[django_celery_beat.validators.month_of_year_validator], verbose_name='Month(s) Of The Year')),
                ('timezone', timezone_field.fields.TimeZoneField(default=django_celery_beat.models.crontab_schedule_celery_timezone, help_text='Timezone to Run the Cron Schedule on. Default is UTC.', verbose_name='Cron Timezone')),
            ],
            options={
                'verbose_name': 'task crontab',
                'verbose_name_plural': 'task crontabs',
                'db_table': 'core_task_crontab',
                'ordering': ['name'],
                'abstract': False,
            },
            bases=(data.schedule.models.ScheduleModelMixin, models.Model),
        ),
        migrations.CreateModel(
            name='TaskDatetime',
            fields=[
                ('created', models.DateTimeField(editable=False, null=True)),
                ('updated', models.DateTimeField(editable=False, null=True)),
                ('id', models.CharField(editable=False, max_length=64, primary_key=True, serialize=False)),
                ('name', models.CharField(editable=False, max_length=256)),
                ('clocked_time', models.DateTimeField(help_text='Run the task at clocked time', verbose_name='Clock Time')),
            ],
            options={
                'verbose_name': 'task datetime',
                'verbose_name_plural': 'task datetimes',
                'db_table': 'core_task_datetime',
                'ordering': ['name'],
                'abstract': False,
            },
            bases=(data.schedule.models.ScheduleModelMixin, models.Model),
        ),
        migrations.CreateModel(
            name='TaskInterval',
            fields=[
                ('created', models.DateTimeField(editable=False, null=True)),
                ('updated', models.DateTimeField(editable=False, null=True)),
                ('id', models.CharField(editable=False, max_length=64, primary_key=True, serialize=False)),
                ('name', models.CharField(editable=False, max_length=256)),
                ('every', models.IntegerField(help_text='Number of interval periods to wait before running the task again', validators=[django.core.validators.MinValueValidator(1)], verbose_name='Number of Periods')),
                ('period', models.CharField(choices=[('days', 'Days'), ('hours', 'Hours'), ('minutes', 'Minutes'), ('seconds', 'Seconds'), ('microseconds', 'Microseconds')], help_text='The type of period between task runs (Example: days)', max_length=24, verbose_name='Interval Period')),
            ],
            options={
                'verbose_name': 'task interval',
                'verbose_name_plural': 'task intervals',
                'db_table': 'core_task_interval',
                'ordering': ['name'],
                'abstract': False,
            },
            bases=(data.schedule.models.ScheduleModelMixin, models.Model),
        ),
        migrations.CreateModel(
            name='ScheduledTask',
            fields=[
                ('created', models.DateTimeField(editable=False, null=True)),
                ('updated', models.DateTimeField(editable=False, null=True)),
                ('id', models.CharField(editable=False, max_length=64, primary_key=True, serialize=False)),
                ('task', models.CharField(help_text='The Name of the Celery Task that Should be Run.  (Example: "proj.tasks.import_contacts")', max_length=200, verbose_name='Task Name')),
                ('queue', models.CharField(blank=True, default=None, help_text='Queue defined in CELERY_TASK_QUEUES. Leave None for default queuing.', max_length=200, null=True, verbose_name='Queue Override')),
                ('exchange', models.CharField(blank=True, default=None, help_text='Override Exchange for low-level AMQP routing', max_length=200, null=True, verbose_name='Exchange')),
                ('routing_key', models.CharField(blank=True, default=None, help_text='Override Routing Key for low-level AMQP routing', max_length=200, null=True, verbose_name='Routing Key')),
                ('headers', models.TextField(blank=True, default='{}', help_text='JSON encoded message headers for the AMQP message.', verbose_name='AMQP Message Headers')),
                ('priority', models.PositiveIntegerField(blank=True, default=None, help_text='Priority Number between 0 and 255. Supported by: RabbitMQ, Redis (priority reversed, 0 is highest).', null=True, validators=[django.core.validators.MaxValueValidator(255)], verbose_name='Priority')),
                ('expires', models.DateTimeField(blank=True, help_text='Datetime after which the schedule will no longer trigger the task to run', null=True, verbose_name='Expires Datetime')),
                ('expire_seconds', models.PositiveIntegerField(blank=True, help_text='Timedelta with seconds which the schedule will no longer trigger the task to run', null=True, verbose_name='Expires timedelta with seconds')),
                ('one_off', models.BooleanField(default=False, help_text='If True, the schedule will only run the task a single time', verbose_name='One-off Task')),
                ('start_time', models.DateTimeField(blank=True, help_text='Datetime when the schedule should begin triggering the task to run', null=True, verbose_name='Start Datetime')),
                ('enabled', models.BooleanField(default=True, help_text='Set to False to disable the schedule', verbose_name='Enabled')),
                ('last_run_at', models.DateTimeField(blank=True, editable=False, help_text='Datetime that the schedule last triggered the task to run. Reset to None if enabled is set to False.', null=True, verbose_name='Last Run Datetime')),
                ('total_run_count', models.PositiveIntegerField(default=0, editable=False, help_text='Running count of how many times the schedule has triggered the task', verbose_name='Total Run Count')),
                ('date_changed', models.DateTimeField(auto_now=True, help_text='Datetime that this PeriodicTask was last modified', verbose_name='Last Modified')),
                ('description', models.TextField(blank=True, help_text='Detailed description about the details of this Periodic Task', verbose_name='Description')),
                ('name', models.CharField(editable=False, max_length=256)),
                ('args', systems.models.fields.EncryptedDataField(default=[])),
                ('kwargs', systems.models.fields.EncryptedDataField(default={})),
                ('clocked', models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='scheduledtask_relation', to='schedule.taskdatetime')),
                ('crontab', models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='scheduledtask_relation', to='schedule.taskcrontab')),
                ('interval', models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='scheduledtask_relation', to='schedule.taskinterval')),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='user.user')),
            ],
            options={
                'verbose_name': 'scheduled task',
                'verbose_name_plural': 'scheduled tasks',
                'db_table': 'core_scheduled_task',
                'ordering': ['name'],
                'abstract': False,
            },
            bases=(data.schedule.models.ScheduleModelMixin, models.Model),
        ),
    ]
