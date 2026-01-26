from django.core.management.base import BaseCommand
# from django.utils import timezone
# from django_site_queue import models
import psutil
from datetime import timedelta, datetime, timezone
import requests
from django_site_queue import  jsondb
from django.utils import timezone as dj_tz
import shutil
import os

PLUS_8 = timezone(timedelta(hours=8))

class Command(BaseCommand):
    help = 'Clear out any expired temporary bookings that have been abandoned by the user'

    def handle(self, *args, **options):

        sitequeuesession = None
        sitesession = None

        # this need to change look up queue groups in db/json/queue_groups 
        print ("Purging idle sessions")
        queue_groups = jsondb.get_queue_groups()
        for queue_group in queue_groups:
            jsondb.delete_waiting_expiry_idle_sessions(queue_group["group_unique_key"])