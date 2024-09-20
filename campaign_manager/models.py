from django.db import models
from django.utils import timezone


class LinkType(models.TextChoices):
    PROFILE = 'profile', 'profile'
    POST = 'post', 'post'


class Status(models.TextChoices):
    PENDING = 'Pending', 'pending'
    PROCESSING = 'Processing', 'processing'
    IN_PROGRESS = 'In progress', 'in_progress'
    COMPLETED = 'Completed', 'completed'
    PARTIAL = 'Partial', 'in_progress'
    CANCELED = 'Canceled', 'completed'
    PRE_COMPLETE = 'Pre_complete', 'pre_complete'


class Provider(models.Model):
    api_url = models.CharField(max_length=200)
    name = models.CharField(max_length=100, default="")
    key = models.CharField(max_length=100, default="")
    budget = models.FloatField()

    def __str__(self):
        return self.name

    def get_available_services(self, platform, link_type):
        return list(self.services.filter(platform=platform, link_type=link_type).values_list("service_type__name",
                                                                                             flat=True).distinct())

    def get_active_tasks(self):
        return ",".join(list(self.tasks.exclude(status__in=[Status.COMPLETED, Status.CANCELED, Status.PARTIAL]).values_list("ext_order_id", flat=True)))


class ServiceType(models.Model):
    class Name(models.TextChoices):
        LIKE = 'like', 'like'
        COMMENT = 'comment', 'comment'
        SHARE = 'share', 'share'
        VIEW = 'view', 'view'
        REPOST = 'repost', 'repost'
        SEND = 'send', 'send'
        FOLLOW = 'follow', 'follow'

    name = models.CharField(max_length=20, choices=Name.choices, default=Name.VIEW)

    def __str__(self):
        return self.name


class ProviderPlatform(models.Model):
    class Name(models.TextChoices):
        LINKEDIN = 'ln', 'linkedin'
        TIKTOK = 'tt', 'tiktok'
        TELEGRAM = 'tg', 'telegram'
        INSTAGRAM = 'ig', 'instagram'

    name = models.CharField(max_length=20, choices=Name.choices, default=Name.LINKEDIN)

    def __str__(self):
        return self.name


class PlatformServiceManager(models.Manager):

    def get_providers_by_platform(self, platform, link_type):
        provider_ids = self.filter(platform=platform).prefetch_related('provider').distinct().values_list('provider',
                                                                                                          flat=True)
        return [Provider.objects.get(pk=provider_id) for provider_id in provider_ids]


class PlatformService(models.Model):
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE, related_name="services")
    platform = models.ForeignKey(ProviderPlatform, on_delete=models.CASCADE)
    service_type = models.ForeignKey(ServiceType, on_delete=models.CASCADE)
    link_type = models.CharField(max_length=20, choices=LinkType.choices, default=LinkType.POST)
    service_id = models.CharField(max_length=20)
    min = models.IntegerField(default=1)
    max = models.IntegerField(default=1)
    comfort_value = models.IntegerField(default=0)
    comfort_interval = models.IntegerField(default=10)
    pre_complete_minutes = models.IntegerField(default=48 * 60,
                                               help_text="Duration in minutes before running the next task of the same type. Default is 48 hours.")
    objects = PlatformServiceManager()

    def __str__(self):
        return self.service_id


class Order(models.Model):
    name = models.CharField(max_length=100, default="")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    link = models.CharField(max_length=256, default="")
    link_type = models.CharField(max_length=20, choices=LinkType.choices, default=LinkType.POST)
    platform = models.ForeignKey(ProviderPlatform, on_delete=models.CASCADE)
    spent = models.FloatField(default=0.0)
    budget = models.FloatField(default=5)
    deadline = models.IntegerField(default=48 * 60)
    total_followers = models.IntegerField(default=50)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class ServiceTaskManager(models.Manager):
    def get_busy_services(self, platform, link_type, link):
        return list(
            self.exclude(status__in=[Status.COMPLETED, Status.CANCELED, Status.PARTIAL]).filter(platform=platform,
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
    objects = ServiceTaskManager()
    def __str__(self):
        return "Task {0}".format(self.id)
