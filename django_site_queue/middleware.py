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
     #   print ("CACHE")
       if request.path == '/':
            response['Cache-Control'] = 'public, max-age=60'
       elif request.path[:5] == '/api/':
            response['Cache-Control'] = 'private, no-store'
       elif request.path[:8] == '/static/':
            response['Cache-Control'] = 'public, max-age=300'
       elif request.path[:7] == '/media/':
            response['Cache-Control'] = 'public, max-age=3600'
       elif request.path[:17] == '/site-queue/view/':
            response['Cache-Control'] = 'public, max-age=60'
       else:
            pass
            #response['Cache-Control'] = 'private, no-store'
       return response

