from django.contrib import admin
import models



# Register your models here.

@admin.register(models.HLSPreset)
class HLSPresetAdmin(admin.ModelAdmin):
    pass

@admin.register(models.H264Preset)
class H264PresetAdmin(admin.ModelAdmin):
    pass
@admin.register(models.Format)
class FormatAdmin(admin.ModelAdmin):
    pass

@admin.register(models.Job)
class JobAdmin(admin.ModelAdmin):
    pass

@admin.register(models.Config)
class ConfigAdmin(admin.ModelAdmin):
    pass

