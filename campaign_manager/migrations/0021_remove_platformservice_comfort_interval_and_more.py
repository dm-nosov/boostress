# Generated by Django 5.1.1 on 2024-09-25 12:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('campaign_manager', '0020_servicehealthlog_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='platformservice',
            name='comfort_interval',
        ),
        migrations.RemoveField(
            model_name='platformservice',
            name='comfort_value',
        ),
        migrations.AddField(
            model_name='platformservice',
            name='force_complete_after_min',
            field=models.IntegerField(default=120),
        ),
    ]
