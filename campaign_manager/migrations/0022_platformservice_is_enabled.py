# Generated by Django 5.1.1 on 2024-09-25 13:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('campaign_manager', '0021_remove_platformservice_comfort_interval_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='platformservice',
            name='is_enabled',
            field=models.BooleanField(default=True),
        ),
    ]
