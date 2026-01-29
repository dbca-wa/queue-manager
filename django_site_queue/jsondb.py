from pathlib import Path
from datetime import timedelta, datetime, timezone
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
    file = Path(settings.QUEUE_STORE_DB+"/waiting_total/{}.json".format(group_key))    
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
    epoch_ms = int(time.time() * 1000)
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
            sub_directory = Path(str(settings.QUEUE_STORE_DB)+"/queue_sessions/waiting/{}/{}".format(group_key,i))            
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

def get_session_by_id(group_key,session_id):    
    
    directory = Path(settings.QUEUE_STORE_DB+"/queue_sessions/active/{}".format(group_key))    
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
            #print ("FDDD")                                                        
            return (f)    

    directory = settings.QUEUE_STORE_DB+"/queue_sessions/waiting/{}".format(group_key)
    directory_list = os.listdir(directory)
    for dir in directory_list:
        sub_directory = Path(settings.QUEUE_STORE_DB+"/queue_sessions/waiting/{}/{}".format(group_key,dir))
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
    return None

def delete_session(group_key,session_id):
    status = None
    try: 
        session_file = get_session_by_id(group_key,session_id)
        try:
            
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

def get_queue_position_by_id(group_key,session_id):
    if session_id is None:
        return None
    directory = settings.QUEUE_STORE_DB+"./queue_sessions/waiting/{}".format(group_key)
    directory_list = os.listdir(directory)
    position_count = 0
    directory_list = sorted(directory_list, key=int)
    
    for dir in directory_list:
        sub_directory = Path(settings.QUEUE_STORE_DB+"./queue_sessions/waiting/{}/{}".format(group_key,dir))        
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
                    print ("FOUND POISTION 2 {}".format(position_count))
                    return position_count  
    return None                   
        

def delete_active_expiry_idle_sessions(group_key):
    queue_group = get_queue_group(group_key)
    idle_limit_seconds = queue_group["idle_limit_seconds"]

    directory = Path(settings.QUEUE_STORE_DB+"/queue_sessions/active/{}".format(group_key))

    for f in directory.iterdir(): 
        if f.is_file():            
            file_path_lock = Path(str(f)+".lock")
            if file_path_lock.exists():
                print ("Lock file exists"+str(file_path_lock))
                continue
            file_path = Path(f)
            if file_path.exists():
                # Load JSON file into a variable
                with file_path.open("r", encoding="utf-8") as f:
                    try:
                        data = json.load(f)
                        now_dt = datetime.now().astimezone(PLUS_8)
                        idle_dt = datetime.strptime(data["idle"], "%Y-%m-%d %H:%M:%S") 
                        idle_dt = dj_tz.make_aware(idle_dt, PLUS_8)
                        expiry_dt = datetime.strptime(data["expiry"], "%Y-%m-%d %H:%M:%S") 
                        expiry_dt = dj_tz.make_aware(expiry_dt, PLUS_8)
                        # expiry_dt = expiry_dt.replace(tzinfo=timezone.utc)
                        if expiry_dt < now_dt:
                            if file_path.exists():  
                                try:                          
                                    os.remove(file_path)                                
                                    print ("Session Expired, File Deleted: "+str(file_path)+":"+str(expiry_dt)+":"+str(now_dt))     
                                     
                                except Exception as y:
                                    print ("Error removing "+str(file_path))
                                    print (y)
                        
                        idle_dt_subtract = datetime.now().astimezone(PLUS_8)-timedelta(seconds=idle_limit_seconds)
                        if idle_dt < idle_dt_subtract:                                              
                            if file_path.exists():                            
                                try:                          
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
                        
                        
                    
                  
    # files = [f for f in directory.iterdir() if f.is_file()]
    
    # print(files)
def delete_waiting_expiry_idle_sessions(group_key):
    queue_group = get_queue_group(group_key)
    idle_limit_seconds = queue_group["idle_limit_seconds"]

    directory_session_limit = settings.DIRECTORY_SESSION_LIMIT    
    i = 1
    previous_file_count = directory_session_limit
    while i <= settings.DIRECTORY_FOLDER_LIMIT:
        
        sub_directory = Path(settings.QUEUE_STORE_DB+"/queue_sessions/waiting/{}/{}".format(group_key,i))
        print ("Checking Directory: {}".format(sub_directory))
        if os.path.isdir(sub_directory):            
            files = [f for f in sub_directory.iterdir() if f.is_file()]     
            for f in files:
                file_path_lock = Path(str(f)+".lock")
                if file_path_lock.exists():
                    print ("Lock file exists"+str(file_path_lock))
                    continue                
                if f.is_file():
                    with f.open("r", encoding="utf-8") as fe:
                        try:
                            data = json.load(fe)
                            now_dt = datetime.now().astimezone(PLUS_8)
                            idle_dt = datetime.strptime(data["idle"], "%Y-%m-%d %H:%M:%S") 
                            idle_dt = dj_tz.make_aware(idle_dt, PLUS_8)         
                            idle_dt_subtract = datetime.now().astimezone(PLUS_8)-timedelta(seconds=idle_limit_seconds)
                            if idle_dt < idle_dt_subtract:                                                                   
                                try:                          
                                    os.remove(f)                                
                                    print ("Idle Session Expired, File Deleted: "+str(f))      
                                except Exception as y:
                                    print ("Error removing "+str(f))
                                    print (y)                                
                        except Exception as e:
                            print (e)
                            try:
                                os.remove(f)
                                print ("Removing file "+str(f))
                            except Exception as d:
                                print ("Issue removing "+str(f))
                                print (d)
        i += 1                                  

def get_active_sessions_total(group_key):    
    os.makedirs(settings.QUEUE_STORE_DB+"/queue_sessions/active/{}".format(group_key), exist_ok=True)
    directory = Path(settings.QUEUE_STORE_DB+"/queue_sessions/active/{}".format(group_key))
    file_count = sum(1 for f in directory.iterdir() if f.is_file())
    return file_count


def get_waiting_session_total(group_key):
    os.makedirs(settings.QUEUE_STORE_DB+"/queue_sessions/waiting/{}".format(group_key), exist_ok=True)
    directory = settings.QUEUE_STORE_DB+"/queue_sessions/waiting/{}".format(group_key)
    file_count = 0
    for root, dirs, files in os.walk(directory):
        file_count += len(files)
    return file_count


def get_longest_waiting(group_key, stl):

    longest_waiting = []
    directory = settings.QUEUE_STORE_DB+"/queue_sessions/waiting/{}".format(group_key)
    file_count = 0
    directory_list = os.listdir(directory)
    directory_list = sorted(directory_list, key=int)
    # directory_list = sorted(directory_list)
    file_count = 0
    for dir in directory_list:
        sub_directory = Path(settings.QUEUE_STORE_DB+"/queue_sessions/waiting/{}/{}".format(group_key,dir))
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

    return longest_waiting


def wait_queue_rotate(group_key):        
    directory_session_limit = settings.DIRECTORY_SESSION_LIMIT    
    i = 1
    previous_file_count = directory_session_limit
    while i <= settings.DIRECTORY_FOLDER_LIMIT:
        
        sub_directory = Path(settings.QUEUE_STORE_DB+"/queue_sessions/waiting/{}/{}".format(group_key,i))
        if os.path.isdir(sub_directory):            
            files = [f for f in sub_directory.iterdir() if f.is_file()]     
            # files.sort(key=lambda f: f.stat().st_mtime, reverse=False)
            files.sort()       
            file_count = len(files)
            if i > 1:
                waiting_room_space = directory_session_limit - previous_file_count
                if waiting_room_space > 0:
                    files.sort(key=lambda f: f.stat().st_mtime, reverse=False) 
                    for f in files:
                        if f.is_file():          
                            session_filename = os.path.basename(f)  
                            previous_path = Path(str(previous_sub_directory)+"/"+session_filename)
                            
                            
                            try: 
                                shutil.copyfile(f, previous_path)
                                os.remove(f)
                                print ("Removing file "+str(f))
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
        sub_directory = Path(settings.QUEUE_STORE_DB+"/queue_sessions/waiting/{}/{}".format(group_key,i))
        # print ("Checking Directory: {}".format(sub_directory))
        if os.path.isdir(sub_directory):            
            files = [f for f in sub_directory.iterdir() if f.is_file()]     
            for f in files:
                if f.is_file():
                    with f.open("r", encoding="utf-8") as fe:
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
            os.remove(f)
            print ("Deleting"+str(f))
            deletion_count = deletion_count + 1

    directory = settings.QUEUE_STORE_DB+"/queue_sessions/waiting/{}".format(group_key)
    directory_list = os.listdir(directory)
    for dir in directory_list:
        sub_directory = Path(settings.QUEUE_STORE_DB+"/queue_sessions/waiting/{}/{}/".format(group_key,dir))
        files = [f for f in sub_directory.iterdir() if f.is_file()]
        files.sort()
        for f in files:
            if f.is_file():                  
                os.remove(f)
                print ("Deleting"+str(f))
                deletion_count = deletion_count + 1
    return deletion_count