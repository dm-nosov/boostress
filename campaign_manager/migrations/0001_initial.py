# Generated by Django 5.1.1 on 2024-09-08 20:21

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Provider',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('api_url', models.CharField(max_length=200)),
                ('name', models.CharField(default='', max_length=100)),
                ('budget', models.FloatField()),
            ],
        ),
        migrations.CreateModel(
            name='ProviderPlatform',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('platform', models.CharField(choices=[('ln', 'linkedin'), ('tt', 'tiktok'), ('ig', 'instagram')], default='ln', max_length=20)),
            ],
        ),
        migrations.CreateModel(
            name='ServiceType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(choices=[('like', 'like'), ('comment', 'comment'), ('share', 'share'), ('view', 'view')], default='view', max_length=20)),
            ],
        ),
        migrations.CreateModel(
            name='PlatformService',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('service_id', models.CharField(max_length=20)),
                ('min', models.IntegerField(default=1)),
                ('max', models.IntegerField(default=1)),
                ('provider', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='campaign_manager.provider')),
                ('platform', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='campaign_manager.providerplatform')),
                ('service_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='campaign_manager.servicetype')),
            ],
        ),
        migrations.CreateModel(
            name='ServiceTask',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('pending', 'pending'), ('in_progress', 'in_progress'), ('completed', 'completed')], default='pending', max_length=20)),
                ('budget', models.FloatField()),
                ('spent', models.FloatField()),
                ('platform', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='campaign_manager.providerplatform')),
                ('service', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='campaign_manager.platformservice')),
            ],
        ),
    ]
