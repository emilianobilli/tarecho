from django.shortcuts import render
from django.http import HttpResponse
# Create your views here.

from django.core.exceptions import *

def view_AdminRedirect(request):
    ret = HttpResponse('', status=301)
    ret['Location'] = 'admin/'
    return ret

