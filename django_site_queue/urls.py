from django.conf.urls import url
#from django_site_queue import views
from django_site_queue import api
from django_site_queue import views

urlpatterns = [
    url(r'^api/check-create-session/$', api.check_create_session, name='check-create-session'),
    url(r'^site-queue/view/$', views.QueuePage.as_view(), name='site-queue-page'),
    url(r'^site-queue/set-session/$', views.setsession, name='site-set-session'),
]
