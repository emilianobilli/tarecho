#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Stand Alone Script
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
import os
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

from elemento.M3U8   import M3U8
from elemento.M3U8   import M3U8Error

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# System
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
from daemon import Daemon
from sys    import exit
from sys    import argv
from subprocess import check_call
from subprocess import CalledProcessError
import logging
import os



#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Basic Config 
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
LOG_FILE = './log/elemento.log'
ERR_FILE = './log/elemento.err'
PID_FILE = './pid/elemento.pid'


def jobWorker (ffmpeg, tmp_path, job):

    hls_preset  = job.hls_preset
    input_file  = job.input_filename
    input_path  = job.input_path
    basename    = job.basename
    output_path = job.output_path
    

    if not input_path.endswith('/'):
	input_path = input_path + '/'

    abs_filename = input_path + input_file
    if not os.path.isfile(abs_filename):
	job.status  = 'E'
	job.message = 'Input filename does not exist: %s' % abs_filename
	exit(0)
    #
    # Trae la lista completa de perfiles de transcodificacion
    h264_preset_list = hls_preset.h264_presets.all()

    # 
    # Crea el root playlist
    m3u8_playlist = M3U8(hls_preset.playlist_root(basename))


    for h264_preset in h264_preset_list:
	try:
	    playlist = dispatchTranscode(ffmpeg, abs_filename, output_path, basename, tmp_path, hls_preset, h264_preset)
	except DispatchError as e:
	    job.status  = 'E'
	    job.message = str(e)
	    exit(0)




def dispatchTranscode (ffmpeg, input_file, dst_path, dst_basename, tmp_path, hls_preset, h264_preset):

    if not dst_path.endswith('/'):
	dst_path = dst_path + '/'
    if not tmp_path.endswith('/'):
	tmp_path = tmp_path + '/'

    logging.info('dispatchTranscode(): Input: %s' % input_file)
    logging.info('dispatchTranscode(): Path: %s'  % dst_path)
    logging.info('dispatchTranscode(): Basename: %s' % dst_basename) 
    logging.info('dispatchTranscode(): HLS Preset: %s' % hls_preset)
    logging.info('dispatchTranscode(): H264 Preset: %s' % h264_preset)
 
    ffmpeg_transcode_command_line = '%s -i %s %s %s' % (ffmpeg,
					                input_file,
					                hls_preset.ffmpeg_segmenter_options(),
					                h264_preset.ffmpeg_params(tmp_path, dst_basename))

    logging.info('dispatchTranscode(): Command Line: %s' % ffmpeg_transcode_command_line)   

    #	Nombre de destino del file transcodificado
    destination_temporal_name = h264_preset.filename(dst_basename)

    #   Nombre de destino del playlist
    destination_playlist_name = hls_preset.playlist_filename(h264_preset, dst_basename)


    ffmpeg_segmenter_command_line = '%s -i %s %s' % (ffmpeg,
						     tmp_path + destination_temporal_name,
						     hls_preset.ffmpeg_params(dst_path, dst_basename, h264_preset))

    print ffmpeg_transcode_command_line
    print ffmpeg_segmenter_command_line




def ElementoMain():
    
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

    if not os.path.isdir(config.temporal_path):
	logging.error("ElementoMain(): Temporal Path not Found")
	exit(-1)

    tmp_path = config.temporal_path

    if not os.path.isfile(config.ffmpeg_bin):
	logging.error("ElementoMain(): ffmpeg at path: %s not found" % config.ffmpeg_bin)
	exit(-1)


   
    ffmpeg_bin = config.ffmpeg_bin

    x = HLSPreset.objects.all()
    for a in x:
	for preset in a.h264_presets.all():
	    dispatchTranscode('ffmpeg', 'flenson', '/home', 'ftrasn', 'tmp', a, preset)	

#    print '%s %s' % (a.ffmpeg_segmenter_options(), preset.ffmpeg_params('/home/', 'putito'))
#	print a.ffmpeg_params('/home/', 'putito', preset)




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