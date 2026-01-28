import re
import datetime
from django.urls import reverse
from django.http import Http404, HttpResponse, JsonResponse, HttpResponseRedirect
from django.utils import timezone

class CacheControl(object):

    def __init__(self, get_response):
            self.get_response = get_response

    def __call__(self, request):
       response= self.get_response(request)

       if request.path == '/':
            response['Cache-Control'] = 'public, max-age=60'
            response['Surrogate-Control'] = 'public, max-age=60'
       elif request.path[:5] == '/api/':
            response['Cache-Control'] = 'private, no-store'            
       elif request.path[:8] == '/static/':
            response['Cache-Control'] = 'public, max-age=300'
            response['Surrogate-Control'] = 'public, max-age=300'
       elif request.path[:7] == '/media/':
            response['Cache-Control'] = 'public, max-age=3600'
            response['Surrogate-Control'] = 'public, max-age=3600'
       elif request.path[:17] == '/site-queue/view/':            
            response['Cache-Control'] = 'public, max-age=60'
            response['Surrogate-Control'] = 'public, max-age=60'
       elif request.path[:31] == '/site-queue/service-restricted/':
            response['Cache-Control'] = 'public, max-age=3600'
            response['Surrogate-Control'] = 'public, max-age=3600'
       elif request.path[:26] == '/site-queue/max-threshold/':
            response['Cache-Control'] = 'public, max-age=3600'
            response['Surrogate-Control'] = 'public, max-age=3600'            
            response['Vary'] = 'Origin' 
            response.delete_cookie('sessionid')
            response.headers.pop('Set-Cookie', None)
            if 'Set-Cookie' in response:
                print ("deleting cookie")
                del response['Set-Cookie']            
       elif request.path[:25] == '/site-queue/waiting-room/':
            response['Cache-Control'] = 'public, max-age=3600'   
            response['Surrogate-Control'] = 'public, max-age=3600'         
       else:
            pass
            #response['Cache-Control'] = 'private, no-store'
       return response

