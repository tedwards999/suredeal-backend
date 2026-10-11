from paddle_billing.Notifications.Secret import Secret
from paddle_billing.Notifications.Verifier import Verifier

from core.models import BillingCustomer, Subscription

# Paddle's own SDK default (5s) is tight enough that normal network/queueing
# latency on a first delivery attempt could cause false rejections. 5 minutes
# is a conventional, still-tight replay window (e.g. Stripe's default).
WEBHOOK_TIMESTAMP_TOLERANCE_SECONDS = 300

SUBSCRIPTION_EVENT_TYPES = {'subscription.created', 'subscription.updated', 'subscription.canceled'}
CUSTOMER_EVENT_TYPES = {'customer.created', 'customer.updated'}


def verify_signature(request, secret_key):
    verifier = Verifier(maximum_variance=WEBHOOK_TIMESTAMP_TOLERANCE_SECONDS)
    return verifier.verify(request, Secret(secret_key))


def handle_event(event_type, data):
    if event_type in SUBSCRIPTION_EVENT_TYPES:
        _upsert_subscription(data)
    elif event_type in CUSTOMER_EVENT_TYPES:
        _upsert_customer(data)
    elif event_type == 'transaction.completed':
        pass  # subscription.* events already keep status/access current
    # else: unrecognized event type — ignore rather than error


def _upsert_customer(data):
    BillingCustomer.objects.update_or_create(
        paddle_customer_id=data['id'],
        defaults={'email': data.get('email', '')},
    )


def _upsert_subscription(data):
    # customer.created normally arrives first, but delivery order isn't
    # guaranteed, so create a placeholder if it hasn't yet.
    billing_customer, _ = BillingCustomer.objects.get_or_create(
        paddle_customer_id=data['customer_id'],
    )

    items = data.get('items') or []
    price_id = items[0]['price']['id'] if items else ''
    product_id = items[0]['price']['product_id'] if items else ''

    scheduled_change = data.get('scheduled_change')

    Subscription.objects.update_or_create(
        paddle_subscription_id=data['id'],
        defaults={
            'billing_customer': billing_customer,
            'status': data['status'],
            'price_id': price_id,
            'product_id': product_id,
            'scheduled_change_action': scheduled_change['action'] if scheduled_change else None,
            'scheduled_change_at': scheduled_change['effective_at'] if scheduled_change else None,
        },
    )
