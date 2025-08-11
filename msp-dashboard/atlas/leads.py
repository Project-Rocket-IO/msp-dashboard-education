from django.db.models import Field
from accounts.models import TechnicianUser
from apps.models import LeadCompany
from atlas.models import ChatHistory
import json
from django.conf import settings
import openai
import re
from decimal import Decimal

openai.api_key = settings.OPENAI_API_KEY

def create_lead_prompt(message):
    return f"""
    The user is requesting to create or update a lead. Extract the following information from the user's input and return it as a valid JSON string:

    Required fields for creation:
    - name (string, the lead company name)
    - contact_first (string, contact's first name)
    - contact_last (string, contact's last name)
    - email (string, contact's email address)

    Optional fields:
    - score (integer, lead score)
    - address_1 (string, primary address)
    - address_2 (string, secondary address)
    - zip (string, zip/postal code)
    - city (string, city)
    - state (string, state/province)
    - country (string, country)
    - timezone (string, timezone)
    - website (string, company website URL)
    - phone (string, phone number)
    - industry (string, industry type)
    - fax (string, fax number)

    Rules:
    - Return the response as a valid JSON string with double quotes around keys and string values
    - Set missing values to null (do not infer or guess values)
    - Email must be a valid email format
    - Phone and fax numbers should include country codes if provided
    - Industry should match one of the available industry types
    - If the user specifies "with a name X" or "to name X", set new_name to X for updates
    - Extract lead names from quotes if present (e.g., "TechCorp Inc" -> name: "TechCorp Inc")
    - Extract contact information in various formats:
      * "first name: John" -> contact_first: "John"
      * "last name: Smith" -> contact_last: "Smith"
      * "email=john@techcorp.com" -> email: "john@techcorp.com"
      * "contact_first = John" -> contact_first: "John"
      * "contact_last = Smith" -> contact_last: "Smith"

    Common patterns:
    - "Create a new lead TechCorp Inc" -> name: "TechCorp Inc"
    - "first name: John" -> contact_first: "John"
    - "last name: Smith" -> contact_last: "Smith"
    - "email=john@techcorp.com" -> email: "john@techcorp.com"
    - "score=85" -> score: 85
    - "address=123 Main St" -> address_1: "123 Main St"
    - "city=New York" -> city: "New York"
    - "state=NY" -> state: "NY"
    - "zip=10001" -> zip: "10001"
    - "country=United States" -> country: "United States"
    - "timezone=EST" -> timezone: "EST"
    - "website=https://techcorp.com" -> website: "https://techcorp.com"
    - "phone=+1-555-123-4567" -> phone: "+1-555-123-4567"
    - "industry=Technology" -> industry: "Technology"
    - "fax=+1-555-123-4568" -> fax: "+1-555-123-4568"

    The user's input: "{message}"

    Example response format:
    {{
        "name": "TechCorp Inc",
        "contact_first": "John",
        "contact_last": "Smith",
        "email": "john@techcorp.com",
        "score": null,
        "address_1": null,
        "address_2": null,
        "zip": null,
        "city": null,
        "state": null,
        "country": null,
        "timezone": null,
        "website": null,
        "phone": null,
        "industry": null,
        "fax": null
    }}

    Now, process the input and return the extracted fields in this exact JSON format.
    """

def extract_lead_fields(message):
    try:
        prompt = create_lead_prompt(message)
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
            
            # Manual extraction of lead information if GPT didn't capture it
            message_lower = message.lower()
            if not extracted_data.get("name"):
                # Extract lead name from quotes or context
                quoted_names = re.findall(r'"([^"]+)"', message)
                if quoted_names:
                    extracted_data["name"] = quoted_names[0]
                    print(f"Manually extracted lead name from quotes: {extracted_data['name']}")
                else:
                    # Look for lead name after "lead" keyword
                    words = message.split()
                    for i, word in enumerate(words):
                        if word.lower() == "lead" and i + 1 < len(words):
                            potential_name = words[i + 1]
                            if potential_name and not potential_name.lower() in ["create", "add", "new", "make", "to", "it", "name"]:
                                extracted_data["name"] = potential_name
                                print(f"Manually extracted lead name: {extracted_data['name']}")
                                break
            
            # Handle "Update Lead name X to Y" pattern
            if "update" in message_lower and "name" in message_lower and "to" in message_lower:
                # Extract the current name and new name
                name_pattern = r'name\s+([^\s]+)\s+to\s+([^\s]+)'
                match = re.search(name_pattern, message_lower)
                if match:
                    current_name = match.group(1)
                    new_name = match.group(2)
                    extracted_data["name"] = current_name.title()
                    extracted_data["new_name"] = new_name.title()
                    print(f"Extracted update pattern - current: {extracted_data['name']}, new: {extracted_data['new_name']}")
            
            # Manual extraction of contact information
            if not extracted_data.get("contact_first") or not extracted_data.get("contact_last"):
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
            
            # Manual extraction of email
            if not extracted_data.get("email"):
                email_patterns = [
                    r'email\s*[=:]\s*([^\s,]+)',
                    r'email\s*=\s*([^\s,]+)',
                    r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{{2,}})'
                ]
                for pattern in email_patterns:
                    match = re.search(pattern, message_lower)
                    if match:
                        extracted_data["email"] = match.group(1)
                        print(f"Manually extracted email: {extracted_data['email']}")
                        break
            
            return extracted_data
        except json.JSONDecodeError as e:
            print(f"JSON Parse Error: {e}")
            print(f"Response content that failed to parse: {response_content}")
            return {"response": f"Failed to parse input: {str(e)}", "error": True}
    except Exception as e:
        print(f"Error in extract_lead_fields: {e}")
        return {"response": f"Failed to extract lead data: {str(e)}", "error": True}

def get_lead_context(request=None):
    if request and hasattr(request, 'session'):
        return request.session.get('lead_context', {})
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

def merge_lead_context(current_context, extracted_data):
    """
    Merge new data with existing context, only updating non-None values
    """
    merged = current_context.copy()
    for key, value in extracted_data.items():
        if value is not None:
            merged[key] = value
    return merged

def save_lead_context(request, context):
    if request and hasattr(request, 'session'):
        request.session['lead_context'] = context
        request.session.modified = True

def clear_lead_context(request):
    if request and hasattr(request, 'session'):
        if 'lead_context' in request.session:
            del request.session['lead_context']
            request.session.modified = True

def validate_lead_data(lead_data):
    # Get action_intent from the data if available, otherwise infer from new_name
    action_intent = lead_data.get('action_intent')
    if not action_intent:
        action_intent = 'UPDATE' if lead_data.get('new_name') else 'CREATE'
    
    required_fields = {
        'CREATE': ['name', 'contact_first', 'contact_last', 'email'],
        'UPDATE': ['name', 'contact_first', 'contact_last', 'email']
    }
    
    missing_fields = []
    db_lead = None
    if action_intent == 'UPDATE' and lead_data.get('name'):
        from apps.models import LeadCompany
        db_lead = LeadCompany.objects.filter(name__iexact=lead_data['name']).first()
    
    for field in required_fields[action_intent]:
        if not lead_data.get(field):
            # For UPDATE, try to get from DB
            if action_intent == 'UPDATE' and db_lead and hasattr(db_lead, field):
                value = getattr(db_lead, field, None)
                if value:
                    lead_data[field] = value
                else:
                    missing_fields.append(field)
            else:
                missing_fields.append(field)
    
    if missing_fields:
        field_names = ', '.join(missing_fields)
        if action_intent == 'CREATE':
            return {
                "response": f"Please provide the following required information: {field_names}. For example: 'Create a new lead TechCorp Inc with first name: John, last name: Smith, email: john@techcorp.com'",
                "error": True
            }
        else:
            return {
                "response": f"Please provide the following required information to update: {field_names}.",
                "error": True
            }
    
    # Validate email format only for CREATE or if email is being updated
    if lead_data.get('email') and (action_intent == 'CREATE' or lead_data.get('email')):
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, lead_data['email']):
            return {
                "response": "Please provide a valid email address.",
                "error": True
            }
    
    return {"error": False}

def get_lead_in_context(lead_name=None):
    try:
        if lead_name:
            lead = LeadCompany.objects.filter(name__iexact=lead_name).first()
        else:
            # Get the most recent lead
            lead = LeadCompany.objects.order_by('-date_added').first()
        
        if not lead:
            return None
        
        return lead
    except LeadCompany.MultipleObjectsReturned:
        return None

def create_lead(lead_data, conversation_key):
    try:
        print(f"Creating lead with data: {lead_data}")
        
        # Check if lead with same email already exists
        if lead_data.get('email'):
            existing_lead = LeadCompany.objects.filter(email__iexact=lead_data['email']).first()
            if existing_lead:
                return {
                    "response": f"A lead with email '{lead_data['email']}' already exists.",
                    "error": True
                }
        
        model_data = {
            'name': lead_data['name'],
            'contact_first': lead_data['contact_first'],
            'contact_last': lead_data['contact_last'],
            'email': lead_data['email'],
            'score': lead_data.get('score'),
            'address_1': lead_data.get('address_1'),
            'address_2': lead_data.get('address_2'),
            'zip': lead_data.get('zip'),
            'city': lead_data.get('city'),
            'state': lead_data.get('state'),
            'country': lead_data.get('country'),
            'timezone': lead_data.get('timezone'),
            'website': lead_data.get('website'),
            'phone': lead_data.get('phone'),
            'industry': lead_data.get('industry'),
            'fax': lead_data.get('fax'),
        }
        
        print(f"Model data: {model_data}")
        
        lead = LeadCompany.objects.create(**model_data)
        
        print(f"Lead created successfully: {lead.name}")
        
        return {
            "response": f"Lead '{lead.name}' created successfully!",
            "lead_id": lead.id,
            "error": False
        }
        
    except Exception as e:
        print(f"Error creating lead: {e}")
        return {"response": f"Failed to create lead: {str(e)}", "error": True}

def update_lead(lead_data, conversation_key):
    print(f"Updating lead with data: {lead_data}")
    
    lead = get_lead_in_context(lead_data.get("name"))
    if not lead:
        return {
            "response": "No matching lead found for update. Please provide a valid lead name.",
            "error": True
        }
    
    print(f"Found lead: {lead.name} (ID: {lead.id})")
    
    updated_fields = {}
    new_name = lead_data.get("new_name")
    if new_name and new_name != lead.name:
        if LeadCompany.objects.filter(name__iexact=new_name).exclude(id=lead.id).exists():
            return {
                "response": f"A lead named '{new_name}' already exists. Choose a unique name.",
                "error": True
            }
        lead.name = new_name
        updated_fields["name"] = new_name

    # Handle other fields
    for field, value in lead_data.items():
        if field not in ('name', 'new_name') and value is not None:
            if hasattr(lead, field):
                current_value = getattr(lead, field)
                if current_value != value:
                    setattr(lead, field, value)
                    updated_fields[field] = value
                    print(f"Updated field {field}: {current_value} -> {value}")

    print(f"Updated fields: {updated_fields}")

    if updated_fields:
        try:
            lead.save()
            return {
                "response": f"Lead '{lead.name}' updated successfully!",
                "updated_fields": updated_fields,
                "error": False
            }
        except Exception as e:
            return {"response": f"Failed to update lead: {str(e)}", "error": True}
    else:
        return {"response": "No changes detected, lead remains the same.", "error": False} 