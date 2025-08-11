from django.shortcuts import render, redirect
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.base import TemplateView
from djstripe.models import Product
import stripe
import json
from pages.utils import create_user_without_billing

# Create your views here.

from django.views.generic.base import TemplateView

class PaymentsView(TemplateView):
    pass

payments_portal = PaymentsView.as_view(template_name="payments/payments.html")

def pricing_page(request):
    return render(request, 'payments/pricing-page.html', {
        'products': Product.objects.all()
    })

# new
@csrf_exempt
def stripe_config(request):
    if request.method == 'GET':
        stripe_config = {'publicKey': settings.STRIPE_PUBLISH_KEY}
        return JsonResponse(stripe_config, safe=False)


@csrf_exempt
def basic_checkout_session(request):
    if request.method == 'GET':
        domain_url = 'https://rocket-command.com/payments/'
        stripe.api_key = settings.STRIPE_SECRET_KEY
        try:
            # Create new Checkout Session for the order
            # Other optional params include:
            # [billing_address_collection] - to display billing address details on the page
            # [customer] - if you have an existing Stripe Customer ID
            # [payment_intent_data] - capture the payment later
            # [customer_email] - prefill the email input in the form
            # For full details see https://stripe.com/docs/api/checkout/sessions/create

            # ?session_id={CHECKOUT_SESSION_ID} means the redirect will have the session ID set as a query param
            checkout_session = stripe.checkout.Session.create(
                line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                    'name': 'Base Package',
                    },
                    'unit_amount': 2500,
                },
                'quantity': 1,
                }],
                payment_method_types=['card'],
                mode='payment',
                success_url=domain_url + 'success?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=domain_url,
            )
            return JsonResponse({'sessionId': checkout_session['id']})
        except Exception as e:
            return JsonResponse({'error': str(e)})

@csrf_exempt
def premium_checkout_session(request):
    if request.method == 'GET':
        domain_url = 'https://rocket-command.com/payments/'
        stripe.api_key = settings.STRIPE_SECRET_KEY
        try:
            # Create new Checkout Session for the order
            # Other optional params include:
            # [billing_address_collection] - to display billing address details on the page
            # [customer] - if you have an existing Stripe Customer ID
            # [payment_intent_data] - capture the payment later
            # [customer_email] - prefill the email input in the form
            # For full details see https://stripe.com/docs/api/checkout/sessions/create

            # ?session_id={CHECKOUT_SESSION_ID} means the redirect will have the session ID set as a query param
            checkout_session = stripe.checkout.Session.create(
                line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                    'name': 'Premium Package',
                    },
                    'unit_amount': 5000,
                },
                'quantity': 1,
                }],
                payment_method_types=['card'],
                mode='payment',
                success_url=domain_url + 'success?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=domain_url,
            )
            return JsonResponse({'sessionId': checkout_session['id']})
        except Exception as e:
            return JsonResponse({'error': str(e)})

@csrf_exempt
def allinc_checkout_session(request):
    if request.method == 'GET':
        domain_url = 'https://rocket-command.com/payments/'
        stripe.api_key = settings.STRIPE_SECRET_KEY
        try:
            # Create new Checkout Session for the order
            # Other optional params include:
            # [billing_address_collection] - to display billing address details on the page
            # [customer] - if you have an existing Stripe Customer ID
            # [payment_intent_data] - capture the payment later
            # [customer_email] - prefill the email input in the form
            # For full details see https://stripe.com/docs/api/checkout/sessions/create

            # ?session_id={CHECKOUT_SESSION_ID} means the redirect will have the session ID set as a query param
            checkout_session = stripe.checkout.Session.create(
                line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                    'name': 'All Inclusive Package',
                    },
                    'unit_amount': 7500,
                },
                'quantity': 1,
                }],
                payment_method_types=['card'],
                mode='payment',
                success_url=domain_url + 'success?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=domain_url,
            )
            return JsonResponse({'sessionId': checkout_session['id']})
        except Exception as e:
            return JsonResponse({'error': str(e)})

@csrf_exempt
def stripe_webhook(request):
    """Handle Stripe webhooks for payment completion"""
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.DJSTRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        # Invalid payload
        return JsonResponse({'error': 'Invalid payload'}, status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return JsonResponse({'error': 'Invalid signature'}, status=400)

    # Handle the event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        
        # Check if this is a user creation payment
        if session.get('metadata', {}).get('user_email'):
            # This is a user creation payment
            user_email = session['metadata']['user_email']
            user_name = session['metadata']['user_name']
            role_id = int(session['metadata']['role_id'])
            role_name = session['metadata']['role_name']
            
            print(f"Payment completed for user creation: {user_name} ({user_email}) as {role_name}")
            
            # Create the user using the stored metadata
            try:
                from pages.utils import create_user_without_billing
                
                # Prepare form data from metadata (as tuple to match expected format)
                form_data = (
                    session['metadata'].get('first_name', ''),
                    session['metadata'].get('last_name', ''),
                    user_email,
                    session['metadata'].get('client_id', ''),
                    role_id,
                    session['metadata'].get('phone', ''),
                    session['metadata'].get('title', ''),
                    session['metadata'].get('password', '')
                )
                
                # Create the user without billing (since payment is already completed)
                result = create_user_without_billing(form_data)
                
                if result['success']:
                    print(f"User created successfully: {user_email}")
                else:
                    print(f"Failed to create user: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                print(f"Error creating user in webhook: {str(e)}")
            
    elif event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        print(f"Payment succeeded: {payment_intent['id']}")
    elif event['type'] == 'payment_intent.payment_failed':
        payment_intent = event['data']['object']
        print(f"Payment failed: {payment_intent['id']}")
    else:
        print(f"Unhandled event type: {event['type']}")

    return JsonResponse({'status': 'success'})