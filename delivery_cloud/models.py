from django.db import models
from django.db.models import Max, Q
from django.utils import timezone

from campaign_manager.models import PlatformService, Status

OP_SEND = "send"
OP_FWD = "forward"


class Agent(models.Model):
    api_url = models.CharField(max_length=255, default="")
    endpoint_url = models.CharField(max_length=255, default="")
    token = models.CharField(max_length=255, default="")
    name = models.CharField(max_length=50, default="")

    def __str__(self):
        return self.name


class AgentOperation(models.Model):
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE)
    name = models.CharField(max_length=50, default="")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    def __str__(self):
        return self.name


class AgentService(models.Model):
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE)
    name = models.CharField(max_length=50, default="")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    service = models.ForeignKey(PlatformService, on_delete=models.CASCADE)
    is_ref = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class AgentResource(models.Model):
    RESOURCE_TYPE_CHOICES = [
        ('photo', 'Photo'),
        ('video', 'Video'),
    ]
    
    created = models.DateTimeField(auto_now_add=True)
    url = models.CharField(max_length=255, default="")
    is_active = models.BooleanField(default=True)
    resource_type = models.CharField(max_length=10, choices=RESOURCE_TYPE_CHOICES, default='photo')
    caption = models.CharField(max_length=255, blank=True, null=True)


class Endpoint(models.Model):
    ext_id = models.CharField(max_length=50, default="")
    name = models.CharField(max_length=50, default="")
    label = models.CharField(max_length=50, default="")
    message_qty = models.IntegerField(default=0)
    json_params = models.JSONField(default=dict)

    def __str__(self):
        return self.name


class AgentOpResultManager(models.Manager):
    @staticmethod
    def get_available_endpoints(last_message_hrs):
        hours_ago = timezone.now() - timezone.timedelta(hours=last_message_hrs)
        return Endpoint.objects.annotate(
            latest_op_created=Max('agentopresult__created')
        ).filter(
            Q(latest_op_created__lt=hours_ago) | Q(latest_op_created__isnull=True)
        )

    def get_active_deployments(self, last_deploy_hrs):
        hours_ago = timezone.now() - timezone.timedelta(hours=last_deploy_hrs)
        active_deployments = self.filter(created__gt=hours_ago)
        return active_deployments


class AgentOpResult(models.Model):
    endpoint = models.ForeignKey(Endpoint, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    ref_id = models.CharField(max_length=50, default="")
    ref_url = models.CharField(max_length=255, default="")
    is_fwd = models.BooleanField(default=False)
    objects = AgentOpResultManager()

    def __str__(self):
        return self.ref_url