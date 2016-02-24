from __future__ import unicode_literals

from django.db import models

from datetime import datetime



# Create your models here.

class Format(models.Model):
    name	     = models.CharField(max_length=50, help_text="Name of the format")
    extension	     = models.CharField(max_length=5, help_text="Extension of the result file")

    def __unicode__(self):
	return self.name

class Config(models.Model):
    enable	      = models.BooleanField()
    date	      = models.DateField(auto_now=False, auto_now_add=True)
    YES_NO = (
	('Y', 'Yes'),
	('N', 'No')
    )
    LOG_LEVEL = (
	('0', 'panic'),
        ('8', 'fatal'),
	('16', 'error'),
	('24', 'warning'),
	('32', 'info'),
	('40', 'verbose'),
	('48', 'debug')
    )
    workers	      = models.IntegerField(default=2, help_text="Max number of simultaneous Workers")
    temporal_path     = models.CharField(max_length=255, help_text="Path to temporal destination Files")
    output_basepath   = models.CharField(max_length=255, help_text="Output Basepath")
    delete_on_success = models.CharField(max_length=1, choices=YES_NO, help_text="Automatic delete after transcode -- Not Available YET")
    report_loglevel   = models.CharField(max_length=2, choices=LOG_LEVEL, help_text="ffmpeg log level")
    ffmpeg_bin	      = models.CharField(max_length=255, help_text="ffmpeg executable")
    advanced_options  = models.CharField(max_length=255, default='-loglevel error -y', help_text="Advanced ffmpeg options for particular implementations")

    def __unicode__(self):
	return str(self.date)
	
class H264Preset(models.Model):
    H264 = (
	('libx264', 'libx264'),
    )
    AAC  = (
	('libfdk_aac', 'libfdk_aac'),
    )
    PROFILES = (
	('baseline','baseline'),
	('main','main'),
	('high','high'),
	('high10','high10'),
	('high422','high422'),
	('high444','high444'),
    )
    LEVELS = (
	('3.0','3.0'),
	('3.1','3.1'),
	('4.0','4.0'),
	('4.1','4.1'),
	('4.2','4.2'),
    )
    PIX_FMT = (
       ('yuv420p', 'yuv420p'),
       ('yuv422p', 'yuv422p'),
    )

    name		= models.CharField(max_length=50, help_text="Name of the Preset")
    format		= models.ForeignKey(Format)
    suffix		= models.CharField(max_length=50, help_text="Text between basename and extension")
    video_codec		= models.CharField(max_length=20, choices=H264,  help_text="Video Library")
    pixel_format        = models.CharField(max_length=20, choices=PIX_FMT,default='yuv420p',  help_text="Pixel Format")
    resolution		= models.CharField(max_length=20, help_text="Video Resolution: WxH")
    framerate		= models.CharField(max_length=5,  help_text="Video Frame Rate")
    video_bitrate	= models.CharField(max_length=50, help_text="Video Bit Rate expressed in Kbps")
    buffer_size		= models.CharField(max_length=50, help_text="Video Buffer Size expressed in Kbps")
    gop_size		= models.CharField(max_length=50, help_text="GOP Size")
    reference_frames	= models.CharField(max_length=50, help_text="Number of Referense Frames")
    crf			= models.CharField(max_length=2, default='18' ,help_text="Constant Rate Factor: 0 Better, 50 worst")
    profile		= models.CharField(max_length=20, choices=PROFILES, help_text="H264 Profiles")
    level		= models.CharField(max_length=20, choices=LEVELS, help_text="H264 Levels")
    audio_codec		= models.CharField(max_length=20, choices=AAC, help_text="Audio Library")
    audio_bitrate	= models.CharField(max_length=20, help_text="Audio Bit Rate expressed in Kbps")
    
    def __unicode__(self):
	return self.name

    def ffmpeg_audio(self):
	return '-c:a %s -b:a %sk' % (self.audio_codec, 
				     self.audio_bitrate)


    def ffmpeg_video (self):
        return  '-s %s -c:v %s -pix_fmt %s -crf %s -g %s -refs %s -b:v %sk -minrate %sk -maxrate %sk -bufsize %sk -profile:v %s -level %s -r %s' % (self.resolution,
                                                                                                                                                    self.video_codec,
                                                                                                                                                    self.pixel_format,
                                                                                                                                                    self.crf,
                                                                                                                                                    self.gop_size,
                                                                                                                                                    self.reference_frames,
                                                                                                                                                    self.video_bitrate,
                                                                                                                                                    self.video_bitrate,
                                                                                                                                                    self.video_bitrate,
                                                                                                                                                    self.buffer_size,
                                                                                                                                                    self.profile,
                                                                                                                                                    self.level,
                                                                                                                                                    self.framerate)

    def ffmpeg_format(self):
	return '-f %s' % (self.format.name)


    def filename(self, output_basename):
	return '%s_%s.%s' % (output_basename,
			     self.suffix,
			     self.format.extension)

    def filename_base(self, output_basename):
	return '%s_%s' % (output_basename,
			  self.suffix)


    def ffmpeg_params(self, dstpath, output_basename):
	if not dstpath.endswith('/'):
	    dstpath = dstpath + '/'
	return '%s %s %s %s%s' % (self.ffmpeg_audio(),
			        self.ffmpeg_video(),
			        self.ffmpeg_format(),
				dstpath,
				self.filename(output_basename))

    



class HLSPreset(models.Model):
    name	 = models.CharField(max_length=50, help_text="Name of the Preset")
    segment_time = models.CharField(max_length=6, help_text="Segment time expressed in seconds")
    extension	 = models.CharField(max_length=5, default='m3u8', help_text="Playlist Extension")
    h264_presets = models.ManyToManyField(H264Preset)


    def __unicode__(self):
	return self.name

    def ffmpeg_segmenter_options(self):
	return '-force_key_frames "expr:gte(t,n_forced*%s)"' % (self.segment_time)

    def playlist_root(self, basename):
	return '%s.%s' % (basename,
			  self.extension)

    def playlist_filename(self, preset, basename):
	return '%s_%s.%s' % (basename,
			     preset.suffix,
			     self.extension)

    def video_filename(self, preset, basename):
	return '%s_%s_%s%s.%s' % (basename,
				  preset.suffix,
				  '%',
				  'd',
				  preset.format.extension)

    def ffmpeg_params(self, dstpath, basename, preset):
	if not dstpath.endswith('/'):
	    dstpath = dstpath + '/'
	return '-codec copy -map 0 -f segment -segment_time %s -segment_format %s -segment_list %s%s -segment_list_type %s %s%s' % (self.segment_time,
																    preset.format.name,
																    dstpath,
																    self.playlist_filename(preset,basename),
																    self.extension,
																    dstpath,
																    self.video_filename(preset, basename))



class Job(models.Model):
    STATUS = (
	('Q', 'Queued'),
	('P', 'Processing'),
	('D', 'Done'),
	('E', 'Error')
    )
    name	      = models.CharField(max_length=50, help_text="Name of the Job")
#    creation_time     = models.DateTimeField(auto_now=True)
#    start_time	      = models.DateTimeField(blank=True)
#    end_time          = models.DateTimeField(blank=True)
    worker_pid	      = models.IntegerField(default=-1)	
    hls_preset	      = models.ForeignKey(HLSPreset)
    input_filename    = models.CharField(max_length=255, help_text="Input File")
    input_path	      = models.CharField(max_length=255, help_text="Input Path")
    basename	      = models.CharField(max_length=100, help_text="Destination Basename")
    system_path       = models.BooleanField(help_text="If this option is checked, the output path is relative and the root is the value output_basepath setted in config")
    output_path	      = models.CharField(max_length=255, help_text="Destination Path")
    priority	      = models.CharField(max_length=1, default='9', help_text="0: Max priority, 9 Min Priority")
    status	      = models.CharField(max_length=1, choices=STATUS, default='D', help_text="Job Status")
    progress	      = models.IntegerField(default=0, help_text="Job Progress")
    message	      = models.CharField(max_length=510, blank=True,  help_text="Error or Warning message")
    
    def __unicode__(self):
	return '%d:%s' % (self.id, self.name)

class OutputFile(models.Model):
    job	     = models.ForeignKey(Job)
    path     = models.CharField(max_length=255)
    filename = models.CharField(max_length=255)

    def __unicode__(self):
	return self.filename



