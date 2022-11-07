from django.core.management.base import BaseCommand
from django.utils import timezone
from django_site_queue import models
import psutil
from datetime import timedelta, datetime
import requests

class Command(BaseCommand):
    help = 'Delete all sessions in queue,  both active and waiting.'

    def handle(self, *args, **options):
        print ("Starting to delete Queue Sessions")
        models.SiteQueueManager.objects.filter().delete()
        print ("Finished deleting Queue Sessions")
