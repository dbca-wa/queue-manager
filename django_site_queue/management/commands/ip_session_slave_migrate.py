from django.core.management.base import BaseCommand
from django.utils import timezone
import shutil
from datetime import timedelta, datetime
from pathlib import Path
from django_site_queue import jsondb
from django.conf import settings
import os

class Command(BaseCommand):
    help = 'Move logs data to network storage'

    def handle(self, *args, **options):

        queue_groups = jsondb.get_queue_groups()
        for queue_group in queue_groups:
            group_unique_key = queue_group["group_unique_key"]
            
            sub_directory = Path(settings.QUEUE_STORE_DB_SLAVE_TMP+"/ip_session_log/{}".format(group_unique_key))    
            for log_file in sub_directory.glob('**/*.log'):
                try:
                    print(f"Processing: {log_file}")
                    master_file = str(log_file).replace(settings.QUEUE_STORE_DB_SLAVE_TMP, settings.QUEUE_STORE_DB)
                    log_file_name = os.path.basename(master_file)
                    master_file_base_dir = str(master_file).replace(log_file_name,"")                
                    os.makedirs(master_file_base_dir, exist_ok=True)  
                    with Path(master_file).open('a', encoding='utf-8') as outfile:
                        content = log_file.read_text(encoding='utf-8')
                        outfile.write(content)
                    os.remove(log_file)
                except Exception as e:
                    print ("Error migrating ip log file "+str(log_file))
                    print (e)                


            # files = [f for f in sub_directory.iterdir() if f.is_file()]
            # # files.sort(key=lambda f: f.stat().st_mtime, reverse=False)
            # files.sort()
            # for f in files:
            #     print (f)
            #     try: 
            #         session_filename = os.path.basename(f)  
            #         shutil.copyfile(f, settings.QUEUE_STORE_DB+"/queue_sessions/waiting/{}/{}/{}".format(group_unique_key,str(settings.DIRECTORY_FOLDER_LIMIT),session_filename))
            #         os.remove(f)
            #         print ("Removing file "+str(f))
            #     except Exception as e:
            #         print ("Error removing "+str(f))
            #         print (e)                

            