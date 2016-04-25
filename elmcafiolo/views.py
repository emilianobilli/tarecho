from django.shortcuts import render
from django.http import HttpResponse
import json

import elm

# Create your views here.

from models import Preset
from models import Transcoder
from models import Job

from django.core.exceptions import *

http_POST_OK    = 201
http_REQUEST_OK = 200
http_NOT_FOUND  = 404


def elmcafiolo_GetPostJob(request):

    #
    # Determinar si es un Get o un Post
    if request.method == 'GET':
        return elmcafiolo_GetJob(request)


    if request.method == 'POST':
        return elmcafiolo_PostJob(request)
	

def elmcafiolo_GetJob(request):

    response = []
    #
    # Para todos los trabajos:
    #   - Armar el json de respuesta
    for job in Job.objects.all():
        response.append({"job":
                            {"id": job.id, "name": job.name}
                        })

    #
    # La unica respuesta para esto es OK
    status = http_REQUEST_OK
    return HttpResponse(json.dumps(response), status=status, content_type='application/json')


def elmcafiolo_PostJob(request):
    jsonData = json.loads(request.body)

    try:
	preset = Preset.objects.get(name=jsonData['job']['preset'])
    except ObjectDoesNotExist:
        status = http_NOT_FOUND
        return HttpResponse(json.dumps({'message': 'Preset not found'}), status=status, content_type='application/json')

    job = Job()
    job.name               = jsonData['job']['name']
    job.input_filename     = jsonData['job']['input_filename']
    job.input_path         = jsonData['job']['input_path']
    job.basename           = jsonData['job']['basename']
    job.preset		   = preset
    job.priority           = jsonData['job']['priority']
    job.output_path        = jsonData['job']['output_path']
    job.status             = 'Q' # Queue

    job.save()

    response = {"job": {"id": job.id, "name": job.name}}
    #
    # La unica respuesta para esto es OK

    status = http_POST_OK
    return HttpResponse(json.dumps(response), status=status, content_type='application/json')


def elmcafiolo_GetJobId(request, id):
    #
    # Buscar el Job que se esta pidiendo
    try:
        job = Job.objects.get(id = id)
    except ObjectDoesNotExist:
        status = http_NOT_FOUND
        return HttpResponse(json.dumps({}), status=status, content_type='application/json')

    if job.transcoder is None:
	transcoder = ''
    else:
	transcoder = job.transcoder.name

    response = { "job" :
                        {
                            "id": job.id ,
                            "name": job.name    ,
                            "preset": job.preset.name,
                            "input_filename":job.input_filename ,
                            "input_path": job.input_path ,
			    "transcoder": transcoder,
                            "basename": job.basename,
                            "output_path": job.output_path,
                            "priority": job.priority ,
                            "status": job.status ,
                            "progress": job.progress ,
                            "message": job.message
                        }
                }

    status = http_REQUEST_OK
    return HttpResponse(json.dumps(response), status=status, content_type='application/json')



def elmcafiolo_GetJobIdOutputFile(request, id):
    #
    # Buscar el Job que se esta pidiendo
    try:
        job = Job.objects.get(id = id)
    except ObjectDoesNotExist:
        status = http_NOT_FOUND
        return HttpResponse(json.dumps({}), status=status, content_type='application/json')
    
    oflst = []
    if job.transcoder is not None:
	server = elm.elmServer(job.transcoder.ip, job.transcoder.port)
	jobElm = elm.elmJob(server, job.job_id)
    
    
	file_list = jobElm.files()

	for output_file in file_list:
    	    oflst.append({"path": output_file['path'], "filename": output_file['filename']})


    response = {"job":
                 {
                  "id": job.id,
                  "name": job.name,
                  "outputfile": oflst
                 }
               }

    status = http_REQUEST_OK
    return HttpResponse(json.dumps(response), status=status, content_type='application/json')








