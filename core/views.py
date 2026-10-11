from decimal import Decimal

from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.http import HttpResponse
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from knox.models import AuthToken
from knox.views import LoginView as KnoxLoginView
from rest_framework import generics, status
from rest_framework.authentication import BasicAuthentication
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import Customer, Event, EventType, Invoice, Membership, Organization, Product, Quote
from core.pdf import build_invoice_pdf, build_quote_pdf
from core.serializers import (
    AcceptInviteSerializer,
    CustomerSerializer,
    EventSerializer,
    InvoiceSerializer,
    InviteCreateSerializer,
    MembershipSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    ProductSerializer,
    QuoteSerializer,
    RegisterSerializer,
    RoleUpdateSerializer,
)


def get_organization_for_user(user):
    organization = Organization.objects.filter(owner=user).first()
    if organization:
        return organization
    membership = (
        Membership.objects.filter(user=user, accepted_at__isnull=False)
        .select_related('organization')
        .first()
    )
    return membership.organization if membership else None


class LoginView(KnoxLoginView):
    authentication_classes = [BasicAuthentication]
    permission_classes = [IsAuthenticated]


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        staff_member = serializer.save()
        _, token = AuthToken.objects.create(staff_member.user)
        return Response({'token': token}, status=status.HTTP_201_CREATED)


class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = User.objects.filter(email=serializer.validated_data['email']).first()
        if user:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            send_mail(
                subject='Reset your SureDeal password',
                message=f'Use this link to reset your password: /reset-password?uid={uid}&token={token}',
                from_email=None,
                recipient_list=[user.email],
            )
        return Response({'detail': 'If an account exists for that email, a reset link has been sent.'})


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            user = User.objects.get(pk=force_str(urlsafe_base64_decode(data['uid'])))
        except (User.DoesNotExist, ValueError, TypeError, OverflowError):
            user = None
        if user is None or not default_token_generator.check_token(user, data['token']):
            return Response({'detail': 'Invalid or expired reset link.'}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(data['new_password'])
        user.save()
        return Response({'detail': 'Password has been reset.'})


class OrganizationMembersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        organization = get_organization_for_user(request.user)
        if organization is None:
            return Response({'detail': 'No organization found for this account.'}, status=status.HTTP_404_NOT_FOUND)
        memberships = organization.memberships.all().order_by('-invited_at')
        return Response({
            'owner': {
                'email': organization.owner.email,
                'name': organization.owner.get_full_name(),
                'role': 'owner',
                'role_display': 'Owner',
            },
            'members': MembershipSerializer(memberships, many=True).data,
        })


class OrganizationInviteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        organization = get_organization_for_user(request.user)
        if organization is None:
            return Response({'detail': 'No organization found for this account.'}, status=status.HTTP_404_NOT_FOUND)
        if organization.owner_id != request.user.id:
            return Response({'detail': 'Only the workspace owner can invite members.'}, status=status.HTTP_403_FORBIDDEN)
        serializer = InviteCreateSerializer(data=request.data, context={'organization': organization})
        serializer.is_valid(raise_exception=True)
        membership = Membership.objects.create(
            organization=organization,
            email=serializer.validated_data['email'],
            role=serializer.validated_data['role'],
        )
        send_mail(
            subject=f'You have been invited to join {organization.name} on SureDeal',
            message=f'Use this link to join: /join?token={membership.invite_token}',
            from_email=None,
            recipient_list=[membership.email],
        )
        return Response(MembershipSerializer(membership).data, status=status.HTTP_201_CREATED)


class AcceptInviteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AcceptInviteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        membership = Membership.objects.filter(invite_token=serializer.validated_data['token']).first()
        if membership is None:
            return Response({'detail': 'Invalid invite link.'}, status=status.HTTP_400_BAD_REQUEST)
        if not membership.is_pending:
            return Response({'detail': 'This invite has already been used.'}, status=status.HTTP_400_BAD_REQUEST)
        if membership.is_expired:
            return Response({'detail': 'This invite has expired.'}, status=status.HTTP_400_BAD_REQUEST)
        membership.user = request.user
        membership.accepted_at = timezone.now()
        membership.save()
        return Response(MembershipSerializer(membership).data)


class MembershipRoleView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, membership_id):
        organization = get_organization_for_user(request.user)
        if organization is None:
            return Response({'detail': 'No organization found for this account.'}, status=status.HTTP_404_NOT_FOUND)
        if organization.owner_id != request.user.id:
            return Response({'detail': 'Only the workspace owner can change member roles.'}, status=status.HTTP_403_FORBIDDEN)
        membership = Membership.objects.filter(pk=membership_id, organization=organization).first()
        if membership is None:
            return Response({'detail': 'Member not found.'}, status=status.HTTP_404_NOT_FOUND)
        if membership.is_pending:
            return Response({'detail': 'Only active members\' roles can be changed.'}, status=status.HTTP_400_BAD_REQUEST)
        serializer = RoleUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        membership.role = serializer.validated_data['role']
        membership.save()
        return Response(MembershipSerializer(membership).data)


class CustomerListCreateView(generics.ListCreateAPIView):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated]


class CustomerDetailView(generics.RetrieveUpdateAPIView):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated]


class ProductListCreateView(generics.ListCreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]


class ProductDetailView(generics.RetrieveUpdateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]


class QuoteListCreateView(generics.ListCreateAPIView):
    queryset = Quote.objects.all()
    serializer_class = QuoteSerializer
    permission_classes = [IsAuthenticated]


class QuoteDetailView(generics.RetrieveUpdateAPIView):
    queryset = Quote.objects.all()
    serializer_class = QuoteSerializer
    permission_classes = [IsAuthenticated]


class QuoteResendView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        quote = Quote.objects.filter(pk=pk).first()
        if quote is None:
            return Response({'detail': 'Quote not found.'}, status=status.HTTP_404_NOT_FOUND)
        event_type, _ = EventType.objects.get_or_create(name='Sent')
        Event.objects.create(quote=quote, event_type=event_type, event_date=timezone.now().date())
        return Response(QuoteSerializer(quote).data)


class InvoiceListCreateView(generics.ListCreateAPIView):
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer
    permission_classes = [IsAuthenticated]


class InvoiceDetailView(generics.RetrieveUpdateAPIView):
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer
    permission_classes = [IsAuthenticated]


class EventListCreateView(generics.ListCreateAPIView):
    serializer_class = EventSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Event.objects.all().order_by('-event_date', '-id')
        event_type = self.request.query_params.get('event_type')
        if event_type:
            if event_type.isdigit():
                queryset = queryset.filter(event_type_id=int(event_type))
            else:
                queryset = queryset.filter(event_type__name__iexact=event_type)
        date_from = self.request.query_params.get('date_from')
        if date_from:
            queryset = queryset.filter(event_date__gte=date_from)
        date_to = self.request.query_params.get('date_to')
        if date_to:
            queryset = queryset.filter(event_date__lte=date_to)
        limit = self.request.query_params.get('limit')
        if limit and limit.isdigit():
            queryset = queryset[:int(limit)]
        return queryset


class DashboardMetricsView(APIView):
    """
    Quote stage (Draft/Sent/Viewed/Accepted) isn't a stored field — Quote has
    no status column — so it's derived here from the most advanced Event
    logged against each quote.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        sent_type = EventType.objects.filter(name__iexact='Sent').first()
        viewed_type = EventType.objects.filter(name__iexact='Viewed').first()
        accepted_type = EventType.objects.filter(name__iexact='Accepted').first()

        sent_ids = set(Event.objects.filter(event_type=sent_type).values_list('quote_id', flat=True)) if sent_type else set()
        viewed_ids = set(Event.objects.filter(event_type=viewed_type).values_list('quote_id', flat=True)) if viewed_type else set()
        accepted_ids = set(Event.objects.filter(event_type=accepted_type).values_list('quote_id', flat=True)) if accepted_type else set()

        pipeline = {
            'Draft': {'count': 0, 'value': Decimal('0')},
            'Sent': {'count': 0, 'value': Decimal('0')},
            'Viewed': {'count': 0, 'value': Decimal('0')},
            'Accepted': {'count': 0, 'value': Decimal('0')},
        }
        total_revenue = Decimal('0')
        quote_values = []

        for quote in Quote.objects.all().prefetch_related('quotelineitem_set'):
            value = sum((item.line_total for item in quote.quotelineitem_set.all()), Decimal('0'))
            quote_values.append(value)
            if quote.id in accepted_ids:
                stage = 'Accepted'
                total_revenue += value
            elif quote.id in viewed_ids:
                stage = 'Viewed'
            elif quote.id in sent_ids:
                stage = 'Sent'
            else:
                stage = 'Draft'
            pipeline[stage]['count'] += 1
            pipeline[stage]['value'] += value

        quotes_sent_count = len(sent_ids | viewed_ids | accepted_ids)
        acceptance_rate = round(len(accepted_ids) / quotes_sent_count * 100, 1) if quotes_sent_count else 0
        avg_quote_value = round(sum(quote_values) / len(quote_values), 2) if quote_values else Decimal('0')

        return Response({
            'total_revenue': str(total_revenue),
            'quotes_sent': quotes_sent_count,
            'acceptance_rate': acceptance_rate,
            'avg_quote_value': str(avg_quote_value),
            'pipeline': [
                {'stage': stage, 'count': data['count'], 'value': str(data['value'])}
                for stage, data in pipeline.items()
            ],
        })


class PublicQuoteView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, token):
        quote = Quote.objects.filter(public_token=token).first()
        if quote is None:
            return Response({'detail': 'Quote not found.'}, status=status.HTTP_404_NOT_FOUND)
        viewed_type, _ = EventType.objects.get_or_create(name='Viewed')
        Event.objects.create(quote=quote, event_type=viewed_type, event_date=timezone.now().date())
        return Response(QuoteSerializer(quote).data)


class PublicInvoiceView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, token):
        invoice = Invoice.objects.filter(public_token=token).first()
        if invoice is None:
            return Response({'detail': 'Invoice not found.'}, status=status.HTTP_404_NOT_FOUND)
        viewed_type, _ = EventType.objects.get_or_create(name='Viewed')
        Event.objects.create(invoice=invoice, event_type=viewed_type, event_date=timezone.now().date())
        return Response(InvoiceSerializer(invoice).data)


class QuotePDFView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        quote = Quote.objects.filter(pk=pk).first()
        if quote is None:
            return Response({'detail': 'Quote not found.'}, status=status.HTTP_404_NOT_FOUND)
        buffer = build_quote_pdf(quote)
        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="quote-{quote.pk}.pdf"'
        return response


class InvoicePDFView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        invoice = Invoice.objects.filter(pk=pk).first()
        if invoice is None:
            return Response({'detail': 'Invoice not found.'}, status=status.HTTP_404_NOT_FOUND)
        buffer = build_invoice_pdf(invoice)
        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="invoice-{invoice.pk}.pdf"'
        return response


class PublicQuotePDFView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, token):
        quote = Quote.objects.filter(public_token=token).first()
        if quote is None:
            return Response({'detail': 'Quote not found.'}, status=status.HTTP_404_NOT_FOUND)
        downloaded_type, _ = EventType.objects.get_or_create(name='Downloaded')
        Event.objects.create(quote=quote, event_type=downloaded_type, event_date=timezone.now().date())
        buffer = build_quote_pdf(quote)
        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="quote-{quote.pk}.pdf"'
        return response


class PublicInvoicePDFView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, token):
        invoice = Invoice.objects.filter(public_token=token).first()
        if invoice is None:
            return Response({'detail': 'Invoice not found.'}, status=status.HTTP_404_NOT_FOUND)
        downloaded_type, _ = EventType.objects.get_or_create(name='Downloaded')
        Event.objects.create(invoice=invoice, event_type=downloaded_type, event_date=timezone.now().date())
        buffer = build_invoice_pdf(invoice)
        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="invoice-{invoice.pk}.pdf"'
        return response
