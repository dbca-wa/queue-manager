from django.core.management.base import BaseCommand
# from django.utils import timezone
# from django_site_queue import models
import psutil
from datetime import timedelta, datetime, timezone
import requests
from django_site_queue import  jsondb
from django.utils import timezone as dj_tz
from filelock import FileLock
import shutil
import os
import time
PLUS_8 = timezone(timedelta(hours=8))

class Command(BaseCommand):
    help = 'Clear out any expired temporary bookings that have been abandoned by the user'

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument('start', nargs='+', type=int)    
        parser.add_argument('finish', nargs='+', type=int)    

    def handle(self, *args, **options):
        start = options['start'][0]   
        finish = options['finish'][0]   
        sitequeuesession = None
        sitesession = None

        # this need to change look up queue groups in db/json/queue_groups
        # queue_groups = ["parkstayv2"]
        queue_groups = jsondb.get_queue_groups()
        
        total_active_session = 0
        total_waiting_session = 0
        for queue_group in queue_groups:
            queue_group_name = queue_group["group_unique_key"]
            jsondb.wait_queue_rotate(queue_group_name, start, finish)