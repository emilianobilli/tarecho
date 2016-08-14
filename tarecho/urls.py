"""tarecho URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""


from django.conf.urls import url
from django.contrib import admin


import settings

ELEMENTO   = False
ELMCAFIOLO = False
IMEN       = False

if 'elemento.apps.ElementoConfig' in settings.INSTALLED_APPS:
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Elemento
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    from elemento.views import elemento_GetPostJob
    from elemento.views import elemento_GetJobId
    from elemento.views import elemento_GetJobIdOutputFile
    from elemento.views import elemento_GetConfig
    from elemento.views import elemento_GetPresetName
    from elemento.views import elemento_GetFormats
    elemento_patterns = [  
	    url(r'^elemento/api/job/$', elemento_GetPostJob),
        url(r'^elemento/api/job/(?P<id>\d+)/$', elemento_GetJobId),
        url(r'^elemento/api/job/(?P<id>\d+)/outputfile/$', elemento_GetJobIdOutputFile),
        url(r'^elemento/api/config/$', elemento_GetConfig),
        url(r'^elemento/api/preset/(?P<name>.+)/$', elemento_GetPresetName),
        url(r'^elemento/api/formats/$', elemento_GetFormats)
    ]
    ELEMENTO = True

if 'elmcafiolo.apps.ElmcafioloConfig' in settings.INSTALLED_APPS:
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# ElemCafiolo
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    from elmcafiolo.views import elmcafiolo_GetPostJob
    from elmcafiolo.views import elmcafiolo_GetJobId
    from elmcafiolo.views import elmcafiolo_GetJobIdOutputFile
    from elmcafiolo.views import elmcafiolo_IsScheduleableJob
    elmcafiolo_patterns = [
	    url(r'^elmcafiolo/api/job/$', elmcafiolo_GetPostJob),
        url(r'^elmcafiolo/api/job/(?P<id>\d+)/$', elmcafiolo_GetJobId),
        url(r'^elmcafiolo/api/job/(?P<id>\d+)/outputfile/$', elmcafiolo_GetJobIdOutputFile),
        url(r'^elmcafiolo/api/job/issched/(?P<preset>\w{0,50})/$', elmcafiolo_IsScheduleableJob)
    ]
    ELMCAFIOLO = True

if 'imen.apps.ImenConfig' in settings.INSTALLED_APPS:
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Imen
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    from imen.views import imen_GetPostJob
    from imen.views import imen_GetJobId
    imen_patterns = [
	    url(r'^imen/api/job/$', imen_GetPostJob),
        url(r'^imen/api/job/(?P<id>\d+)/$', imen_GetJobId)
    ]
    IMEN = True


import views


admin.site.site_header = 'TaReCho'

urlpatterns = [
    url(r'^$', views.view_AdminRedirect),
    url(r'^admin/', admin.site.urls)
]

#elemento_patterns = [  
#    url(r'^elemento/api/job/$', elemento_GetPostJob),
#    url(r'^elemento/api/job/(?P<id>\d+)/$', elemento_GetJobId),
#    url(r'^elemento/api/job/(?P<id>\d+)/outputfile/$', elemento_GetJobIdOutputFile),
#    url(r'^elemento/api/config/$', elemento_GetConfig),
#    url(r'^elemento/api/preset/(?P<name>.+)/$', elemento_GetPresetName),
#    url(r'^elemento/api/formats/$', elemento_GetFormats)
#]

if ELEMENTO is True:
    urlpatterns = urlpatterns + elemento_patterns

if ELMCAFIOLO is True:
    urlpatterns = urlpatterns + elmcafiolo_patterns

if IMEN is True:
    urlpatterns = urlpatterns + imen_patterns
