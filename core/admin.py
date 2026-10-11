from django.contrib import admin

from core.models import Company, Customer, EventType, Region, StaffMember

admin.site.register(EventType)
admin.site.register(Region)
admin.site.register(Company)
admin.site.register(StaffMember)
admin.site.register(Customer)
