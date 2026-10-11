from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from core.models import (
    ORGANIZATION_ROLE_CHOICES,
    Customer,
    Event,
    Membership,
    Product,
    Quote,
    QuoteLineItem,
    StaffMember,
)


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField()
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, validators=[validate_password])
    first_name = serializers.CharField(required=False, allow_blank=True, default='')
    last_name = serializers.CharField(required=False, allow_blank=True, default='')
    title = serializers.CharField(required=False, allow_blank=True, default='')
    phone = serializers.CharField(required=False, allow_blank=True, default='')

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError('This username is already taken.')
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('An account with this email already exists.')
        return value

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
        )
        return StaffMember.objects.create(
            user=user,
            title=validated_data['title'],
            email=validated_data['email'],
            phone=validated_data['phone'] or None,
        )


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, validators=[validate_password])


class InviteCreateSerializer(serializers.Serializer):
    email = serializers.EmailField()
    role = serializers.ChoiceField(choices=ORGANIZATION_ROLE_CHOICES)

    def validate_email(self, value):
        organization = self.context['organization']
        if Membership.objects.filter(organization=organization, email=value).exists():
            raise serializers.ValidationError('This email has already been invited.')
        return value


class MembershipSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    is_pending = serializers.BooleanField(read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    name = serializers.SerializerMethodField()

    class Meta:
        model = Membership
        fields = ['id', 'email', 'name', 'role', 'role_display', 'is_pending', 'is_expired', 'invited_at', 'accepted_at']

    def get_name(self, obj):
        return obj.user.get_full_name() if obj.user else ''


class AcceptInviteSerializer(serializers.Serializer):
    token = serializers.CharField()


class RoleUpdateSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=ORGANIZATION_ROLE_CHOICES)


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ['id', 'name', 'surname', 'title', 'email', 'phone', 'company', 'staff_member', 'added_date']
        read_only_fields = ['added_date']


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'cost_price', 'sales_price', 'margin']


class QuoteLineItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuoteLineItem
        fields = ['id', 'product', 'quantity', 'price', 'discount', 'line_total']


class QuoteEventSerializer(serializers.ModelSerializer):
    event_type_name = serializers.CharField(source='event_type.name', read_only=True)

    class Meta:
        model = Event
        fields = ['id', 'event_date', 'event_type', 'event_type_name']


class QuoteSerializer(serializers.ModelSerializer):
    line_items = QuoteLineItemSerializer(many=True, source='quotelineitem_set', required=False)
    events = QuoteEventSerializer(many=True, source='event_set', read_only=True)

    class Meta:
        model = Quote
        fields = [
            'id', 'customer', 'date_issued', 'next_follow_up', 'expiry_date', 'notes',
            'line_items', 'events',
        ]
        read_only_fields = ['date_issued']

    def create(self, validated_data):
        line_items_data = validated_data.pop('quotelineitem_set', [])
        quote = Quote.objects.create(**validated_data)
        for item_data in line_items_data:
            QuoteLineItem.objects.create(quote=quote, **item_data)
        return quote

    def update(self, instance, validated_data):
        line_items_data = validated_data.pop('quotelineitem_set', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if line_items_data is not None:
            instance.quotelineitem_set.all().delete()
            for item_data in line_items_data:
                QuoteLineItem.objects.create(quote=instance, **item_data)
        return instance
