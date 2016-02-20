from django.shortcuts import render
from django.http import HttpResponse
import json

# Create your views here.

from models import Job
from models import OutputFile

from django.core.exceptions import *

http_REQUEST_OK = 200
http_NOT_FOUND  = 404


def view_GetPostJob(request):

    #
    # Determinar si es un Get o un Post
    if request.method == 'GET':
	return view_GetJob(request)


    if request.method == 'POST':
	return view_PostJob(request)


def view_GetJob(request):

    response = []
    #
    # Para todos los trabajos:
    # 	- Armar el json de respuesta
    for job in Job.objects.all():
	response.append({"job": 
			    {"id": job.id, "name": job.name}
			})

    #
    # La unica respuesta para esto es OK
    status = http_REQUEST_OK
    return HttpResponse(json.dumps(response), status=status, content_type='application/json') 


def view_PostJob(request):

    pass


def view_GetJobId (request, id):

    #
    # Buscar el Job que se esta pidiendo
    try:
	job = Job.objects.get(id = id)
    except ObjectDoesNotExist:
	status = http_NOT_FOUND
	return HttpResponse(json.dumps({}), status=status, content_type='application/json')

    
    response = { "job" :
			{ 
			    "id": job.id ,
			    "name": job.name	,
			    "worker_pid": job.worker_pid,
			    "hls_preset_id": job.hls_preset.id,
			    "input_filename":job.input_filename ,
			    "input_path": job.input_path ,
			    "basename": job.basename,
			    "system_path": job.system_path,
			    "output_path": job.output_path,
			    "priority": job.priority ,
			    "status": job.status ,
			    "progress": job.progress ,
			    "message": job.message 
			}
		}

    status = http_REQUEST_OK
    return HttpResponse(json.dumps(response), status=status, content_type='application/json')
    

def view_GetJobIdOutputFile(request, id):
    #
    # Buscar el Job que se esta pidiendo
    try:
	job = Job.objects.get(id = id)
    except ObjectDoesNotExist:
	status = http_NOT_FOUND
	return HttResponse(json.dumps({}), status=status, content_type='application/json')

    oflst = []
    for output_file in OutputFile.objects.filter(job=job):
	oflst.append({"path": output_file.path, "filename": output_path.filename})

	
    response = {"job":
	         {
		  "id": job.id,
	          "name": job.name,
		  "outputfile": oflst
		 }
    	       }

    status = http_REQUEST_OK
    return HttpResponse(json.dumps(response), status=status, content_type='application/json')
