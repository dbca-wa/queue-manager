import logging
from django.db.models import Q
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.views.generic.base import View, TemplateView
from django.conf import settings
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie
from django import forms
from django.views.generic.base import View, TemplateView
from django.template.loader import get_template
from django.template.loader import render_to_string
from django_site_queue import models
from django import shortcuts
from django import http
from typing import Any
from confy import env

class Home(TemplateView):
    # preperation to replace old homepage with screen designs..

    template_name = 'site_queue/home.html'
    # def render_to_response(self, context):

    #     template = get_template(self.template_name)
    #     response = HttpResponse(template.render(context))
    #     response["Access-Control-Allow-Headers"] = "*"
    #     return response
 
    # def get_context_data(self, **kwargs):
    #     context = super(Home, self).get_context_data(**kwargs)
    #     context['VERSION_NO'] = settings.VERSION_NO
    #     context['QUEUE_URL'] = env('QUEUE_URL','')
    #     return context

class WaitingRoom(TemplateView):
    # preperation to replace old homepage with screen designs..

    template_name = 'site_queue/waiting_room.html'

    def get(self, request: http.HttpRequest, *args: Any, **kwargs: Any) -> http.HttpResponse:
        """Provides the GET request endpoint for the HomePage view.
        Args:
            request (http.HttpRequest): The incoming HTTP request.
            *args (Any): Extra positional arguments.
            **kwargs (Any): Extra keyword arguments.
        Returns:
            http.HttpResponse: The rendered template response.
        """
        # Construct Context
        context: dict[str, Any] = {}
        queue_group_name = kwargs['queue_group_name']
        
        template_header_key='dbcablack'
        context['queue_manager_exist'] = False
        context['queue_manager_obj'] = {}
        
        queue_manager_obj = models.SiteQueueManagerGroup.objects.filter(group_unique_key=queue_group_name)
        if queue_manager_obj.count() > 0:
            template_header_key=queue_manager_obj[0].template_header_key
            context['queue_manager_exist'] = True
            context['queue_manager_obj'] = queue_manager_obj[0]
            print (context['queue_manager_obj'])
        
            
        context['template_group'] = template_header_key
        # Render Template and Return
        return shortcuts.render(request, self.template_name, context)


class QueueExpired(TemplateView):
    # preperation to replace old homepage with screen designs..

    template_name = 'site_queue/queue_expired.html'

    def get(self, request: http.HttpRequest, *args: Any, **kwargs: Any) -> http.HttpResponse:
        """Provides the GET request endpoint for the HomePage view.
        Args:
            request (http.HttpRequest): The incoming HTTP request.
            *args (Any): Extra positional arguments.
            **kwargs (Any): Extra keyword arguments.
        Returns:
            http.HttpResponse: The rendered template response.
        """
        # Construct Context
        context: dict[str, Any] = {}
        queue_group_name = kwargs['queue_group_name']
        
        template_header_key='dbcablack'
        context['queue_manager_exist'] = False
        context['queue_manager_obj'] = {}
        queue_manager_obj = models.SiteQueueManagerGroup.objects.filter(group_unique_key=queue_group_name)
        if queue_manager_obj.count() > 0:
            template_header_key=queue_manager_obj[0].template_header_key
            context['queue_manager_exist'] = True
            context['queue_manager_obj'] = queue_manager_obj[0]
            print (context['queue_manager_obj'])        
            
        context['template_group'] = template_header_key
        # Render Template and Return
        return shortcuts.render(request, self.template_name, context)


class QueuePage(TemplateView):
    # preperation to replace old homepage with screen designs..

    template_name = 'site_queue/queue.html'
    def render_to_response(self, context):

        template = get_template(self.template_name)
        #context['csrf_token_value'] = get_token(self.request)
        response = HttpResponse(template.render(context))
        response["Access-Control-Allow-Headers"] = "*"
        #response["X-Frame-Options"] = "ALLOW-FROM https://mooring-uat.dbca.wa.gov.au"
        return response
 
    def get_context_data(self, **kwargs):
        context = super(QueuePage, self).get_context_data(**kwargs)
        context['VERSION_NO'] = settings.VERSION_NO
        context['QUEUE_URL'] = env('QUEUE_URL','')
        return context


class SetSessionPage(TemplateView):
    # preperation to replace old homepage with screen designs..

    template_name = 'site_queue/set_session.html'
    def render_to_response(self, context):

        template = get_template(self.template_name)
        #context['csrf_token_value'] = get_token(self.request)
        return HttpResponse(template.render(context))

    def get_context_data(self, **kwargs):
        context = super(SetSessionPage, self).get_context_data(**kwargs)
        #context = template_context(self.request)
        #APP_TYPE_CHOICES = []
        #APP_TYPE_CHOICES_IDS = []
        return context

def setsession(request):
    rendered = render_to_string('site_queue/set_session.html', { 'foo': 'bar' })
    response = HttpResponse(rendered, content_type='text/html')
    CORS_SITES = env('CORS_SITES', '')
    CORS_SITES2 = env('CORS_SITES2', '')
   
    response["Access-Control-Allow-Origin"] = "*" 
    response["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    response["Access-Control-Max-Age"] = "0"
    response["Access-Control-Allow-Headers"] = "*"
    if CORS_SITES:
       response["X-FRAME-OPTIONS"] = "ALLOW-FROM "+CORS_SITES
    if CORS_SITES2:
       response["Content-Security-Policy"] =  "frame-ancestors "+CORS_SITES2 
    #response.set_cookie('sitequeuesession', session_key)
    return response

