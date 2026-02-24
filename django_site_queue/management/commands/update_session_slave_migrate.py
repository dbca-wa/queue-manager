from django.core.management.base import BaseCommand
from django.utils import timezone
import shutil
from datetime import timedelta, datetime, timezone, date
from pathlib import Path
from django_site_queue import jsondb
from django.conf import settings
import os
import json
PLUS_8 = timezone(timedelta(hours=8))

class Command(BaseCommand):
    help = 'Move new session to central network storage to sync with other slaves'

    def handle(self, *args, **options):

        queue_groups = jsondb.get_queue_groups()
        for queue_group in queue_groups:
            group_unique_key = queue_group["group_unique_key"]
            
            sub_directory = Path(settings.QUEUE_STORE_DB_SLAVE_TMP+"/update_session/{}".format(group_unique_key))    
            files = [f for f in sub_directory.iterdir() if f.is_file()]
            # files.sort(key=lambda f: f.stat().st_mtime, reverse=False)
            files.sort()
            for f in files:
                print (f)
                try: 
                    idle_data = {}
                    session_filename = os.path.basename(f)  
                    print (session_filename)
                    session_filename_split = session_filename.split("_session_")
                    print (session_filename_split)
                    session_id_val = session_filename_split[1]  
                    print (session_id_val)          
                    session_id_val = session_id_val.replace(".json","") 
                    print (session_id_val)
                    session_file_id = jsondb.get_session_by_id(group_unique_key,session_id_val, source='master')
                    print (session_file_id)
                    # file_path = session_file_id
                    with f.open("r", encoding="utf-8") as f2:
                        try: 
                            session_data = json.load(f2)
                            # session_data['idle'] = (datetime.now().astimezone(PLUS_8)).strftime("%Y-%m-%d %H:%M:%S")
                        except Exception as e:
                            print ("Exception open json file")
                            print (e)
                    if len(session_data) > 0:
                        if f.exists():
                            session_filename = os.path.basename(f)
                            session_filename_split = session_filename.split("_session_")
                            session_id_val = session_filename_split[1]     
                            session_id_val = session_id_val.replace(".json","")   
                            idle_data["idle"] = (datetime.now().astimezone(PLUS_8)).strftime("%Y-%m-%d %H:%M:%S")
                            jsondb.save_session_idle(session_id_val,idle_data,group_unique_key)                    
                    # shutil.copyfile(f, settings.QUEUE_STORE_DB+"/queue_sessions/waiting/{}/{}/{}".format(group_unique_key,str(settings.DIRECTORY_FOLDER_LIMIT),session_filename))
                    os.remove(f)
                    print ("Removing file "+str(f))
                    
                    
                except Exception as e:
                    print ("Error removing "+str(f))
                    print (e)                

            