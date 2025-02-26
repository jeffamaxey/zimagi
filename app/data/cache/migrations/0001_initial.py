# Generated by Django 3.2.10 on 2022-01-02 18:49

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Cache',
            fields=[
                ('created', models.DateTimeField(editable=False, null=True)),
                ('updated', models.DateTimeField(editable=False, null=True)),
                ('id', models.CharField(editable=False, max_length=64, primary_key=True, serialize=False)),
                ('name', models.CharField(editable=False, max_length=2000)),
                ('requests', models.PositiveBigIntegerField(default=0)),
            ],
            options={
                'verbose_name': 'cache',
                'verbose_name_plural': 'caches',
                'db_table': 'core_cache',
                'ordering': ['-requests'],
                'abstract': False,
            },
        ),
    ]
