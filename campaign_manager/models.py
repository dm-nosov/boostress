from datetime import timedelta

from django.db import models
from django.utils import timezone
from django_celery_beat.models import PeriodicTask, IntervalSchedule, CrontabSchedule


class LinkType(models.TextChoices):
    PROFILE = 'profile', 'profile'
    POST = 'post', 'post'
    COMMENT = 'comment', 'comment'
    ADS_POST = 'ads_post', 'ads_post'
    WEB_TRAFFIC = 'web_traffic', 'web_traffic'


class Status(models.TextChoices):
    PENDING = 'Pending', 'pending'
    PROCESSING = 'Processing', 'processing'
    IN_PROGRESS = 'In progress', 'in_progress'
    COMPLETED = 'Completed', 'completed'
    PARTIAL = 'Partial', 'in_progress'
    CANCELED = 'Canceled', 'completed'
    PRE_COMPLETE = 'Pre_complete', 'pre_complete'


class ProviderType(models.TextChoices):
    B11D = 'b11d', 'b11d'
    U1U = 'u1u', 'u1u'


class Provider(models.Model):
    api_url = models.CharField(max_length=200)
    api_type = models.CharField(max_length=20, choices=ProviderType.choices, default=ProviderType.B11D)
    name = models.CharField(max_length=100, default="")
    key = models.CharField(max_length=100, default="")
    budget = models.FloatField()

    def __str__(self):
        return self.name

    def get_available_services(self, platform, link_type, min_since_created):
        return list(self.services.filter(platform=platform, link_type=link_type, is_enabled=True,
                                         start_after__lte=min_since_created,
                                         end_after__gt=min_since_created).values_list(
            "service_type__name",
            flat=True).distinct())

    def get_active_tasks(self):
        return ",".join(list(
            ServiceTask.objects.get_active_tasks().filter(provider=self).values_list(
                "ext_order_id", flat=True)))

    def force_complete_tasks(self):
        active_tasks = ServiceTask.objects.get_active_tasks().filter(provider=self)
        for task in active_tasks:
            if task.created + timedelta(minutes=task.force_complete_after_min) < timezone.now():
                ServiceHealthLog.objects.create(
                    entry="Service {} could not deliver within {} minutes, replacing".format(task.service.service_id,
                                                                                             task.force_complete_after_min))
                task.status = Status.COMPLETED
                task.save()


class ServiceHealthLog(models.Model):
    entry = models.CharField(max_length=256, default="")
    created = models.DateTimeField(auto_now_add=True)


class ServiceTypes(models.TextChoices):
    LIKE = 'like', 'like'
    COMMENT = 'comment', 'comment'
    SHARE = 'share', 'share'
    VIEW = 'view', 'view'
    REPOST = 'repost', 'repost'
    SEND = 'send', 'send'
    SAVE = 'save', 'save'
    FOLLOW = 'follow', 'follow'
    COMMENT_EMOJI = 'com_emoji', 'com_emoji'
    VISIT = 'visit', 'visit'
    VIDEO_VIEW = 'video_view', 'video_view'


class ServiceType(models.Model):
    name = models.CharField(max_length=20, choices=ServiceTypes.choices, default=ServiceTypes.VIEW)

    def __str__(self):
        return self.name


class PlatformName(models.TextChoices):
    LINKEDIN = 'ln', 'linkedin'
    TIKTOK = 'tt', 'tiktok'
    TELEGRAM = 'tg', 'telegram'
    INSTAGRAM = 'ig', 'instagram'


class ProviderPlatform(models.Model):
    name = models.CharField(max_length=20, choices=PlatformName.choices, default=PlatformName.LINKEDIN)

    def __str__(self):
        return self.name


class PlatformServiceManager(models.Manager):

    def get_providers_by_platform(self, platform, link_type):
        provider_ids = self.filter(platform=platform).prefetch_related('provider').distinct().values_list('provider',
                                                                                                          flat=True)
        return [Provider.objects.get(pk=provider_id) for provider_id in provider_ids]


class PlatformService(models.Model):
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE, related_name="services")
    name = models.CharField(max_length=100, default="")
    platform = models.ForeignKey(ProviderPlatform, on_delete=models.CASCADE)
    service_type = models.ForeignKey(ServiceType, on_delete=models.CASCADE)
    link_type = models.CharField(max_length=20, choices=LinkType.choices, default=LinkType.POST)
    service_id = models.CharField(max_length=20)
    service_meta = models.TextField(default="")
    is_enabled = models.BooleanField(default=True)
    min = models.IntegerField(default=1)
    max = models.IntegerField(default=1)
    force_complete_after_min = models.IntegerField(default=2 * 60)
    pre_complete_minutes = models.IntegerField(default=48 * 60,
                                               help_text="Duration in minutes before running the next task of the same type. Default is 48 hours.")
    start_after = models.IntegerField(default=0)
    end_after = models.IntegerField(default=99999)
    objects = PlatformServiceManager()

    def __str__(self):
        return self.service_id


class OrderManager(models.Manager):
    def get_active_orders(self):
        return self.exclude(status__in=[Status.COMPLETED, Status.CANCELED, Status.PARTIAL])

    def get_deployment_order(self):
        return self.get_or_create(name="DEPLOYMENT-TASKS",
                                  status=Status.IN_PROGRESS,
                                  link="",
                                  platform=ProviderPlatform.objects.get(name=PlatformName.TELEGRAM),
                                  budget=9999999,
                                  deadline=999999,
                                  time_sensible=False,
                                  total_followers=1000)


class Order(models.Model):
    name = models.CharField(max_length=100, default="")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    link = models.CharField(max_length=256, default="")
    link_type = models.CharField(max_length=20, choices=LinkType.choices, default=LinkType.POST)
    platform = models.ForeignKey(ProviderPlatform, on_delete=models.CASCADE)
    spent = models.FloatField(default=0.0)
    budget = models.FloatField(default=5)
    deadline = models.IntegerField(default=48 * 60)
    time_sensible = models.BooleanField(default=True,
                                        help_text="The QTYs mimic the decrease in the attention span throughout the time")
    total_followers = models.IntegerField(default=50)
    natural_time_cycles = models.BooleanField(default=False,
                                              help_text="Use with something permanently running to mimic the changes to datetime activity cycles")
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    objects = OrderManager()

    def __str__(self):
        return self.name

    def get_last_completed_task_time(self, resource_link, service):
        last_task = self.tasks.filter(link=resource_link, service=service).last()
        if last_task:
            return last_task.created + last_task.force_complete_after_min
        return timezone.now() - timezone.timedelta(days=7)

class ServiceTaskManager(models.Manager):

    def get_active_tasks(self):
        return self.exclude(status__in=[Status.COMPLETED, Status.CANCELED, Status.PARTIAL])

    def get_busy_services(self, platform, link_type, link):
        return list(
            self.get_active_tasks().filter(platform=platform,
                                           link_type=link_type,
                                           link=link).values_list(
                "service__service_type__name", flat=True).distinct())


class ServiceTask(models.Model):
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE, null=True, related_name="tasks")
    platform = models.ForeignKey(ProviderPlatform, on_delete=models.CASCADE)
    service = models.ForeignKey(PlatformService, on_delete=models.CASCADE)
    link_type = models.CharField(max_length=20, choices=LinkType.choices, default=LinkType.POST)
    link = models.CharField(max_length=256, default="")
    spent = models.FloatField(default=0.0)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, null=True, blank=True, related_name="tasks")
    ext_order_id = models.CharField(max_length=40, default="")
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    extras = models.CharField(max_length=200, default="")
    pre_complete_minutes = models.IntegerField(default=48 * 60,
                                               help_text="Duration in minutes before running the next task of the same type. Default is 48 hours.")
    force_complete_after_min = models.IntegerField(default=2 * 60)
    objects = ServiceTaskManager()

    def __str__(self):
        return "Task {0}".format(self.id)


class EngagementConfigManager(models.Manager):
    def get_config(self, link_type, service_type, platform_name) -> (int, int):
        exact_config = self.filter(link_type=link_type, service_type=service_type, platform_name=platform_name).first()
        if exact_config:
            return exact_config.min, exact_config.max

        type_config = self.filter(link_type=link_type, service_type=service_type).first()
        if type_config:
            return type_config.min, type_config.max

        service_config = self.filter(service_type=service_type).first()
        if service_config:
            return service_config.min, service_config.max

        return 8, 12


class EngagementConfig(models.Model):
    name = models.CharField(max_length=100, default="")
    link_type = models.CharField(max_length=20, choices=LinkType.choices, default=LinkType.POST, null=True, blank=True)
    service_type = models.CharField(max_length=20, choices=ServiceTypes.choices, default=ServiceTypes.VIEW, null=True,
                                    blank=True)
    platform_name = models.CharField(max_length=20, choices=PlatformName.choices, default=PlatformName.LINKEDIN,
                                     null=True, blank=True)
    min = models.IntegerField(default=1)
    max = models.IntegerField(default=1)
    objects = EngagementConfigManager()
