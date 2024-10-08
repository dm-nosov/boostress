# Generated by Django 5.1.1 on 2024-09-09 08:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('campaign_manager', '0008_provider_key'),
    ]

    operations = [
        migrations.RenameField(
            model_name='providerplatform',
            old_name='platform',
            new_name='name',
        ),
        migrations.AddField(
            model_name='platformservice',
            name='comfort_interval',
            field=models.IntegerField(default=10),
        ),
        migrations.AddField(
            model_name='platformservice',
            name='comfort_value',
            field=models.IntegerField(default=0),
        ),
    ]
