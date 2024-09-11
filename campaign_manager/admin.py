import os
from django.contrib import admin
from boostress.local_settings import *
from django.contrib.auth import get_user_model
from .models import Provider, ServiceType, ProviderPlatform, PlatformService, ServiceTask, Order
from django.db.models.signals import post_migrate


class ProviderAdmin(admin.ModelAdmin):
    list_display = ('api_url', 'name', 'budget')


class ProviderPlatformAdmin(admin.ModelAdmin):
    list_display = ('name',)


class ServiceTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)


class PlatformServiceAdmin(admin.ModelAdmin):
    list_display = ('service_id', 'provider', 'platform', 'service_type', 'link_type', 'min', 'max')


class ServiceTaskAdmin(admin.ModelAdmin):
    list_display = ('status', 'provider', 'platform', 'service', 'link_type', 'link', 'spent')
    readonly_fields = ['spent', ]


class OrderAdmin(admin.ModelAdmin):
    list_display = ('name', 'status', 'platform', 'link_type', 'link', 'spent', 'budget')


admin.site.register(Provider, ProviderAdmin)
admin.site.register(ProviderPlatform, ProviderPlatformAdmin)
admin.site.register(ServiceType, ServiceTypeAdmin)
admin.site.register(PlatformService, PlatformServiceAdmin)
admin.site.register(ServiceTask, ServiceTaskAdmin)
admin.site.register(Order, OrderAdmin)

ADMIN_USER = os.getenv('ADMIN_USER', 'admin')
ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'email@example.com')


def create_superuser(sender, **kwargs):
    user_model = get_user_model()
    if not user_model.objects.filter(username=ADMIN_USER).exists():
        user_model.objects.create_superuser(ADMIN_USER, ADMIN_EMAIL, ADMIN_PASSWORD)


post_migrate.connect(create_superuser)
