from django.shortcuts import render
from django.http import HttpResponse
import json

# Create your views here.

from models import Job
from models import OutputFile
from models import Config
from models import HLSPreset
from models import H264Preset
from models import Format

from django.core.exceptions import *

http_POST_OK    = 201
http_REQUEST_OK = 200
http_NOT_FOUND  = 404

def elemento_GetPostJob(request):

    #
    # Determinar si es un Get o un Post
    if request.method == 'GET':
	return elemento_GetJob(request)


    if request.method == 'POST':
	return elemento_PostJob(request)


def elemento_GetJob(request):

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


def elemento_PostJob(request):

    jsonData = json.loads(request.body)

    job = Job()
    job.input_filename     = jsonData['job']['input_filename']
    job.input_path         = jsonData['job']['input_path']
    job.name               = jsonData['job']['name']
    job.basename           = jsonData['job']['basename']
    if 'hls_preset_id' in jsonData['job']:
        job.hls_preset_id      = jsonData['job']['hls_preset_id']
    if 'h264_preset_id' in jsonData['job']:
	job.h264_preset_id = jsonData['job']['h264_preset_id']
    job.priority           = jsonData['job']['priority']
    job.output_path        = jsonData['job']['output_path']
    job.system_path        = jsonData['job']['system_path']
    job.status		   = 'Q' # Queue

    job.save()

    response = {"job": {"id": job.id, "name": job.name}}
    #
    # La unica respuesta para esto es OK

    status = http_POST_OK
    return HttpResponse(json.dumps(response), status=status, content_type='application/json') 



def elemento_GetJobId (request, id):

    #
    # Buscar el Job que se esta pidiendo
    try:
	job = Job.objects.get(id = id)
    except ObjectDoesNotExist:
	status = http_NOT_FOUND
	return HttpResponse(json.dumps({}), status=status, content_type='application/json')

    if job.hls_preset is not None:
	hls_preset_id = job.hls_preset.id
    else:
	hls_preset_id = ''

    if job.h264_preset is not None:
	h264_preset_id = job.h264_preset.id
    else:
	h264_preset_id = ''
   

    response = { "job" :
			{ 
			    "id": job.id ,
			    "name": job.name	,
			    "worker_pid": job.worker_pid,
			    "hls_preset_id": hls_preset_id,
			    "h264_preset_id": h264_preset_id,
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


def elemento_GetPresetName(request, name):
    try:
	preset = HLSPreset.objects.get(name=name)
	response = { "preset" : { "id": preset.id, "type": "hls" } }
    except:
	try:
	    preset = H264Preset.objects.get(name=name)
	    response = { "preset" : { "id": preset.id, "type": "h264" } }
	except:
	    status = http_NOT_FOUND
	    return HttpResponse(json.dumps({}), status=status, content_type='application/json')
    

    status = http_REQUEST_OK
    return HttpResponse(json.dumps(response), status=status, content_type='application/json')


def elemento_GetJobIdOutputFile(request, id):
    #
    # Buscar el Job que se esta pidiendo
    try:
	job = Job.objects.get(id = id)
    except ObjectDoesNotExist:
	status = http_NOT_FOUND
	return HttpResponse(json.dumps({}), status=status, content_type='application/json')

    oflst = []
    for output_file in OutputFile.objects.filter(job=job):
	oflst.append({"path": output_file.path, "filename": output_file.filename})

	
    response = {"job":
	         {
		  "id": job.id,
	          "name": job.name,
		  "outputfile": oflst
		 }
    	       }

    status = http_REQUEST_OK
    return HttpResponse(json.dumps(response), status=status, content_type='application/json')

def elemento_GetFormats(request):
        
    flst = []
    formats = Format.objects.all()
    for f in formats:
	flst.append({"name": f.name, "parameters": f.parameters, "extension": f.extension})
    
    status = http_REQUEST_OK
    return HttpResponse(json.dumps({"formats": flst}), status=status, content_type='application/json')



def elemento_GetConfig(request):
    if request.method == 'GET':
	try:
	    config = Config.objects.get(enable = True)
	except ObjectDoesNotExist:
	    status = http_NOT_FOUND
	    return HttpResponse(json.dumps({}), status=status, content_type='application/json')
	
	response = {"config":
		     {
		      "workers": config.workers,
		      "temporal_path": config.temporal_path,
		      "output_basepath": config.output_basepath,
                      "delete_on_success": config.delete_on_success,
		      "report_loglevel": config.report_loglevel,
                      "ffmpeg_bin": config.ffmpeg_bin,
                      "advanced_options": config.advanced_options
		     }
		   }
	status = http_REQUEST_OK
	return HttpResponse(json.dumps(response), status=status, content_type='application/json')