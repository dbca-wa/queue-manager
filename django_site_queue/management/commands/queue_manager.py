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
        total_active_session = 0
        total_waiting_session = 0
        for queue_group in queue_groups:

            #session_total_limit = 2
            #session_limit_seconds = 20
            #cpu_percentage_limit = 10
            #idle_limit_seconds = 15
            #active_session_url = "/"
            #waiting_queue_enabled = False
            #queue_group_name = 'default'
            #queue_domain = ''
            #queue_url = ''

            #if queue_group.count() > 0:
            session_total_limit = queue_group.session_total_limit
            session_limit_seconds = queue_group.session_limit_seconds
            cpu_percentage_limit = queue_group.cpu_percentage_limit
            idle_limit_seconds = queue_group.idle_limit_seconds
            active_session_url = queue_group.active_session_url
            waiting_queue_enabled = queue_group.waiting_queue_enabled
            queue_group_name = queue_group.group_unique_key
            queue_domain = queue_group.queue_domain
            queue_url = queue_group.queue_url
            ping_url_enabled = queue_group.ping_url_enabled
            ping_url = queue_group.ping_url
            ping_url_limit = queue_group.ping_url_limit
            ping_url_current = queue_group.ping_url_current 

            #session_total_limit = int(env('SESSION_TOTAL_LIMIT', 2))
            #session_limit_seconds = int(env('SESSION_LIMIT_SECONDS', 20))
            #cpu_percentage_limit = int(env('CPU_PERCENTAGE_LIMIT', 10))
            #idle_limit_seconds = int(env('IDLE_LIMIT_SECONDS', 15))
            #active_session_url = env('ACTIVE_SESSION_URL', "/")
            #waiting_queue_enabled = env('WAITING_QUEUE_ENABLED','False')
            #queue_group_name = env('QUEUE_GROUP_NAME','default')
            #queue_domain = env('QUEUE_DOMAIN','')
            #queue_url = env ('QUEUE_URL','')

            memory_session = {}

            idle_seconds = 3000
            expiry_seconds = 3000
            queue_position = 1000
            session_count = 0
            staff_loggedin = False

            session_key = ''

            #print (queue_group)
            #sitesession_query = models.SiteQueueManager.objects.filter(queue_group=queue_group)
            #print (sitesession_query)
            #print (sitesession_query.count())
            #if sitesession_query.count() > 0:

            idle_dt_subtract = datetime.now(timezone.utc)-timedelta(seconds=idle_limit_seconds)
            models.SiteQueueManager.objects.filter(expiry__lte=datetime.now(timezone.utc), status=1, queue_group=queue_group).delete()
            models.SiteQueueManager.objects.filter(idle__lte=idle_dt_subtract, queue_group=queue_group).delete()

            total_active_session = models.SiteQueueManager.objects.filter(status=1, expiry__gte=datetime.now(timezone.utc),is_staff=False, queue_group=queue_group).count()
            total_waiting_session = models.SiteQueueManager.objects.filter(status=0, expiry__gte=datetime.now(timezone.utc), queue_group=queue_group).count()
            cpu_percentage = psutil.cpu_percent(interval=None)

            session_count = models.SiteQueueManager.objects.filter(session_key=sitequeuesession,expiry__gte=datetime.now(timezone.utc),queue_group=queue_group).count()
            stl = session_total_limit

            longest_waiting = models.SiteQueueManager.objects.filter(status=0, expiry__gte=datetime.now(timezone.utc),queue_group=queue_group).order_by('created')[:stl]

            for sitesession in longest_waiting:
                 #sitesession = sitesession_query[0]
                 ##stl = session_total_limit

                 ##sqm = models.SiteQueueManager.objects.filter(status=0, expiry__gte=datetime.now(timezone.utc),queue_group=queue_group).order_by('created')
                 ##


                 ### Clean up stale sessions
                 ##idle_dt_subtract = datetime.now(timezone.utc)-timedelta(seconds=idle_limit_seconds)
                 ##models.SiteQueueManager.objects.filter(expiry__lte=datetime.now(timezone.utc), status=1, queue_group=queue_group).delete()
                 ##models.SiteQueueManager.objects.filter(idle__lte=idle_dt_subtract, queue_group=queue_group).delete()

                 ##total_active_session = models.SiteQueueManager.objects.filter(status=1, expiry__gte=datetime.now(timezone.utc),is_staff=False, queue_group=queue_group).count()
                 ##total_waiting_session = models.SiteQueueManager.objects.filter(status=0, expiry__gte=datetime.now(timezone.utc), queue_group=queue_group).count()
                 ##cpu_percentage = psutil.cpu_percent(interval=None)

                 ##session_count = models.SiteQueueManager.objects.filter(session_key=sitequeuesession,expiry__gte=datetime.now(timezone.utc),queue_group=queue_group).count()


                 #if session_total_limit > 3:
                 #     stl = 3
                 #longest_waiting = models.SiteQueueManager.objects.filter(status=0, expiry__gte=datetime.now(timezone.utc),queue_group=queue_group).order_by('created')[:stl]
                 #print (longest_waiting)
                 #print (longest_waiting)
                 if total_active_session < session_total_limit and sitesession.status != 1:
                       #if cpu_percentage < cpu_percentage_limit:
                       for lw in longest_waiting:
                           if sitesession.session_key == lw.session_key:
                               if ping_url_current > ping_url_limit:
                                   print ("Site Load Response Time Limit (waiting for lower response time '"+str(ping_url_current)+"' ) = "+str(ping_url_limit)) 
                                   sitesession.expiry = datetime.now(timezone.utc)+timedelta(seconds=session_limit_seconds)
                               else:
                                   print ("Session Activated: "+sitesession.session_key)
                                   session_status = 1
                                   sitesession.status = session_status
                                   sitesession.expiry = datetime.now(timezone.utc)+timedelta(seconds=session_limit_seconds)
                           else:
                               sitesession.expiry = datetime.now(timezone.utc)+timedelta(seconds=session_limit_seconds)
                       #else:
                       #    sitesession.expiry = datetime.now(timezone.utc)+timedelta(seconds=session_limit_seconds)

                 if sitesession.status == 0:
                        sitesession.expiry = datetime.now(timezone.utc)+timedelta(seconds=session_limit_seconds)
                 if staff_loggedin is True:
                        session_status = 1
                        sitesession.status = session_status
                        sitesession.expiry = datetime.now(timezone.utc)+timedelta(seconds=session_limit_seconds)
                        sitesession.is_staff=staff_loggedin

                 sitesession.idle=datetime.now(timezone.utc)	
                 sitesession.save()
        print (datetime.now().strftime("%A, %d %b %Y %H:%M:%S")+" : ACTIVE Sessions ("+str(total_active_session)+") Waiting Sessions ("+str(total_waiting_session)+")")

