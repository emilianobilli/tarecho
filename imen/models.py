from __future__ import unicode_literals

from django.db import models

# Create your models here.

class Config(models.Model):
    enable          = models.BooleanField()
    date            = models.DateField(auto_now=False, auto_now_add=True)
    ffmpeg_bin      = models.CharField(max_length=255, help_text="ffmpeg executable")


class ThumbPreset(models.Model):
    name                = models.CharField(max_length=50, help_text="Name of the Preset")
    rate                = models.IntegerField(default=5, help_text="Interval between thunmbnail in seconds")
    extension           = models.CharField(max_length=5, default='jpg', help_text="Image Extension")
    width               = models.CharField(max_length=20, blank=True, help_text="Thumbs Width")
    height              = models.CharField(max_length=20, blank=True, help_text="Thumbs Height")
    aspect_ratio        = models.CharField(max_length=20, blank=True, help_text="Thumbs Aspect Ratio: W:H")
    sprite              = models.BooleanField()
    sp_quality          = models.CharField(max_length=3, blank=True, default='75', help_text="Sprite jpg quality. Best quality 100")
    enable              = models.BooleanField()

    def __unicode__(self):
       return self.name


class Job(models.Model):
    STATUS = (
        ('Q', 'Queued'),
        ('P', 'Processing'),
        ('D', 'Done'),
        ('E', 'Error')
    )
    creation_time   = models.DateTimeField(auto_now=False, auto_now_add=True)
    thumb_preset    = models.ForeignKey(ThumbPreset, blank=True, null=True)
    input_filename  = models.CharField(max_length=255, help_text="Input File")
    input_path      = models.CharField(max_length=255, help_text="Input Path")
    basename        = models.CharField(max_length=100, help_text="Destination Basename")
    output_path     = models.CharField(max_length=255, help_text="Destination Path")
    priority        = models.CharField(max_length=1, default='9', help_text="0: Max priority, 9 Min Priority")
    status          = models.CharField(max_length=1, choices=STATUS, default='D', help_text="Job Status")
    progress        = models.IntegerField(default=0, help_text="Job Progress")
    message         = models.CharField(max_length=510, blank=True, help_text="Error or Warning message")

    def __unicode__(self):
        return str(self.id)