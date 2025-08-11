from django.db.models import Field
from accounts.models import TechnicianUser
from apps.models import SalesRequests, ClientCompany, ClientTeamMembers
from atlas.models import ChatHistory
import json
from django.conf import settings
import openai
import re
from decimal import Decimal

openai.api_key = settings.OPENAI_API_KEY

def create_sales_prompt(message):
    return f"""
    The user is requesting to create or update a sale. Extract the following information from the user's input and return it as a valid JSON string:

    Required fields for creation:
    - name (string, the sales title/name)
    - value (float, the sale value in dollars)
    - owner (string, the technician username who owns the sale)
    - client (string, the client company name)

    Optional fields:
    - due_date (string, YYYY-MM-DD or "today" or "tomorrow")
    - contact (string, the contact person's name)
    - description (string, sale description)
    - type (string, sales type - defaults to "New Sale" when creating)

    Rules:
    - Return the response as a valid JSON string with double quotes around keys and string values
    - Set missing values to null (do not infer or guess values)
    - Value should be a number (e.g., 5000.00 for $5000)
    - Owner should be a technician username
    - Client should be an existing client company name
    - Type should be one of: "New Sale", "Proposal Created", "Proposal Sent", "Proposal Executed", "Sale Closed"
    - If the user specifies "with a name X" or "to name X", set new_name to X for updates
    - Extract sale names from quotes if present (e.g., "Enterprise Software Deal" -> name: "Enterprise Software Deal")
    - Extract client names from context (e.g., "for client TechCorp" -> client: "TechCorp")
    - Extract owner assignments (e.g., "assign to admin" -> owner: "admin")
    - Extract values in various formats:
      * "$5000" -> value: 5000.0
      * "5000 dollars" -> value: 5000.0
      * "value=5000" -> value: 5000.0
      * "5000" -> value: 5000.0

    Common patterns:
    - "Create a new sale Enterprise Software Deal" -> name: "Enterprise Software Deal"
    - "value=5000" -> value: 5000.0
    - "assign to admin" -> owner: "admin"
    - "for client TechCorp" -> client: "TechCorp"
    - "due today" -> due_date: "today"
    - "due tomorrow" -> due_date: "tomorrow"
    - "type=Proposal Created" -> type: "Proposal Created"

    The user's input: "{message}"

    Example response format:
    {{
        "name": "Enterprise Software Deal",
        "value": 5000.0,
        "owner": "admin",
        "client": "TechCorp",
        "due_date": null,
        "contact": null,
        "description": null,
        "type": null
    }}

    Now, process the input and return the extracted fields in this exact JSON format.
    """

def extract_sales_fields(message):
    try:
        prompt = create_sales_prompt(message)
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a data extraction assistant. Extract information from user messages and return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1
        )
        response_content = response.choices[0].message.content.strip()
        print(f"OpenAI response: {response_content}")
        
        try:
            extracted_data = json.loads(response_content)
            print("Extracted data:", extracted_data)
            
            # Manual extraction of sale information if GPT didn't capture it
            if not extracted_data.get("name"):
                message_lower = message.lower()
                # Extract sale name from quotes or context
                quoted_names = re.findall(r'"([^"]+)"', message)
                if quoted_names:
                    extracted_data["name"] = quoted_names[0]
                    print(f"Manually extracted sale name from quotes: {extracted_data['name']}")
                else:
                    # Look for sale name after "sale" keyword
                    words = message.split()
                    for i, word in enumerate(words):
                        if word.lower() == "sale" and i + 1 < len(words):
                            potential_name = words[i + 1]
                            if potential_name and not potential_name.lower() in ["create", "add", "new", "make", "to", "it"]:
                                extracted_data["name"] = potential_name
                                print(f"Manually extracted sale name: {extracted_data['name']}")
                                break
            
            # Manual extraction of value
            if not extracted_data.get("value"):
                message_lower = message.lower()
                value_patterns = [
                    r'\$(\d+(?:\.\d{{2}})?)',
                    r'(\d+(?:\.\d{{2}})?)\s*dollars?',
                    r'value\s*[=:]\s*(\d+(?:\.\d{{2}})?)',
                    r'(\d+(?:\.\d{{2}})?)'
                ]
                for pattern in value_patterns:
                    match = re.search(pattern, message_lower)
                    if match:
                        try:
                            extracted_data["value"] = float(match.group(1))
                            print(f"Manually extracted value: {extracted_data['value']}")
                            break
                        except ValueError:
                            continue
            
            # Manual extraction of owner and client with improved logic
            # If 'owner' is a known technician username, use as owner; if not, treat as possible client
            from accounts.models import TechnicianUser
            if not extracted_data.get("owner") or not extracted_data.get("client"):
                message_lower = message.lower()
                # Try to extract both owner and client from patterns
                # Owner: assign to admin, owner = admin, etc.
                owner_patterns = [
                    r'assign\s+(?:to\s+)?(\w+)',
                    r'owner\s*[=:]\s*(\w+)',
                    r'owner\s*=\s*(\w+)'
                ]
                found_owner = None
                for pattern in owner_patterns:
                    match = re.search(pattern, message_lower)
                    if match:
                        candidate = match.group(1)
                        # Check if this is a valid technician username
                        if TechnicianUser.objects.filter(auth_user__username__iexact=candidate).exists():
                            extracted_data["owner"] = candidate
                            found_owner = candidate
                            print(f"[extract_sales_fields] Used technician username for owner: {candidate}")
                        else:
                            # If not a valid technician, treat as possible client
                            if not extracted_data.get("client"):
                                extracted_data["client"] = candidate.title()
                                print(f"[extract_sales_fields] Treated '{candidate}' as client name")
                        break
                # Client: for client X, client = X, etc.
                if not extracted_data.get("client"):
                    client_patterns = [
                        r'for\s+client\s+([^,\s]+(?:\s+[^,\s]+)*)',
                        r'client\s+([^,\s]+(?:\s+[^,\s]+)*)',
                        r'client\s*[=:]\s*([^,\s]+(?:\s+[^,\s]+)*)'
                    ]
                    for pattern in client_patterns:
                        match = re.search(pattern, message_lower)
                        if match:
                            extracted_data["client"] = match.group(1).title()
                            print(f"[extract_sales_fields] Manually extracted client: {extracted_data['client']}")
                            break
                # If owner is still not a valid technician, prompt for a valid username
                if extracted_data.get("owner") and not TechnicianUser.objects.filter(auth_user__username__iexact=extracted_data["owner"]).exists():
                    print(f"[extract_sales_fields] Owner '{extracted_data['owner']}' is not a valid technician username. Prompting for valid owner.")
                    extracted_data["owner"] = None
            
            # Manual extraction of due_date
            if not extracted_data.get("due_date"):
                message_lower = message.lower()
                if "due today" in message_lower:
                    extracted_data["due_date"] = "today"
                    print(f"Manually extracted due_date: {extracted_data['due_date']}")
                elif "due tomorrow" in message_lower:
                    extracted_data["due_date"] = "tomorrow"
                    print(f"Manually extracted due_date: {extracted_data['due_date']}")
            
            # Manual extraction of type
            if not extracted_data.get("type"):
                message_lower = message.lower()
                type_patterns = [
                    r'type\s*[=:]\s*([^,\s]+(?:\s+[^,\s]+)*)',
                    r'type\s*=\s*([^,\s]+(?:\s+[^,\s]+)*)'
                ]
                for pattern in type_patterns:
                    match = re.search(pattern, message_lower)
                    if match:
                        extracted_data["type"] = match.group(1).title()
                        print(f"Manually extracted type: {extracted_data['type']}")
                        break
            
            return extracted_data
        except json.JSONDecodeError as e:
            print(f"JSON Parse Error: {e}")
            print(f"Response content that failed to parse: {response_content}")
            return {"response": f"Failed to parse input: {str(e)}", "error": True}
    except Exception as e:
        print(f"Error in extract_sales_fields: {e}")
        return {"response": f"Failed to extract sales data: {str(e)}", "error": True}

def get_sales_context(request=None):
    if request and hasattr(request, 'session'):
        return request.session.get('sales_context', {})
    else:
        # Fallback to ChatHistory
        history_entries = ChatHistory.objects.order_by('timestamp')
        if history_entries.exists():
            last_entry = history_entries.last()
            try:
                return json.loads(last_entry.bot_response)
            except:
                return {}
    return {}

def merge_sales_context(current_context, extracted_data):
    """
    Merge new data with existing context, only updating non-None values
    """
    merged = current_context.copy()
    for key, value in extracted_data.items():
        if value is not None:
            merged[key] = value
    return merged

def save_sales_context(request, context):
    if request and hasattr(request, 'session'):
        request.session['sales_context'] = context
        request.session.modified = True

def clear_sales_context(request):
    if request and hasattr(request, 'session'):
        if 'sales_context' in request.session:
            del request.session['sales_context']
            request.session.modified = True

def validate_sales_data(sales_data):
    # Get action_intent from the data if available, otherwise infer from new_name
    action_intent = sales_data.get('action_intent')
    if not action_intent:
        action_intent = 'UPDATE' if sales_data.get('new_name') else 'CREATE'
    
    required_fields = {
        'CREATE': ['name', 'value', 'owner', 'client'],
        'UPDATE': ['name', 'value', 'owner', 'client']
    }
    
    missing_fields = []
    db_sale = None
    if action_intent == 'UPDATE' and sales_data.get('name'):
        from apps.models import SalesRequests
        db_sale = SalesRequests.objects.filter(name__iexact=sales_data['name']).first()
        if db_sale:
            print(f"[DEBUG] DB Sale: name={db_sale.name}, value={db_sale.value}, owner={getattr(db_sale.owner, 'auth_user', None)}, client={getattr(db_sale.client, 'name', None)}")
    
    for field in required_fields[action_intent]:
        if not sales_data.get(field):
            # For UPDATE, try to get from DB
            if action_intent == 'UPDATE' and db_sale and hasattr(db_sale, field):
                value = getattr(db_sale, field, None)
                if value is not None:
                    # Handle ForeignKey fields differently
                    if field == 'owner' and hasattr(value, 'auth_user'):
                        username = getattr(value.auth_user, 'username', None)
                        if username:
                            sales_data[field] = username
                            print(f"[DEBUG] Used DB owner username: {username}")
                        else:
                            missing_fields.append(field)
                    elif field == 'client' and hasattr(value, 'name'):
                        client_name = value.name
                        if client_name:
                            sales_data[field] = client_name
                            print(f"[DEBUG] Used DB client name: {client_name}")
                        else:
                            missing_fields.append(field)
                    else:
                        sales_data[field] = value
                        print(f"[DEBUG] Used DB value for {field}: {value}")
                else:
                    missing_fields.append(field)
            else:
                missing_fields.append(field)
    
    if missing_fields:
        field_names = ', '.join(missing_fields)
        if action_intent == 'CREATE':
            return {
                "response": f"Please provide the following required information: {field_names}. For example: 'Create a new sale Enterprise Software Deal with value=5000, assign to admin, for client TechCorp'",
                "error": True
            }
        else:
            return {
                "response": f"Please provide the following required information to update: {field_names}.",
                "error": True
            }
    
    # Validate value is a number only for CREATE or if value is being updated
    if sales_data.get('value') and (action_intent == 'CREATE' or sales_data.get('value')):
        try:
            float(sales_data['value'])
        except (ValueError, TypeError):
            return {
                "response": "Please provide a valid numeric value for the sale.",
                "error": True
            }
    
    return {"error": False}

def get_sales_in_context(sales_name=None):
    try:
        if sales_name:
            sale = SalesRequests.objects.filter(name__iexact=sales_name).first()
        else:
            # Get the most recent sale
            sale = SalesRequests.objects.order_by('-create_date').first()
        
        if not sale:
            return None
        
        return sale
    except SalesRequests.MultipleObjectsReturned:
        return None

def create_sales(sales_data, conversation_key):
    try:
        print(f"Creating sales with data: {sales_data}")
        
        # Look up the client by name
        client_name = sales_data.get('client')
        if client_name:
            try:
                client = ClientCompany.objects.get(name__iexact=client_name)
                print(f"Found client: {client.name}")
            except ClientCompany.DoesNotExist:
                return {
                    "response": f"Client '{client_name}' does not exist. Please create the client first or use an existing client name.",
                    "error": True
                }
        else:
            return {"response": "Client is required for sales creation.", "error": True}
        
        # Look up the owner (technician) by username
        owner_username = sales_data.get('owner')
        if owner_username:
            try:
                owner = TechnicianUser.objects.get(auth_user__username__iexact=owner_username)
                print(f"Found owner: {owner.auth_user.username}")
            except TechnicianUser.DoesNotExist:
                return {
                    "response": f"Technician '{owner_username}' does not exist. Please assign a valid technician.",
                    "error": True
                }
        else:
            return {"response": "Owner is required for sales creation.", "error": True}
        
        # Handle contact if provided
        contact = None
        if sales_data.get('contact'):
            try:
                contact = ClientTeamMembers.objects.filter(
                    client=client,
                    first_name__iexact=sales_data['contact']
                ).first()
                if not contact:
                    # Try last name
                    contact = ClientTeamMembers.objects.filter(
                        client=client,
                        last_name__iexact=sales_data['contact']
                    ).first()
                print(f"Found contact: {contact.first_name if contact else 'None'}")
            except Exception as e:
                print(f"Error finding contact: {e}")
        
        # Handle due_date parsing
        due_date = None
        if sales_data.get('due_date'):
            from datetime import date
            due_date_str = sales_data.get('due_date')
            if due_date_str.lower() == 'today':
                due_date = date.today()
            elif due_date_str.lower() == 'tomorrow':
                from datetime import timedelta
                due_date = date.today() + timedelta(days=1)
            else:
                try:
                    due_date = date.fromisoformat(due_date_str)
                except ValueError:
                    return {
                        "response": f"Invalid date format for due_date: {due_date_str}. Please use YYYY-MM-DD format or 'today'/'tomorrow'.",
                        "error": True
                    }
        
        model_data = {
            'name': sales_data['name'],
            'client': client,
            'type': sales_data.get('type') or 'New Sale',  # Default to 'New Sale'
            'value': float(sales_data['value']),
            'owner': owner,
            'contact': contact,
            'due_date': due_date,
            'description': sales_data.get('description'),
        }
        
        print(f"Model data: {model_data}")
        
        sale = SalesRequests.objects.create(**model_data)
        
        print(f"Sales created successfully: {sale.name}")
        
        return {
            "response": f"Sales '{sale.name}' created successfully!",
            "sales_id": sale.id,
            "error": False
        }
        
    except Exception as e:
        print(f"Error creating sales: {e}")
        return {"response": f"Failed to create sales: {str(e)}", "error": True}

def update_sales(sales_data, conversation_key):
    print(f"Updating sales with data: {sales_data}")
    
    sale = get_sales_in_context(sales_data.get("name"))
    if not sale:
        return {
            "response": "No matching sales found for update. Please provide a valid sales name.",
            "error": True
        }
    
    print(f"Found sales: {sale.name} (ID: {sale.id})")
    
    updated_fields = {}
    new_name = sales_data.get("new_name")
    if new_name and new_name != sale.name:
        if SalesRequests.objects.filter(name__iexact=new_name).exclude(id=sale.id).exists():
            return {
                "response": f"A sales named '{new_name}' already exists. Choose a unique name.",
                "error": True
            }
        sale.name = new_name
        updated_fields["name"] = new_name

    # Handle due_date with proper parsing
    if sales_data.get('due_date'):
        from datetime import date
        due_date_str = sales_data.get('due_date')
        if due_date_str.lower() == 'today':
            sale.due_date = date.today()
            updated_fields['due_date'] = str(date.today())
        elif due_date_str.lower() == 'tomorrow':
            from datetime import timedelta
            sale.due_date = date.today() + timedelta(days=1)
            updated_fields['due_date'] = str(date.today() + timedelta(days=1))
        else:
            try:
                sale.due_date = date.fromisoformat(due_date_str)
                updated_fields['due_date'] = due_date_str
            except ValueError:
                return {
                    "response": f"Invalid date format for due_date: {due_date_str}. Please use YYYY-MM-DD format or 'today'/'tomorrow'.",
                    "error": True
                }

    # Handle owner update
    if sales_data.get('owner'):
        try:
            owner = TechnicianUser.objects.get(auth_user__username__iexact=sales_data['owner'])
            if sale.owner != owner:
                sale.owner = owner
                updated_fields['owner'] = sales_data['owner']
                print(f"Updated owner: {sale.owner.auth_user.username}")
        except TechnicianUser.DoesNotExist:
            return {
                "response": f"Technician '{sales_data['owner']}' does not exist. Please assign a valid technician.",
                "error": True
            }

    # Handle client update
    if sales_data.get('client'):
        try:
            client = ClientCompany.objects.get(name__iexact=sales_data['client'])
            if sale.client != client:
                sale.client = client
                updated_fields['client'] = sales_data['client']
                print(f"Updated client: {sale.client.name}")
        except ClientCompany.DoesNotExist:
            return {
                "response": f"Client '{sales_data['client']}' does not exist. Please use an existing client name.",
                "error": True
            }

    # Handle other fields
    for field, value in sales_data.items():
        if field not in ('name', 'new_name', 'owner', 'client', 'due_date') and value is not None:
            if hasattr(sale, field):
                current_value = getattr(sale, field)
                if current_value != value:
                    setattr(sale, field, value)
                    updated_fields[field] = value
                    print(f"Updated field {field}: {current_value} -> {value}")

    print(f"Updated fields: {updated_fields}")

    if updated_fields:
        try:
            sale.save()
            return {
                "response": f"Sales '{sale.name}' updated successfully!",
                "updated_fields": updated_fields,
                "error": False
            }
        except Exception as e:
            return {"response": f"Failed to update sales: {str(e)}", "error": True}
    else:
        return {"response": "No changes detected, sales remains the same.", "error": False} 