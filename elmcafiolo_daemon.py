from django.db.models import Q
import django
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tarecho.settings")
django.setup()

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Elemento
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
from elm import *

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Imen
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
from imen_api import *

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

ELEMENTO_TYPE = 'ELO'
IMEN_TYPE = 'IME'



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


#def getTranscodersSlots():
#    enabledList = Transcoder.objects.filter(enabled = True)
#    slots = 0
#    for trans in enabledList:
#        slots = slots + trans.slots
#    return slots


def getBestTranscoder(preset):
    presetTrans = preset.transcoder.all()
    enabledList = Transcoder.objects.filter(enabled = True)
    transList = []

    for trans in enabledList:
        if trans in presetTrans:
            transList.append(trans)

    bestTrans = None
    bestTransFreeSlots = 0
    type = preset.type


    for trans in transList:
        activeJobs = len(Job.objects.filter(transcoder = trans).filter(Q(status = 'Q') | Q(status = 'P')).filter(type = type))
        freeSlots = trans.slots - activeJobs
        if freeSlots > bestTransFreeSlots:
            bestTransFreeSlots = freeSlots
            bestTrans = trans

    return bestTrans



def getScheduleableJob():
    #max_slots = getTranscodersSlots()
    #used_slots = len(Job.objects.filter(Q(status = 'Q') | Q(status = 'P')))

    #jobs = []

    jobs = Job.objects.filter(status='U').order_by('-priority')
    for job in jobs:
        transcoder = getBestTranscoder(job.preset)
        if transcoder is not None:
            job.transcoder = transcoder
            job.type = job.preset.type
            job.save()
            return job


    #if max_slots - used_slots > 0:
    #   jobs = Job.objects.filter(status='U').order_by('-priority')

    #if len(jobs) > 0:
    #   return jobs[0]



def startElmJob(job):
    transcoder = job.transcoder
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
        job.status = 'Q'
        job.save()
    except elmError as e:
        job.message = 'Could not send job to transcoder ' + transcoder
        transcoder.enabled = False
        transcoder.save()
        return None

    return job.job_id
    
def startImenJob(job):
    transcoder = job.transcoder
    try:
        imen = imenServer(transcoder.ip, transcoder.port)
    except imenError as e:
        transcoder.enable   = False
        transcoder.message  = e
        transcoder.save()
        # agregar logueo
        return None

    jobImen = imenJob(imen)
    jobImen.input_filename      = job.input_filename
    jobImen.thumb_preset        = job.preset.name
    jobImen.input_path           = job.input_path
    jobImen.basename             = job.basename
    jobImen.output_path          = job.output_path

    try:
        job.job_id = jobImen.start()
        job.status = 'Q'
        job.save()
    except imenError as e:
        job.message = 'Could not send job to transcoder ' + transcoder
        transcoder.enabled = False
        transcoder.save()
        return None

    return job.job_id


def updateElmJobStatus(job):
    try:
        elm = elmServer(job.transcoder.ip, job.transcoder.port)
    except elmError as e:
        job.status = 'E'
        job.message = 'Transcoder ' + transcoder + 'unavailable'
        job.save()
        transcoder.enabled = False
        transcoder.save()
    
    jobElm = elmJob(elm, job.job_id)
    jobStatus = jobElm.status()
    job.status  = jobStatus
    job.message = jobElm.message()
    job.save()


def updateImenJobStatus(job):
    try:
        imen = imenServer(job.transcoder.ip, job.transcoder.port)
    except elmError as e:
        job.status = 'E'
        job.message = 'Transcoder ' + transcoder + 'unavailable'
        job.save()
        transcoder.enabled = False
        transcoder.save()

    jobImen = imenJob(imen, job.job_id)
    jobStatus = jobImen.status()
    job.status = jobStatus
    job.message = jobImen.message()
    job.save()

def elmCafioloMain():

    logging.basicConfig(format   = '%(asctime)s - elemento.py -[%(levelname)s]: %(message)s',
                        filename = LOG_FILE,
                        level    = logging.INFO)

    initTranscoders()
    
    while True:

        job = getScheduleableJob()

        while job is not None:

            if job.type == ELEMENTO_TYPE:
                startElmJob(job)
            elif job.type == IMEN_TYPE:
                startImenJob(job)
            else:
                job.status = 'E'
                job.message = "Unrecognized job type: " + str(job.type)
                job.save()

            job = getScheduleableJob()

        job_list = Job.objects.filter(Q(status = 'Q') | Q(status = 'P'))
        for job in job_list:
            if job.type == ELEMENTO_TYPE:
                updateElmJobStatus(job)
            elif job.type == IMEN_TYPE:
                updateImenJobStatus(job)

        time.sleep(30)



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

    




