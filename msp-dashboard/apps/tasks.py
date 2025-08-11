from celery import shared_task
from apps.models import QuickBooksToken
from apps.views.utils import get_auth_client
from intuitlib.exceptions import AuthClientError

@shared_task(bind=True, name="apps.tasks.refresh_quickbooks_tokens")
def refresh_quickbooks_tokens(self):
    """
    Task to refresh QuickBooks tokens every 23 hours
    """
    try:
        # Get all QuickBooks tokens
        tokens = QuickBooksToken.objects.all()
        auth_client = get_auth_client()

        print(f"Refreshing {len(tokens)} QuickBooks tokens")
        print("Auth client: ", auth_client)

        for token in tokens:
            try:
                # Refresh the token
                auth_client.refresh(refresh_token=token.refresh_token)

                # Update the token in database
                token.refresh_token = auth_client.refresh_token
                token.expires_in = auth_client.x_refresh_token_expires_in
                token.is_refresh_token_replaced = True
                token.save()

                print(
                    f"Token refreshed for {token.mspcompany.company_name}: {token.refresh_token}"
                )

            except AuthClientError as e:
                print(
                    f"Error refreshing token for {token.mspcompany.company_name}: {str(e)}"
                )
                continue

    except Exception as e:
        print(f"Error in refresh_quickbooks_tokens task: {str(e)}")
        raise
