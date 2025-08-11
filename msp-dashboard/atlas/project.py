import json
from django.conf import settings
import openai
from django.db.models import Q
from accounts.models import TechnicianUser
from apps.models import ProjectList, ClientCompany
from atlas.models import ChatHistory
from django.db import IntegrityError
import re

openai.api_key = settings.OPENAI_API_KEY

def create_project_prompt(message):
    return f"""
    The user is requesting to create or update a project. Extract the following information from the user's input and return it as a valid JSON string:
    
    Required fields for creation:
    - name (string)
    - client (string, client company name)
    - assignment (list of technician usernames, e.g., ["john_doe", "ali"])

    Optional fields:
    - new_name (string, for updates)
    - description (string)
    - end_date (string, YYYY-MM-DD)
    - due_date (string, YYYY-MM-DD)
    - status (string, e.g., "open", "in_progress", "completed")
    - priority (string, e.g., "low", "medium", "high")

    Rules:
    - Return the response as a valid JSON string with double quotes around keys and string values
    - Set missing values to null (do not infer or guess values)
    - assignment should be an array of technician usernames or null if not provided
    - Dates should be in YYYY-MM-DD format or null
    - If the input suggests an update (e.g., "change name to"), extract the new name as "new_name"

    The user's input: "{message}"
    
    Example response format:
    {{
        "name": "Website Redesign",
        "new_name": null,
        "client": "ABC Corp",
        "assignment": ["john_doe", "ali"],
        "description": "Redesign company website",
        "end_date": "2025-06-01",
        "due_date": "2025-05-15",
        "status": "open",
        "priority": "high"
    }}

    Now, process the input and return the extracted fields in this exact JSON format.
    """

def extract_project_fields(message):
    prompt = create_project_prompt(message)
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
        extracted_data = json.loads(response_content)
        print("Extracted data:", extracted_data)
        return extracted_data
    except Exception as e:
        print(f"Extraction Error: {e}")
        return {"response": f"Failed to parse input: {str(e)}", "error": True}

def get_project_context(request=None):
    """
    Get project context from session or initialize default.
    If request is provided, use session-based context.
    Otherwise, fall back to ChatHistory-based context for backward compatibility.
    """
    if request and hasattr(request, 'session'):
        # Use session-based context
        context = request.session.get('project_context', {
            "name": None,
            "new_name": None,
            "client": None,
            "assignment": None,
            "description": None,
            "end_date": None,
            "due_date": None,
            "status": None,
            "priority": None
        })
        print("Session-based project context:", context)
        return context
    else:
        # Fallback to ChatHistory-based context
        context = {
            "name": None,
            "new_name": None,
            "client": None,
            "assignment": None,
            "description": None,
            "end_date": None,
            "due_date": None,
            "status": None,
            "priority": None
        }
        if ChatHistory.objects.exists():
            history_entries = ChatHistory.objects.order_by('timestamp')
            for entry in history_entries:
                if "project" in entry.user_input.lower() or "You're almost there! Please provide for project" in entry.bot_response:
                    try:
                        past_data = extract_project_fields(entry.user_input)
                        if not past_data.get("error"):
                            context = merge_project_context(context, past_data)
                    except Exception as e:
                        print(f"Error re-extracting context: {e}")
        print("ChatHistory-based project context:", context)
        return context

def merge_project_context(current_context, extracted_data):
    """
    Merge new data into existing context, preserving existing values unless explicitly overridden.
    Only update fields that are not None in extracted_data.
    """
    merged = current_context.copy()
    for key, value in extracted_data.items():
        if value is not None:
            merged[key] = value
    return merged

def save_project_context(request, context):
    """
    Save project context to session.
    """
    if request and hasattr(request, 'session'):
        request.session['project_context'] = context
        request.session.modified = True
        print("Saved project context to session:", context)

def clear_project_context(request):
    """
    Clear project context from session.
    """
    if request and hasattr(request, 'session'):
        if 'project_context' in request.session:
            del request.session['project_context']
            request.session.modified = True
            print("Cleared project context from session")

def validate_project_data(project_data):
    print("Validating project data:", project_data)
    missing_fields = []
    required_fields = ["name", "client", "assignment"]
    action_intent = project_data.get("action_intent", "CREATE")

    # For CREATE actions, we need all required fields
    if action_intent == "CREATE":
        for field in required_fields:
            if not project_data.get(field):
                missing_fields.append(field)

    # For UPDATE actions, we need at least name
    elif action_intent == "UPDATE":
        if not project_data.get("name"):
            missing_fields.append("name")

    if missing_fields:
        if action_intent == "CREATE":
            return {
                "response": f"Please provide the required information for project creation: {', '.join(missing_fields)}.",
                "error": True,
                "missing_fields": missing_fields,
                "current_data": project_data
            }
        else:
            return {
                "response": f"Please provide the project name for the update.",
                "error": True,
                "missing_fields": missing_fields,
                "current_data": project_data
            }

    # Validate email format if provided
    email = project_data.get("email")
    if email and not re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", email):
        return {
            "response": "Please provide a valid email address.",
            "error": True,
            "missing_fields": ["email"]
        }

    return {
        "success": "Project data is valid",
        "project_data": project_data,
        "response": "Data is valid",
        "error": False
    }

def get_project_in_context(project_name=None):
    if project_name:
        try:
            project = ProjectList.objects.filter(name__iexact=project_name).first()
            return project
        except ProjectList.MultipleObjectsReturned:
            return {
                "response": f"Multiple projects named '{project_name}' found. Please use a unique project name.",
                "error": True
            }
    return None

def create_project(project_data, conversation_key):
    try:
        model_data = {
            'name': project_data['name'],
            'client': project_data['client'],
            'description': project_data.get('description'),
            'end_date': project_data.get('end_date'),
            'due_date': project_data.get('due_date'),
            'status': project_data.get('status'),
            'priority': project_data.get('priority'),
        }

        assignment_usernames = project_data.get('assignment')
        if assignment_usernames:
            try:
                assigned_technicians = []
                for username in assignment_usernames:
                    technician = TechnicianUser.objects.get(auth_user__username__iexact=username)
                    assigned_technicians.append(technician)
                model_data['assignment'] = assigned_technicians
            except TechnicianUser.DoesNotExist as e:
                return {
                    "response": f"Sorry, one or more technicians do not exist. Please assign valid technicians.",
                    "error": True
                }
        else:
            return {"response": "At least one assigned technician is required for the project.", "error": True}

        project = ProjectList.objects.create(**model_data)
        return {
            "response": f"Project '{project.name}' created successfully!",
            "project_id": project.id,
            "error": False
        }

    except IntegrityError as e:
        return {"response": f"Failed to create project: {str(e)}", "error": True}
    except Exception as e:
        return {"response": f"Failed to create project: {str(e)}", "error": True}

def update_project(project_data, conversation_key):
    project = get_project_in_context(project_data.get("name"))
    if isinstance(project, dict) and project.get("error"):
        return project
    if not project:
        return {
            "response": "No matching project found for update. Please provide a valid project name.",
            "error": True
        }
    
    updated_fields = {}
    new_name = project_data.get("new_name")
    if new_name and new_name != project.name:
        if ProjectList.objects.filter(name__iexact=new_name).exists():
            return {
                "response": f"A project named '{new_name}' already exists. Choose a unique name.",
                "error": True
            }
        project.name = new_name
        updated_fields["name"] = new_name

    for field, value in project_data.items():
        if field == 'assignment' and value is not None:
            try:
                assigned_technicians = []
                for username in value:
                    technician = TechnicianUser.objects.get(auth_user__username__iexact=username)
                    assigned_technicians.append(technician)
                project.assignment.set(assigned_technicians)
                updated_fields['assignment'] = value
            except TechnicianUser.DoesNotExist:
                return {
                    "response": f"Sorry, one or more technicians do not exist. Please assign valid technicians.",
                    "error": True
                }
        elif field not in ('name', 'new_name') and value is not None and getattr(project, field, None) != value:
            setattr(project, field, value)
            updated_fields[field] = value

    if updated_fields:
        try:
            project.save()
            return {
                "response": f"Project '{project.name}' updated successfully!",
                "updated_fields": updated_fields,
                "error": False
            }
        except IntegrityError as e:
            return {"response": f"Failed to update project: {str(e)}", "error": True}
        except Exception as e:
            return {"response": f"Failed to update project: {str(e)}", "error": True}
    else:
        return {"response": "No changes detected, project remains the same.", "error": False}
