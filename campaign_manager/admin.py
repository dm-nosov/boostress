import os
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from boostress.local_settings import *
from django.contrib.auth import get_user_model
from .models import Provider, ServiceType, ProviderPlatform, PlatformService, ServiceTask, Order, ServiceHealthLog
from django.db.models.signals import post_migrate
from django_celery_results.models import TaskResult
from django_celery_results.admin import TaskResultAdmin

from version import VERSION

admin.site.site_header = 'Boostress Admin {}'.format(VERSION)

class ProviderAdmin(admin.ModelAdmin):
    list_display = ('api_url', 'name', 'budget')


class ProviderPlatformAdmin(admin.ModelAdmin):
    list_display = ('name',)


class ServiceTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)


class PlatformServiceAdmin(admin.ModelAdmin):
    def enable_tasks(modeladmin, request, queryset):
        queryset.update(is_enabled=True)
        modeladmin.message_user(request, "Selected tasks have been enabled.")

    def disable_tasks(modeladmin, request, queryset):
        queryset.update(is_enabled=False)
        modeladmin.message_user(request, "Selected tasks have been disabled.")

    actions = [enable_tasks, disable_tasks]
    list_display = ('is_enabled', 'service_id', 'provider', 'platform', 'service_type', 'link_type', 'min', 'max')


class ServiceTaskAdmin(admin.ModelAdmin):
    list_display = ('status', 'provider', 'platform', 'service', 'link_type', 'link', 'spent')
    readonly_fields = ['spent', 'created', 'updated']


class ServiceTaskInline(admin.TabularInline):
    model = ServiceTask
    extra = 0  # No extra empty forms
    can_delete = False

    def get_clickable_link(self, obj):
        value = getattr(obj, 'status')
        if hasattr(value, 'pk'):  # If it's a related object
            url = reverse(f'admin:{value._meta.app_label}_{value._meta.model_name}_change', args=[value.pk])
        else:  # If it's a regular field
            url = reverse(f'admin:{obj._meta.app_label}_{obj._meta.model_name}_change', args=[obj.pk])
        return format_html('<a href="{}">{}</a>', url, value)

    readonly_fields = ['get_clickable_link', 'provider', 'platform', 'get_service_type', 'get_link_type', 'spent',
                       'created', 'updated']  # Make all fields readonly
    fields = (
        'get_clickable_link', 'provider', 'platform', 'get_service_type', 'get_link_type', 'spent', 'created',
        'updated')
    max_num = 0  # Prevents adding new books

    def get_service_type(self, obj):
        return obj.service.service_type if obj.service else None

    def get_link_type(self, obj):
        return obj.service.link_type if obj.service else None


class OrderAdmin(admin.ModelAdmin):
    inlines = [ServiceTaskInline]
    list_display = ('name', 'status', 'platform', 'link_type', 'link', 'budget', 'spent', 'created')
    readonly_fields = ['spent', 'created', 'updated']

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if obj is None:  # This is a new object being created
            last_order = Order.objects.last()
            next_id = last_order.id + 1 if last_order else 1
            form.base_fields['name'].initial = "Order {}, ".format(next_id)
        return form


class CustomTaskResultAdmin(TaskResultAdmin):
    list_display = ('task_id', 'periodic_task_name', 'date_done',
                    'status', 'result')
    search_fields = TaskResultAdmin.search_fields + ('result', 'periodic_task_name')


class ServiceHealthLogAdmin(admin.ModelAdmin):
    list_display = ('entry', 'created')
    readonly_fields = ['entry']


admin.site.unregister(TaskResult)
admin.site.register(TaskResult, CustomTaskResultAdmin)

admin.site.register(Provider, ProviderAdmin)
admin.site.register(ProviderPlatform, ProviderPlatformAdmin)
admin.site.register(ServiceType, ServiceTypeAdmin)
admin.site.register(PlatformService, PlatformServiceAdmin)
admin.site.register(ServiceTask, ServiceTaskAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(ServiceHealthLog, ServiceHealthLogAdmin)

ADMIN_USER = os.getenv('ADMIN_USER', 'admin')
ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'email@example.com')


def create_superuser(sender, **kwargs):
    user_model = get_user_model()
    if not user_model.objects.filter(username=ADMIN_USER).exists():
        user_model.objects.create_superuser(ADMIN_USER, ADMIN_EMAIL, ADMIN_PASSWORD)


post_migrate.connect(create_superuser)
