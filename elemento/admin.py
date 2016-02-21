from django.contrib import admin
import models



# Register your models here.

@admin.register(models.HLSPreset)
class HLSPresetAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'segment_time', 'extension' ]

@admin.register(models.H264Preset)
class H264PresetAdmin(admin.ModelAdmin):
    list_display = ['name', 'resolution', 'video_bitrate', 'audio_bitrate', 'level', 'profile' ]

@admin.register(models.Format)
class FormatAdmin(admin.ModelAdmin):
    pass

@admin.register(models.Job)
class JobAdmin(admin.ModelAdmin):
    list_display = [ 'id', 'priority', 'name', 'worker_pid', 'input_filename', 'status', 'progress', 'message' ]

@admin.register(models.Config)
class ConfigAdmin(admin.ModelAdmin):
    list_display = ['id', 'date', 'enable', 'workers' ]

@admin.register(models.OutputFile)
class OutputFileAdminn(admin.ModelAdmin):
    list_display = [ 'job', 'path', 'filename' ]

