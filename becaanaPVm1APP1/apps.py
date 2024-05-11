from django.apps import AppConfig

class YourAppConfig(AppConfig):

    name = 'becaanaPVm1APP1'

    def ready(self):
        from . import signals # import your signals.py