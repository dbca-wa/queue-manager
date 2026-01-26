import traceback
import base64
import json
# from six.moves.urllib.parse import urlparse
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
# from django.utils import timezone
# from django_site_queue import models
from django.utils.crypto import get_random_string
from datetime import datetime, timedelta, timezone
from django_site_queue import  jsondb
# from django.utils import timezone
from confy import env
from django.urls import reverse
from django.utils import timezone as dj_tz
import psutil
import time
from wagov_utils.components.json_auth.auth_middleware_backend import _JSONAuthStore

PLUS_8 = timezone(timedelta(hours=8))
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
    QUEUE_URL_ENV = settings.QUEUE_URL
    queue_group_name = request.GET['queue_group']
    script_exempt_key = request.GET.get('script_exempt_key',None)
    # queue_group = models.SiteQueueManagerGroup.objects.filter(group_unique_key=request.GET['queue_group']) 

    queue_group = jsondb.get_queue_group(queue_group_name)

    group_unique_key = 'unknown'
    if queue_group is None:
        print ("THIS RESPONSE 1")
        response = HttpResponse(json.dumps({'status_code': 500, 'message': 'unable to find site queue manager group'}), content_type='application/json', status=500)
        # response.set_cookie('sitequeuesession', session_key, max_age=2592000, domain=QUEUE_DOMAIN)
        return response

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
    queue_inactivity_url =''
    queue_waiting_room_url = ''
    if queue_group:
        group_unique_key = queue_group["group_unique_key"]
        queue_inactivity_url = QUEUE_URL_ENV+'/site-queue/queue-expired/'+group_unique_key+'/'
        queue_waiting_room_url = QUEUE_URL_ENV+'/site-queue/waiting-room/'+group_unique_key+'/'
        session_total_limit = queue_group["session_total_limit"]
        session_limit_seconds = queue_group["session_limit_seconds"]
        cpu_percentage_limit = queue_group["cpu_percentage_limit"]
        idle_limit_seconds = queue_group["idle_limit_seconds"]
        max_queue_session_limit = queue_group["max_queue_session_limit"]
        active_session_url = queue_group["active_session_url"]
        waiting_queue_enabled = queue_group["waiting_queue_enabled"]
        queue_group_name = queue_group["group_unique_key"]
        queue_domain = queue_group["queue_domain"]
        queue_url = queue_group["queue_url"]
        time_left_enabled = queue_group["time_left_enabled"]
        max_queue_url_redirect = queue_group["max_queue_url_redirect"]
        show_queue_position = queue_group["show_queue_position"]
        custom_message = queue_group["custom_message"]

        ping_url_enabled = queue_group["ping_url_enabled"]
        ping_url = queue_group["ping_url"]
        ping_url_limit = float(queue_group["ping_url_limit"])
        # ping_url_current = queue_group["ping_url_current"]
        browser_inactivity_timeout = queue_group["browser_inactivity_timeout"]
        browser_inactivity_redirect = queue_group["browser_inactivity_redirect"]
        browser_inactivity_enabled = queue_group["browser_inactivity_enabled"]
        queue_name = queue_group["queue_name"]
        more_info_link = queue_group["more_info_link"]

        ping_url_current = 0
        try:
            ping_url_current_obj =jsondb.get_queue_ping(queue_group_name)
            if ping_url_current_obj:
                    if "ping_response" in ping_url_current_obj:
                        
                        ping_url_current= float(ping_url_current_obj["ping_response"])
                        
        except Exception as e:
            print ("PING Response error")
            print (e)


    memory_session = {}

    idle_seconds = 3000
    expiry_seconds = 3000
    queue_position = 1000
    session_count = 0
    staff_loggedin = False
     
    session_key = '' 

    try:
        
        if 'session_key' in request.GET:

            if len(request.GET['session_key']) > 10: 

                 session_key = request.GET['session_key']

                 memory_session['sitequeuesession'] = session_key
                 memory_session['sitequeuesession_getcreated'] = 'yes'
                 memory_session['sitequeuesession_ipaddress'] = get_client_ip(request)
                 memory_session['sitequeuesession_created'] = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
                 memory_session['sitequeuesession_agent'] = request.META['HTTP_USER_AGENT']


        if 'sitequeuesession' not in memory_session:
             if 'sitequeuesession' in request.COOKIES:
                
                session_key = request.COOKIES.get('sitequeuesession','')
                memory_session['sitequeuesession'] = session_key
                memory_session['sitequeuesession_getcreated'] = 'cookie'
                memory_session['sitequeuesession_ipaddress'] = get_client_ip(request)
                memory_session['sitequeuesession_created'] = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
                memory_session['sitequeuesession_agent'] = request.META['HTTP_USER_AGENT']
        
        
        if request.user.is_authenticated:
             if request.user.is_staff is True:
                   pass
                   #staff_loggedin = True

        total_active_session = jsondb.get_active_sessions_total(queue_group_name)
        total_waiting_session = jsondb.get_waiting_session_total(queue_group_name)
        
        if 'sitequeuesession' in memory_session:
             sitequeuesession = memory_session['sitequeuesession']
        else:
             memory_session['sitequeuesession']  = None 


        session_file_id =  None
        if sitequeuesession is not None:           
            session_file_id = jsondb.get_session_by_id(queue_group_name,sitequeuesession)            
            if session_file_id is None:
                time.sleep(2)
                session_file_id = jsondb.get_session_by_id(queue_group_name,sitequeuesession)
            if session_file_id is None:          
                time.sleep(1)
                session_file_id = jsondb.get_session_by_id(queue_group_name,sitequeuesession)
        
        
        session_count = 0
        if session_file_id is not None:        
            session_data = jsondb.get_queue_session(session_file_id)
            now_dt = datetime.now().astimezone(PLUS_8)
            expiry_dt = datetime.strptime(session_data["expiry"], "%Y-%m-%d %H:%M:%S") 
            expiry_dt = dj_tz.make_aware(expiry_dt, PLUS_8)
            if expiry_dt < now_dt:
                print ("SESSION EXPIRED")
        
            session_count = 1
        
          
        # sitequeuesession = None
        if sitequeuesession is None or session_count == 0:
            session_status = "Waiting"
            #if total_active_session >= session_total_limit:
            # START -- Disabling, will send everyone to queue and the cron job give fairer allocated spots 
            #if total_active_session < session_total_limit and total_waiting_session == 0:
            #      session_status = 1
            # END --

            if total_active_session < session_total_limit:
                if total_waiting_session == 0:
                    session_status = "Active"

            if ping_url_current > ping_url_limit:
                  session_status = "Waiting"
            # if cpu_percentage > cpu_percentage_limit:
            #       session_status = 0
            if staff_loggedin is True:
                  session_status = "Active"
            # print ("session_status")
            # print (session_status)
            # print (session_count)
            # print (session_total_limit)
            # print (total_active_session)
            # print (total_waiting_session)
            
            #if session_key:
            #     pass
            #else: 
            browser_agent = ''
            if 'HTTP_USER_AGENT' in request.META:
                browser_agent = request.META['HTTP_USER_AGENT']
                if script_exempt_key == settings.SCRIPT_EXEMPT_KEY:
                    pass
                else:
                    if 'python' in browser_agent:
                        response = HttpResponse(json.dumps({"status:": 500, 'message': "Agent Forbidden"}), content_type='application/json', status=500)
                        return response
            
            session_key = get_random_string(length=60, allowed_chars=u'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
            expiry=(datetime.now().astimezone(PLUS_8)+timedelta(seconds=session_limit_seconds)).strftime("%Y-%m-%d %H:%M:%S")
            sitesession = {"session_key":session_key,"idle":datetime.now().astimezone(PLUS_8).strftime("%Y-%m-%d %H:%M:%S"), "expiry": expiry,"status": session_status,"ipaddress" : get_client_ip(request), "is_staff": staff_loggedin,"queue_group" : group_unique_key, "browser_agent" : browser_agent}
            # sitesession = models.SiteQueueManager.objects.create(session_key=session_key,idle=datetime.now(timezone.utc), expiry=expiry,status=session_status,ipaddress=get_client_ip(request), is_staff=staff_loggedin,queue_group=queue_group[0], browser_agent=browser_agent)
            jsondb.new_queue_session(session_key,sitesession,group_unique_key)

            memory_session['sitequeuesession'] = session_key
            memory_session['sitequeuesession_ipaddress'] = get_client_ip(request) 
            memory_session['sitequeuesession_created'] = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
            memory_session['sitequeuesession_getcreated'] = 'no'
            request.COOKIES['sitequeuesession'] = session_key
            memory_session['sitequeuesession_agent'] = request.META['HTTP_USER_AGENT']
        else:
            session_file_id = jsondb.get_session_by_id(queue_group_name,sitequeuesession)            
            if session_file_id is not None:                
                sitesession = jsondb.get_queue_session(session_file_id)

            # if models.SiteQueueManager.objects.filter(session_key=sitequeuesession).count() > 0:
                #  sitesession_query = models.SiteQueueManager.objects.filter(session_key=sitequeuesession,queue_group=queue_group[0])
                #  sitesession = sitesession_query[0]
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
                
                sitesession['idle']=(datetime.now().astimezone(PLUS_8)).strftime("%Y-%m-%d %H:%M:%S")
                if sitesession["status"] == "Waiting":
                    sitesession["expiry"]=(datetime.now().astimezone(PLUS_8)+timedelta(seconds=session_limit_seconds)).strftime("%Y-%m-%d %H:%M:%S")
                    

                sitesession["ipaddress"]=get_client_ip(request)
                jsondb.save_queue_session(session_file_id,sitesession)
                # sitesession.save()
            else:
                raise ValidationError("Error no session Found")


        queue_position = jsondb.get_queue_position_by_id(queue_group_name,sitequeuesession)

        #queue_position =0
        # if models.SiteQueueManager.objects.filter(session_key=session_key).count() > 0:
        #      sqm =  models.SiteQueueManager.objects.filter(session_key=session_key)[0]
        #      queue_position = models.SiteQueueManager.objects.filter(id__lte=sqm.id, status=0, expiry__gt=datetime.now(timezone.utc),queue_group=queue_group[0]).order_by('id').count()


        sitesession["idle"] 
        now_dt = datetime.now().astimezone(PLUS_8)
        idle_dt = datetime.strptime(sitesession["idle"], "%Y-%m-%d %H:%M:%S") 
        idle_dt = dj_tz.make_aware(idle_dt, PLUS_8)
        expiry_dt = datetime.strptime(sitesession["expiry"], "%Y-%m-%d %H:%M:%S") 
        expiry_dt = dj_tz.make_aware(expiry_dt, PLUS_8)        

        idle_seconds = (now_dt-idle_dt).seconds
        expiry_seconds = (expiry_dt-now_dt).seconds
        wait_time = 100 
        if queue_position:
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
        print ("EXCEPTION ERROR")
        print (e)
        pass

    if waiting_queue_enabled == False or waiting_queue_enabled == "False":
        if sitesession is None:
            mydict = {'status': "Active", 'idle': None, 'expiry': None}
            sitesession = dotdict(mydict) 
        sitesession["status"] = "Active"
        sitesession["idle"] = (datetime.now().astimezone(PLUS_8)).strftime("%Y-%m-%d %H:%M:%S")
        sitesession["expiry"] = (datetime.now().astimezone(PLUS_8)+timedelta(hours=10)).strftime("%Y-%m-%d %H:%M:%S")


       
        # NEED TO ADD SAVE ACTICATION
    
    CORS_SITES = env('CORS_SITES', None)
    QUEUE_DOMAIN = env('QUEUE_DOMAIN', '')
    if session_key is None:
        session_key = ''
    if sitesession:
        if "expiry" in sitesession:
            site_session_expiry = sitesession["expiry"]
        else:
            site_session_expiry = ''
        if "idle" in sitesession:
            site_session_idle = sitesession["idle"]
        else:
            site_session_idle = ''    
        if "status" in sitesession:
            site_session_status = sitesession["status"]
        else:
            site_session_status= ''                      
        
    else:
        site_session_expiry = ''
        site_session_idle = ''
        site_session_status = '' 

    if settings.DEBUG is True: 
        # print (sitesession["expiry"])
#        print({'url':active_session_url, 'queueurl': reverse('site-queue-page'),'session': memory_session['sitequeuesession'], 'idle_seconds':idle_seconds,'expiry': sitesession["expiry"]})#, 'idle': sitesession["idle"],'status': sitesession["status"],'total_active_session': total_active_session})#, 'total_waiting_session': total_waiting_session,'expiry_seconds': expiry_seconds,'session_key': session_key, 'queue_position' : queue_position ,'wait_time' : wait_time ,'waiting_queue_enabled': waiting_queue_enabled, 'wq': env('WAITING_QUEUE_ENABLED','False'), 'time_left_enabled': time_left_enabled, 'browser_inactivity_timeout': browser_inactivity_timeout, 'browser_inactivity_redirect': browser_inactivity_redirect, 'browser_inactivity_enabled': browser_inactivity_enabled,'custom_message': custom_message,'queue_name': queue_name, 'more_info_link' : more_info_link, 'show_queue_position': show_queue_position, 'max_queue_session_limit': max_queue_session_limit, 'max_queue_url_redirect': max_queue_url_redirect,'queue_inactivity_url': queue_inactivity_url, 'queue_waiting_room_url': queue_waiting_room_url })
        
        # print ("SITESESSION")
        # print (sitesession)
        # print ("VAR")
        # print (active_session_url)
        # print (reverse('site-queue-page'))
        # print (memory_session['sitequeuesession'])
        # print (idle_seconds)
        # print (site_session_expiry)
        # print (site_session_idle)
        # print (site_session_status)
        # print (total_active_session)
        # print (total_waiting_session)
        # print (expiry_seconds)
        # print (session_key)
        # print (queue_position)
        # print (wait_time)
        # print (waiting_queue_enabled)
        # print (env('WAITING_QUEUE_ENABLED','False'))
        # print (time_left_enabled)
        # print (browser_inactivity_timeout)
        # print (browser_inactivity_redirect)
        # print (browser_inactivity_enabled)
        # print (custom_message)
        # print (queue_name)
        # print (more_info_link)
        # print (show_queue_position)
        # print (max_queue_session_limit)
        # print (max_queue_url_redirect)
        # print (queue_inactivity_url)
        # print (queue_waiting_room_url)
        response = HttpResponse(json.dumps({'url':active_session_url, 'queueurl': reverse('site-queue-page'),'session': memory_session['sitequeuesession'], 'idle_seconds':idle_seconds,'expiry': site_session_expiry, 'idle': site_session_idle,'status': site_session_status,'total_active_session': total_active_session, 'total_waiting_session': total_waiting_session,'expiry_seconds': expiry_seconds,'session_key': session_key, 'queue_position' : queue_position ,'wait_time' : wait_time ,'waiting_queue_enabled': waiting_queue_enabled, 'wq': env('WAITING_QUEUE_ENABLED','False'), 'time_left_enabled': time_left_enabled, 'browser_inactivity_timeout': browser_inactivity_timeout, 'browser_inactivity_redirect': browser_inactivity_redirect, 'browser_inactivity_enabled': browser_inactivity_enabled,'custom_message': custom_message,'queue_name': queue_name, 'more_info_link' : more_info_link, 'show_queue_position': show_queue_position, 'max_queue_session_limit': max_queue_session_limit, 'max_queue_url_redirect': max_queue_url_redirect,'queue_inactivity_url': queue_inactivity_url, 'queue_waiting_room_url': queue_waiting_room_url }), content_type='application/json')
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        response["Access-Control-Max-Age"] = "0"
        response["Access-Control-Allow-Headers"] = "*"
        response["X-Frame-Options"] = "allow-from *"

        response.set_cookie('sitequeuesession', session_key, max_age=2592000, samesite=None, domain=QUEUE_DOMAIN)
        return response
    else:
        #response = HttpResponse(json.dumps({'url':active_session_url, 'queueurl': reverse('site-queue-page'),'status': models.SiteQueueManager.QUEUE_STATUS[sitesession.status][1],'session_key': session_key, 'queue_position' : queue_position, 'wait_time' : wait_time, 'time_left_enabled': time_left_enabled,'browser_inactivity_timeout': browser_inactivity_timeout, 'browser_inactivity_redirect': browser_inactivity_redirect,  'waiting_queue_enabled': waiting_queue_enabled, 'browser_inactivity_enabled': browser_inactivity_enabled,'custom_message': custom_message, 'custom_message': custom_message,'queue_name': queue_name, 'more_info_link' : more_info_link  }), content_type='application/json')        
        response = HttpResponse(json.dumps({'url':active_session_url, 'queueurl': reverse('site-queue-page'),'session': memory_session['sitequeuesession'], 'idle_seconds':idle_seconds,'expiry': site_session_expiry, 'idle': site_session_idle,'status': site_session_status,'total_active_session': total_active_session, 'total_waiting_session': total_waiting_session,'expiry_seconds': expiry_seconds,'session_key': session_key, 'queue_position' : queue_position ,'wait_time' : wait_time ,'waiting_queue_enabled': waiting_queue_enabled, 'wq': env('WAITING_QUEUE_ENABLED','False'), 'time_left_enabled': time_left_enabled, 'browser_inactivity_timeout': browser_inactivity_timeout, 'browser_inactivity_redirect': browser_inactivity_redirect, 'browser_inactivity_enabled': browser_inactivity_enabled,'custom_message': custom_message,'queue_name': queue_name, 'more_info_link' : more_info_link, 'show_queue_position': show_queue_position, 'max_queue_session_limit' : max_queue_session_limit, 'max_queue_url_redirect': max_queue_url_redirect,'queue_inactivity_url': queue_inactivity_url, 'queue_waiting_room_url': queue_waiting_room_url  }), content_type='application/json')
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



def expire_session(request, *args, **kwargs):
    session_key = request.GET.get('session_key',None)
    queue_group = request.GET.get('queue_group',None)
    if session_key: 
        delete_success = jsondb.delete_session(queue_group,session_key)
        if delete_success is True:
        # if models.SiteQueueManager.objects.filter(session_key=session_key).count() > 0:             
            #sqm =  models.SiteQueueManager.objects.filter(session_key=session_key).update(status=2, expiry=datetime.now())
            # sqm =  models.SiteQueueManager.objects.filter(session_key=session_key).delete()
            print ('SESSION EXPIRED : '+ session_key)            
            response = HttpResponse(json.dumps({"status_code": 200,"message": "completed successfully"}), content_type='application/json')
            response["Access-Control-Allow-Origin"] = "*" 
            response["Access-Control-Allow-Methods"] = "GET, OPTIONS"
            response["Access-Control-Max-Age"] = "0"
            response["Access-Control-Allow-Headers"] = "*"
            response["X-Frame-Options"] = "allow-from *"        
            return response
    
    response = HttpResponse(json.dumps({"status_code": 401,"message": "Access Forbidden"}), content_type='application/json')
    response["Access-Control-Allow-Origin"] = "*" 
    response["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    response["Access-Control-Max-Age"] = "0"
    response["Access-Control-Allow-Headers"] = "*"
    response["X-Frame-Options"] = "allow-from *"        
    return response



def queue_status(request, *args, **kwargs):
    
#group_unique_key=request.GET['queue_group']

    queue_groups = jsondb.get_queue_groups()
    queue_hash = {}
    for qg in queue_groups:
        queue_hash[qg["group_unique_key"]] = {"total_active_session" : 0, "total_waiting_session" : 0, "queue_error": False}
        # total_active_session = models.SiteQueueManager.objects.filter(status=1, expiry__gte=datetime.now(timezone.utc),is_staff=False,queue_group=qg).count()
        # total_waiting_session = models.SiteQueueManager.objects.filter(status=0, expiry__gte=datetime.now(timezone.utc),queue_group=qg).count()
        total_active_session = jsondb.get_active_sessions_total(qg["group_unique_key"])
        total_waiting_session = jsondb.get_waiting_session_total(qg["group_unique_key"])
        queue_hash[qg["group_unique_key"]]['total_active_session'] = total_active_session
        queue_hash[qg["group_unique_key"]]['total_waiting_session'] = total_waiting_session
        if total_waiting_session > 0:
            if total_active_session > 0:
                pass
            else:
                queue_hash[qg["group_unique_key"]]['queue_error'] = True
    response = HttpResponse(json.dumps(queue_hash), content_type='application/json')
    return response


def get_active_sessions(request, *args, **kwargs):

    json_resp = {"status": 401, "message": "Access Denied"}
    if request.user.is_authenticated:
            a = _JSONAuthStore()
            u = a.get_user_record(request.user.email)
            
            if "Admin" in u["groups"]:

                start = request.GET.get("start",0)
                length = request.GET.get("length",10)
                draw = request.GET.get("draw",0)
                search = request.GET.get("search",0)
                queue_group = request.GET.get("queue_group",None)
                
                total_active_session = jsondb.get_active_sessions_total(queue_group)
                active_sessions_json = jsondb.get_active_sessions(queue_group, int(start), int(length), search)
                
                json_resp = {
                    "draw": draw,
                    "recordsTotal": total_active_session,
                    "recordsFiltered": active_sessions_json["recordsFiltered"],
                    "data": active_sessions_json["data"]

                }

    response = HttpResponse(json.dumps(json_resp), content_type='application/json')
    return response


def get_waiting_sessions(request, *args, **kwargs):


    json_resp = {"status": 401, "message": "Access Denied"}
    if request.user.is_authenticated:
        a = _JSONAuthStore()
        u = a.get_user_record(request.user.email)
        
        if "Admin" in u["groups"]:

            start = request.GET.get("start",0)
            length = request.GET.get("length",10)
            draw = request.GET.get("draw",0)
            search = request.GET.get("search",0)
            queue_group = request.GET.get("queue_group",None)
            total_active_session = jsondb.get_waiting_session_total(queue_group)
            active_sessions_json = jsondb.get_waiting_sessions(queue_group, int(start), int(length), search)
            
            json_resp = {
                "draw": draw,
                "recordsTotal": total_active_session,
                "recordsFiltered": active_sessions_json["recordsFiltered"],
                "data": active_sessions_json["data"]

            }

            response = HttpResponse(json.dumps(json_resp), content_type='application/json')
            return response
    else:
        response = HttpResponse(json.dumps({"status:" : 401, "message": "Access Denied"}), content_type='application/json')
        return response        