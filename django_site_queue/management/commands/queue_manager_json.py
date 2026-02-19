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
from django.utils.crypto import get_random_string

PLUS_8 = timezone(timedelta(hours=8))

class Command(BaseCommand):
    help = 'The purpose of this script is to manage the queue and progress session through the queue and remove session that should no longer be needed'

    def handle(self, *args, **options):

        sitequeuesession = None
        sitesession = None

        # this need to change look up queue groups in db/json/queue_groups
        # queue_groups = ["parkstayv2"]
        queue_groups = jsondb.get_queue_groups()
        
        total_active_session = 0
        total_waiting_session = 0
        for queue_group in queue_groups:
            # queue_group = jsondb.get_queue_group(queue_group_name)

            session_total_limit = queue_group["session_total_limit"]
            session_limit_seconds = queue_group["session_limit_seconds"]
            cpu_percentage_limit = queue_group["cpu_percentage_limit"]
            idle_limit_seconds = queue_group["idle_limit_seconds"]
            active_session_url = queue_group["active_session_url"]
            waiting_queue_enabled = queue_group["waiting_queue_enabled"]
            queue_group_name = queue_group["group_unique_key"]
            queue_domain = queue_group["queue_domain"]
            queue_url = queue_group["queue_url"]
            ping_url_enabled = queue_group["ping_url_enabled"]
            ping_url = queue_group["ping_url"]
            ping_url_limit = float(queue_group["ping_url_limit"])
            # ping_url_current = queue_group["ping_url_current"] 

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
            
            jsondb.delete_active_expiry_idle_sessions(queue_group_name)
            
            # jsondb.wait_queue_rotate(queue_group_name)
            total_active_session = jsondb.get_active_sessions_total(queue_group_name)
            total_waiting_session = jsondb.get_waiting_session_total(queue_group_name)                                                
            stl = session_total_limit
            data = {"total_waiting_session": total_waiting_session}
            jsondb.save_queue_waiting_total(data,queue_group_name)
            # stl = 2
            longest_waiting = jsondb.get_longest_waiting(queue_group_name, stl)
            
            print ("Queue Log Date: "+datetime.now().strftime("%A, %d %b %Y %H:%M:%S")+" : "+queue_group_name+" Active Sessions ("+str(total_active_session)+") Waiting Sessions ("+str(total_waiting_session)+")")
            print ("Report,"+ datetime.now().strftime("%A, %d %b %Y %H:%M:%S")+","+queue_group_name+",Active Sessions,"+str(total_active_session)+",Waiting Sessions,"+str(total_waiting_session)+"")

            for sitesession_file in longest_waiting:
                total_active_session = jsondb.get_active_sessions_total(queue_group_name)
                sitesession = jsondb.get_queue_session(sitesession_file)
                if sitesession is not None:                           
                    if total_active_session < session_total_limit and sitesession['status'] != "Active":                    
                        if ping_url_current > ping_url_limit:
                            print ("Site Load Response Time Limit (waiting for lower response time '"+str(ping_url_current)+"' ) = "+str(ping_url_limit)) 
                            sitesession["expiry"] = (datetime.now().astimezone(PLUS_8)+timedelta(seconds=session_limit_seconds)).strftime("%Y-%m-%d %H:%M:%S")
                        else:
                            print ("Session Activated: "+sitesession["session_key"])
                            session_status = "Active"
                            sitesession["status"] = session_status
                            sitesession["expiry"] = (datetime.now().astimezone(PLUS_8)+timedelta(seconds=session_limit_seconds)).strftime("%Y-%m-%d %H:%M:%S")                            
                            sitesession["activated"] = (datetime.now().astimezone(PLUS_8)).strftime("%Y-%m-%d %H:%M:%S")
                            sitesession["activated_session_id"] = get_random_string(length=60, allowed_chars=u'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')

                    if sitesession['status'] == "Waiting":
                            sitesession['expiry'] = (datetime.now().astimezone(PLUS_8)+timedelta(seconds=session_limit_seconds)).strftime("%Y-%m-%d %H:%M:%S")
                    if staff_loggedin is True:
                            session_status = 1
                            sitesession['status'] = session_status
                            sitesession['expiry']= (datetime.now().astimezone(PLUS_8)+timedelta(seconds=session_limit_seconds)).strftime("%Y-%m-%d %H:%M:%S")
                            sitesession['is_staff']=staff_loggedin
                                                
                    sitesession['idle']=(datetime.now().astimezone(PLUS_8)).strftime("%Y-%m-%d %H:%M:%S")
                    jsondb.save_queue_session(sitesession_file,sitesession)
                    sitesession = jsondb.get_queue_session(sitesession_file)
                    print (sitesession_file)
                    if sitesession:
                        if sitesession["status"]  == "Active":
                            print ("Migrate to Active folder")
                            try:
                                LOCK_PATH = str(sitesession_file)+".lock" 
                                lock = FileLock(LOCK_PATH)
                                with lock:
                                    session_filename = os.path.basename(sitesession_file)

                                    active_sitesession_file = "db/json/queue_sessions/active/{}/{}".format(queue_group_name,session_filename)
                                    shutil.copyfile(sitesession_file, active_sitesession_file)  
                                    #time.sleep(.1)
                                    #os.remove(sitesession_file)   
                                    print ("Removing file "+str(sitesession_file))
                                try:       
                                    os.remove(LOCK_PATH)
                                except Exception as k:
                                    print ("Error Removing "+str(LOCK_PATH))
                                    print (k)

                            except Exception as e:
                                print ("Error Saving File:"+str(sitesession_file))
                                print (e)                                
