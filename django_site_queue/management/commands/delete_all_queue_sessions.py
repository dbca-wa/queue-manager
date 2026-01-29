from django.core.management.base import BaseCommand
from django.utils import timezone
# from django_site_queue import models
import psutil
from datetime import timedelta, datetime
from django_site_queue import jsondb
import requests

class Command(BaseCommand):
    help = 'Delete all sessions in queue,  both active and waiting.'

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument('queue_group', nargs='+', type=str)

    def handle(self, *args, **options):
        print ("Starting to delete Queue Sessions")
        queue_group = options['queue_group'][0]        
        deleted_sessions = jsondb.delete_all_sessions(queue_group)
        print ("Deleted Sessions {}".format(str(deleted_sessions)))
        print ("Finished deleting Queue Sessions")
