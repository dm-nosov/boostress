import json
from datetime import timedelta

from celery.signals import task_postrun
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django_celery_beat.models import IntervalSchedule, PeriodicTask
from django_celery_results.models import TaskResult

from campaign_manager.models import Order


@task_postrun.connect
def update_task_result(sender=None, task_id=None, task=None, **kwargs):
    try:
        # Fetch the task result by its task_id
        task_result = TaskResult.objects.get(task_id=task_id)

        # Update the fields
        task_result.periodic_task_name = sender.periodic_task_name
        task_result.worker = task.request.hostname

        task_result.save(update_fields=['periodic_task_name', 'worker'])
    except TaskResult.DoesNotExist:
        pass  # Handle the case where the result isn't found


@receiver(post_save, sender=Order)
def product_created(sender, instance: Order, created, **kwargs):
    if created and instance.time_sensible:
        # Schedule for the first hour (every minute)
        minute_schedule, _ = IntervalSchedule.objects.get_or_create(every=1, period=IntervalSchedule.MINUTES)

        # Schedule for after the first hour (every 17 minutes)
        seventeen_min_schedule, _ = IntervalSchedule.objects.get_or_create(every=17, period=IntervalSchedule.MINUTES)

        # Create the task for the first hour
        PeriodicTask.objects.get_or_create(
            name='{} - 1H'.format(instance.name),
            task='campaign_manager.tasks.process_order',
            interval=minute_schedule,
            start_time=timezone.now(),
            expires=timezone.now() + timedelta(minutes=90),
            args=json.dumps([instance.id])
        )

        # Create the task for after the first hour
        PeriodicTask.objects.get_or_create(
            name='{} - 2H+'.format(instance.name),
            task='campaign_manager.tasks.process_order',
            interval=seventeen_min_schedule,
            start_time=timezone.now() + timedelta(minutes=90),
            args=json.dumps([instance.id]),
            expires=timezone.now() + timedelta(hours=24 * 2),
        )
