"""
URL configuration for suredeal project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path

from core.views import (
    AcceptInviteView,
    CustomerDetailView,
    CustomerListCreateView,
    DashboardMetricsView,
    EventListCreateView,
    InvoiceDetailView,
    InvoiceListCreateView,
    LoginView,
    MembershipRoleView,
    OrganizationInviteView,
    OrganizationMembersView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    InvoicePDFView,
    ProductDetailView,
    ProductListCreateView,
    PublicInvoicePDFView,
    PublicInvoiceView,
    PublicQuotePDFView,
    PublicQuoteView,
    QuoteDetailView,
    QuoteListCreateView,
    QuotePDFView,
    QuoteResendView,
    RegisterView,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/register/', RegisterView.as_view(), name='register'),
    path('api/auth/login/', LoginView.as_view(), name='knox_login'),
    path('api/auth/password-reset/', PasswordResetRequestView.as_view(), name='password_reset_request'),
    path('api/auth/password-reset/confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('api/auth/', include('knox.urls')),
    path('api/organization/members/', OrganizationMembersView.as_view(), name='organization_members'),
    path('api/organization/invites/', OrganizationInviteView.as_view(), name='organization_invite'),
    path('api/organization/invites/accept/', AcceptInviteView.as_view(), name='organization_invite_accept'),
    path('api/organization/members/<int:membership_id>/role/', MembershipRoleView.as_view(), name='membership_role'),
    path('api/customers/', CustomerListCreateView.as_view(), name='customer_list_create'),
    path('api/customers/<int:pk>/', CustomerDetailView.as_view(), name='customer_detail'),
    path('api/products/', ProductListCreateView.as_view(), name='product_list_create'),
    path('api/products/<int:pk>/', ProductDetailView.as_view(), name='product_detail'),
    path('api/quotes/', QuoteListCreateView.as_view(), name='quote_list_create'),
    path('api/quotes/<int:pk>/', QuoteDetailView.as_view(), name='quote_detail'),
    path('api/quotes/<int:pk>/resend/', QuoteResendView.as_view(), name='quote_resend'),
    path('api/invoices/', InvoiceListCreateView.as_view(), name='invoice_list_create'),
    path('api/invoices/<int:pk>/', InvoiceDetailView.as_view(), name='invoice_detail'),
    path('api/events/', EventListCreateView.as_view(), name='event_list_create'),
    path('api/dashboard/metrics/', DashboardMetricsView.as_view(), name='dashboard_metrics'),
    path('api/public/quotes/<str:token>/', PublicQuoteView.as_view(), name='public_quote'),
    path('api/public/invoices/<str:token>/', PublicInvoiceView.as_view(), name='public_invoice'),
    path('api/quotes/<int:pk>/pdf/', QuotePDFView.as_view(), name='quote_pdf'),
    path('api/invoices/<int:pk>/pdf/', InvoicePDFView.as_view(), name='invoice_pdf'),
    path('api/public/quotes/<str:token>/pdf/', PublicQuotePDFView.as_view(), name='public_quote_pdf'),
    path('api/public/invoices/<str:token>/pdf/', PublicInvoicePDFView.as_view(), name='public_invoice_pdf'),
]
