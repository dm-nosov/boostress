# Generated by Django 5.1.1 on 2024-09-09 05:50

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('campaign_manager', '0005_alter_servicetask_order'),
    ]

    operations = [
        migrations.AlterField(
            model_name='servicetask',
            name='order',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='campaign_manager.order'),
        ),
    ]
