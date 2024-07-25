from django.conf.urls import url
#from django_site_queue import views
from django_site_queue import api
from django_site_queue import views
from django.urls import path, re_path, include

urlpatterns = [
    path('', views.Home.as_view(), name='home'),
    url(r'^api/check-create-session/$', api.check_create_session, name='check-create-session'),
    url(r'^api/expire-session/$', api.expire_session, name='expire-session'),
    url(r'^api/status/$', api.queue_status, name='expire-session'),
    url(r'^site-queue/view/$', views.QueuePage.as_view(), name='site-queue-page'),
    re_path(r'^site-queue/waiting-room/(?P<queue_group_name>[A-Za-z0-9\-\_]+)/$', views.WaitingRoom.as_view(), name='site-waiting-room'),
    re_path(r'^site-queue/queue-expired/(?P<queue_group_name>[A-Za-z0-9\-\_]+)/$', views.QueueExpired.as_view(), name='site-queue-expired'),
    #re_path(r'^api/monitor/(?P<pk>[0-9]+)/$', api.get_monitor_info_by_id, name='python_package_advisory'), 
    url(r'^site-queue/set-session/$', views.setsession, name='site-set-session'),
]
