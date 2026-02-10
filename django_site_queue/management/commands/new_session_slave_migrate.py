from django.core.management.base import BaseCommand
from django.utils import timezone
import shutil
from datetime import timedelta, datetime
from pathlib import Path
from django_site_queue import jsondb
from django.conf import settings
import os

class Command(BaseCommand):
    help = 'Clear out any expired temporary bookings that have been abandoned by the user'

    def handle(self, *args, **options):

        queue_groups = jsondb.get_queue_groups()
        for queue_group in queue_groups:
            group_unique_key = queue_group["group_unique_key"]
            
            sub_directory = Path(settings.QUEUE_STORE_DB_SLAVE_TMP+"/{}".format(group_unique_key))    
            files = [f for f in sub_directory.iterdir() if f.is_file()]
            # files.sort(key=lambda f: f.stat().st_mtime, reverse=False)
            files.sort()
            for f in files:
                print (f)
                try: 
                    session_filename = os.path.basename(f)  
                    shutil.copyfile(f, settings.QUEUE_STORE_DB+"/queue_sessions/waiting/{}/{}/{}".format(group_unique_key,str(settings.DIRECTORY_FOLDER_LIMIT),session_filename))
                    os.remove(f)
                    print ("Removing file "+str(f))
                except Exception as e:
                    print ("Error removing "+str(f))
                    print (e)                

            