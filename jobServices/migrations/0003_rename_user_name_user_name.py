# Generated by Django 4.2.23 on 2025-06-30 08:45

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('jobServices', '0002_user_user_name'),
    ]

    operations = [
        migrations.RenameField(
            model_name='user',
            old_name='user_name',
            new_name='name',
        ),
    ]
