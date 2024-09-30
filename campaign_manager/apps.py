from django.apps import AppConfig


class CampaignManagerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'campaign_manager'

    def ready(self):
        from campaign_manager import signals
