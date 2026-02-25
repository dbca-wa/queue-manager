from django.core.management.base import BaseCommand
from django.utils import timezone
# from django_site_queue import models
import psutil
from datetime import timedelta, datetime
from django_site_queue import jsondb
import requests

class Command(BaseCommand):
    help = 'Delete all sessions in queue,  both active and waiting.'

    def handle(self, *args, **options):
        print ("Starting to delete Queue Sessions")
        queue_groups = jsondb.get_queue_groups()
        for queue_group in queue_groups:       
            group_unique_key = queue_group["group_unique_key"]         
            active_sessions = jsondb.delete_active_expiry_idle_sessions(group_unique_key)
            deleted_sessions = jsondb.clean_recently_deleted(group_unique_key)
            expired_queue_positons = jsondb.clean_queue_position_sessions(group_unique_key)
            idle_queue_positons = jsondb.clean_queue_idle_sessions(group_unique_key)
            print ("Deleted Sessions {}".format(str(deleted_sessions)))
            print ("Finished deleting Queue Sessions")