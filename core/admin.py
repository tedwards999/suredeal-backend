from django.contrib import admin

from core.models import Company, EventType, Region

admin.site.register(EventType)
admin.site.register(Region)
admin.site.register(Company)
