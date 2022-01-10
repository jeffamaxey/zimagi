# Generated by Django 4.0.1 on 2022-01-10 06:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('group', '0003_alter_group_parent'),
        ('user', '0002_alter_user_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='groups',
            field=models.ManyToManyField(related_name='%(class)s_relations', to='group.Group'),
        ),
    ]
