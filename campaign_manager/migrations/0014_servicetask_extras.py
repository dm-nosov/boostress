# Generated by Django 5.1.1 on 2024-09-09 16:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('campaign_manager', '0013_order_created_servicetask_created_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='servicetask',
            name='extras',
            field=models.CharField(default='', max_length=200),
        ),
    ]
