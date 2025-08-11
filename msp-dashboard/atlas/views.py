from django.conf import settings
import openai
import spacy
import json
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from atlas.state import ACTIVE_INTENTS
from time import time
from django.db import transaction
from accounts.models import TechnicianUser
from apps.models import TicketList, ClientCompany, ProjectList, LeadCompany, SalesRequests
from atlas.models import ChatHistory
from atlas.tickets import extract_ticket_fields, merge_context, validate_ticket_data, create_ticket, update_ticket, get_ticket_in_context, get_ticket_context, save_ticket_context, clear_ticket_context
from atlas.client import extract_client_fields, merge_client_context, validate_client_data, create_client, update_client, get_client_in_context, get_client_context, save_client_context, clear_client_context
from atlas.project import extract_project_fields, merge_project_context, validate_project_data, create_project, update_project, get_project_in_context, get_project_context, save_project_context, clear_project_context
from atlas.leads import extract_lead_fields, merge_lead_context, validate_lead_data, create_lead, update_lead, get_lead_in_context, get_lead_context, save_lead_context, clear_lead_context
from atlas.sales import extract_sales_fields, merge_sales_context, validate_sales_data, create_sales, update_sales, get_sales_in_context, get_sales_context, save_sales_context, clear_sales_context


openai.api_key = settings.OPENAI_API_KEY
nlp = spacy.load("en_core_web_sm")

create_keywords = {"create", "add", "new", "register", "open", "make"}
update_keywords = {"update", "modify", "edit", "change", "adjust"}
ticket_keywords = {"ticket", "issue", "task", "bug", "problem"}
client_keywords = {"client", "company", "customer", "organization", "business"}
project_keywords = {"project", "proj", "initiative", "work"}
lead_keywords = {"lead", "prospect", "potential"}
sales_keywords = {"sale", "deal", "opportunity", "revenue"}

def classify_intent(text):
    text_lower = text.lower()
    print(f"Classifying intent for: '{text}'")
    
    action_intent = "UNKNOWN"
    model_intent = None
    cancel_keywords = {"cancel", "stop", "abort", "end"}

    # Check for cancel keywords
    if any(keyword in text_lower for keyword in cancel_keywords):
        print("Detected CANCEL intent")
        return "CANCEL", None

    # Check for action keywords with priority for UPDATE when context suggests it
    # First check for explicit update patterns
    update_patterns = [
        "change", "update", "modify", "edit", "adjust",
        "to be valued at", "to be", "change to", "update to"
    ]
    
    for pattern in update_patterns:
        if pattern in text_lower:
            action_intent = "UPDATE"
            print(f"Detected UPDATE action with pattern: {pattern}")
            break
    
    # If no update pattern found, check for create keywords
    if action_intent == "UNKNOWN":
        for keyword in create_keywords:
            if keyword in text_lower:
                action_intent = "CREATE"
                print(f"Detected CREATE action with keyword: {keyword}")
                break
        
        if action_intent == "UNKNOWN":
            for keyword in update_keywords:
                if keyword in text_lower:
                    action_intent = "UPDATE"
                    print(f"Detected UPDATE action with keyword: {keyword}")
                    break

    # Check for model keywords with improved detection
    # For CREATE actions, prioritize explicit ticket creation when "ticket" is mentioned
    if action_intent == "CREATE":
        # Check for explicit ticket creation patterns first
        ticket_creation_patterns = [
            "create a new ticket",
            "create new ticket", 
            "make a new ticket",
            "make new ticket",
            "add a new ticket",
            "add new ticket",
            "create ticket",
            "make ticket",
            "add ticket"
        ]
        
        for pattern in ticket_creation_patterns:
            if pattern in text_lower:
                model_intent = "TICKET"
                print(f"Detected TICKET model with creation pattern: {pattern}")
                break
        
        # If no explicit ticket creation pattern, check for client creation patterns
        if not model_intent:
            client_creation_patterns = [
                "create a new client",
                "create new client", 
                "make a new client",
                "make new client",
                "add a new client",
                "add new client",
                "create client",
                "make client",
                "add client"
            ]
            
            for pattern in client_creation_patterns:
                if pattern in text_lower:
                    model_intent = "CLIENT"
                    print(f"Detected CLIENT model with creation pattern: {pattern}")
                    break
        
        # If no explicit client creation pattern, check for lead creation patterns
        if not model_intent:
            lead_creation_patterns = [
                "create a new lead",
                "create new lead", 
                "make a new lead",
                "make new lead",
                "add a new lead",
                "add new lead",
                "create lead",
                "make lead",
                "add lead"
            ]
            
            for pattern in lead_creation_patterns:
                if pattern in text_lower:
                    model_intent = "LEAD"
                    print(f"Detected LEAD model with creation pattern: {pattern}")
                    break
        
        # If no explicit lead creation pattern, check for sales creation patterns
        if not model_intent:
            sales_creation_patterns = [
                "create a new sale",
                "create new sale", 
                "make a new sale",
                "make new sale",
                "add a new sale",
                "add new sale",
                "create sale",
                "make sale",
                "add sale"
            ]
            
            for pattern in sales_creation_patterns:
                if pattern in text_lower:
                    model_intent = "SALES"
                    print(f"Detected SALES model with creation pattern: {pattern}")
                    break
        
        # If no explicit creation pattern, check for model keywords
        if not model_intent:
            # Check for ticket keywords first (since they're more specific)
            for keyword in ticket_keywords:
                if keyword in text_lower:
                    model_intent = "TICKET"
                    print(f"Detected TICKET model with keyword: {keyword}")
                    break
            
            # Then check for client keywords
            if not model_intent:
                for keyword in client_keywords:
                    if keyword in text_lower:
                        model_intent = "CLIENT"
                        print(f"Detected CLIENT model with keyword: {keyword}")
                        break
            
            # Then check for lead keywords
            if not model_intent:
                for keyword in lead_keywords:
                    if keyword in text_lower:
                        model_intent = "LEAD"
                        print(f"Detected LEAD model with keyword: {keyword}")
                        break
            
            # Then check for sales keywords
            if not model_intent:
                for keyword in sales_keywords:
                    if keyword in text_lower:
                        model_intent = "SALES"
                        print(f"Detected SALES model with keyword: {keyword}")
                        break
    
    # For UPDATE actions, check for model keywords
    elif action_intent == "UPDATE":
        # Check for ticket keywords first (since they're more specific)
        for keyword in ticket_keywords:
            if keyword in text_lower:
                model_intent = "TICKET"
                print(f"Detected TICKET model with keyword: {keyword}")
                break
        
        # Then check for client keywords
        if not model_intent:
            for keyword in client_keywords:
                if keyword in text_lower:
                    model_intent = "CLIENT"
                    print(f"Detected CLIENT model with keyword: {keyword}")
                    break
        
        # Then check for lead keywords
        if not model_intent:
            for keyword in lead_keywords:
                if keyword in text_lower:
                    model_intent = "LEAD"
                    print(f"Detected LEAD model with keyword: {keyword}")
                    break
        
        # Then check for sales keywords
        if not model_intent:
            for keyword in sales_keywords:
                if keyword in text_lower:
                    model_intent = "SALES"
                    print(f"Detected SALES model with keyword: {keyword}")
                    break
        
        # Then check for project keywords
        if not model_intent:
            for keyword in project_keywords:
                if keyword in text_lower:
                    model_intent = "PROJECT"
                    print(f"Detected PROJECT model with keyword: {keyword}")
                    break
    
    # Check for project keywords (only if not already identified)
    if not model_intent:
        for keyword in project_keywords:
            if keyword in text_lower:
                model_intent = "PROJECT"
                print(f"Detected PROJECT model with keyword: {keyword}")
                break

    # Special case: if we have a CREATE action but no model, and the text contains quotes or specific names,
    # assume it's a client creation (common use case)
    if action_intent == "CREATE" and not model_intent:
        # Check for quoted names or specific company indicators
        import re
        quoted_names = re.findall(r'"([^"]+)"', text)
        if quoted_names or any(word in text_lower for word in ["group", "corp", "inc", "llc", "ltd", "company"]):
            model_intent = "CLIENT"
            print(f"Detected CLIENT model based on quoted name or company indicators")
    
    # If still no model but we have CREATE action, default to CLIENT for common cases
    if action_intent == "CREATE" and not model_intent:
        model_intent = "CLIENT"
        print(f"Defaulting to CLIENT model for CREATE action")

    print(f"Final classification: action={action_intent}, model={model_intent}")
    return action_intent, model_intent

def get_conversation_key(request):
    if 'conversation_key' not in request.session:
        key = str(time())
        request.session['conversation_key'] = key
        request.session.modified = True
    return request.session['conversation_key']

def detect_new_conversation(message, conversation_key, model_intent, request):
    """
    Detect if this is a new conversation by checking for new creation keywords.
    """
    message_lower = message.lower()
    
    # Check for new creation keywords
    new_creation_keywords = [
        "create a new", "make a new", "add a new", "new client", "new ticket", "new project", "new lead", "new sale",
        "create new", "make new", "add new"
    ]
    
    # Check if this is a new creation request
    is_new_creation = any(keyword in message_lower for keyword in new_creation_keywords)
    
    # Check if this mentions a different client/ticket/project/lead/sale than what's in context
    current_context = None
    if model_intent == "CLIENT":
        current_context = request.session.get('client_context', {})
        current_name = current_context.get('name')
    elif model_intent == "TICKET":
        current_context = request.session.get('ticket_context', {})
        current_name = current_context.get('ticket_name')
    elif model_intent == "PROJECT":
        current_context = request.session.get('project_context', {})
        current_name = current_context.get('name')
    elif model_intent == "LEAD":
        current_context = request.session.get('lead_context', {})
        current_name = current_context.get('name')
    elif model_intent == "SALES":
        current_context = request.session.get('sales_context', {})
        current_name = current_context.get('name')
    
    # Extract potential new name from message
    import re
    quoted_names = re.findall(r'"([^"]+)"', message)
    if quoted_names:
        new_name = quoted_names[0]
        if current_name and new_name.lower() != current_name.lower():
            print(f"Detected new {model_intent.lower()}: {new_name} (was: {current_name})")
            return True
    
    # Check for company/client keywords followed by different names
    if model_intent == "CLIENT":
        words = message_lower.split()
        for i, word in enumerate(words):
            if word in ["client", "company", "group", "corp", "inc", "llc"] and i + 1 < len(words):
                potential_name = words[i + 1]
                if current_name and potential_name.lower() != current_name.lower():
                    print(f"Detected new client: {potential_name} (was: {current_name})")
                    return True
    
    return is_new_creation

def clear_all_context(request):
    """
    Clear all context from session.
    """
    clear_client_context(request)
    clear_ticket_context(request)
    clear_project_context(request)
    clear_lead_context(request)
    clear_sales_context(request)
    if 'conversation_key' in request.session:
        del request.session['conversation_key']
        request.session.modified = True
    print("Cleared all context from session")

@csrf_exempt
def atlas_chatbot(request):
    if request.method != "POST":
        response = {"response": "Invalid request method. Use POST.", "error": True}
        with transaction.atomic():
            ChatHistory.objects.create(
                user_input="",
                bot_response=response["response"]
            )
        return JsonResponse(response, status=405)

    try:
        # Handle both JSON and form-encoded data
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            message = data.get("message")
        else:
            # Handle form-encoded data
            message = request.POST.get("prompt") or request.POST.get("message")
        
        print(f"Received message: {message}")
        print(f"Session keys: {request.session.keys()}")
        print(f"Session data: {request.session.items()}")

        if not message:
            response = {"response": "No message provided", "error": True}
            with transaction.atomic():
                ChatHistory.objects.create(
                    user_input="",
                    bot_response=response["response"]
                )
            return JsonResponse(response, status=400)

        if message.lower() == "clear":
            with transaction.atomic():
                ChatHistory.objects.all().delete()
            ACTIVE_INTENTS.clear()
            # Clear all context from session
            clear_client_context(request)
            clear_ticket_context(request)
            clear_project_context(request)
            request.session.flush()
            print("Cleared ChatHistory, ACTIVE_INTENTS, and session")
            return JsonResponse({"response": "Chatbot state cleared. What would you like to do next?", "error": False})

        conversation_key = get_conversation_key(request)
        print(f"Conversation key: {conversation_key}")
        print(f"ACTIVE_INTENTS state: {ACTIVE_INTENTS}")
        print(f"ChatHistory exists: {ChatHistory.objects.exists()}")

        if message.lower() in {"cancel", "stop", "abort", "end"}:
            with transaction.atomic():
                ChatHistory.objects.all().delete()
            ACTIVE_INTENTS.pop(conversation_key, None)
            # Clear all context from session
            clear_client_context(request)
            clear_ticket_context(request)
            clear_project_context(request)
            if 'conversation_key' in request.session:
                del request.session['conversation_key']
                request.session.modified = True
            response = {"response": "Task cancelled. What would you like to do next?", "error": False}
            with transaction.atomic():
                ChatHistory.objects.create(
                    user_input=message,
                    bot_response=response["response"]
                )
            return JsonResponse(response)

        if not ChatHistory.objects.exists() and conversation_key not in ACTIVE_INTENTS:
            action_intent, model_intent = classify_intent(message)
            print(f"DEBUG: Classified intent - Action: {action_intent}, Model: {model_intent}")
            
            if action_intent == "CANCEL":
                response = {"response": "No task to cancel. What would you like to do next?", "error": False}
                return JsonResponse(response)

            # Check if this is a new conversation
            if model_intent and detect_new_conversation(message, conversation_key, model_intent, request):
                print(f"Detected new conversation for {model_intent}, clearing context")
                clear_all_context(request)
                with transaction.atomic():
                    ChatHistory.objects.all().delete()
                ACTIVE_INTENTS.clear()

            if not model_intent or action_intent == "UNKNOWN":
                print(f"DEBUG: Falling back to generic LLM response - model_intent: {model_intent}, action_intent: {action_intent}")
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant managing tickets, clients, and projects."},
                        {"role": "user", "content": message}
                    ]
                )
                answer = response.choices[0].message.content.strip()
                return JsonResponse({"response": answer, "error": False})

            ACTIVE_INTENTS[conversation_key] = {
                "action_intent": action_intent,
                "model_intent": model_intent
            }
            print(f"Locked intent: {action_intent}/{model_intent}")
        elif conversation_key in ACTIVE_INTENTS:
            action_intent = ACTIVE_INTENTS[conversation_key]["action_intent"]
            model_intent = ACTIVE_INTENTS[conversation_key]["model_intent"]
            print(f"Using locked intent: {action_intent}/{model_intent}")
            
            # Check if this is a new conversation even within an active session
            if detect_new_conversation(message, conversation_key, model_intent, request):
                print(f"Detected new conversation within active session, clearing context")
                clear_all_context(request)
                with transaction.atomic():
                    ChatHistory.objects.all().delete()
                ACTIVE_INTENTS.clear()
                
                # Reclassify intent for the new conversation
                action_intent, model_intent = classify_intent(message)
                if model_intent:
                    ACTIVE_INTENTS[conversation_key] = {
                        "action_intent": action_intent,
                        "model_intent": model_intent
                    }
                    print(f"New conversation locked intent: {action_intent}/{model_intent}")
        else:
            # This case should only happen if there's ChatHistory but no active intent
            # Try to recover context from ChatHistory
            history_entries = ChatHistory.objects.order_by('timestamp')
            print("ChatHistory for intent:", [(entry.user_input, entry.bot_response) for entry in history_entries])
            
            if not history_entries.exists():
                # No ChatHistory and no active intent - this is a fresh start
                action_intent, model_intent = classify_intent(message)
                print(f"Fresh start - Classified intent: {action_intent}/{model_intent}")
                
                if not model_intent or action_intent == "UNKNOWN":
                    print(f"DEBUG: Falling back to generic LLM response - model_intent: {model_intent}, action_intent: {action_intent}")
                    response = openai.ChatCompletion.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "You are a helpful assistant managing tickets, clients, and projects."},
                            {"role": "user", "content": message}
                        ]
                    )
                    answer = response.choices[0].message.content.strip()
                    return JsonResponse({"response": answer, "error": False})
                
                ACTIVE_INTENTS[conversation_key] = {
                    "action_intent": action_intent,
                    "model_intent": model_intent
                }
                print(f"Fresh start locked intent: {action_intent}/{model_intent}")
            else:
                # Try to recover intent from ChatHistory
                action_intent, model_intent = None, None
                for entry in list(history_entries):
                    input_lower = entry.user_input.lower()
                    if any(kw in input_lower for kw in ticket_keywords):
                        model_intent = "TICKET"
                        action_intent = "CREATE" if any(k in input_lower for k in create_keywords) else \
                                        "UPDATE" if any(k in input_lower for k in update_keywords) else "CREATE"
                        break
                    elif any(kw in input_lower for kw in client_keywords):
                        model_intent = "CLIENT"
                        action_intent = "CREATE" if any(k in input_lower for k in create_keywords) else \
                                    "UPDATE" if any(k in input_lower for k in update_keywords) else "CREATE"
                        break
                    elif any(kw in input_lower for kw in project_keywords):
                        model_intent = "PROJECT"
                        action_intent = "CREATE" if any(k in input_lower for k in create_keywords) else \
                                    "UPDATE" if any(k in input_lower for k in update_keywords) else "CREATE"
                        break
                    elif any(kw in input_lower for kw in lead_keywords):
                        model_intent = "LEAD"
                        action_intent = "CREATE" if any(k in input_lower for k in create_keywords) else \
                                    "UPDATE" if any(k in input_lower for k in update_keywords) else "CREATE"
                        break
                    elif any(kw in input_lower for kw in sales_keywords):
                        model_intent = "SALES"
                        action_intent = "CREATE" if any(k in input_lower for k in create_keywords) else \
                                    "UPDATE" if any(k in input_lower for k in update_keywords) else "CREATE"
                        break

                if not model_intent:
                    response = {"response": "Conversation lost context. Please start a new task.", "error": True}
                    with transaction.atomic():
                        ChatHistory.objects.create(
                            user_input=message,
                            bot_response=response["response"]
                        )
                    return JsonResponse(response, status=400)

                ACTIVE_INTENTS[conversation_key] = {
                    "action_intent": action_intent,
                    "model_intent": model_intent
                }
                print(f"Recovered intent: {action_intent}/{model_intent}")

        new_action_intent, _ = classify_intent(message)
        if new_action_intent in {"CREATE", "UPDATE", "DELETE"} and new_action_intent != action_intent:
            action_intent = new_action_intent
            ACTIVE_INTENTS[conversation_key]["action_intent"] = action_intent
            print(f"Updated action_intent: {action_intent}/{model_intent}")

        if model_intent == "TICKET":
            extracted_data = extract_ticket_fields(message)
            if "error" in extracted_data:
                with transaction.atomic():
                    ChatHistory.objects.create(
                        user_input=message,
                        bot_response=extracted_data["response"]
                    )
                return JsonResponse(extracted_data, status=400)

            ticket_context = get_ticket_context(request)
            merged_data = merge_context(ticket_context, extracted_data)
            merged_data["action_intent"] = action_intent
            print("Merged Ticket Data:", merged_data)
            
            # Save updated context to session
            save_ticket_context(request, merged_data)

            validation_result = validate_ticket_data(merged_data)
            if validation_result.get("error", False):
                with transaction.atomic():
                    ChatHistory.objects.create(
                        user_input=message,
                        bot_response=validation_result["response"]
                    )
                return JsonResponse({
                    "response": validation_result["response"],
                    "error": True,
                    "current_data": merged_data
                }, status=200)

            original_name = merged_data.get("ticket_name")
            new_name = merged_data.get("new_ticket_name")
            
            if action_intent == "CREATE":
                if TicketList.objects.filter(name__iexact=original_name).exists():
                    response = {"response": f"Ticket '{original_name}' already exists.", "error": True}
                else:
                    response = create_ticket(merged_data, conversation_key)
            elif action_intent == "UPDATE":
                if not TicketList.objects.filter(name__iexact=original_name).exists():
                    response = {"response": f"Ticket '{original_name}' not found.", "error": True}
                elif new_name and TicketList.objects.filter(name__iexact=new_name).exists():
                    response = {"response": f"Ticket '{new_name}' already exists.", "error": True}
                else:
                    response = update_ticket(merged_data, conversation_key)
            else:
                response = {"response": "Invalid ticket operation", "error": True}

            with transaction.atomic():
                ChatHistory.objects.create(
                    user_input=message,
                    bot_response=response["response"]
                )
                if not response.get("error", False):
                    ChatHistory.objects.all().delete()
                    ACTIVE_INTENTS.pop(conversation_key, None)
                    clear_ticket_context(request)
                    if 'conversation_key' in request.session:
                        del request.session['conversation_key']
                        request.session.modified = True
            return JsonResponse(response)

        elif model_intent == "CLIENT":
            print(f"DEBUG: Processing CLIENT intent for message: {message}")
            extracted_data = extract_client_fields(message)
            if "error" in extracted_data:
                with transaction.atomic():
                    ChatHistory.objects.create(
                        user_input=message,
                        bot_response=extracted_data["response"]
                    )
                return JsonResponse(extracted_data, status=400)

            client_context = get_client_context(request)
            merged_data = merge_client_context(client_context, extracted_data)
            merged_data["action_intent"] = action_intent
            print("Merged Client Data:", merged_data)
            
            # Save updated context to session
            save_client_context(request, merged_data)

            validation_result = validate_client_data(merged_data)
            if validation_result.get("error", False):
                with transaction.atomic():
                    ChatHistory.objects.create(
                        user_input=message,
                        bot_response=validation_result["response"]
                    )
                return JsonResponse({
                    "response": validation_result["response"],
                    "error": True,
                    "current_data": merged_data
                }, status=200)

            original_name = merged_data.get("name")
            new_name = merged_data.get("new_name")

            if action_intent == "CREATE":
                if ClientCompany.objects.filter(name__iexact=original_name).exists():
                    response = {"response": f"Client '{original_name}' already exists.", "error": True}
                else:
                    response = create_client(merged_data, conversation_key)
            elif action_intent == "UPDATE":
                if not ClientCompany.objects.filter(name__iexact=original_name).exists():
                    response = {"response": f"Client '{original_name}' not found.", "error": True}
                elif new_name and ClientCompany.objects.filter(name__iexact=new_name).exists():
                    response = {"response": f"Client '{new_name}' already exists.", "error": True}
                else:
                    response = update_client(merged_data, conversation_key)
            else:
                response = {"response": "Invalid client operation", "error": True}

            with transaction.atomic():
                ChatHistory.objects.create(
                    user_input=message,
                    bot_response=response["response"]
                )
                if not response.get("error", False):
                    ChatHistory.objects.all().delete()
                    ACTIVE_INTENTS.pop(conversation_key, None)
                    clear_client_context(request)
                    if 'conversation_key' in request.session:
                        del request.session['conversation_key']
                        request.session.modified = True
            return JsonResponse(response)

        elif model_intent == "PROJECT":
            extracted_data = extract_project_fields(message)
            if "error" in extracted_data:
                with transaction.atomic():
                    ChatHistory.objects.create(
                        user_input=message,
                        bot_response=extracted_data["response"]
                    )
                return JsonResponse(extracted_data, status=400)

            project_context = get_project_context(request)
            merged_data = merge_project_context(project_context, extracted_data)
            merged_data["action_intent"] = action_intent
            print("Merged Project Data:", merged_data)
            
            # Save updated context to session
            save_project_context(request, merged_data)

            validation_result = validate_project_data(merged_data)
            if validation_result.get("error", False):
                with transaction.atomic():
                    ChatHistory.objects.create(
                        user_input=message,
                        bot_response=validation_result["response"]
                    )
                return JsonResponse({
                    "response": validation_result["response"],
                    "error": True,
                    "current_data": merged_data
                }, status=200)
            original_name = merged_data.get("name")
            new_name = merged_data.get("new_name")

            if action_intent == "CREATE":
                if ProjectList.objects.filter(name__iexact=original_name).exists():
                    response = {"response": f"Project '{original_name}' already exists.", "error": True}
                else:
                    response = create_project(merged_data, conversation_key)
            elif action_intent == "UPDATE":
                if not ProjectList.objects.filter(name__iexact=original_name).exists():
                    response = {"response": f"Project '{original_name}' not found.", "error": True}
                elif new_name and ProjectList.objects.filter(name__iexact=new_name).exists():
                    response = {"response": f"Project '{new_name}' already exists.", "error": True}
                else:
                    response = update_project(merged_data, conversation_key)
            else:
                response = {"response": "Invalid project operation", "error": True}

            with transaction.atomic():
                ChatHistory.objects.create(
                    user_input=message,
                    bot_response=response["response"]
                )
                if not response.get("error", False):
                    ChatHistory.objects.all().delete()
                    ACTIVE_INTENTS.pop(conversation_key, None)
                    clear_project_context(request)
                    if 'conversation_key' in request.session:
                        del request.session['conversation_key']
                        request.session.modified = True
            return JsonResponse(response)

        elif model_intent == "LEAD":
            extracted_data = extract_lead_fields(message)
            if "error" in extracted_data:
                with transaction.atomic():
                    ChatHistory.objects.create(
                        user_input=message,
                        bot_response=extracted_data["response"]
                    )
                return JsonResponse(extracted_data, status=400)

            lead_context = get_lead_context(request)
            merged_data = merge_lead_context(lead_context, extracted_data)
            merged_data["action_intent"] = action_intent
            print("Merged Lead Data:", merged_data)
            
            # Save updated context to session
            save_lead_context(request, merged_data)

            validation_result = validate_lead_data(merged_data)
            if validation_result.get("error", False):
                with transaction.atomic():
                    ChatHistory.objects.create(
                        user_input=message,
                        bot_response=validation_result["response"]
                    )
                return JsonResponse({
                    "response": validation_result["response"],
                    "error": True,
                    "current_data": merged_data
                }, status=200)

            original_name = merged_data.get("name")
            new_name = merged_data.get("new_name")

            if action_intent == "CREATE":
                if LeadCompany.objects.filter(name__iexact=original_name).exists():
                    response = {"response": f"Lead '{original_name}' already exists.", "error": True}
                else:
                    response = create_lead(merged_data, conversation_key)
            elif action_intent == "UPDATE":
                if not LeadCompany.objects.filter(name__iexact=original_name).exists():
                    response = {"response": f"Lead '{original_name}' not found.", "error": True}
                elif new_name and LeadCompany.objects.filter(name__iexact=new_name).exists():
                    response = {"response": f"Lead '{new_name}' already exists.", "error": True}
                else:
                    response = update_lead(merged_data, conversation_key)
            else:
                response = {"response": "Invalid lead operation", "error": True}

            with transaction.atomic():
                ChatHistory.objects.create(
                    user_input=message,
                    bot_response=response["response"]
                )
                if not response.get("error", False):
                    ChatHistory.objects.all().delete()
                    ACTIVE_INTENTS.pop(conversation_key, None)
                    clear_lead_context(request)
                    if 'conversation_key' in request.session:
                        del request.session['conversation_key']
                        request.session.modified = True
            return JsonResponse(response)

        elif model_intent == "SALES":
            extracted_data = extract_sales_fields(message)
            if "error" in extracted_data:
                with transaction.atomic():
                    ChatHistory.objects.create(
                        user_input=message,
                        bot_response=extracted_data["response"]
                    )
                return JsonResponse(extracted_data, status=400)

            sales_context = get_sales_context(request)
            merged_data = merge_sales_context(sales_context, extracted_data)
            merged_data["action_intent"] = action_intent
            print("Merged Sales Data:", merged_data)
            
            # Save updated context to session
            save_sales_context(request, merged_data)

            validation_result = validate_sales_data(merged_data)
            if validation_result.get("error", False):
                with transaction.atomic():
                    ChatHistory.objects.create(
                        user_input=message,
                        bot_response=validation_result["response"]
                    )
                return JsonResponse({
                    "response": validation_result["response"],
                    "error": True,
                    "current_data": merged_data
                }, status=200)

            original_name = merged_data.get("name")
            new_name = merged_data.get("new_name")

            if action_intent == "CREATE":
                if SalesRequests.objects.filter(name__iexact=original_name).exists():
                    response = {"response": f"Sales '{original_name}' already exists.", "error": True}
                else:
                    response = create_sales(merged_data, conversation_key)
            elif action_intent == "UPDATE":
                if not SalesRequests.objects.filter(name__iexact=original_name).exists():
                    response = {"response": f"Sales '{original_name}' not found.", "error": True}
                elif new_name and SalesRequests.objects.filter(name__iexact=new_name).exists():
                    response = {"response": f"Sales '{new_name}' already exists.", "error": True}
                else:
                    response = update_sales(merged_data, conversation_key)
            else:
                response = {"response": "Invalid sales operation", "error": True}

            with transaction.atomic():
                ChatHistory.objects.create(
                    user_input=message,
                    bot_response=response["response"]
                )
                if not response.get("error", False):
                    ChatHistory.objects.all().delete()
                    ACTIVE_INTENTS.pop(conversation_key, None)
                    clear_sales_context(request)
                    if 'conversation_key' in request.session:
                        del request.session['conversation_key']
                        request.session.modified = True
            return JsonResponse(response)

    except Exception as e:
        print("ERROR:", e)
        response = {"response": f"An unexpected error occurred: {str(e)}", "error": True}
        with transaction.atomic():
            ChatHistory.objects.create(
                user_input=message or "Unknown",
                bot_response=response["response"]
            )
        return JsonResponse(response, status=500)
