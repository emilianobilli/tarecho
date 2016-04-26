#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Stand Alone Script
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
import os
import shutil
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tarecho.settings")
django.setup()


#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Base Exceptions
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
from django.core.exceptions import *

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# App Model
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
from elemento.models import HLSPreset
from elemento.models import H264Preset
from elemento.models import Config
from elemento.models import Job
from elemento.models import OutputFile

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# M3U8 Lite Library
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
from elemento.m3u8   import M3U8
from elemento.m3u8   import M3U8Error
from elemento.m3u8   import M3U8GetFiles

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# System
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
from daemon import Daemon
from sys    import exit
from sys    import argv
from subprocess import Popen
from subprocess import PIPE
from os   import waitpid
from os   import fork
from os   import getpid
from os   import wait
from os   import WNOHANG
from os   import path
from os   import mkdir
from os   import unlink

import time
import logging
import shlex

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Signals
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
from signal import signal
from signal import SIGCHLD
from signal import SIG_IGN


#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Basic Config 
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
LOG_FILE = './log/elemento.log'
ERR_FILE = './log/elemento.err'
PID_FILE = './pid/elemento.pid'
REPORT_DIR = './reports/'


class DispatchError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)


def _mkdir_recursive(p):
    sub_path = path.dirname(p)
    if not path.exists(sub_path):
        _mkdir_recursive(sub_path)
    if not path.exists(p):
        mkdir(p)



#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# workerDie(): Manejador de la signal SIGCHLD, comprueba que el hijo no haya muerto 
#              de manera inesperada y corrige el resultado de la transferencia
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
def workerDie(signaln, frame):
    pid, status = waitpid(-1, WNOHANG)
    while pid != 0:
	try:
	    # Busca cual es el hijo que termino
	    J = Job.objects.get(worker_pid=pid)
	    if J.status == 'P':
    		# Fallo inesperadamente
    		logging.error('WorkerDie(): Worker [Pid=%d] died with status [%d]' % (pid,status))
    	        logging.error('WorkerDie(): Job [%s] in error state' % J)
	        J.status = 'E'
    		J.message  = 'Worker died Unexpectedly'
    		J.save()
	    else:
    		logging.info('WorkerDie(): Worker [Pid=%d] end, Transco result = %s' % (pid,J.message))
	except:
	    # No lo encontro, es un hijo no reconocido
	    logging.error('WorkerDie(): Unregistred worker die [Pid=%d], status = %d ' % (pid, status))
	try:
	    pid, status = waitpid(-1, WNOHANG)
	except OSError as e:
	    #
	    # Si no tiene hijos tira un error
	    #
	    if e.errno == 10:
		break;




def getScheduleableJob(config):
    
    max_workers    = config.workers
    active_workers = len(Job.objects.filter(status='P'))

    jobs = []

    if max_workers - active_workers >= 1:
	jobs = Job.objects.filter(status='Q').order_by('-priority')

    if len(jobs) > 0:
	return jobs[0]

    return None



def forkWorker(job=None,config=None):

    if job is None or config is None:
	logging.error('ForkWorker(): Job can not be None')
	return False

    logging.info('ForkWorker(): Starting Worker for Job[%s]' % (job))


    if job.system_path is True:
	# En este caso el output_path es el system_path de la configuracion
	# mas el output_path del Job
	base = config.output_basepath
	path = job.output_path
    
	if base.endswith('/') and path.startswith('/'):
	    output_path = base + path[1:]
	elif not base.endswith('/') and not path.startswith('/'):
	    output_path = base + '/' + path
	else:
	    output_path = base + path
    else:
	output_path = job.output_path

    try:
        _mkdir_recursive(output_path)
    except OSError as e:
        logging.error('forkWorker(): Unable to create output_path: %s' % output_path)
        job.status  = 'E'
        job.message = 'forkWorker(): Unable to create output_path: %s' % output_path
        job.save()
        return False


    job.output_path = output_path
    job.status = 'P'
    job.save()

    try:
	Pid = fork()
    except OSError as e:
	logging.error('forkWorker(): Can not call fork() -> [%s]' % e.strerror)
	return False

    if Pid == 0:
	workerPid = getpid()
	job.worker_pid = workerPid
	job.save()

	#
	# Dispatch a worker
	
	jobWorker(config.ffmpeg_bin, config.temporal_path, job, config.report_loglevel, config.advanced_options)

	

    logging.info('ForkWorker(): Worker Pid -> [%d]' % Pid)
    return True


def jobWorker (ffmpeg, tmp_path, job, report_log_level, advanced_options):

    hls_preset  = job.hls_preset
    input_file  = job.input_filename
    input_path  = job.input_path
    basename    = job.basename
    output_path = job.output_path
    

    if not input_path.endswith('/'):
	input_path = input_path + '/'

    abs_filename = input_path + input_file
    if not path.isfile(abs_filename):
	job.status  = 'E'
	job.message = 'Input filename does not exist: %s' % abs_filename
	job.save()
	exit(0)
    #
    # Trae la lista completa de perfiles de transcodificacion
    if hls_preset is None:
	h264_preset_list = []
	h264_preset_list.append(job.h264_preset)
	m3u8_playlist = None
    else:    
        h264_preset_list = hls_preset.h264_presets.all()

	# 
	# Crea el root playlist
	m3u8_playlist = M3U8(hls_preset.playlist_root(basename))


    for h264_preset in h264_preset_list:
	try:
	    playlist = dispatchTranscode(ffmpeg, abs_filename, output_path, basename, tmp_path, hls_preset, h264_preset, report_log_level, advanced_options)
	except DispatchError as e:
	    job.status  = 'E'
	    job.message = e.value
	    job.save()
	    exit(0)

	if not output_path.endswith('/'):
	    output_path = output_path + '/'

	if not path.isfile(output_path+playlist):
	    job.status = 'E'
	    job.message = 'Playlist could not be found at: %s%s' % (output_path, playlist)
	    job.save()
	    exit(0)

	# TODO: Falta scanear y agregar los archivos    
	try:
	    if hls_preset is not None:
	        files = M3U8GetFiles(output_path+playlist)
	    else:
		files = []
	except M3U8Error as e:
	    job.status = 'E'
	    job.message = 'Error getting files from playlist [ %s%s ]: %s' % (output_path, playlist, e)
	    job.save()
	    exit(0)

	NewFile = OutputFile()
	NewFile.job  = job
	NewFile.path = output_path
	NewFile.filename = playlist
	NewFile.save()
    
	for f  in files:
	    NewFile = OutputFile()
	    NewFile.job      = job
	    NewFile.path = output_path
	    NewFile.filename = f
	    NewFile.save()
	#
	# Add Rendition to root Playlist
	if hls_preset is not None:
	    bit_rate = int(h264_preset.video_bitrate) + int(h264_preset.audio_bitrate)
	    m3u8_playlist.addRendition(h264_preset.profile, h264_preset.level, bit_rate, h264_preset.resolution, playlist)
	

    #
    # Graba el Root Playlist
    if hls_preset is not None:
        try:
	    m3u8_playlist.save(output_path)
	except M3U8Error as e:
	    job.status  = 'E'
	    job.message = str(e)
	    job.save()
	    exit(0)
	
    # TODO: Agregar el root playlist
        NewFile = OutputFile()
	NewFile.job  = job
	NewFile.path = output_path 
	NewFile.filename = hls_preset.playlist_root(basename)
	NewFile.save()

    job.status = 'D'
    job.save()

    exit(0)



def launchCommand (cmd, env):
    scmd = shlex.split(cmd)
    proc  = Popen(scmd, stderr=PIPE, env=env, shell=False)
    return proc.communicate()[1]


def dispatchTranscode (ffmpeg, input_file, dst_path, dst_basename, tmp_path, hls_preset, h264_preset, report_log_level, advanced_options):

    if not dst_path.endswith('/'):
	dst_path = dst_path + '/'
    if not tmp_path.endswith('/'):
	tmp_path = tmp_path + '/'

    logging.info('dispatchTranscode(): Input: %s' % input_file)
    logging.info('dispatchTranscode(): Path: %s'  % dst_path)
    logging.info('dispatchTranscode(): Basename: %s' % dst_basename) 
    if hls_preset is not None:
	logging.info('dispatchTranscode(): HLS Preset: %s' % hls_preset)
    logging.info('dispatchTranscode(): H264 Preset: %s' % h264_preset)
 

    #	Nombre de destino del file transcodificado
    destination_temporal_name = h264_preset.filename(dst_basename)

    #   Nombre del reporte que se genera para este archivo
    transcode_report_name = destination_temporal_name + '.log'

    #   Variable de entorno para que se genere el reoprete
    environ = { 'FFREPORT': 'file=%s%s:level=%s' % (REPORT_DIR, transcode_report_name, report_log_level)  }

    #   Si el file de entrada tiene espacios hay que agregar las comillas sino se genera un error al llamar al ffmpeg
    if ' ' in input_file:
	input_file = '"' + input_file + '"'

    #   Se arma la linea de comando para ejecutar
    if hls_preset is not None:
	ffmpeg_transcode_command_line = '%s %s -i %s %s %s' % (ffmpeg,
	    						       advanced_options,
					                       input_file,
					            	       hls_preset.ffmpeg_segmenter_options(),
					                       h264_preset.ffmpeg_params(tmp_path, dst_basename))
    else:
	ffmpeg_transcode_command_line = '%s %s -i %s %s' % (ffmpeg,
	    						    advanced_options,
					                    input_file,
					            	    h264_preset.ffmpeg_params(tmp_path, dst_basename))

    
    #   Construye el log
    logging.info('dispatchTranscode(): Command Line: %s' % ffmpeg_transcode_command_line)   

        
    stderr_return = launchCommand(ffmpeg_transcode_command_line, environ)
    if len(stderr_return) != 0:
	raise DispatchError('ffmpeg exit with non 0 return code, error: %s' % (stderr_return))


    #   Esto comprueba que se haya generado el archivo esperado
    if not path.isfile(tmp_path + destination_temporal_name):
	raise DispatchError('Unable to found temporal filename: %s, check Report: %s for more information' % (tmp_path + destination_temporal_name,
													      transco_report_name))

    logging.info('dispatchTranscode(): Temporal file: %s generated succefully' % tmp_path + destination_temporal_name)
    


    if hls_preset is not None:
        #   Nombre de destino del playlist
	destination_playlist_name = hls_preset.playlist_filename(h264_preset, dst_basename)

	segment_report_name = destination_playlist_name + '.log'

	environ = { 'FFREPORT': 'file=%s%s:level=%s' % (REPORT_DIR, segment_report_name, report_log_level) }

	ffmpeg_segmenter_command_line = '%s %s -i %s %s' % (ffmpeg,
	 						    advanced_options,
						    	    tmp_path + destination_temporal_name,
						    	    hls_preset.ffmpeg_params(dst_path, dst_basename, h264_preset))


        logging.info('dispatchTranscode(): Command Line: %s' % ffmpeg_segmenter_command_line)  

	stderr_return = launchCommand(ffmpeg_segmenter_command_line, environ)
	if len(stderr_return) != 0:
	    raise DispatchError('ffmpeg exit with non 0 return code, error: %s' % (stderr_return))

    else:
	destination_playlist_name = dst_basename + '.' + h264_preset.format.extension
	shutil.copy (tmp_path + destination_temporal_name, dst_path + destination_playlist_name)

    #   Esto comprueba que se haya generado el archivo esperado
    if not path.isfile(dst_path + destination_playlist_name):
	raise DispatchError('Unable to found temporal filename: %s, check Report: %s for more information' % (isfile(dst_path + destination_playlist_name),
													      segment_report_name))

    try:
	unlink(tmp_path + destination_temporal_name)
	logging.info('dispatchTranscode(): Delete: %s' % tmp_path + destination_temporal_name )
    except:
	logging.error('dispatchTranscode(): Unable to detele: %s' % tmp_path + destination_temporal_name )

    return destination_playlist_name




def ElementoMain():
    
    # Registra el manejador de la senial SIGCHLD
    signal(SIGCHLD, workerDie)
    

    logging.basicConfig(format   = '%(asctime)s - elemento.py -[%(levelname)s]: %(message)s', 
			filename = LOG_FILE,
			level    = logging.INFO)    


    try:
	config = Config.objects.get(enable=True)
    except MultipleObjectsReturned:
	logging.error("ElementoMain(): Multiple Enabled Configuration Found")
	exit(-1)
    except ObjectDoesNotExist:
	logging.error("ElementoMain(): No One Enabled Configuration Found")
	exit(-1)

    if not path.isdir(config.temporal_path):
	logging.error("ElementoMain(): Temporal Path not Found")
	exit(-1)

    tmp_path    = config.temporal_path
    
    if not path.isdir(config.output_basepath):
	logging.error("ElementoMain(): Output Path not Found")

    output_path = config.output_basepath

    if not path.isfile(config.ffmpeg_bin):
	logging.error("ElementoMain(): ffmpeg at path: %s not found" % config.ffmpeg_bin)
	exit(-1)


    while True:

	#
	# getScheduleableJob(): Trae un trabajo de transcodificacion en status Queue siempre 
	# 			y cuando tenga capacidad de workers disponibles
	job = getScheduleableJob(config) 

	while job is not None:
	    forkWorker(job, config)
	    
	    job = getScheduleableJob(config) 

	time.sleep(30)
  


class DaemonMain(Daemon):
    def run(self):
        try:
            ElementoMain()
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
