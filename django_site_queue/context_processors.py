"""Context processors for the Django project."""


# Third-Party
from django import conf
from django import http
from django_site_queue import models
from django.conf import settings
# Typing
from typing import Any


def variables(request):
    """Constructs a context dictionary to be passed to the templates.
    Args:
        request (http.HttpRequest): HTTP request object.
    Returns:
        dict[str, Any]: Context for the templates.
    """


    print (request.path)

    # Construct and return context
    return {
        "template_group": "dbcablack",
        #"template_group": "parksv2",
        "template_title": "Queue System",
        "GIT_COMMIT_HASH": conf.settings.GIT_COMMIT_HASH,
        "DJANGO_SETTINGS" : settings
    }