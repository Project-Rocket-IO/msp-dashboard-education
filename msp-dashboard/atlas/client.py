from django.db.models import Field
from django.db import IntegrityError
from accounts.models import TechnicianUser
from apps.models import ClientCompany
from atlas.models import ChatHistory
import json
from django.conf import settings
import openai
import re

openai.api_key = settings.OPENAI_API_KEY

def create_client_prompt(message):
    return f"""
    The user is requesting to create or update a client company. Extract the following information from the user's input and return it as a valid JSON string:

    Required fields:
    - name (the current name of the client to create or update)

    Optional fields (set to null if not provided):
    - contact_first
    - contact_last
    - email
    - main_tech
    - new_name (new name for the client if updating, e.g., "NewCo" in "update client TechNova with name NewCo")
    - industry
    - website

    Rules:
    - Return the response as a valid JSON string with double quotes around keys and string values
    - Set missing values to null (do not infer or guess values)
    - main_tech should be a technician username (e.g., "john_doe")
    - If the user specifies "with a name X" or "to name X", set new_name to X for updates
    - name is the current client identifier; new_name is the desired name
    - email must be a valid email format if provided
    - Extract the client name from quotes if present (e.g., "Alpha Group" -> name: "Alpha Group")
    - If no quotes, extract the name from the context (e.g., "create client TechCorp" -> name: "TechCorp")
    - IMPORTANT: Do NOT extract contact information (first_name, last_name) as client names
    - Only extract client names when they are explicitly mentioned as client/company names
    - If the message contains contact information like "first_name: steven", do NOT set name to "steven"
    
    Contact information extraction patterns (in order of priority):
    - "first name: James" -> contact_first: "James"
    - "first_name: James" -> contact_first: "James"
    - "firstname: James" -> contact_first: "James"
    - "first name = James" -> contact_first: "James"
    - "first_name = James" -> contact_first: "James"
    - "firstname = James" -> contact_first: "James"
    - "last name: Phil" -> contact_last: "Phil"
    - "last_name: Phil" -> contact_last: "Phil"
    - "lastname: Phil" -> contact_last: "Phil"
    - "last name = Phil" -> contact_last: "Phil"
    - "last_name = Phil" -> contact_last: "Phil"
    - "lastname = Phil" -> contact_last: "Phil"
    - "email=omega@omega.com" -> email: "omega@omega.com"
    - "email = omega@omega.com" -> email: "omega@omega.com"
    - "technician=admin" -> main_tech: "admin"
    - "technician = admin" -> main_tech: "admin"
    - "main_tech = admin" -> main_tech: "admin"
    - "assign to admin" -> main_tech: "admin"
    - "contact_first = James" -> contact_first: "James"
    - "contact_last = Phil" -> contact_last: "Phil"

    The user's input: "{message}"

    Example response format:
    {{
        "name": "Omega Group",
        "new_name": null,
        "contact_first": null,
        "contact_last": null,
        "email": null,
        "main_tech": null,
        "industry": null,
        "website": null
    }}

    Now, process the input and return the extracted fields in this exact JSON format.
    """

def extract_client_fields(message):
    print(f"Extracting fields from message: {message}")
    prompt = create_client_prompt(message)
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a precise data extraction assistant that returns valid JSON. Only extract client names when they are explicitly mentioned as client/company names, not when they are contact information like first_name or last_name."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=200
        )
        response_content = response.choices[0].message.content.strip()
        print("Raw GPT response:", response_content)
        
        try:
            extracted_data = json.loads(response_content)
            print("Extracted data:", extracted_data)
            
            # Only extract client name if it's not already set and the message contains explicit client creation language
            if not extracted_data.get("name"):
                # Check if this message is about creating a new client (not providing contact info)
                message_lower = message.lower()
                if any(keyword in message_lower for keyword in ["create client", "new client", "make client", "add client"]):
                    # Try to extract name from the message if GPT didn't get it
                    quoted_names = re.findall(r'"([^"]+)"', message)
                    if quoted_names:
                        extracted_data["name"] = quoted_names[0]
                        print(f"Extracted name from quotes: {extracted_data['name']}")
                    else:
                        # Look for potential company names in the message
                        words = message.split()
                        for i, word in enumerate(words):
                            if word.lower() in ["client", "company", "group", "corp", "inc", "llc"] and i + 1 < len(words):
                                potential_name = words[i + 1]
                                if potential_name and not potential_name.lower() in ["create", "add", "new", "make"]:
                                    extracted_data["name"] = potential_name
                                    print(f"Extracted potential name: {extracted_data['name']}")
                                    break
                else:
                    # This appears to be a follow-up message with contact info, don't extract client name
                    print("Message appears to be contact info, not extracting client name")
            
            # Manual extraction of contact information if GPT didn't capture it
            if not extracted_data.get("contact_first") or not extracted_data.get("contact_last"):
                message_lower = message.lower()
                
                # Extract first name patterns
                if not extracted_data.get("contact_first"):
                    first_name_patterns = [
                        r'first\s*name\s*[=:]\s*(\w+)',
                        r'first_name\s*[=:]\s*(\w+)',
                        r'firstname\s*[=:]\s*(\w+)',
                        r'contact_first\s*[=:]\s*(\w+)'
                    ]
                    for pattern in first_name_patterns:
                        match = re.search(pattern, message_lower)
                        if match:
                            extracted_data["contact_first"] = match.group(1).title()
                            print(f"Manually extracted first name: {extracted_data['contact_first']}")
                            break
                
                # Extract last name patterns
                if not extracted_data.get("contact_last"):
                    last_name_patterns = [
                        r'last\s*name\s*[=:]\s*(\w+)',
                        r'last_name\s*[=:]\s*(\w+)',
                        r'lastname\s*[=:]\s*(\w+)',
                        r'contact_last\s*[=:]\s*(\w+)'
                    ]
                    for pattern in last_name_patterns:
                        match = re.search(pattern, message_lower)
                        if match:
                            extracted_data["contact_last"] = match.group(1).title()
                            print(f"Manually extracted last name: {extracted_data['contact_last']}")
                            break
            
            return extracted_data
        except json.JSONDecodeError as e:
            print(f"JSON Parse Error: {e}")
            print(f"Response content that failed to parse: {response_content}")
            # Fallback: try to extract name manually only if it's a client creation message
            message_lower = message.lower()
            if any(keyword in message_lower for keyword in ["create client", "new client", "make client", "add client"]):
                quoted_names = re.findall(r'"([^"]+)"', message)
                if quoted_names:
                    return {
                        "name": quoted_names[0],
                        "new_name": None,
                        "contact_first": None,
                        "contact_last": None,
                        "email": None,
                        "main_tech": None,
                        "industry": None,
                        "website": None
                    }
            return {"response": f"Failed to parse input: {str(e)}", "error": True}
    except Exception as e:
        print(f"OpenAI API Error: {e}")
        # Fallback: try to extract name manually only if it's a client creation message
        message_lower = message.lower()
        if any(keyword in message_lower for keyword in ["create client", "new client", "make client", "add client"]):
            quoted_names = re.findall(r'"([^"]+)"', message)
            if quoted_names:
                return {
                    "name": quoted_names[0],
                    "new_name": None,
                    "contact_first": None,
                    "contact_last": None,
                    "email": None,
                    "main_tech": None,
                    "industry": None,
                    "website": None
                }
        return {"response": f"Failed to extract client data: {str(e)}", "error": True}

def merge_client_context(existing_context, new_data):
    """
    Merge new data into existing context, preserving existing values unless explicitly overridden.
    Only update fields that are not None in new_data.
    """
    merged = existing_context.copy()
    for key, value in new_data.items():
        if value is not None:
            merged[key] = value
    return merged

def get_client_context(request=None):
    """
    Get client context from session or initialize default.
    If request is provided, use session-based context.
    Otherwise, fall back to ChatHistory-based context for backward compatibility.
    """
    if request and hasattr(request, 'session'):
        # Use session-based context
        context = request.session.get('client_context', {
            "name": None,
            "new_name": None,
            "contact_first": None,
            "contact_last": None,
            "email": None,
            "main_tech": None,
            "industry": None,
            "website": None
        })
        print("Session-based client context:", context)
        return context
    else:
        # Fallback to ChatHistory-based context
        context = {
            "name": None,
            "new_name": None,
            "contact_first": None,
            "contact_last": None,
            "email": None,
            "main_tech": None,
            "industry": None,
            "website": None
        }
        history = ChatHistory.objects.all().order_by('-timestamp')[:10]
        print("ChatHistory for context:", [(h.user_input, h.bot_response) for h in history])
        for entry in history:
            try:
                extracted = extract_client_fields(entry.user_input)
                if not isinstance(extracted, dict) or "error" in extracted:
                    continue
                context = merge_client_context(context, extracted)
            except Exception as e:
                print(f"Error extracting context from {entry.user_input}: {e}")
                continue
        print("ChatHistory-based client context:", context)
        return context

def save_client_context(request, context):
    """
    Save client context to session.
    """
    if request and hasattr(request, 'session'):
        request.session['client_context'] = context
        request.session.modified = True
        print("Saved client context to session:", context)

def clear_client_context(request):
    """
    Clear client context from session.
    """
    if request and hasattr(request, 'session'):
        if 'client_context' in request.session:
            del request.session['client_context']
            request.session.modified = True
            print("Cleared client context from session")

def validate_client_data(extracted_data):
    print("Validating data:", extracted_data)
    missing_fields = []
    required_fields = ["name"]
    action_intent = extracted_data.get("action_intent", "CREATE")

    # For CREATE actions, we need additional fields, but we'll guide the user step by step
    if action_intent == "CREATE":
        # Check if we have the basic required fields for creation
        creation_required = ["contact_first", "contact_last", "email", "main_tech"]
        for field in creation_required:
            if not extracted_data.get(field):
                missing_fields.append(field)

    for field in required_fields:
        if not extracted_data.get(field):
            missing_fields.append(field)

    email = extracted_data.get("email")
    if email and not re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", email):
        return {
            "response": "Please provide a valid email address.",
            "error": True,
            "missing_fields": ["email"]
        }

    if missing_fields:
        # Provide a more helpful response that guides the user
        if action_intent == "CREATE" and len(missing_fields) == len(["contact_first", "contact_last", "email", "main_tech"]):
            return {
                "response": f"Great! I'll help you create client '{extracted_data.get('name')}'. Please provide the contact information: first name, last name, email, and assign a technician.",
                "error": True,
                "missing_fields": missing_fields,
                "current_data": extracted_data
            }
        elif action_intent == "CREATE":
            return {
                "response": f"Please provide the remaining information for client '{extracted_data.get('name')}': {', '.join(missing_fields)}.",
                "error": True,
                "missing_fields": missing_fields,
                "current_data": extracted_data
            }
        else:
            return {
                "response": f"You're almost there! Please provide for client: {', '.join(missing_fields)}.",
                "error": True,
                "missing_fields": missing_fields
            }
    return {
        "success": "Client data is valid",
        "client_data": extracted_data,
        "response": "Data is valid",
        "error": False
    }

def get_client_in_context(client_name=None):
    if client_name:
        try:
            client = ClientCompany.objects.filter(name__iexact=client_name).first()
            return client
        except ClientCompany.MultipleObjectsReturned:
            return {
                "response": f"Multiple clients named '{client_name}' found. Please use a unique client name or email.",
                "error": True
            }
    return None

def create_client(client_data, conversation_key):
    try:
        print(f"Creating client with data: {client_data}")
        
        # Validate required fields
        required_fields = ['name', 'contact_first', 'contact_last', 'email']
        for field in required_fields:
            if not client_data.get(field):
                return {
                    "response": f"Missing required field: {field}",
                    "error": True
                }
        
        model_data = {
            'name': client_data['name'],
            'contact_first': client_data['contact_first'],
            'contact_last': client_data['contact_last'],
            'email': client_data['email'],
            'industry': client_data.get('industry'),
            'website': client_data.get('website'),
        }
        
        print(f"Model data prepared: {model_data}")

        main_tech_username = client_data.get('main_tech')
        if main_tech_username:
            try:
                main_tech = TechnicianUser.objects.get(auth_user__username__iexact=main_tech_username)
                model_data['main_tech'] = main_tech
                print(f"Found technician: {main_tech}")
            except TechnicianUser.DoesNotExist:
                return {
                    "response": f"Sorry, technician '{main_tech_username}' does not exist. Please assign a valid technician.",
                    "error": True
                }
        else:
            return {"response": "Main technician is required for the client.", "error": True}

        print(f"Final model data: {model_data}")
        client = ClientCompany.objects.create(**model_data)
        print(f"Client created successfully: {client.id}")
        
        return {
            "response": f"Client '{client.name}' created successfully!",
            "client_id": client.id,
            "error": False
        }

    except IntegrityError as e:
        print(f"IntegrityError: {e}")
        if "unique constraint" in str(e) and "email" in str(e):
            return {
                "response": f"Failed to create client: Email '{client_data['email']}' already exists. Please use a unique email.",
                "error": True
            }
        return {"response": f"Failed to create client: {str(e)}", "error": True}
    except Exception as e:
        print(f"Exception in create_client: {e}")
        import traceback
        traceback.print_exc()
        return {"response": f"Failed to create client: {str(e)}", "error": True}

def update_client(client_data, conversation_key):
    client = get_client_in_context(client_data.get("name"))
    if isinstance(client, dict) and client.get("error"):
        return client
    if not client:
        return {
            "response": "No matching client found for update. Please provide a valid client name.",
            "error": True
        }
    updated_fields = {}
    new_name = client_data.get("new_name")
    if new_name and new_name != client.name:
        if ClientCompany.objects.filter(name__iexact=new_name).exists():
            return {
                "response": f"A client named '{new_name}' already exists. Choose a unique name.",
                "error": True
            }
        client.name = new_name
        updated_fields["name"] = new_name

    for field, value in client_data.items():
        if field == 'main_tech' and value is not None:
            try:
                main_tech = TechnicianUser.objects.get(auth_user__username__iexact=value)
                if client.main_tech != main_tech:
                    client.main_tech = main_tech
                    updated_fields['main_tech'] = value
            except TechnicianUser.DoesNotExist:
                return {
                    "response": f"Sorry, technician '{value}' does not exist. Please assign a valid technician.",
                    "error": True
                }
        elif field == 'email' and value is not None and value != client.email:
            if ClientCompany.objects.filter(email=value).exclude(id=client.id).exists():
                return {
                    "response": f"Failed to update client: Email '{value}' is already in use by another client.",
                    "error": True
                }
            client.email = value
            updated_fields['email'] = value
        elif field not in ('name', 'new_name') and value is not None and getattr(client, field, None) != value:
            setattr(client, field, value)
            updated_fields[field] = value

    if updated_fields:
        try:
            client.save()
            return {
                "response": f"Client '{client.name}' updated successfully!",
                "updated_fields": updated_fields,
                "error": False
            }
        except IntegrityError as e:
            if "unique constraint" in str(e) and "email" in str(e):
                return {
                    "response": f"Failed to update client: Email '{client_data.get('email')}' is already in use by another client.",
                    "error": True
                }
            return {"response": f"Failed to update client: {str(e)}", "error": True}
        except Exception as e:
            return {"response": f"Failed to update client: {str(e)}", "error": True}
    else:
        return {"response": "No changes detected, client remains the same.", "error": False}
