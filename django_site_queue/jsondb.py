from pathlib import Path
from datetime import timedelta, datetime, timezone, date
from django.utils import timezone as dj_tz
from django.conf import settings
from filelock import FileLock
import json
import os
import shutil
import time

PLUS_8 = timezone(timedelta(hours=8))

def get_queue_groups():
    queue_groups = []
    sub_directory = Path(settings.QUEUE_STORE_DB+"/queue_groups/")
    # print ("Checking Directory: {}".format(sub_directory))
    if os.path.isdir(sub_directory):            
        files = [f for f in sub_directory.iterdir() if f.is_file()]     
        for f in files:
            if str(f).endswith('.json'):
                if f.is_file():
                    with f.open("r", encoding="utf-8") as fe:
                        data = json.load(fe)        
                        if "group_unique_key" in data:
                            queue_groups.append(data)
    return queue_groups

def get_queue_group(group_key):    
    # Path to the JSON file
    try:        
        file_path = Path(settings.QUEUE_STORE_DB+"./queue_groups/{}.json".format(group_key))
        if file_path.exists():
            # Load JSON file into a variable
            with file_path.open("r", encoding="utf-8") as f:
                data = json.load(f)            
            return data
    except Exception as e:
        print (e)

    return None

# def check_queue_session_deleted(group_unique_key,session_key):
#     session_deleted = False
#     now = datetime.now()
#     year = now.year
#     month = now.month
#     day = now.day

#     sub_directory = settings.QUEUE_STORE_DB_TMP+"./queue_sessions/deleted/{}/{}/{}/{}".format(group_unique_key, year, month, day)
#     if os.path.exists(sub_directory+"/"+session_key+".json") is True:
#         session_deleted = True
#     return session_deleted

def check_queue_session_deleted_recently(group_unique_key,session_key):
    session_deleted = False
    sub_directory = settings.QUEUE_STORE_DB_TMP+"./queue_sessions/deleted_recently/{}".format(group_unique_key)
    if os.path.exists(sub_directory+"/"+session_key+".json") is True:
        session_deleted = True
    return session_deleted
    
def get_queue_session(file):    
    # Path to the JSON file
    
    try:        
        file_path = file
        if file_path.exists():
            # Load JSON file into a variable
            with file_path.open("r", encoding="utf-8") as f:
                try: 
                    data = json.load(f)            
                except Exception as e:
                    print ("ERROR Opening {}".format(file_path))
                    print (e)
                    try:                        
                        # os.remove(file_path) JASON
                        print ("----- >Removing file (get_queue_session)"+str(file_path))
                    except Exception as d:
                        print ("Error removing (get_queue_session):"+str(d))
                        print (d)
                    return None
            return data
    except Exception as e:
        print (e)

    return None


def save_queue_session(file,data):    
    # Path to the JSON file
    
    try:
        LOCK_PATH = str(file)+".lock" 
        lock = FileLock(LOCK_PATH)
        with lock:
            json_text = json.dumps(data, ensure_ascii=False, indent=2)
            with open(file, "w") as f:
                f.write(json_text)
        try:       
            os.remove(LOCK_PATH)
        except Exception as k:
            print ("Error Removing "+str(LOCK_PATH))
            print (k)
    except Exception as e:
        print ("Error Saving File:"+str(file))
        print (e)

    return None

def save_queue_session_slave(file,data,group_unique_key):    
    # Path to the JSON file    
    try:
        session_filename = os.path.basename(file)
        
        os.makedirs(settings.QUEUE_STORE_DB_SLAVE_TMP+"/update_session/{}/".format(group_unique_key), exist_ok=True)        
        sub_directory = settings.QUEUE_STORE_DB_SLAVE_TMP+"/update_session/{}/".format(group_unique_key)
        json_text = json.dumps(data, ensure_ascii=False, indent=2)
        with open(sub_directory+session_filename, "w") as f:
            f.write(json_text)
    except Exception as e:
        print ("Error Saving File:"+str(file))
        print (e)

    return None


def get_queue_position(session_key, group_key):    
    # Path to the JSON file 
    position_obj = {'queue_position': None, 'queue_position_epoch': None}   
    try:        
        file_path = Path(settings.QUEUE_STORE_DB_TMP+"/queue_position/{}/{}.txt".format(group_key,session_key))
        if file_path.exists():
            # Load JSON file into a variable
            stat_info = os.stat(file_path)
            
            # Access the nanosecond modification time attribute
            st_mtime_ns = stat_info.st_mtime_ns       
            position_obj['queue_position_epoch'] =  str(st_mtime_ns)

            with file_path.open("r", encoding="utf-8") as f:
                try: 
                    data = f.read()
                    position_obj['queue_position'] = int(data)
                except Exception as e:
                    print ("ERROR Opening {}".format(file_path))
                    print (e)
                    return None
            return position_obj
    except Exception as e:
        print (e)

    return None

def save_queue_position(session_key,data,group_key):    
    # Path to the JSON file
    os.makedirs(settings.QUEUE_STORE_DB+"/queue_position/{}".format(group_key), exist_ok=True)
    try:      

        file = settings.QUEUE_STORE_DB+"/queue_position/{}/{}.txt".format(group_key,session_key)        
        json_text = json.dumps(data, ensure_ascii=False, indent=2)
        with open(file, "w") as f:
            f.write(json_text)
    except Exception as e:
        print ("Error Saving File:"+str(file))
        print (e)
    return None


def get_session_idle(session_key, group_key, source="tmp" ):  

    source_dir = settings.QUEUE_STORE_DB_TMP
    if source == 'master':
        source_dir = settings.QUEUE_STORE_DB      
    # Path to the JSON file     
    data = None
    try:        
        file_path = Path(source_dir+"/queue_idle/{}/{}.json".format(group_key,session_key))
        if file_path.exists():                                    
            with file_path.open("r", encoding="utf-8") as f:
                try: 
                    data = json.load(f)
                    
                except Exception as e:
                    print ("ERROR Opening {}".format(file_path))
                    print (e)
                    return None
            return data
    except Exception as e:
        print (e)

    return None

def save_session_idle(session_key,data,group_key):    
    # Path to the JSON file
    os.makedirs(settings.QUEUE_STORE_DB+"/queue_idle/{}".format(group_key), exist_ok=True)
    try:      

        file = settings.QUEUE_STORE_DB+"/queue_idle/{}/{}.json".format(group_key,session_key)        
        json_text = json.dumps(data, ensure_ascii=False, indent=2)
        with open(file, "w") as f:
            f.write(json_text)
    except Exception as e:
        print ("Error Saving File:"+str(file))
        print (e)
    return None


def save_queue_ping(data,group_key):    
    # Path to the JSON file
    os.makedirs(settings.QUEUE_STORE_DB+"/ping_status/", exist_ok=True)
    try:      

        file = settings.QUEUE_STORE_DB+"/ping_status/{}.json".format(group_key)        
        json_text = json.dumps(data, ensure_ascii=False, indent=2)
        with open(file, "w") as f:
            f.write(json_text)
    except Exception as e:
        print ("Error Saving File:"+str(file))
        print (e)
    return None

def save_queue_waiting_total(data,group_key):    
    # Path to the JSON file
    os.makedirs(settings.QUEUE_STORE_DB+"/waiting_total/", exist_ok=True)
    try:      

        file = settings.QUEUE_STORE_DB+"/waiting_total/{}.json".format(group_key)        
        json_text = json.dumps(data, ensure_ascii=False, indent=2)
        with open(file, "w") as f:
            f.write(json_text)
    except Exception as e:
        print ("Error Saving File:"+str(file))
        print (e)
    return None

def get_queue_waiting_total_cached(group_key):    
    # Path to the JSON file
    file = Path(settings.QUEUE_STORE_DB_TMP+"/waiting_total/{}.json".format(group_key))    
    try:        
        file_path = file
        if os.path.exists(file_path):
            # Load JSON file into a variable
            with file_path.open("r", encoding="utf-8") as f:
                data = json.load(f)            
            return data
    except Exception as e:
        print (e)

    return None


def get_queue_ping(group_key):    
    # Path to the JSON file
    file = Path(settings.QUEUE_STORE_DB+"/ping_status/{}.json".format(group_key))    
    try:        
        file_path = file
        if os.path.exists(file_path):
            # Load JSON file into a variable
            with file_path.open("r", encoding="utf-8") as f:
                data = json.load(f)            
            return data
    except Exception as e:
        print (e)

    return None


def new_queue_session(session_key,data, group_key):    
    epoch_ms = int(time.time() * 1000000000)
    epoch_ms_str = str(epoch_ms)  
    
    if data["status"] == "Active":        
        os.makedirs(settings.QUEUE_STORE_DB+"/queue_sessions/active/{}".format(group_key), exist_ok=True)  
        directory = settings.QUEUE_STORE_DB+"/queue_sessions/active/{}".format(group_key)
        session_file = directory+"/"+epoch_ms_str+"_session_"+session_key+".json"        
    else:     
        os.makedirs(settings.QUEUE_STORE_DB_SLAVE_TMP+"/new_session/{}/".format(group_key), exist_ok=True)        
        sub_directory = settings.QUEUE_STORE_DB_SLAVE_TMP+"/new_session/{}/".format(group_key)
        session_file = str(sub_directory)+"/"+epoch_ms_str+"_session_"+session_key+".json"
    
    if session_file:       
        try:                  
            json_text = json.dumps(data, ensure_ascii=False, indent=2)
            with open(session_file, "w") as f:
                f.write(json_text)
        except Exception as e:
            print ("Error Saving File:"+session_file)
            print (e)
            return None 
    
    return session_file


def new_queue_session_09022026(session_key,data, group_key):    
    epoch_ms = int(time.time() * 1000000000)
    epoch_ms_str = str(epoch_ms)  
    os.makedirs(settings.QUEUE_STORE_DB+"/queue_sessions/active/{}".format(group_key), exist_ok=True)  
    if data["status"] == "Active":        
        directory = settings.QUEUE_STORE_DB+"/queue_sessions/active/{}".format(group_key)
        session_file = directory+"/"+epoch_ms_str+"_session_"+session_key+".json"        
    else:
        directory = settings.QUEUE_STORE_DB+"/queue_sessions/waiting/{}".format(group_key)
        directory_list = os.listdir(directory)
        directory_session_limit = settings.DIRECTORY_SESSION_LIMIT
        session_file = None
        i = settings.DIRECTORY_FOLDER_LIMIT
        
        while i != 0:                           
            sub_directory = Path(str(settings.QUEUE_STORE_DB)+"/queue_sessions/waiting/{}/{}".format(group_key,str(i)))            
            if os.path.isdir(sub_directory):
                pass
            else:
                os.mkdir(sub_directory)            
                      
            files = [f for f in sub_directory.iterdir() if f.is_file()]            
            file_count = len(files)
            
            if file_count == 0:
                insert_sub_directory = i

            if file_count < directory_session_limit and file_count != 0:
                insert_sub_directory = i
                break

            if file_count >= directory_session_limit:
                insert_sub_directory = i + 1
                break

            # if file_count < directory_session_limit:                    
            #     session_file = str(sub_directory)+"/"+epoch_ms_str+"_session_"+session_key+".json"
                    # break
                
            
                #session_file = str(sub_directory)+"/"+epoch_ms_str+"_session_"+session_key+".json"
                # break
            i -= 1        


        sub_directory = Path(str(settings.QUEUE_STORE_DB)+"/queue_sessions/waiting/{}/{}".format(group_key,insert_sub_directory))
        session_file = str(sub_directory)+"/"+epoch_ms_str+"_session_"+session_key+".json"
    
    if session_file:       
        try:                  
            json_text = json.dumps(data, ensure_ascii=False, indent=2)
            with open(session_file, "w") as f:
                f.write(json_text)
        except Exception as e:
            print ("Error Saving File:"+session_file)
            print (e)
            return None 
    
    return session_file

def save_ip_new_session_log(session_key,ipaddress, group_key):
        
    today = date.today()
    datetime_string = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Extract the day, month, and year
    day_value = today.day
    month_value = today.month
    year_value = today.year
    storage_directory = settings.QUEUE_STORE_DB_SLAVE_TMP+"/ip_session_log/{}/{}/{}/{}".format(group_key, str(year_value), str(month_value), str(day_value))
    os.makedirs(storage_directory, exist_ok=True)  

    with open(storage_directory+"/"+ipaddress+".log", 'a') as f:
        f.write(datetime_string+"-!-"+ipaddress+"-!-"+session_key+"\n")


def get_session_by_id(group_key,session_id, source='tmp'):    
      
    source_dir = settings.QUEUE_STORE_DB_TMP
    if source == 'master':
        source_dir = settings.QUEUE_STORE_DB

    directory = Path(source_dir+"/queue_sessions/active/{}".format(group_key))  
    os.makedirs(directory, exist_ok=True)  
    files = [f for f in directory.iterdir() if f.is_file()]    
    # files.sort(key=lambda f: f.stat().st_mtime, reverse=False)
    files.sort()
    
    for f in files:
        # print (f)
        # if f.is_file():  
        session_filename = os.path.basename(f)
        session_filename_split = session_filename.split("_session_")
        session_id_val = session_filename_split[1]    
        #print ("IDVAL"+session_id_val)        
        if session_id_val == session_id+".json":                                                          
            return (f)    

    # directory = settings.QUEUE_STORE_DB+"/queue_sessions/waiting/{}".format(group_key)
    # directory_list = os.listdir(directory)
    i = 1
    while i <= settings.DIRECTORY_FOLDER_LIMIT:          
    # for dir in directory_list:
        sub_directory = Path(source_dir+"/queue_sessions/waiting/{}/{}".format(group_key,str(i)))
        
        if os.path.isdir(sub_directory):
            files = [f for f in sub_directory.iterdir() if f.is_file()]
            # files.sort(key=lambda f: f.stat().st_mtime, reverse=False)
            files.sort()
            for f in files:
                #if f.is_file():  
                session_filename = os.path.basename(f)
                session_filename_split = session_filename.split("_session_")
                session_id_val = session_filename_split[1]                              
                if session_id_val == session_id+".json":                                                                        
                    return (f)   
        i += 1    
    if source == 'tmp':
        session_resp = get_session_by_id(group_key,session_id, source='master')
        return session_resp
    return None

def delete_session(group_key,session_id):
    status = None
    try: 
        session_file = get_session_by_id(group_key,session_id)
        try:            
            sitesession = jsondb.get_queue_session(session_file_id)
            sitesession["status"] = "Deleted"
            sitesession["removed_date"] = (datetime.now().astimezone(PLUS_8)).strftime("%Y-%m-%d %H:%M:%S")
            move_session_to_deleted(group_key,session_id, sitesession)            
            os.remove(session_file)
            print ("Removing file "+str(session_file))
        except Exception as k:
            print ("Error removing "+str(session_file))
            print (k)
        status = True
    except Exception as e:
        print (e)
        status = True
    return status

def get_queue_position_by_id(group_key,session_id,source='tmp'):

    source_dir = settings.QUEUE_STORE_DB_TMP
    if source == 'master':
        source_dir = settings.QUEUE_STORE_DB
        

    if session_id is None:
        return None
    # directory = settings.QUEUE_STORE_DB+"./queue_sessions/waiting/{}".format(group_key)
    # directory_list = os.listdir(directory)    
    # directory_list = sorted(directory_list, key=int)
    position_count = 0

    i = 1
    while i <= settings.DIRECTORY_FOLDER_LIMIT:   
    # for dir in directory_list:
        sub_directory = Path(source_dir+"./queue_sessions/waiting/{}/{}".format(group_key,str(i)))     
        os.makedirs(sub_directory, exist_ok=True)   
        files = [f for f in sub_directory.iterdir() if f.is_file()]
        # files.sort(key=lambda f: f.stat().st_mtime, reverse=False)
        files.sort()
        for f in files:
            if f.is_file():  
                if ".lock" in str(f):
                    continue
                position_count = position_count + 1                
                session_filename = os.path.basename(f)
                session_filename_split = session_filename.split("_session_")
                session_id_val = session_filename_split[1]                   
                if session_id_val == session_id+".json":
                    # print ("FOUND POSITION {}".format(position_count))
                    return position_count  
        i += 1
    return None                   

def clean_recently_deleted(group_unique_key):
    sub_directory = Path(str(settings.QUEUE_STORE_DB)+"/queue_sessions/deleted_recently/{}".format(group_unique_key))            
    if os.path.isdir(sub_directory):
        pass
    else:
        os.mkdir(sub_directory)            
                
    for f in sub_directory.iterdir():        
        if ".lock" not in str(f):
            if str(f).endswith('.json'):                    
                file_mtime = os.path.getmtime(f)
                now = time.time()          
                age_in_seconds = now - file_mtime
                if age_in_seconds > 7200:
                    try:
                        os.remove(f)                                                                                                                    
                        print ("Removing File {}".format(str(f)))
                    except Exception as y:
                        print ("Error removing "+str(f))
                        print (y)      

def clean_queue_position_sessions(group_unique_key):
    sub_directory = Path(str(settings.QUEUE_STORE_DB)+"/queue_position/{}".format(group_unique_key))            
    if os.path.isdir(sub_directory):
        pass
    else:
        os.mkdir(sub_directory)            
                
    for f in sub_directory.iterdir():        
        if ".lock" not in str(f):
            if str(f).endswith('.txt'):                    
                file_mtime = os.path.getmtime(f)
                now = time.time()          
                age_in_seconds = now - file_mtime
                if age_in_seconds > 900:
                    try:
                        os.remove(f)                                                                                                                    
                        print ("Removing File {}".format(str(f)))
                    except Exception as y:
                        print ("Error removing "+str(f))
                        print (y)                    

def clean_queue_idle_sessions(group_unique_key):
    sub_directory = Path(str(settings.QUEUE_STORE_DB)+"/queue_idle/{}".format(group_unique_key))            
    if os.path.isdir(sub_directory):
        pass
    else:
        os.mkdir(sub_directory)            
                
    for f in sub_directory.iterdir():        
        if ".lock" not in str(f):
            if str(f).endswith('.json'):                    
                file_mtime = os.path.getmtime(f)
                now = time.time()          
                age_in_seconds = now - file_mtime
                if age_in_seconds > 900:
                    try:
                        os.remove(f)                                                                                                                    
                        print ("Removing File {}".format(str(f)))
                    except Exception as y:
                        print ("Error removing "+str(f))
                        print (y) 


def move_session_to_deleted(group_unique_key, session_id, json_data):
    dir1 = session_id[0:2]
    dir2 = session_id[2:4]

    now = datetime.now()
    year = now.year
    month = now.month
    day = now.day

    os.makedirs(settings.QUEUE_STORE_DB+"./queue_sessions/deleted/{}/{}/{}/{}".format(group_unique_key, year, month, day), exist_ok=True)        
    sub_directory = settings.QUEUE_STORE_DB+"./queue_sessions/deleted/{}/{}/{}/{}".format(group_unique_key, year, month, day)
    json_text = json.dumps(json_data, ensure_ascii=False, indent=2)
    with open(sub_directory+"/"+session_id+".json", "w") as f:
        f.write(json_text)

    os.makedirs(settings.QUEUE_STORE_DB+"./queue_sessions/deleted_recently/{}".format(group_unique_key), exist_ok=True)
    sub_directory = settings.QUEUE_STORE_DB+"./queue_sessions/deleted_recently/{}".format(group_unique_key)

    with open(sub_directory+"/"+session_id+".json", "w") as f:
        f.write(json_text)

          



def delete_active_expiry_idle_sessions(group_key):
    queue_group = get_queue_group(group_key)
    idle_limit_seconds = queue_group["idle_limit_seconds"]

    directory = Path(settings.QUEUE_STORE_DB+"/queue_sessions/active/{}".format(group_key))

    for f in directory.iterdir(): 
        try:
            if f.is_file():            
                file_path_lock = Path(str(f)+".lock")
                if file_path_lock.exists():
                    print ("Lock file exists"+str(file_path_lock))
                    continue
                file_path = Path(f)                
                if file_path.exists():
                    stats = file_path.stat()                    
                    file_modified_time = datetime.fromtimestamp(stats.st_mtime)
                    past_time = datetime.now() - timedelta(minutes=30)
                    if file_modified_time > past_time:
                        pass                        
                    else:
                        print ("File Session Deleted (Idle Past) : "+str(file_path))                        
                        os.remove(file_path)
                        continue
                    # Load JSON file into a variable
                    with file_path.open("r", encoding="utf-8") as f:
                        try:                            
                            session_filename = os.path.basename(file_path)                            
                            session_filename_split = session_filename.split("_session_")
                            session_id_val = session_filename_split[1]
                            session_id_val = session_id_val.replace(".json","")
                            data = json.load(f)
                            idle_data = get_session_idle(session_id_val, group_key, "master" ) 
                            now_dt = datetime.now().astimezone(PLUS_8)
                            idle_dt = datetime.strptime(idle_data["idle"], "%Y-%m-%d %H:%M:%S") 
                            idle_dt = dj_tz.make_aware(idle_dt, PLUS_8)
                            expiry_dt = datetime.strptime(data["expiry"], "%Y-%m-%d %H:%M:%S") 
                            expiry_dt = dj_tz.make_aware(expiry_dt, PLUS_8)
                            # expiry_dt = expiry_dt.replace(tzinfo=timezone.utc)
                            if expiry_dt < now_dt:
                                if file_path.exists():  
                                    try:
                                        print (session_id_val)
                                        data["status"] = "Deleted"
                                        data["removed_date"] = (datetime.now().astimezone(PLUS_8)).strftime("%Y-%m-%d %H:%M:%S")
                                        move_session_to_deleted(group_key,session_id_val, data)
                                        os.remove(file_path)                                                                
                                        print ("Session Expired, File Deleted: "+str(file_path)+":"+str(expiry_dt)+":"+str(now_dt))     
                                        
                                    except Exception as y:
                                        print ("Error removing "+str(file_path))
                                        print (y)
                            
                            idle_dt_subtract = datetime.now().astimezone(PLUS_8)-timedelta(seconds=idle_limit_seconds)
                            if idle_dt < idle_dt_subtract:                                              
                                if file_path.exists():                            
                                    try:            
                                        data["status"] = "Deleted"
                                        data["removed_date"] = (datetime.now().astimezone(PLUS_8)).strftime("%Y-%m-%d %H:%M:%S")                                               
                                        move_session_to_deleted(group_key,session_id_val, data)       
                                        os.remove(file_path)                                
                                        print ("Idle Session Expired, File Deleted: "+str(file_path)+":"+str(expiry_dt)+":"+str(now_dt))      
                                    except Exception as y:
                                        print ("Error removing "+str(file_path))
                                        print (y)                   
                        except Exception as e:
                            print ("DELETE EXCEPTION IDLE EXPIRED")
                            print (e)
                            # try:
                            #     os.remove(file_path)
                            #     print ("Removing file "+str(file_path))
                            # except Exception as d:
                            #     print ("Issue removing "+str(file_path))
                            #     print (d)
        except Exception as e:
            print ("Error in loop for file : "+ str(f))
            print (e)                            
                            
                        
                    
                  
    # files = [f for f in directory.iterdir() if f.is_file()]
    
    # print(files)
def delete_waiting_expiry_idle_sessions(group_key):
    queue_group = get_queue_group(group_key)
    idle_limit_seconds = queue_group["idle_limit_seconds"]

    directory_session_limit = settings.DIRECTORY_SESSION_LIMIT    
    i = 1
    previous_file_count = directory_session_limit
    while i <= settings.DIRECTORY_FOLDER_LIMIT:
        
        sub_directory = Path(settings.QUEUE_STORE_DB+"/queue_sessions/waiting/{}/{}".format(group_key,str(i)))
        print ("Checking Directory: {}".format(sub_directory))
        if os.path.isdir(sub_directory):            
            files = [f for f in sub_directory.iterdir() if f.is_file()]     
           
            for f in files:
                try:
                    file_path_lock = Path(str(f)+".lock")
                    if file_path_lock.exists():
                        print ("Lock file exists"+str(file_path_lock))
                        continue   
                    print (f)             
                    if f.is_file():
                        with f.open("r", encoding="utf-8") as fe:
                            try:
                                session_filename = os.path.basename(f)                            
                                session_filename_split = session_filename.split("_session_")
                                session_id_val = session_filename_split[1]
                                session_id_val = session_id_val.replace(".json","")

                                data = json.load(fe)                
                                idle_data = get_session_idle(session_id_val, group_key, "master" )                
                                now_dt = datetime.now().astimezone(PLUS_8)
                                idle_dt = datetime.strptime(idle_data["idle"], "%Y-%m-%d %H:%M:%S") 
                                idle_dt = dj_tz.make_aware(idle_dt, PLUS_8)         
                                idle_dt_subtract = datetime.now().astimezone(PLUS_8)-timedelta(seconds=idle_limit_seconds)
                                activated_idle_dt_subtract = datetime.now().astimezone(PLUS_8)-timedelta(seconds=60)
                                if idle_dt < idle_dt_subtract:                                                                   
                                    try:              

                                        data["status"] = "Deleted"
                                        data["removed_date"] = (datetime.now().astimezone(PLUS_8)).strftime("%Y-%m-%d %H:%M:%S")            
                                        move_session_to_deleted(group_key,session_id_val, data)
                                        os.remove(f)                                
                                        print ("Idle Session Expired, File Deleted: "+str(f))      
                                    except Exception as y:
                                        print ("Error removing "+str(f))
                                        print (y)   
                                
                                if "activated" in data:                                    
                                    activated_dt = datetime.strptime(data["activated"], "%Y-%m-%d %H:%M:%S")
                                    if activated_dt < activated_idle_dt_subtract:                                        
                                        try:     
                                            data["status"] = "Deleted"
                                            data["removed_date"] = (datetime.now().astimezone(PLUS_8)).strftime("%Y-%m-%d %H:%M:%S")            
                                            move_session_to_deleted(group_key,session_id_val, data)                                                                 
                                            os.remove(f)                                
                                            print ("Activated Idle Session Expired, File Deleted: "+str(f))      
                                        except Exception as y:
                                            print ("Error removing activated idle session "+str(f))
                                            print (y)                                           

                            except Exception as e:
                                print (e)
                                try:
                                    os.remove(f)
                                    print ("Removing file "+str(f))
                                except Exception as d:
                                    print ("Issue removing "+str(f))
                                    print (d)
                except Exception as e:
                    print ("Error in file loop")
                    print (e)
        i += 1                                  

def get_new_session_slave_total(group_key):     
    
    directory = Path(settings.QUEUE_STORE_DB_SLAVE_TMP+"/new_session/{}".format(group_key))
    os.makedirs(directory, exist_ok=True)   
    file_count = 0    
    for f in directory.iterdir():        
        if ".lock" not in str(f):
            if str(f).endswith('.json'):
                file_count = file_count + 1    
    return file_count

def get_active_sessions_total(group_key):        
    directory = Path(settings.QUEUE_STORE_DB+"/queue_sessions/active/{}".format(group_key))
    file_count = 0    
    for f in directory.iterdir():        
        if ".lock" not in str(f):
            if str(f).endswith('.json'):
                file_count = file_count + 1    
    return file_count


def get_waiting_session_total(group_key):          
    file_count = 0
    i = 1
    while i <= settings.DIRECTORY_FOLDER_LIMIT:       
        sub_directory = Path(settings.QUEUE_STORE_DB+"./queue_sessions/waiting/{}/{}".format(group_key,str(i)))        
        if os.path.isdir(sub_directory):
            for f in sub_directory.iterdir():                
                if ".lock" not in str(f):
                    if str(f).endswith('.json'):
                        file_count = file_count + 1
        i += 1 
    return file_count             

def get_active_session_list(group_key):
    active_sessions = []

    sub_directory = Path(settings.QUEUE_STORE_DB+"/queue_sessions/active/{}".format(group_key))    
    files = [f for f in sub_directory.iterdir() if f.is_file()]
    # files.sort(key=lambda f: f.stat().st_mtime, reverse=False)
    files.sort()
    for f in files:
        if f.is_file():  
            if ".lock" in str(f):
                continue                
            active_sessions.append(f)
    

    return active_sessions

def get_longest_waiting(group_key, stl):

    longest_waiting = []
    #directory = settings.QUEUE_STORE_DB+"/queue_sessions/waiting/{}".format(group_key)
    file_count = 0
    # directory_list = os.listdir(directory)
    # directory_list = sorted(directory_list, key=int)
    # directory_list = sorted(directory_list)
    file_count = 0
    i = 1
    while i <= settings.DIRECTORY_FOLDER_LIMIT:        
        sub_directory = Path(settings.QUEUE_STORE_DB+"/queue_sessions/waiting/{}/{}".format(group_key,str(i)))    
    # for dir in directory_list:
        # sub_directory = Path(settings.QUEUE_STORE_DB+"/queue_sessions/waiting/{}/{}".format(group_key,i))
        files = [f for f in sub_directory.iterdir() if f.is_file()]
        # files.sort(key=lambda f: f.stat().st_mtime, reverse=False)
        files.sort()
        for f in files:
            if f.is_file():  
                if ".lock" in str(f):
                    continue                
                longest_waiting.append(f)
                file_count = file_count + 1
                if file_count >= stl:                    
                    break
        if file_count >= stl:            
            break   
        i += 1             

    return longest_waiting

def set_wait_queue_position(group_key):        
    
    directory_session_limit = settings.DIRECTORY_SESSION_LIMIT    
    i = 1
    previous_file_count = directory_session_limit
    position_start = 1 
    while i <= settings.DIRECTORY_FOLDER_LIMIT:                        
        sub_directory = Path(settings.QUEUE_STORE_DB+"/queue_sessions/waiting/{}/{}".format(group_key,str(i)))
        if os.path.isdir(sub_directory):            
            files = [f for f in sub_directory.iterdir() if f.is_file()]     
            # files.sort(key=lambda f: f.stat().st_mtime, reverse=False)
            files.sort()       
            file_count = len(files)
            if file_count > 0:                
                # files.sort(key=lambda f: f.stat().st_mtime, reverse=False) 
                for f in files:
                    if f.is_file():   
                        if str(f).endswith('.json'):
                            try:
                                if ".lock" not in str(f):
                                    session_filename = os.path.basename(f)
                                    session_filename_split = session_filename.split("_session_")
                                    session_id_val = session_filename_split[1]     
                                    session_id_val = session_id_val.replace(".json","")                                   
                                    # LOCK_PATH = str(f)+".lock" 
                                    # lock = FileLock(LOCK_PATH)
                                    
                                    # with lock:                                                     
                                    #     sitesession = get_queue_session(f)    
                                    #     sitesession['queue_position'] = position_start                                
                                    #     sitesession['queue_position_epoch'] = int(time.time() * 1000)
                                    # try:       
                                    #     os.remove(LOCK_PATH)
                                    # except Exception as k:
                                    #     print ("Error Removing "+str(LOCK_PATH))
                                    #     print (k)         
                                    try:                                                                                       
                                        save_queue_position(session_id_val,position_start,group_key)
                                    except Exception as e:
                                        print ("Error saving position")
                                        print (e)
                                    print (str(f) + "with position "+str(position_start))
                                    position_start = position_start + 1                            
                                     
                            except Exception as e:
                                position_start = position_start + 1
                                print ("EXCEPTION Error Updating Queue Position")
                                print (e)
                                                
        i += 1

def wait_queue_rotate(group_key,start, finish):        
    directory_session_limit = settings.DIRECTORY_SESSION_LIMIT    
    i = 1
    previous_file_count = directory_session_limit
    while i <= settings.DIRECTORY_FOLDER_LIMIT:        
        if i >= start and i <= finish: 
            sub_directory = Path(settings.QUEUE_STORE_DB+"/queue_sessions/waiting/{}/{}".format(group_key,str(i)))
            if os.path.isdir(sub_directory):            
                files = [f for f in sub_directory.iterdir() if f.is_file()]     
                # files.sort(key=lambda f: f.stat().st_mtime, reverse=False)
                files.sort()       
                file_count = len(files)
                if i > 1:
                    waiting_room_space = directory_session_limit - previous_file_count
                    if waiting_room_space > 0:
                        # files.sort(key=lambda f: f.stat().st_mtime, reverse=False) 
                        for f in files:
                            if f.is_file():          
                                session_filename = os.path.basename(f)  
                                previous_path = Path(str(previous_sub_directory)+"/"+session_filename)
                                
                                
                                try: 
                                    if ".lock" not in str(f):
                                        LOCK_PATH = str(f)+".lock" 
                                        lock = FileLock(LOCK_PATH)
                                        with lock:                                    
                                            shutil.copyfile(f, previous_path)
                                            os.remove(f)
                                            print ("Removing file "+str(f))
                                        try:       
                                            os.remove(LOCK_PATH)
                                        except Exception as k:
                                            print ("Error Removing "+str(LOCK_PATH))
                                            print (k)                                        
                                        
                                except Exception as e:
                                    print ("Error removing "+str(f))
                                    print (e)

                previous_sub_directory = sub_directory  
                previous_file_count = file_count

        i += 1


def get_active_sessions(group_key, start, length, search):        
    directory = Path(settings.QUEUE_STORE_DB+"/queue_sessions/active/{}".format(group_key))
    end = start + length
    active_session_count = 1
    active_sessions = []
    for f in directory.iterdir():
        if f.is_file():            
            file_path = Path(f)
            if file_path.exists():
                # Load JSON file into a variable
                with file_path.open("r", encoding="utf-8") as f:
                    try:
                        data = json.load(f)

                        if len(search) > 0:
                            if data["session_key"] in search or data["ipaddress"] in search or data["ipaddress"] in search  or data["ipaddress"] in search:
                                pass
                            else:
                                continue
            
                        if active_session_count > start and active_session_count <= end:
                            active_sessions.append(data)

                        if active_session_count > end:
                            break
                        active_session_count = active_session_count + 1
                    except Exception as e:
                        print ("Skipping Active "+str(f)+" due to read issues")
                        print (e)
    json_resp = {"data": active_sessions, "recordsFiltered": active_session_count}
    return json_resp



def get_waiting_sessions(group_key, start, length, search):
    waiting_sessions = []
    end = start + length
    waiting_session_count = 1    
    directory_session_limit = settings.DIRECTORY_SESSION_LIMIT    
    i = 1
    previous_file_count = directory_session_limit
    while i <= settings.DIRECTORY_FOLDER_LIMIT:
        sub_directory = Path(settings.QUEUE_STORE_DB+"/queue_sessions/waiting/{}/{}".format(group_key,str(i)))
        # print ("Checking Directory: {}".format(sub_directory))
        if os.path.isdir(sub_directory):            
            files = [f for f in sub_directory.iterdir() if f.is_file()]     
            for f in files:
                if f.is_file():
                    with f.open("r", encoding="utf-8") as fe:
                        try:
                            data = json.load(fe)
                            if len(search) > 0:
                                if data["session_key"] in search or data["ipaddress"] in search or data["ipaddress"] in search  or data["ipaddress"] in search:
                                    pass
                                else:
                                    continue
                
                            if waiting_session_count > start and waiting_session_count <= end:
                                waiting_sessions.append(data)

                            if waiting_session_count > end:
                                break
                            waiting_session_count = waiting_session_count + 1
                        except Exception as e:
                            print ("Skipping Waiting "+str(f)+" due to read issues")
                            print (e)
        i += 1
    json_resp = {"data": waiting_sessions, "recordsFiltered": waiting_session_count}
    return json_resp



def delete_all_sessions(group_key):    
    directory = Path(settings.QUEUE_STORE_DB+"/queue_sessions/active/{}/".format(group_key))    
    files = [f for f in directory.iterdir() if f.is_file()]    
    files.sort()
    
    deletion_count = 0
    for f in files:
        if f.is_file(): 
            try:             
                os.remove(f)
                print ("Deleting "+str(f))
                deletion_count = deletion_count + 1
            except Exception as e:
                print ("Error deleting {}".format(str(f)))
                print (e)               

    directory = settings.QUEUE_STORE_DB+"/queue_sessions/waiting/{}".format(group_key)
    directory_list = os.listdir(directory)
    for dir in directory_list:
        sub_directory = Path(settings.QUEUE_STORE_DB+"/queue_sessions/waiting/{}/{}/".format(group_key,dir))
        files = [f for f in sub_directory.iterdir() if f.is_file()]
        files.sort()
        for f in files:
            if f.is_file(): 
                try:                 
                    os.remove(f)
                    print ("Deleting : "+str(f))
                    deletion_count = deletion_count + 1
                except Exception as e:
                    print ("Error deleting {}".format(str(f)))
                    print (e)
    return deletion_count