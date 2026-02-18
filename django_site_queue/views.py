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
# from django_site_queue import models
from django import shortcuts
from django import http
from typing import Any
from confy import env
from django_site_queue import  jsondb
from django.views.generic.edit import FormView
from django.contrib.auth.forms import AuthenticationForm
from django.urls import reverse_lazy

from wagov_utils.components.json_auth.no_signal_login import login_without_signal


# your_app/views.py
from django.contrib.auth.forms import AuthenticationForm
from django.views.generic.edit import FormView
from django.urls import reverse_lazy
from django.contrib.auth import authenticate
from django.http import HttpResponseRedirect
from django.core.exceptions import PermissionDenied

# your_app/views.py
from django.views import View as DjangoView
from django.contrib import messages
from django.contrib.auth import BACKEND_SESSION_KEY, HASH_SESSION_KEY, SESSION_KEY

from wagov_utils.components.json_auth.no_signal_login import login_without_signal
from wagov_utils.components.json_auth.auth_middleware_backend import _JSONAuthStore

class JSONLoginView(FormView):
    template_name = "registration/login.html"  # your template path
    form_class = AuthenticationForm
    success_url = reverse_lazy("home")

    def form_valid(self, form):
        username = form.cleaned_data["username"]
        password = form.cleaned_data["password"]

        user = authenticate(self.request, username=username, password=password)
        if user is None:
            form.add_error(None, "Invalid credentials")
            return self.form_invalid(form)

        if getattr(user, "is_active", True) is False:
            raise PermissionDenied("User inactive")

        backend_path = getattr(user, "backend", None) or \
            "ywagov_utils.components.json_auth.auth_middleware_backend.JSONFileOnlyBackend"

        login_without_signal(self.request, user, backend_path=backend_path)
        return HttpResponseRedirect(self.get_success_url())




class JSONLogoutView(View):
    """
    DB-free logout. Removes auth keys from session and rotates it,
    without touching the DB or emitting signals.
    """
    success_url = reverse_lazy("login")  # change to your post-logout page

    def _logout(self, request):
        # Remove the auth keys explicitly (same keys Django uses)
        request.session.pop(SESSION_KEY, None)           # _auth_user_id
        request.session.pop(BACKEND_SESSION_KEY, None)   # _auth_user_backend
        request.session.pop(HASH_SESSION_KEY, None)      # _auth_user_hash

        # Rotate/flush session for security (similar to django.contrib.auth.logout)
        request.session.flush()

        # Optional: add a user-facing message
        try:
            messages.success(request, "You have been logged out.")
        except Exception:
            # messages framework may be disabled; ignore
            pass

    def post(self, request, *args, **kwargs):
        self._logout(request)
        return HttpResponseRedirect(self.get_success_url())

    # If you prefer GET to log out directly (like Django's default LogoutView),
    # leave this as-is. If you want a confirmation page, replace with a template.
    def get(self, request, *args, **kwargs):
        self._logout(request)
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return str("/")


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

class Admin(TemplateView):
    template_name = 'site_queue/admin/home.html'
    def get(self, request: http.HttpRequest, *args: Any, **kwargs: Any) -> http.HttpResponse:
        context: dict[str, Any] = {}
        if request.user.is_authenticated:
            a = _JSONAuthStore()
            u = a.get_user_record(request.user.email)
            context["json_user"] = u
            
            if u: 
                if u["groups"]:            
                    if "Admin" in u["groups"]:
                        queue_groups = jsondb.get_queue_groups()
                        context['queue_groups'] = queue_groups  
                        for i in queue_groups:                
                            i["total_active_session"] = jsondb.get_active_sessions_total(i["group_unique_key"])
                            i["total_waiting_session"] = jsondb.get_waiting_session_total(i["group_unique_key"]) 
                 
        # Render Template and Return
        return shortcuts.render(request, self.template_name, context)  


class AdminActiveSessions(TemplateView):
    template_name = 'site_queue/admin/active_sessions.html'

    def get(self, request: http.HttpRequest, *args: Any, **kwargs: Any) -> http.HttpResponse:
        context: dict[str, Any] = {}
        queue_group_name = kwargs['queue_group_name']
        context['queue_group_name'] = queue_group_name        
        if request.user.is_authenticated:
            a = _JSONAuthStore()
            u = a.get_user_record(request.user.email)
            context["json_user"] = u
            if u: 
                if u["groups"]:             
                    if "Admin" in u["groups"]:
                        pass
                        
        # Render Template and Return
        return shortcuts.render(request, self.template_name, context)  

class AdminWaitingSessions(TemplateView):
    template_name = 'site_queue/admin/waiting_sessions.html'

    def get(self, request: http.HttpRequest, *args: Any, **kwargs: Any) -> http.HttpResponse:
        context: dict[str, Any] = {}
        queue_group_name = kwargs['queue_group_name']
        context['queue_group_name'] = queue_group_name
        if request.user.is_authenticated:
            a = _JSONAuthStore()
            u = a.get_user_record(request.user.email)
            context["json_user"] = u
            if u: 
                if u["groups"]:             
                    if "Admin" in u["groups"]:
                        pass        
        # Render Template and Return
        return shortcuts.render(request, self.template_name, context)  



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
        queue_manager_obj = jsondb.get_queue_group(queue_group_name)
        # print (queue_manager_obj )
        # queue_manager_obj = models.SiteQueueManagerGroup.objects.filter(group_unique_key=queue_group_name)
        if queue_manager_obj:
            template_header_key=queue_manager_obj["template_header_key"]
            active_session_url=queue_manager_obj["active_session_url"]
            context['logo_url'] = queue_manager_obj["active_session_url"]
            context['queue_manager_exist'] = True
            context['queue_manager_obj'] = queue_manager_obj
            # print (context['queue_manager_obj'])
            
        
            
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

        queue_manager_obj = jsondb.get_queue_group(queue_group_name)
        if queue_manager_obj:
            template_header_key=queue_manager_obj["template_header_key"]
            active_session_url=queue_manager_obj["active_session_url"]
            context['logo_url'] = queue_manager_obj["active_session_url"]
            context['queue_manager_exist'] = True
            context['queue_manager_obj'] = queue_manager_obj

        # queue_manager_obj = models.SiteQueueManagerGroup.objects.filter(group_unique_key=queue_group_name)
        # if queue_manager_obj.count() > 0:
        #     template_header_key=queue_manager_obj[0].template_header_key
        #     active_session_url=queue_manager_obj[0].active_session_url
        #     context['logo_url'] = active_session_url            
        #     context['queue_manager_exist'] = True
        #     context['queue_manager_obj'] = queue_manager_obj[0]
        #     print (context['queue_manager_obj'])        
            
        context['template_group'] = template_header_key
        # Render Template and Return
        return shortcuts.render(request, self.template_name, context)

class ServiceRestricted(TemplateView):
    # preperation to replace old homepage with screen designs..

    template_name = 'site_queue/service_restricted.html'

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

        # queue_manager_obj = models.SiteQueueManagerGroup.objects.filter(group_unique_key=queue_group_name)
        # if queue_manager_obj.count() > 0:
        #     template_header_key=queue_manager_obj[0].template_header_key
        #     active_session_url=queue_manager_obj[0].active_session_url
        #     context['logo_url'] = active_session_url            
        #     context['queue_manager_exist'] = True
        #     context['queue_manager_obj'] = queue_manager_obj[0]
        #     print (context['queue_manager_obj'])        

        queue_manager_obj = jsondb.get_queue_group(queue_group_name)
        if queue_manager_obj:
            template_header_key=queue_manager_obj["template_header_key"]
            active_session_url=queue_manager_obj["active_session_url"]
            context['logo_url'] = queue_manager_obj["active_session_url"]
            context['queue_manager_exist'] = True
            context['queue_manager_obj'] = queue_manager_obj

            
        context['template_group'] = template_header_key
        # Render Template and Return
        return shortcuts.render(request, self.template_name, context)


class ThresholdReached(TemplateView):
    # preperation to replace old homepage with screen designs..

    template_name = 'site_queue/threshold_reached.html'

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
        # queue_manager_obj = models.SiteQueueManagerGroup.objects.filter(group_unique_key=queue_group_name)
        # if queue_manager_obj.count() > 0:
        #     template_header_key=queue_manager_obj[0].template_header_key
        #     active_session_url=queue_manager_obj[0].active_session_url
        #     context['logo_url'] = active_session_url            
        #     context['queue_manager_exist'] = True
        #     context['queue_manager_obj'] = queue_manager_obj[0]
        #     print (context['queue_manager_obj'])       

        queue_manager_obj = jsondb.get_queue_group(queue_group_name)
        if queue_manager_obj:
            template_header_key=queue_manager_obj["template_header_key"]
            active_session_url=queue_manager_obj["active_session_url"]
            context['logo_url'] = queue_manager_obj["active_session_url"]
            context['queue_manager_exist'] = True
            context['queue_manager_obj'] = queue_manager_obj             
            
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

