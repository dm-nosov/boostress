import csv

from django.contrib import admin
from django.contrib.admin import widgets
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import path

from .models import Agent, AgentResource, Endpoint, AgentOpResult, AgentService


class AgentOpResultAdmin(admin.ModelAdmin):
    list_display = ('endpoint', 'created', 'ref_id', 'ref_url', 'is_fwd')


class AgentResourceAdmin(admin.ModelAdmin):
    list_display = ('created', 'url', 'is_active')

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'import/',
                self.admin_site.admin_view(self.import_view),
                name='model-import',
            ),
        ]
        return custom_urls + urls

    def get_import_formats(self):
        return [
            {'name': 'CSV', 'extension': 'csv'},
        ]

    def import_data(self, request, *args, **kwargs):
        if 'csv' in request.FILES:
            csv_file = request.FILES['csv']
            reader = csv.DictReader(csv_file.read().decode('utf-8').splitlines())
            objects = []
            for row in reader:
                obj = AgentResource(
                    url=row['url'],
                    is_active=True,
                )
                if not AgentResource.objects.filter(url=obj.url):
                    objects.append(obj)
            AgentResource.objects.bulk_create(objects)
            return HttpResponse("Data imported successfully!")
        return HttpResponse("No CSV file found.")

    def import_view(self, request):
        if request.method == 'POST':
            return self.import_data(request)
        context = {
            'title': 'Import Data',
            'site_url': '/',
        }
        return render(request, 'admin/import.html', context)

# Register your models here
admin.site.register(Agent)
admin.site.register(AgentService)
admin.site.register(Endpoint)
admin.site.register(AgentOpResult, AgentOpResultAdmin)
admin.site.register(AgentResource, AgentResourceAdmin)
