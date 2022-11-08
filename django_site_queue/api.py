import traceback
import base64
import json
from six.moves.urllib.parse import urlparse
from wsgiref.util import FileWrapper
from django.db import connection, transaction
from django.db.models import Q, Min
from django.http import HttpResponse
from django.core.files.base import ContentFile
from django.core.exceptions import ValidationError
from django.conf import settings
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django_site_queue import models
from django.utils.crypto import get_random_string
from datetime import datetime, timedelta
from django.utils import timezone
from confy import env
from django.urls import reverse
import psutil

# NOTE
# Add Internal User login check and ignore staff membbers from queue checks - DONE
# Add CPU Checks DONE
# Delete old sessions idle and expired - DONE
# Create ENVIRONMENT VAIRABLES DONE
# Disable Option for DEV DONE
# inject into map screen DONE
# README DONE

# Improve queue algorithm - more work on queue order

def check_create_session(request, *args, **kwargs):
    
    sitequeuesession = None
    sitesession = None

    queue_group = models.SiteQueueManagerGroup.objects.filter(group_unique_key=request.GET['queue_group']) 

    session_total_limit = 2
    session_limit_seconds = 20
    cpu_percentage_limit = 10
    idle_limit_seconds = 15
    active_session_url = "/"
    waiting_queue_enabled = False
    queue_group_name = 'default'
    queue_domain = ''
    queue_url = ''
    time_left_enabled = False
    show_queue_position = False
    max_queue_session_limit = 10000
    max_queue_url_redirect = ''
    ping_url_enabled = False
    ping_url = ''
    ping_url_limit = 100
    ping_url_current = 0

    #defaults
    total_active_session = 0
    total_waiting_session = 0
    wait_time = 100
    browser_inactivity_timeout = 300
    browser_inactivity_redirect = '/'
    browser_inactivity_enabled = False
    custom_message = ''
    queue_name = ''
    more_info_link =''
    if queue_group.count() > 0:
        session_total_limit = queue_group[0].session_total_limit
        session_limit_seconds = queue_group[0].session_limit_seconds
        cpu_percentage_limit = queue_group[0].cpu_percentage_limit
        idle_limit_seconds = queue_group[0].idle_limit_seconds
        max_queue_session_limit = queue_group[0].max_queue_session_limit
        active_session_url = queue_group[0].active_session_url
        waiting_queue_enabled = queue_group[0].waiting_queue_enabled
        queue_group_name = queue_group[0].group_unique_key
        queue_domain = queue_group[0].queue_domain
        queue_url = queue_group[0].queue_url
        time_left_enabled = queue_group[0].time_left_enabled
        max_queue_url_redirect = queue_group[0].max_queue_url_redirect
        show_queue_position = queue_group[0].show_queue_position
        custom_message = queue_group[0].custom_message

        ping_url_enabled = queue_group[0].ping_url_enabled
        ping_url = queue_group[0].ping_url
        ping_url_limit = queue_group[0].ping_url_limit
        ping_url_current = queue_group[0].ping_url_current
        browser_inactivity_timeout = queue_group[0].browser_inactivity_timeout
        browser_inactivity_redirect = queue_group[0].browser_inactivity_redirect
        browser_inactivity_enabled = queue_group[0].browser_inactivity_enabled
        queue_name = queue_group[0].queue_name
        more_info_link = queue_group[0].more_info_link


    memory_session = {}

    idle_seconds = 3000
    expiry_seconds = 3000
    queue_position = 1000
    session_count = 0
    staff_loggedin = False
     
    session_key = '' 
    #print (request.COOKIES)
    try:
        if 'session_key' in request.GET:
            if len(request.GET['session_key']) > 10: 
                 #print( "request.GET")
            #session_key = request.COOKIES['sitequeuesession']
                 session_key = request.GET['session_key']
                 #if 'sitequeuesession' in memory_session:
                      #if memory_session['sitequeuesession'] == session_key:
                      #   pass
                      #else:
                 memory_session['sitequeuesession'] = session_key
                 memory_session['sitequeuesession_getcreated'] = 'yes'
                 memory_session['sitequeuesession_ipaddress'] = get_client_ip(request)
                 memory_session['sitequeuesession_created'] = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
                 memory_session['sitequeuesession_agent'] = request.META['HTTP_USER_AGENT']
                 #else:
                 #        memory_session['sitequeuesession'] = session_key
                 #        memory_session['sitequeuesession_getcreated'] = 'yes'
                 #        memory_session['sitequeuesession_ipaddress'] = get_client_ip(request)
                 #        memory_session['sitequeuesession_created'] = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
                 #        memory_session['sitequeuesession_agent'] = request.META['HTTP_USER_AGENT']

        #if request.GET['session_key'] == "":
        #    print ("NEW")
        #    print (memory_session)
        #    print (request.COOKIES)

        if 'sitequeuesession' not in memory_session:
             if 'sitequeuesession' in request.COOKIES:
                  print ("request.COOKIES")
                  session_key = request.COOKIES.get('sitequeuesession','')
                  memory_session['sitequeuesession'] = session_key
                  memory_session['sitequeuesession_getcreated'] = 'cookie'
                  memory_session['sitequeuesession_ipaddress'] = get_client_ip(request)
                  memory_session['sitequeuesession_created'] = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
                  memory_session['sitequeuesession_agent'] = request.META['HTTP_USER_AGENT']
        
        #print (request.session['sitequeuesession'])

        # Clean up stale sessions
        idle_dt_subtract = datetime.now(timezone.utc)-timedelta(seconds=idle_limit_seconds)
        models.SiteQueueManager.objects.filter(expiry__lte=datetime.now(timezone.utc), status=1, queue_group=queue_group[0]).delete()
        models.SiteQueueManager.objects.filter(idle__lte=idle_dt_subtract, queue_group=queue_group[0]).delete()

        if request.user.is_authenticated:
             if request.user.is_staff is True:
                   pass
                   #staff_loggedin = True

        total_active_session = models.SiteQueueManager.objects.filter(status=1, expiry__gte=datetime.now(timezone.utc),is_staff=False,queue_group=queue_group[0]).count()
        total_waiting_session = models.SiteQueueManager.objects.filter(status=0, expiry__gte=datetime.now(timezone.utc),queue_group=queue_group[0]).count()
        cpu_percentage = psutil.cpu_percent(interval=None)
        #print (cpu_percentage)
        if 'sitequeuesession' in memory_session:
             sitequeuesession = memory_session['sitequeuesession']
        else:
             memory_session['sitequeuesession']  = None 


        #### 
        session_count = models.SiteQueueManager.objects.filter(session_key=sitequeuesession,expiry__gte=datetime.now(timezone.utc),queue_group=queue_group[0]).count()
        #if settings.DEBUG is True:

        if sitequeuesession is None or session_count == 0:
            print ('CREATION')
            session_status = 0
            #if total_active_session >= session_total_limit:
            # START -- Disabling, will send everyone to queue and the cron job give fairer allocated spots 
            #if total_active_session < session_total_limit and total_waiting_session == 0:
            #      session_status = 1
            # END --
            if ping_url_current > ping_url_limit:
                  session_status = 0
            if cpu_percentage > cpu_percentage_limit:
                  session_status = 0
            if staff_loggedin is True:
                  session_status = 1

            #if session_key:
            #     pass
            #else: 
            browser_agent = ''
            if 'HTTP_USER_AGENT' in request.META:
               browser_agent = request.META['HTTP_USER_AGENT']

            session_key = get_random_string(length=60, allowed_chars=u'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
            expiry=datetime.now(timezone.utc)+timedelta(seconds=session_limit_seconds)
            sitesession = models.SiteQueueManager.objects.create(session_key=session_key,idle=datetime.now(timezone.utc), expiry=expiry,status=session_status,ipaddress=get_client_ip(request), is_staff=staff_loggedin,queue_group=queue_group[0], browser_agent=browser_agent)

            memory_session['sitequeuesession'] = session_key
            memory_session['sitequeuesession_ipaddress'] = get_client_ip(request) 
            memory_session['sitequeuesession_created'] = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
            memory_session['sitequeuesession_getcreated'] = 'no'
            request.COOKIES['sitequeuesession'] = session_key
            memory_session['sitequeuesession_agent'] = request.META['HTTP_USER_AGENT']
        else:
            if models.SiteQueueManager.objects.filter(session_key=sitequeuesession).count() > 0:
                 sitesession_query = models.SiteQueueManager.objects.filter(session_key=sitequeuesession,queue_group=queue_group[0])
                 sitesession = sitesession_query[0]
                 # check if expired and create new one below
                 stl = session_total_limit
                 #if session_total_limit > 3:
                 #     stl = 3



                 #longest_waiting = models.SiteQueueManager.objects.filter(status=0, expiry__gte=datetime.now(timezone.utc),queue_group=queue_group[0]).order_by('created')[:stl]
                 ##print (longest_waiting)
                 #if total_active_session < session_total_limit and sitesession.status != 1:
                 #      if cpu_percentage < cpu_percentage_limit:
                 #           for lw in longest_waiting:
                 #               if memory_session['sitequeuesession'] == lw.session_key:
                 #                   session_status = 1
                 #                   sitesession.status = session_status
                 #                   sitesession.expiry = datetime.now(timezone.utc)+timedelta(seconds=session_limit_seconds)
                 #               else:
                 #                   sitesession.expiry = datetime.now(timezone.utc)+timedelta(seconds=session_limit_seconds)
                 #      else:
                 #          sitesession.expiry = datetime.now(timezone.utc)+timedelta(seconds=session_limit_seconds)

                 #if sitesession.status == 0:
                 #       sitesession.expiry = datetime.now(timezone.utc)+timedelta(seconds=session_limit_seconds)
                 ##if staff_loggedin is True:
                 ##       session_status = 1
                 ##       sitesession.status = session_status
                 ##       sitesession.expiry = datetime.now(timezone.utc)+timedelta(seconds=session_limit_seconds)
                 ##       sitesession.is_staff=staff_loggedin

                 sitesession.idle=datetime.now(timezone.utc)
                 sitesession.save()
            else:
                 raise ValidationError("Error no session Found")

        #queue_position =0
        if models.SiteQueueManager.objects.filter(session_key=session_key).count() > 0:
             sqm =  models.SiteQueueManager.objects.filter(session_key=session_key)[0]
             queue_position = models.SiteQueueManager.objects.filter(id__lte=sqm.id, status=0, expiry__gt=datetime.now(timezone.utc),queue_group=queue_group[0]).order_by('id').count()


        idle_seconds = (datetime.now(timezone.utc)-sitesession.idle).seconds
        expiry_seconds = (sitesession.expiry-datetime.now(timezone.utc)).seconds
        wait_time = 100 
        if queue_position > 0:
           # calculate wait time
           queue_avg_position = int(queue_position) / int(session_total_limit)
           session_limit_minutes = round(session_limit_seconds / 60)
           wait_time = round(queue_avg_position * session_limit_minutes)
        #if expiry_seconds < 1:
        #      request.session['sitequeuesession'] = None
        #      if total_active_session <= session_total_limit and total_waiting_session == 0:
        #          sitesession.status = 1
        #          sitesession.expiry = datetime.now(timezone.utc)+timedelta(seconds=session_limit_seconds)
        #      else:
        #          sitesession.status = 0
        #          sitesession.expiry = datetime.now(timezone.utc)
        #      sitesession.save() 

        #if idle_limit_seconds > idle_seconds and sitesession.status == 1:
        #booking = utils.get_session_booking(request.session)
        #request.session['sitequeuesession'] = "ThisisaQueueSession"
    except Exception as e:
        print (e)
        pass
    if waiting_queue_enabled == False or waiting_queue_enabled == "False":
         if sitesession is None:
             mydict = {'status': 1, 'idle': None, 'expiry': None}
             sitesession = dotdict(mydict) 
         sitesession.status = 1
         sitesession.idle = datetime.now(timezone.utc)
         sitesession.expiry = datetime.now(timezone.utc)+timedelta(hours=10)

    
    CORS_SITES = env('CORS_SITES', None)
    QUEUE_DOMAIN = env('QUEUE_DOMAIN', '')

    if settings.DEBUG is True:    
        print (sitesession)
        response = HttpResponse(json.dumps({'url':active_session_url, 'queueurl': reverse('site-queue-page'),'session': memory_session['sitequeuesession'], 'idle_seconds':idle_seconds,'expiry': sitesession.expiry.strftime('%d/%m/%Y %H:%M'), 'idle': sitesession.idle.strftime('%d/%m/%Y %H:%M'),'status': models.SiteQueueManager.QUEUE_STATUS[sitesession.status][1],'total_active_session': total_active_session, 'total_waiting_session': total_waiting_session,'expiry_seconds': expiry_seconds,'session_key': session_key, 'queue_position' : queue_position ,'wait_time' : wait_time ,'waiting_queue_enabled': waiting_queue_enabled, 'wq': env('WAITING_QUEUE_ENABLED','False'), 'time_left_enabled': time_left_enabled, 'browser_inactivity_timeout': browser_inactivity_timeout, 'browser_inactivity_redirect': browser_inactivity_redirect, 'browser_inactivity_enabled': browser_inactivity_enabled,'custom_message': custom_message,'queue_name': queue_name, 'more_info_link' : more_info_link, 'show_queue_position': show_queue_position, 'max_queue_session_limit': max_queue_session_limit, 'max_queue_url_redirect': max_queue_url_redirect }), content_type='application/json')
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        response["Access-Control-Max-Age"] = "0"
        response["Access-Control-Allow-Headers"] = "*"
        response["X-Frame-Options"] = "allow-from *"

        response.set_cookie('sitequeuesession', session_key, max_age=2592000, samesite=None, domain=QUEUE_DOMAIN)
        return response
    else:
        #response = HttpResponse(json.dumps({'url':active_session_url, 'queueurl': reverse('site-queue-page'),'status': models.SiteQueueManager.QUEUE_STATUS[sitesession.status][1],'session_key': session_key, 'queue_position' : queue_position, 'wait_time' : wait_time, 'time_left_enabled': time_left_enabled,'browser_inactivity_timeout': browser_inactivity_timeout, 'browser_inactivity_redirect': browser_inactivity_redirect,  'waiting_queue_enabled': waiting_queue_enabled, 'browser_inactivity_enabled': browser_inactivity_enabled,'custom_message': custom_message, 'custom_message': custom_message,'queue_name': queue_name, 'more_info_link' : more_info_link  }), content_type='application/json')
        response = HttpResponse(json.dumps({'url':active_session_url, 'queueurl': reverse('site-queue-page'),'session': memory_session['sitequeuesession'], 'idle_seconds':idle_seconds,'expiry': sitesession.expiry.strftime('%d/%m/%Y %H:%M'), 'idle': sitesession.idle.strftime('%d/%m/%Y %H:%M'),'status': models.SiteQueueManager.QUEUE_STATUS[sitesession.status][1],'total_active_session': total_active_session, 'total_waiting_session': total_waiting_session,'expiry_seconds': expiry_seconds,'session_key': session_key, 'queue_position' : queue_position ,'wait_time' : wait_time ,'waiting_queue_enabled': waiting_queue_enabled, 'wq': env('WAITING_QUEUE_ENABLED','False'), 'time_left_enabled': time_left_enabled, 'browser_inactivity_timeout': browser_inactivity_timeout, 'browser_inactivity_redirect': browser_inactivity_redirect, 'browser_inactivity_enabled': browser_inactivity_enabled,'custom_message': custom_message,'queue_name': queue_name, 'more_info_link' : more_info_link, 'show_queue_position': show_queue_position, 'max_queue_session_limit' : max_queue_session_limit, 'max_queue_url_redirect': max_queue_url_redirect }), content_type='application/json')
        response["Access-Control-Allow-Origin"] = "*" 
        response["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        response["Access-Control-Max-Age"] = "0"
        response["Access-Control-Allow-Headers"] = "*"
        response["X-Frame-Options"] = "allow-from *"
        response.set_cookie('sitequeuesession', session_key, max_age=2592000, domain=QUEUE_DOMAIN)
        return response

def get_client_ip(request):
    x_real_ip = request.META.get('HTTP_X_REAL_IP')
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')

    if x_real_ip:
       ip = x_real_ip
    elif x_forwarded_for:
       ip = x_forwarded_for.split(',')[-1].strip()
    else:
       ip = request.META.get('REMOTE_ADDR')
    return ip


class dotdict(dict):
    """dot.notation access to dictionary attributes"""
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__
#
#    session_key = models.CharField(max_length=256)
#    idle = models.DateTimeField(blank=True, null=True)
#    expiry = models.DateTimeField(blank=True, null=True)
#    status = models.SmallIntegerField(choices=QUEUE_STATUS, default=0)
#    ipaddress = models.CharField(max_length=100)
#    created = models.DateTimeField(auto_now_add=True, editable=False)
#
