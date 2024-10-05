import importlib

from django.conf import settings


def get_sms_client():
    module_name, class_name = settings.SMS_CLIENT_CLASS.rsplit(".", 1)
    module = importlib.import_module(module_name)
    client_class = getattr(module, class_name)
    return client_class()
