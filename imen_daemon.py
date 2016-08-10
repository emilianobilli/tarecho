import django
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tarecho.settings")
django.setup()

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Imen
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
from imen_api import *

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# App Model
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
from imen.models import ThumbPreset
from imen.models import Config
from imen.models import Job

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# System
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
from daemon import Daemon
from sys    import exit
from sys    import argv

import logging
import time

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# ThumbMaker
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
from thumbmaker import ImageTask
from thumbmaker import runImageTask

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Basic Config
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
LOG_FILE = './log/imen.log'
ERR_FILE = './log/imen.err'
PID_FILE = './pid/imen.pid'


def presetsChecker():
    presets = ThumbPreset.objects.filter(enable = True)
    w = 0
    h = 0
    ar = 0
    for preset in presets:
        if preset.width != '':
            w = 1
        if preset.height != '':
            h = 1
        if preset.aspect_ratio != '':
            ar = 1
        sum = w + h + ar
        if sum < 2:
            preset.enable = False
            preset.save()


def getScheduleableJob():
    jobs = Job.objects.filter(status='Q').order_by('-priority')

    presetsChecker()

    for job in jobs:
        if job.thumb_preset.enable:
            return job


def startJob(job, config):
    task = ImageTask()
    task.input_path = job.input_path
    task.input_filename = job.input_filename
    task.outdir = job.output_path
    task.basename = job.basename
    task.rate = job.thumb_preset.rate
    task.width = job.thumb_preset.width
    task.height = job.thumb_preset.height
    task.aspect_ratio = job.thumb_preset.aspect_ratio
    task.sp_flag = job.thumb_preset.sprite
    task.sp_quality = job.thumb_preset.sp_quality
    ffmpeg = config.ffmpeg_bin
    log_path = LOG_FILE

    job.status = 'P'
    job.save()
    try:
        runImageTask(task, ffmpeg, log_path)
        job.status = 'D'
        job.save()
    except:
        job.status = 'E'
        job.message = 'runImageTask error. Check log file.'
        job.save()



def imenMain():

    logging.basicConfig(format   = '%(asctime)s - imen_daemon.py -[%(levelname)s]: %(message)s',
                        filename = LOG_FILE,
                        level    = logging.INFO)

    try:
        config = Config.objects.get(enable=True)
    except MultipleObjectsReturned:
        logging.error("imenMain(): Multiple Enabled Configuration Found")
        exit(-1)
    except ObjectDoesNotExist:
        logging.error("imenMain(): No One Enabled Configuration Found")
        exit(-1)

    if not os.path.isfile(config.ffmpeg_bin):
        logging.error("imenMain(): ffmpeg at path: %s not found" % config.ffmpeg_bin)
        exit(-1)

    while True:

        job = getScheduleableJob()

        while job is not None:
            startJob(job, config)
            job = getScheduleableJob()

        time.sleep(30)



class DaemonMain(Daemon):
    def run(self):
        try:
            imenMain()
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