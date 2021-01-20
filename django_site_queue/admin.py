from django.contrib.gis import admin
from django.contrib.admin import AdminSite
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from django_site_queue import models


@admin.register(models.SiteQueueManagerGroup)
class SiteQueueManagerGroupAdmin(admin.ModelAdmin):
    list_display = ('id','group_name','group_unique_key','session_total_limit','session_limit_seconds','cpu_percentage_limit','idle_limit_seconds','active_session_url','waiting_queue_enabled','queue_domain','queue_url','ping_url_enabled','ping_url','ping_url_limit','ping_url_current')


@admin.register(models.SiteQueueManager)
class SiteQueueManagerClassAdmin(admin.ModelAdmin):
    list_display = ('id','idle','expiry','status','ipaddress','is_staff','created','queue_group','session_key','browser_agent',)
    search_fields = ('ipaddress','session_key',)
    list_filter = ('ipaddress','status','queue_group',)

