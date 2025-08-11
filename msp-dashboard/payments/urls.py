from django.urls import path
from .views import (
    payments_portal,
    pricing_page,
    stripe_config,
    basic_checkout_session,
    premium_checkout_session,
    allinc_checkout_session,
    stripe_webhook,
)

app_name = "payments"

urlpatterns = [
    path('', view=payments_portal, name='payments.payments'),
    path('pricing_page/', view=pricing_page, name='pricing_page'),
    path('config/', view=stripe_config, name='stripe.config'),
    path('basic-checkout-session/', view=basic_checkout_session, name='basic.session'),
    path('premium-checkout-session/', view=premium_checkout_session, name='premium.session'),
    path('allinc-checkout-session/', view=allinc_checkout_session, name='allinc.session'),
    path('webhook/', view=stripe_webhook, name='stripe.webhook'),
]