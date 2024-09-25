# Generated by Django 5.1.1 on 2024-09-25 12:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('campaign_manager', '0019_order_time_sensible'),
    ]

    operations = [
        migrations.CreateModel(
            name='ServiceHealthLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('entry', models.CharField(default='', max_length=256)),
                ('created', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.AddField(
            model_name='servicetask',
            name='force_complete_after_min',
            field=models.IntegerField(default=120),
        ),
        migrations.AlterField(
            model_name='order',
            name='link_type',
            field=models.CharField(choices=[('profile', 'profile'), ('post', 'post'), ('comment', 'comment'), ('ads_post', 'ads_post'), ('web_traffic', 'web_traffic')], default='post', max_length=20),
        ),
        migrations.AlterField(
            model_name='platformservice',
            name='link_type',
            field=models.CharField(choices=[('profile', 'profile'), ('post', 'post'), ('comment', 'comment'), ('ads_post', 'ads_post'), ('web_traffic', 'web_traffic')], default='post', max_length=20),
        ),
        migrations.AlterField(
            model_name='servicetask',
            name='link_type',
            field=models.CharField(choices=[('profile', 'profile'), ('post', 'post'), ('comment', 'comment'), ('ads_post', 'ads_post'), ('web_traffic', 'web_traffic')], default='post', max_length=20),
        ),
        migrations.AlterField(
            model_name='servicetype',
            name='name',
            field=models.CharField(choices=[('like', 'like'), ('comment', 'comment'), ('share', 'share'), ('view', 'view'), ('repost', 'repost'), ('send', 'send'), ('follow', 'follow'), ('com_emoji', 'com_emoji'), ('visit', 'visit')], default='view', max_length=20),
        ),
    ]
