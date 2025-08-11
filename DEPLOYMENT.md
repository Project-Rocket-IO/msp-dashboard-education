# Deployment Guide for Digital Ocean

This guide outlines the step-by-step process for deploying the application on Digital Ocean.

## Prerequisites
- Docker and Docker Compose installed on the server
- Access to the repository
- Ngrok for local development testing
- Intuit Developer Portal access
- Stripe account

## Deployment Steps

### 1. Repository Setup
```bash
git clone https://github.com/Project-Rocket-IO/msp-dashboard
cd msp-dashboard/msp-dashboard
```

### 2. Environment Configuration
1. Configure the `.env` file with the following variables (follow sample.env for more info):
   - Intuit credentials:
     - `INTUIT_CLIENT_ID`
     - `INTUIT_CLIENT_SECRET`
   - Django settings:
     - `DJANGO_SECRET_KEY`
     - `ALLOWED_HOSTS`
     - `CSRF_TRUSTED_ORIGINS`
   - Stripe configuration:
     - `STRIPE_PUBLIC_KEY`
     - `STRIPE_SECRET_KEY`
   - QuickBooks settings:
     - `QUICKBOOKS_WEBHOOK_VERIFICATION_TOKEN`
     - `QUICKBOOKS_REDIRECT_CALLBACK_URL`
     - `QUICKBOOKS_ENVIRONMENT` (set to 'production' or 'sandbox')

### 3. Intuit Developer Portal Configuration
1. Log in to the Intuit Developer Portal
2. Update the Redirect URIs to match your deployment URL
3. Enable the following webhook permissions:
   - Invoice
   - Payment
   - Customer

### 4. Application Deployment
1. Start the application in detached mode:
   ```bash
   docker-compose up -d
   ```

### 5. Superuser Creation
1. Access the application container:
   ```bash
   docker exec -it <app-container> bash
   ```
2. Activate the virtual environment:
   ```bash
   source venv/bin/activate
   ```
3. Create a superuser:
   ```bash
   python manage.py createsuperuser
   ```
4. Exit the container:
   ```bash
   exit
   ```

## Verification
After deployment, verify the following:
- Application is accessible via the configured domain
- QuickBooks integration is working
- Stripe payments are processing correctly
- Webhooks are receiving and processing events

## Troubleshooting
If you encounter any issues during deployment:
1. Check the Docker logs: `docker-compose logs`
2. Verify all environment variables are correctly set
3. Ensure all required ports are open and accessible
4. Confirm QuickBooks webhook permissions are properly configured

## Support
For additional support or questions, please contact the development team or refer to the project documentation.

