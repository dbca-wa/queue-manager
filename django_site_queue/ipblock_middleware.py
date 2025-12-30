import re
import datetime
from django.urls import reverse
from django.http import Http404, HttpResponse, JsonResponse, HttpResponseRedirect
from django.utils import timezone

class IPMonitor(object):

    def __init__(self, get_response):
            self.get_response = get_response

    def __call__(self, request):
        response= self.get_response(request)
        ip_address = self.get_client_ip(request)
        print (request.path[:31])
        if request.path[:31] == '/site-queue/service-restricted/':
            print (ip_address)
        return response


    def get_client_ip(self, request):
        x_real_ip = request.META.get('HTTP_X_REAL_IP')
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        
        if x_real_ip:
            ip = x_real_ip
        elif x_forwarded_for:
            ip = x_forwarded_for.split(',')[-1].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip