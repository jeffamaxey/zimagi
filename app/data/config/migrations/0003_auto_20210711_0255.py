# Generated by Django 3.2.4 on 2021-07-11 06:55

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('config', '0002_auto_20190406_2145'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='config',
            unique_together=set(),
        ),
        migrations.RemoveField(
            model_name='config',
            name='environment',
        ),
    ]