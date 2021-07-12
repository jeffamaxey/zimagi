# Generated by Django 3.2.4 on 2021-07-11 06:55

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('schedule', '0007_auto_20201108_0218'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='taskcrontab',
            name='environment',
        ),
        migrations.RemoveField(
            model_name='taskdatetime',
            name='environment',
        ),
        migrations.RemoveField(
            model_name='taskinterval',
            name='environment',
        ),
        migrations.AlterUniqueTogether(
            name='scheduledtask',
            unique_together=set(),
        ),
        migrations.RemoveField(
            model_name='scheduledtask',
            name='environment',
        ),
    ]