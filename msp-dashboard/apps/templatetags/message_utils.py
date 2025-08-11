from django import template
import re

register = template.Library()


@register.filter
def extract_client_name(message):
    """
    Extract client name from a message string.
    Expected formats:
    - "{client_name} has negative prepaid amount..."
    - "{client_name} has ${amount} remaining..."
    - "Make sure to ask {client_name} to pay..."
    """
    # Try to match the first word before "has" or "to"
    match = re.search(r"^([^h]+?)(?=\s+has|\s+to)", message)
    if match:
        return match.group(1).strip()
    return ""


@register.filter
def get_message_without_client(message):
    """
    Get the message text without the client name prefix.
    """
    # Remove the client name and any leading/trailing whitespace
    return re.sub(r"^[^h]+?(?=\s+has|\s+to)", "", message).strip()
