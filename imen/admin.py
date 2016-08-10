from django.contrib import admin
import models

# Register your models here.


@admin.register(models.Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ['id', 'basename', 'creation_time', 'thumb_preset', 'priority', 'input_filename', 'status', 'progress', 'message']
    search_fields = ['basename']


@admin.register(models.Config)
class ConfigAdmin(admin.ModelAdmin):
    list_display = ['id', 'date', 'enable']


@admin.register(models.ThumbPreset)
class ThumbPresetAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'rate', 'extension', 'width', 'height', 'aspect_ratio', 'sprite']