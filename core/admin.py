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


@admin.register(EventType)
class EventTypeAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ['company_name', 'company_city', 'company_country', 'company_region', 'company_email']
    search_fields = ['company_name', 'company_email']
    list_filter = ['company_country', 'company_region']


@admin.register(StaffMember)
class StaffMemberAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'email', 'phone']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'email']


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['name', 'surname', 'email', 'company', 'staff_member', 'added_date']
    search_fields = ['name', 'surname', 'email']
    list_filter = ['company']
    date_hierarchy = 'added_date'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'cost_price', 'sales_price', 'margin']
    search_fields = ['name']


@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer', 'date_issued', 'next_follow_up', 'expiry_date']
    search_fields = ['customer__name', 'customer__surname']
    list_filter = ['date_issued']
    date_hierarchy = 'date_issued'


@admin.register(QuoteLineItem)
class QuoteLineItemAdmin(admin.ModelAdmin):
    list_display = ['quote', 'product', 'quantity', 'price', 'discount', 'line_total']


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer', 'source_quote', 'date_issued', 'due_date']
    search_fields = ['customer__name', 'customer__surname']
    list_filter = ['date_issued']
    date_hierarchy = 'date_issued'


@admin.register(InvoiceLineItem)
class InvoiceLineItemAdmin(admin.ModelAdmin):
    list_display = ['invoice', 'product', 'quantity', 'price', 'discount', 'line_total']


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['id', 'event_type', 'event_date', 'quote', 'invoice']
    list_filter = ['event_type', 'event_date']
    date_hierarchy = 'event_date'


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner']
    search_fields = ['name', 'owner__username']


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ['email', 'organization', 'role', 'is_pending', 'invited_at', 'accepted_at']
    list_filter = ['role', 'organization']
    search_fields = ['email']


@admin.register(BillingCustomer)
class BillingCustomerAdmin(admin.ModelAdmin):
    list_display = ['paddle_customer_id', 'email', 'organization', 'created_at']
    search_fields = ['paddle_customer_id', 'email']


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['paddle_subscription_id', 'billing_customer', 'status', 'price_id', 'grants_access']
    list_filter = ['status']
    search_fields = ['paddle_subscription_id']
