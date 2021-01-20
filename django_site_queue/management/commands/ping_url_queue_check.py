from django.core.management.base import BaseCommand
from django.utils import timezone
from django_site_queue import models
import psutil
from datetime import timedelta, datetime
import requests

class Command(BaseCommand):
    help = 'Clear out any expired temporary bookings that have been abandoned by the user'

    def handle(self, *args, **options):

        sitequeuesession = None
        sitesession = None

        queue_groups = models.SiteQueueManagerGroup.objects.filter(waiting_queue_enabled=True)
        for queue_group in queue_groups:

            ping_url_enabled = queue_group.ping_url_enabled
            ping_url = queue_group.ping_url
            ping_url_limit = queue_group.ping_url_limit
            ping_url_current = queue_group.ping_url_current 

            memory_session = {}

            idle_seconds = 3000
            expiry_seconds = 3000
            queue_position = 1000
            session_count = 0
            staff_loggedin = False

            session_key = ''
          
            if ping_url_enabled is True:
                try:
                    ping_url_current = requests.get(ping_url, verify=False, timeout=30).elapsed.total_seconds()
                except:
                    print ("Error loading: Site Load Time ("+ping_url+")")
                    ping_url_current = 1000
                queue_group.ping_url_current= ping_url_current
                queue_group.save()

                print (datetime.now().strftime("%A, %d %b %Y %H:%M:%S")+" : Site Load Time ("+ping_url+") : ("+str(ping_url_current)+"s)")

