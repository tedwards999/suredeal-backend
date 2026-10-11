from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from knox.models import AuthToken
from knox.views import LoginView as KnoxLoginView
from rest_framework import status
from rest_framework.authentication import BasicAuthentication
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import Membership, Organization
from core.serializers import (
    AcceptInviteSerializer,
    InviteCreateSerializer,
    MembershipSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
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
