# Generated by Django 3.0 on 2020-02-02 05:37

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0002_auto_20190406_2145'),
        ('schedule', '0003_auto_20200202_0014'),
    ]

    operations = [
        migrations.AddField(
            model_name='scheduledtask',
            name='user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='user.User'),
        ),
    ]
