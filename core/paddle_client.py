import os

from paddle_billing import Client, Environment, Options

_ENVIRONMENTS = {
    'sandbox': Environment.SANDBOX,
    'production': Environment.PRODUCTION,
}


def get_paddle_client():
    api_key = os.environ['PADDLE_API_KEY']
    environment_name = os.environ['PADDLE_ENVIRONMENT']
    if environment_name not in _ENVIRONMENTS:
        raise RuntimeError(
            f"PADDLE_ENVIRONMENT must be 'sandbox' or 'production', got {environment_name!r}"
        )
    return Client(api_key, options=Options(environment=_ENVIRONMENTS[environment_name]))
