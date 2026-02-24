from django.core.management.base import BaseCommand
import shutil
from datetime import timedelta, datetime, timezone, date
from pathlib import Path
from django_site_queue import jsondb
from django.conf import settings
import os
import time

PLUS_8 = timezone(timedelta(hours=8))

class Command(BaseCommand):
    help = 'Move new session to central network storage to sync with other slaves'

    def handle(self, *args, **options):

        queue_groups = jsondb.get_queue_groups()
        for queue_group in queue_groups:
            group_unique_key = queue_group["group_unique_key"]
            
            sub_directory = Path(settings.QUEUE_STORE_DB_SLAVE_TMP+"/new_session/{}".format(group_unique_key))    
            files = [f for f in sub_directory.iterdir() if f.is_file()]
            # files.sort(key=lambda f: f.stat().st_mtime, reverse=False)
            files.sort()
            for f in files:
                print (f)
                
                try:
                    idle_data = {}
                    session_filename = os.path.basename(f)
                    session_filename_split = session_filename.split("_session_")
                    session_id_val = session_filename_split[1]                    
                    
                    epoch_ms = int(time.time() * 1000000000)
                    epoch_ms_str = str(epoch_ms)              
                    new_session_filename = epoch_ms_str+"_session_"+session_id_val
                    shutil.copyfile(f, settings.QUEUE_STORE_DB+"/queue_sessions/waiting/{}/{}/{}".format(group_unique_key,str(settings.DIRECTORY_FOLDER_LIMIT),new_session_filename))
                    os.remove(f)
  
                    session_id_val = session_id_val.replace(".json","")   
                    idle_data["idle"] = (datetime.now().astimezone(PLUS_8)).strftime("%Y-%m-%d %H:%M:%S")
                    jsondb.save_session_idle(session_id_val,idle_data,group_unique_key)                      
                    print ("Removing file "+str(f))
                except Exception as e:
                    print ("Error removing "+str(f))
                    print (e)                

            