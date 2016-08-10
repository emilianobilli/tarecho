from django.shortcuts import render
from django.http import HttpResponse
import json

# Create your views here.

from models import Job
from models import Config
from models import ThumbPreset

from django.core.exceptions import *

http_POST_OK    = 201
http_REQUEST_OK = 200
http_NOT_FOUND  = 404


def imen_GetPostJob(request):
    # Determinar si es un Get o un Post
    if request.method == 'GET':
        return imen_GetJob(request)

    if request.method == 'POST':
        return imen_PostJob(request)

def imen_GetJob(request):

    response = []
    #
    # Para todos los trabajos:
    # 	- Armar el json de respuesta
    for job in Job.objects.all():
        response.append({"job":
                        {"id": job.id, "basename": job.basename}
                        })

    # La unica respuesta para esto es OK
    status = http_REQUEST_OK
    return HttpResponse(json.dumps(response), status=status, content_type='application/json')

def imen_PostJob(request):

    jsonData = json.loads(request.body)

    try:
        preset = ThumbPreset.objects.get(name=jsonData['job']['thumb_preset'])
    except ObjectDoesNotExist:
        status = http_NOT_FOUND
        return HttpResponse(json.dumps({'message': 'ThumbPreset not found'}), status=status, content_type='application/json')


    job = Job()
    job.input_filename  = jsonData['job']['input_filename']
    job.input_path      = jsonData['job']['input_path']
    job.basename        = jsonData['job']['basename']
    job.thumb_preset    = preset
    job.priority        = jsonData['job']['priority']
    job.output_path     = jsonData['job']['output_path']
    job.status          = 'Q' # Queue

    job.save()

    response = {"job": {"id": job.id}}
    #
    # La unica respuesta para esto es OK

    status = http_POST_OK
    return HttpResponse(json.dumps(response), status=status, content_type='application/json')


def imen_GetJobId(request, id):
    #
    # Buscar el Job que se esta pidiendo
    try:
        job = Job.objects.get(id=id)
    except ObjectDoesNotExist:
        status = http_NOT_FOUND
        return HttpResponse(json.dumps({}), status=status, content_type='application/json')

    response = {"job":
        {
            "id": job.id,
            "thumb_preset": job.thumb_preset.name,
            "input_filename": job.input_filename,
            "input_path": job.input_path,
            "basename": job.basename,
            "output_path": job.output_path,
            "priority": job.priority,
            "status": job.status,
            "progress": job.progress,
            "message": job.message
        }
    }

    status = http_REQUEST_OK
    return HttpResponse(json.dumps(response), status=status, content_type='application/json')

