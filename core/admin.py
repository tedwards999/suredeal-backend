from django.contrib import admin

from core.models import (
    BillingCustomer,
    Company,
    Customer,
    Event,
    EventType,
    Invoice,
    InvoiceLineItem,
    Membership,
    Organization,
    Product,
    Quote,
    QuoteLineItem,
    Region,
    StaffMember,
    Subscription,
)

admin.site.register(EventType)
admin.site.register(Region)
admin.site.register(Company)
admin.site.register(StaffMember)
admin.site.register(Customer)
admin.site.register(Product)
admin.site.register(Quote)
admin.site.register(QuoteLineItem)
admin.site.register(Invoice)
admin.site.register(InvoiceLineItem)
admin.site.register(Event)
admin.site.register(Organization)
admin.site.register(Membership)
admin.site.register(BillingCustomer)
admin.site.register(Subscription)
