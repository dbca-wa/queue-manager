from django.core.management.base import BaseCommand
# from django.utils import timezone
# from django_site_queue import models
import psutil
from datetime import timedelta, datetime, timezone
from django.conf import settings
import requests
from django_site_queue import  jsondb
from django.utils import timezone as dj_tz
from filelock import FileLock
import shutil
import os
import time
from django.utils.crypto import get_random_string
from  pathlib import Path

PLUS_8 = timezone(timedelta(hours=8))

class Command(BaseCommand):
    help = 'Update Waiting Queue Total'

    def handle(self, *args, **options):

        sitequeuesession = None
        sitesession = None

        # this need to change look up queue groups in db/json/queue_groups
        # queue_groups = ["parkstayv2"]
        queue_groups = jsondb.get_queue_groups()
        
        total_active_session = 0
        total_waiting_session = 0
        for queue_group in queue_groups:
            session_total_limit = queue_group["session_total_limit"]
            queue_group_name = queue_group["group_unique_key"]
            total_waiting_session = jsondb.get_waiting_session_total(queue_group_name)                                                
            data = {"total_waiting_session": total_waiting_session}
            jsondb.save_queue_waiting_total(data,queue_group_name)
