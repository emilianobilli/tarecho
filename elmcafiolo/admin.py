from django.contrib import admin
import models

# Register your models here.

@admin.register(models.Preset)
class PresetAdmin(admin.ModelAdmin):
    list_display = ['name']


@admin.register(models.Transcoder)
class TranscoderAdmin(admin.ModelAdmin):
    list_display = ['name', 'ip', 'port', 'slots', 'preset_master', 'enabled']


@admin.register(models.Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'preset', 'job_id', 'transcoder', 'status', 'message']
    search_fields = ['name']