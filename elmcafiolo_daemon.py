import django
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tarecho.settings")
django.setup()

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Elemento
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
from elm import *

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# App Model
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
from elmcafiolo.models import Preset
from elmcafiolo.models import Transcoder
from elmcafiolo.models import Job

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# System
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
from daemon import Daemon
from sys    import exit
from sys    import argv

import logging
import time

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Basic Config
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
LOG_FILE = './log/elmcafiolo.log'
ERR_FILE = './log/elmcafiolo.err'
PID_FILE = './pid/elmcafiolo.pid'




def initTranscoders():
    enabledList = Transcoder.objects.filter(enabled = True)
    for trans in enabledList:
	try:
	    elm = elmServer(trans.ip, trans.port)
	    trans.slots = elm.workers()
	    trans.save()
	except elmError as e:
	    trans.enabled = False
	    trans.message = e
	    trans.save()
	    logging.error('elmServer(): Error %s' % e)


def getTranscodersSlots():
    enabledList = Transcoder.objects.filter(enabled = True)
    slots = 0
    for trans in enabledList:
	slots = slots + trans.slots
    return slots 


def getBestTranscoder():
    enabledList = Transcoder.objects.filter(enabled = True)
    bestTrans = None
    bestTransFreeSlots = 0
    for trans in enabledList:
	activeJobs = len(Job.objects.filter(transcoder = trans, status ='P'))
	freeSlots = trans.slots - activeJobs
	if freeSlots > bestTransFreeSlots:
	    bestTransFreeSlots = freeSlots
	    bestTrans = trans
    return bestTranscoder



def getScheduleableJob():
    max_slots = getTranscodersSlots()
    used_slots = len(Job.objects.filter(status = 'P'))

    jobs = []    

    if max_slots - used_slots > 0:
	jobs = Job.objects.filter(status='Q').order_by('-priority')

    if len(jobs) > 0:
	return jobs[0]



def startJob(job, transcoder):
    try:
	elm = elmServer(transcoder.ip, transcoder.port)
	presetId, presetType = elm.preset(job.preset.name)
    except elmError as e:
	transcoder.enable   = False
	transcoder.message  = e
	transcoder.save()
	# agregar logueo
	return None

    if presetId is None:
	job.status = 'E'
	job.message = 'Preset ID not found'
	job.save()
	return None
    if presetType is None:
	job.status = 'E'
	job.message = 'Preset type not found'
	job.save()
	return None

    jobElm = elmJob(elm)
    jobElm.name               = job.name
    jobElm.input_filename     = job.input_filename
    if presetType == 'hls':
        jobElm.hls_preset_id  = presetId
    if presetType == 'h264':
	jobElm.h264_preset_id = presetId
    jobElm.input_path         = job.input_path
    jobElm.basename           = job.basename
    jobElm.system_path        = False
    jobElm.output_path        = job.output_path

    try:
	job.job_id = jobElm.start()
	job.transcoder = transcoder
	job.status = 'P'
	job.save()
    except elmError as e:
	# agregar logueo
	transcoder.enabled = False
	transcoder.save()
	return None

    return job.job_id
    
	

def updateJobStatus(job):
    try:
	elm = elmServer(job.transcoder.ip, job.transcoder.port)
    except elmError as e:
	# loguear error
	pass
    
    jobElm = elmJob(elm, job.job_id)
    jobStatus = jobElm.status()
    if jobStatus == 'D' or jobStatus == 'E': 
	job.status  = jobStatus
	job.message = jobElm.message()
	job.save()



def elmCafioloMain():

    logging.basicConfig(format   = '%(asctime)s - elemento.py -[%(levelname)s]: %(message)s',
                        filename = LOG_FILE,
                        level    = logging.INFO)

    initTranscoders()
    
    while True:
	
	job = getScheduleableJob()
	
	while job is not None:
    	
	    transcoder = getBestTranscoder()

	    if transcoder is not None:
		startJob(job, transcoder)
	    else:
		break
	    job = getScheduleableJob()

	job_list = Job.objects.filter(status = 'P')

	for job in job_list:
	    updateJobStatus(job)

	time.sleep(60)



class DaemonMain(Daemon):
    def run(self):
        try:
            elmCafioloMain()
        except KeyboardInterrupt:
            exit()

if __name__ == "__main__":
    daemon = DaemonMain(PID_FILE, stdout=LOG_FILE, stderr=ERR_FILE)
    if len(argv) == 2:
        if 'start'     == argv[1]:
            daemon.start()
        elif 'stop'    == argv[1]:
            daemon.stop()
        elif 'restart' == argv[1]:
            daemon.restart()
        elif 'run'     == argv[1]:
            daemon.run()
        elif 'status'  == argv[1]:
            daemon.status()
        else:
            print "Unknown command"
            exit(2)
        exit(0)
    else:
        print "usage: %s start|stop|restart|run" % argv[0]
        exit(2)

    




