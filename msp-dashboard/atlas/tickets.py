from django.db.models import Field
from accounts.models import TechnicianUser
from apps.models import TicketList, ClientCompany, ProjectList, ClientWorkTypeRate
from atlas.models import ChatHistory
import json
from django.conf import settings
import openai
import re
from decimal import Decimal

openai.api_key = settings.OPENAI_API_KEY

def create_ticket_prompt(message):
    return f"""
    The user is requesting to create or update a ticket. Extract the following information from the user's input and return it as a valid JSON string:

    Required fields for creation:
    - ticket_name (string, the identifier of the ticket)
    - client (string, client company name)
    - assigned_to (list of technician usernames, e.g., ["john_doe", "ali"])

    Optional fields:
    - new_ticket_name (string, new name for updates)
    - description (string)
    - end_date (string, YYYY-MM-DD or "today" or "tomorrow")
    - due_date (string, YYYY-MM-DD or "today" or "tomorrow")
    - ticket_type (string, e.g., "bug", "feature", "task")
    - status (string, e.g., "open", "in_progress", "closed")
    - priority (string, e.g., "low", "medium", "high")
    - project (string, project name)

    Rules:
    - Return the response as a valid JSON string with double quotes around keys and string values
    - Set missing values to null (do not infer or guess values)
    - assigned_to should be an array of technician usernames or null
    - Dates can be in YYYY-MM-DD format or relative terms like "today" or "tomorrow"
    - If the user specifies "with a name X" or "to name X", set new_ticket_name to X for updates
    - Extract ticket names from quotes if present (e.g., "VPN Install" -> ticket_name: "VPN Install")
    - Extract client names from context (e.g., "make the client Zeta Group" -> client: "Zeta Group")
    - Extract technician assignments (e.g., "assign it to admin" -> assigned_to: ["admin"])
    - When user says "make the client X" or "for client X", extract X as the client name
    - For updates, extract date expressions like "due today" -> due_date: "today"

    Common patterns:
    - "Create a new ticket VPN Install" -> ticket_name: "VPN Install"
    - "assign it to admin" -> assigned_to: ["admin"]
    - "make the client Zeta Group" -> client: "Zeta Group"
    - "for client Zeta Group" -> client: "Zeta Group"
    - "Update ticket Get That Money to be due today" -> ticket_name: "Get That Money", due_date: "today"
    - "due today" -> due_date: "today"
    - "due tomorrow" -> due_date: "tomorrow"

    The user's input: "{message}"

    Example response format:
    {{
        "ticket_name": "Get That Money",
        "new_ticket_name": null,
        "client": null,
        "assigned_to": null,
        "description": null,
        "end_date": null,
        "due_date": "today",
        "ticket_type": null,
        "status": null,
        "priority": null,
        "project": null
    }}

    Now, process the input and return the extracted fields in this exact JSON format.
    """

def extract_ticket_fields(message):
    print(f"Extracting fields from message: {message}")
    prompt = create_ticket_prompt(message)
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a precise data extraction assistant that returns valid JSON."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=200
        )
        response_content = response.choices[0].message.content.strip()
        print("Raw GPT response:", response_content)
        
        try:
            extracted_data = json.loads(response_content)
            print("Extracted data:", extracted_data)
            
            # Manual extraction of ticket information if GPT didn't capture it
            if not extracted_data.get("ticket_name"):
                message_lower = message.lower()
                # Extract ticket name from quotes or context
                quoted_names = re.findall(r'"([^"]+)"', message)
                if quoted_names:
                    extracted_data["ticket_name"] = quoted_names[0]
                    print(f"Manually extracted ticket name from quotes: {extracted_data['ticket_name']}")
                else:
                    # Look for ticket name after "ticket" keyword
                    words = message.split()
                    for i, word in enumerate(words):
                        if word.lower() == "ticket" and i + 1 < len(words):
                            potential_name = words[i + 1]
                            if potential_name and not potential_name.lower() in ["create", "add", "new", "make", "to", "it"]:
                                extracted_data["ticket_name"] = potential_name
                                print(f"Manually extracted ticket name: {extracted_data['ticket_name']}")
                                break
            
            # Manual extraction of client information
            if not extracted_data.get("client"):
                message_lower = message.lower()
                # Look for client patterns
                client_patterns = [
                    r'make the client\s+([^,\s]+(?:\s+[^,\s]+)*)',
                    r'for client\s+([^,\s]+(?:\s+[^,\s]+)*)',
                    r'client\s+([^,\s]+(?:\s+[^,\s]+)*)'
                ]
                for pattern in client_patterns:
                    match = re.search(pattern, message_lower)
                    if match:
                        extracted_data["client"] = match.group(1).title()
                        print(f"Manually extracted client: {extracted_data['client']}")
                        break
            
            # Manual extraction of assigned_to information
            if not extracted_data.get("assigned_to"):
                message_lower = message.lower()
                # Look for assignment patterns
                assignment_patterns = [
                    r'assign\s+(?:it\s+)?to\s+(\w+)',
                    r'assigned\s+to\s+(\w+)',
                    r'assign\s+(\w+)'
                ]
                for pattern in assignment_patterns:
                    match = re.search(pattern, message_lower)
                    if match:
                        technician = match.group(1)
                        extracted_data["assigned_to"] = [technician]
                        print(f"Manually extracted assigned_to: {extracted_data['assigned_to']}")
                        break
            
            return extracted_data
        except json.JSONDecodeError as e:
            print(f"JSON Parse Error: {e}")
            print(f"Response content that failed to parse: {response_content}")
            return {"response": f"Failed to parse input: {str(e)}", "error": True}
    except Exception as e:
        print(f"Extraction Error: {e}")
        return {"response": f"Failed to parse input: {str(e)}", "error": True}

def get_ticket_context(request=None):
    """
    Get ticket context from session or initialize default.
    If request is provided, use session-based context.
    Otherwise, fall back to ChatHistory-based context for backward compatibility.
    """
    if request and hasattr(request, 'session'):
        # Use session-based context
        context = request.session.get('ticket_context', {
            "ticket_name": None,
            "new_ticket_name": None,
            "client": None,
            "assigned_to": None,
            "description": None,
            "end_date": None,
            "due_date": None,
            "ticket_type": None,
            "status": None,
            "priority": None,
            "project": None
        })
        print("Session-based ticket context:", context)
        return context
    else:
        # Fallback to ChatHistory-based context
        context = {
            "ticket_name": None,
            "new_ticket_name": None,
            "client": None,
            "assigned_to": None,
            "description": None,
            "end_date": None,
            "due_date": None,
            "ticket_type": None,
            "status": None,
            "priority": None,
            "project": None
        }
        if ChatHistory.objects.exists():
            history_entries = ChatHistory.objects.order_by('timestamp')
            for entry in history_entries:
                if "ticket" in entry.user_input.lower() or "You're almost there! Please provide for ticket" in entry.bot_response:
                    try:
                        past_data = extract_ticket_fields(entry.user_input)
                        if not past_data.get("error"):
                            context = merge_context(context, past_data)
                    except Exception as e:
                        print(f"Error re-extracting context: {e}")
        print("ChatHistory-based ticket context:", context)
        return context

def merge_context(current_context, extracted_data):
    """
    Merge new data into existing context, preserving existing values unless explicitly overridden.
    Only update fields that are not None in extracted_data.
    """
    merged = current_context.copy()
    for key, value in extracted_data.items():
        if value is not None:
            merged[key] = value
    return merged

def save_ticket_context(request, context):
    """
    Save ticket context to session.
    """
    if request and hasattr(request, 'session'):
        request.session['ticket_context'] = context
        request.session.modified = True
        print("Saved ticket context to session:", context)

def clear_ticket_context(request):
    """
    Clear ticket context from session.
    """
    if request and hasattr(request, 'session'):
        if 'ticket_context' in request.session:
            del request.session['ticket_context']
            request.session.modified = True
            print("Cleared ticket context from session")

def validate_ticket_data(ticket_data):
    print("Validating ticket data:", ticket_data)
    missing_fields = []
    required_fields = ["ticket_name", "client", "assigned_to"]
    action_intent = ticket_data.get("action_intent", "CREATE")

    # For CREATE actions, we need all required fields
    if action_intent == "CREATE":
        for field in required_fields:
            if not ticket_data.get(field):
                missing_fields.append(field)

    # For UPDATE actions, we need at least ticket_name
    elif action_intent == "UPDATE":
        if not ticket_data.get("ticket_name"):
            missing_fields.append("ticket_name")

    if missing_fields:
        if action_intent == "CREATE":
            return {
                "response": f"Please provide the required information for ticket creation: {', '.join(missing_fields)}.",
                "error": True,
                "missing_fields": missing_fields,
                "current_data": ticket_data
            }
        else:
            return {
                "response": f"Please provide the ticket name for the update.",
                "error": True,
                "missing_fields": missing_fields,
                "current_data": ticket_data
            }

    # Validate email format if provided
    email = ticket_data.get("email")
    if email and not re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", email):
        return {
            "response": "Please provide a valid email address.",
            "error": True,
            "missing_fields": ["email"]
        }

    return {
        "success": "Ticket data is valid",
        "ticket_data": ticket_data,
        "response": "Data is valid",
        "error": False
    }

def get_ticket_in_context(ticket_name=None):
    if ticket_name:
        try:
            ticket = TicketList.objects.filter(name__iexact=ticket_name).first()
            return ticket
        except TicketList.MultipleObjectsReturned:
            return {
                "response": f"Multiple tickets named '{ticket_name}' found. Please use a unique ticket name.",
                "error": True
            }
    return None

def create_ticket(ticket_data, conversation_key):
    try:
        print(f"Creating ticket with data: {ticket_data}")
        
        # Look up the client by name
        client_name = ticket_data.get('client')
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
            return {"response": "Client is required for ticket creation.", "error": True}

        model_data = {
            'name': ticket_data['ticket_name'],
            'client': client,  # Use the ClientCompany instance
            'description': ticket_data.get('description'),
            'end_date': ticket_data.get('end_date'),
            'due_date': ticket_data.get('due_date'),
            'ticket_type': ticket_data.get('ticket_type'),
            'status': ticket_data.get('status') or 'New',  # Use 'New' if status is null/empty
            'priority': ticket_data.get('priority'),
            'project': ticket_data.get('project'),
        }
        
        print(f"Model data before work_type: {model_data}")

        # Handle work_type - try to get the default work type for this client
        try:
            work_type = client.work_type_rates.first()
            if work_type:
                model_data['work_type'] = work_type
                print(f"Using existing work_type: {work_type.name}")
            else:
                # Create a default work type for the client if none exists
                work_type = ClientWorkTypeRate.objects.create(
                    client=client,
                    name="Default",
                    rate=Decimal('50.00')
                )
                model_data['work_type'] = work_type
                print(f"Created new work_type: {work_type.name}")
        except Exception as e:
            print(f"Error handling work_type: {e}")
            return {
                "response": f"Failed to set work type for ticket: {str(e)}",
                "error": True
            }
        
        print(f"Final model data: {model_data}")

        assigned_to_usernames = ticket_data.get('assigned_to')
        if assigned_to_usernames:
            try:
                assigned_technicians = []
                for username in assigned_to_usernames:
                    technician = TechnicianUser.objects.get(auth_user__username__iexact=username)
                    assigned_technicians.append(technician)
                # Don't add assignment to model_data, we'll handle it after creation
            except TechnicianUser.DoesNotExist as e:
                return {
                    "response": f"Sorry, one or more technicians do not exist. Please assign valid technicians.",
                    "error": True
                }
        else:
            return {"response": "At least one assigned technician is required for the ticket.", "error": True}

        # Create the ticket first
        ticket = TicketList.objects.create(**model_data)
        
        # Then assign technicians using the ManyToManyField
        if assigned_to_usernames:
            ticket.assignment.set(assigned_technicians)
        
        print(f"Ticket created successfully: {ticket.identifier}")
        
        return {
            "response": f"Ticket '{ticket.name}' created successfully!",
            "ticket_id": ticket.identifier,
            "error": False
        }

    except IntegrityError as e:
        return {"response": f"Failed to create ticket: {str(e)}", "error": True}
    except Exception as e:
        return {"response": f"Failed to create ticket: {str(e)}", "error": True}

def update_ticket(ticket_data, conversation_key):
    print(f"Updating ticket with data: {ticket_data}")
    
    ticket = get_ticket_in_context(ticket_data.get("ticket_name"))
    if isinstance(ticket, dict) and ticket.get("error"):
        return ticket
    if not ticket:
        return {
            "response": "No matching ticket found for update. Please provide a valid ticket name.",
            "error": True
        }
    
    print(f"Found ticket: {ticket.name} (ID: {ticket.identifier})")
    
    updated_fields = {}
    new_name = ticket_data.get("new_ticket_name")
    if new_name and new_name != ticket.name:
        if TicketList.objects.filter(name__iexact=new_name).exists():
            return {
                "response": f"A ticket named '{new_name}' already exists. Choose a unique name.",
                "error": True
            }
        ticket.name = new_name
        updated_fields["name"] = new_name

    # Handle date fields with proper parsing
    if ticket_data.get('due_date'):
        from datetime import date
        due_date_str = ticket_data.get('due_date')
        if due_date_str.lower() == 'today':
            ticket.due_date = date.today()
            updated_fields['due_date'] = str(date.today())
        elif due_date_str.lower() == 'tomorrow':
            from datetime import timedelta
            ticket.due_date = date.today() + timedelta(days=1)
            updated_fields['due_date'] = str(date.today() + timedelta(days=1))
        else:
            try:
                # Try to parse as YYYY-MM-DD format
                ticket.due_date = date.fromisoformat(due_date_str)
                updated_fields['due_date'] = due_date_str
            except ValueError:
                return {
                    "response": f"Invalid date format for due_date: {due_date_str}. Please use YYYY-MM-DD format or 'today'/'tomorrow'.",
                    "error": True
                }

    if ticket_data.get('end_date'):
        from datetime import date
        end_date_str = ticket_data.get('end_date')
        if end_date_str.lower() == 'today':
            ticket.end_date = date.today()
            updated_fields['end_date'] = str(date.today())
        elif end_date_str.lower() == 'tomorrow':
            from datetime import timedelta
            ticket.end_date = date.today() + timedelta(days=1)
            updated_fields['end_date'] = str(date.today() + timedelta(days=1))
        else:
            try:
                ticket.end_date = date.fromisoformat(end_date_str)
                updated_fields['end_date'] = end_date_str
            except ValueError:
                return {
                    "response": f"Invalid date format for end_date: {end_date_str}. Please use YYYY-MM-DD format or 'today'/'tomorrow'.",
                    "error": True
                }

    # Handle assigned_to field (correctly named 'assignment')
    if ticket_data.get('assigned_to') is not None:
        try:
            assigned_technicians = []
            for username in ticket_data.get('assigned_to'):
                technician = TechnicianUser.objects.get(auth_user__username__iexact=username)
                assigned_technicians.append(technician)
            ticket.assignment.set(assigned_technicians)  # Use correct field name
            updated_fields['assigned_to'] = ticket_data.get('assigned_to')
        except TechnicianUser.DoesNotExist:
            return {
                "response": f"Sorry, one or more technicians do not exist. Please assign valid technicians.",
                "error": True
            }

    # Handle other fields
    for field, value in ticket_data.items():
        if field not in ('ticket_name', 'new_ticket_name', 'assigned_to', 'due_date', 'end_date') and value is not None:
            if hasattr(ticket, field):
                current_value = getattr(ticket, field)
                if current_value != value:
                    setattr(ticket, field, value)
                    updated_fields[field] = value
                    print(f"Updated field {field}: {current_value} -> {value}")

    print(f"Updated fields: {updated_fields}")

    if updated_fields:
        try:
            ticket.save()
            return {
                "response": f"Ticket '{ticket.name}' updated successfully!",
                "updated_fields": updated_fields,
                "error": False
            }
        except IntegrityError as e:
            return {"response": f"Failed to update ticket: {str(e)}", "error": True}
        except Exception as e:
            return {"response": f"Failed to update ticket: {str(e)}", "error": True}
    else:
        return {"response": "No changes detected, ticket remains the same.", "error": False}
