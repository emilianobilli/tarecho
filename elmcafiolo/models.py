from __future__ import unicode_literals

from django.db import models

# Create your models here.


class Transcoder(models.Model):
    name            = models.CharField(max_length=50, unique=True, help_text="Name of the Transcoder")
    ip              = models.CharField(max_length=15, help_text="IP of the Transcoder")
    port            = models.IntegerField(help_text="Port of the Transcoder")
    slots           = models.IntegerField(blank=True, null=True, help_text="Availables slots")
    message         = models.CharField(max_length=510, blank=True,  help_text="Error or Warning message")
    preset_master   = models.BooleanField()
    enabled         = models.BooleanField()
    
    def __unicode__(self):
        return self.name


class Preset(models.Model):
    name        = models.CharField(max_length=50, unique=True, help_text="Name of the Preset")
    transcoder  = models.ManyToManyField(Transcoder)

    def __unicode__(self):
        return self.name


class Job(models.Model):
    STATUS = (
                ('U', 'Unassigned'),
                ('Q', 'Queued'),
                ('P', 'Processing'),
                ('D', 'Done'),
                ('E', 'Error')
    )
    name            = models.CharField(max_length=50, help_text="Name of the Job")
    input_filename  = models.CharField(max_length=255, help_text="Input File")
    input_path      = models.CharField(max_length=255, help_text="Input Path")
    basename        = models.CharField(max_length=100, help_text="Destination Basename")
    output_path     = models.CharField(max_length=255, help_text="Destination Path")
    preset          = models.ForeignKey(Preset)
    priority        = models.CharField(max_length=1, default='5', help_text="0: Max priority, 9: Min Priority")
    job_id          = models.IntegerField(blank=True, null=True, help_text="Transcoder job ID")
    transcoder      = models.ForeignKey(Transcoder, blank=True, null=True)
    status          = models.CharField(max_length=1, choices=STATUS, default='U', help_text="Job Status")
    progress        = models.IntegerField(default=0, help_text="Job Progress")
    speed           = models.CharField(max_length=10, blank=True)
    message         = models.CharField(max_length=510, blank=True,  help_text="Error or Warning message")

    def __unicode__(self):
        return self.name
