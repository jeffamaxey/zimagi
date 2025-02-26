# Generated by Django 3.2.10 on 2022-01-02 18:49

from django.db import migrations, models
import systems.models.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('group', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Module',
            fields=[
                ('created', models.DateTimeField(editable=False, null=True)),
                ('updated', models.DateTimeField(editable=False, null=True)),
                ('name', models.CharField(editable=False, max_length=100, primary_key=True, serialize=False)),
                ('config', systems.models.fields.EncryptedDataField(default={}, editable=False)),
                ('provider_type', models.CharField(editable=False, max_length=128, null=True)),
                ('variables', systems.models.fields.EncryptedDataField(default={}, editable=False)),
                ('remote', models.CharField(max_length=256, null=True)),
                ('reference', models.CharField(max_length=128, null=True)),
                ('groups', models.ManyToManyField(related_name='module_relations', to='group.Group')),
            ],
            options={
                'verbose_name': 'module',
                'verbose_name_plural': 'modules',
                'db_table': 'core_module',
                'ordering': ['-provider_type', 'name'],
                'abstract': False,
            },
        ),
    ]
