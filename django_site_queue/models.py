from __future__ import unicode_literals
from datetime import timedelta
from django.conf import settings
from django.contrib.gis.db import models
from django.contrib.postgres.fields import JSONField
from django.urls import reverse
#from django.utils.encoding import python_2_unicode_compatible
#from model_utils import Choices
from django.contrib.auth.models import Group
from django.core.files.storage import FileSystemStorage
from django.core.exceptions import ValidationError


class SiteQueueManagerGroup(models.Model):

    _DATABASE = "site_queue_manager"
    group_name = models.CharField(max_length=256)
    group_unique_key = models.CharField(max_length=40)
    session_total_limit = models.IntegerField(default=2)
    session_limit_seconds = models.IntegerField(default=20)
    cpu_percentage_limit = models.IntegerField(default=60)
    idle_limit_seconds = models.IntegerField(default=15)
    active_session_url_label = models.CharField(max_length=1024, default='This Site')
    active_session_url = models.CharField(max_length=1024)
    waiting_queue_enabled = models.BooleanField(default=False)
    queue_domain = models.CharField(max_length=256)
    queue_url = models.CharField(max_length=256)
    time_left_enabled = models.BooleanField(default=False)
    show_queue_position = models.BooleanField(default=False)
    max_queue_session_limit = models.IntegerField(default=1000)
    max_queue_url_redirect = models.CharField(max_length=256, default='')

    queue_name = models.CharField(max_length=256, help_text="Queue header name to appear on public waiting queue. ", blank=True, null=True)
    custom_message = models.TextField(blank=True, null=True, max_length=650, help_text="Short message to explain the reason for the waiting queue")
    more_info_link = models.CharField(max_length=512, help_text="More info link on public waiting queue", blank=True, null=True)
    browser_inactivity_enabled = models.BooleanField(default=False)
    browser_inactivity_timeout = models.IntegerField(default=60)
    browser_inactivity_redirect = models.CharField(max_length=1024, default='',null=True, blank=True)

    ping_url_enabled = models.BooleanField(default=False)
    ping_url = models.CharField(max_length=1024, default='')
    ping_url_limit = models.FloatField(default=5)
    ping_url_current = models.FloatField(default=0, editable=False)

    template_header_key=models.CharField(max_length=100, default='')

    def __str__(self):
        return self.group_name

#@python_2_unicode_compatible
class SiteQueueManager(models.Model):
    _DATABASE = "site_queue_manager"

    QUEUE_STATUS = (
        (0, 'Waiting'),        # not used
        (1, 'Active'),
    )

    session_key = models.CharField(max_length=256)
    idle = models.DateTimeField(blank=True, null=True)
    expiry = models.DateTimeField(blank=True, null=True)
    status = models.SmallIntegerField(choices=QUEUE_STATUS, default=0)
    ipaddress = models.CharField(max_length=100)
    is_staff = models.BooleanField(default=False)
    queue_group_name = models.CharField(max_length=256, blank=True, null=True)
    queue_group = models.ForeignKey('SiteQueueManagerGroup',  on_delete=models.PROTECT)
    browser_agent = models.CharField(max_length=300, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)

    class Meta:
        managed = True

    def __str__(self):
        return self.session_key


class SiteQueueManagerDBRouter(object):

    def db_for_read(self, model, **hints):
       if model._meta.db_table == 'django_site_queue_sitequeuemanager':
           return 'site_queue_manager'
       return 'default'

    def db_for_write(self, model, **hints):
        if model._meta.db_table == 'django_site_queue_sitequeuemanager':
           return 'site_queue_manager'
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Make sure the auth and contenttypes apps only appear in the
        'auth_db' database.
        """
        if model_name == 'sitequeuemanager':
           db = 'site_queue_manager'
           return settings.DATABASE_APPS_MAPPING.get('site_queue_manager')
        return None
