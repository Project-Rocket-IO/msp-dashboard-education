from django.shortcuts import render
from django.shortcuts import redirect, render, reverse
from django.views.generic import TemplateView
from django.db.models import F
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import *
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from . models import ThreadModel,MessageModel
from projectRocket import settings as SETTINGS
import openai
from apps import models as AppsModels
from django.http import JsonResponse


# Create your views here.
class ChatView(LoginRequiredMixin,TemplateView):
    pass

openai.api_key = SETTINGS.API_KEY

# Chat
apps_chat_view = ChatView.as_view(template_name="chat/chat-inbox.html")
apps_chatbot_view = ChatView.as_view(template_name="chat/chat-results.html")
error_handler = ChatView.as_view(template_name='pages/authentication/auth-404-alt.html')

##################################
##################################
# REAL TIME VIEWS IN USE #########
##################################
##################################

#########
# Chat Inbox

# this is the view for handling errors
def error_handler(request):
    return render(request, 'pages/authentication/auth-404-alt.html')

def apps_chatbot_view(request):

    # if the session does not have a messages key, create one
    if 'messages' not in request.session:
        request.session['messages'] = [
            {"role": "system", 
                "content": "You are now chatting with a user, provide them with comprehensive, short, and concise answers."},
        ]
    if request.method == 'POST':
        # get the prompt from the form
        prompt = request.POST.get('prompt')
        # get the temperature from the form
        temperature = 0.4
        
        # Check if this is an AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            try:
                # append the prompt to the messages list
                request.session['messages'].append({"role": "user", "content": prompt})
                # set the session as modified
                request.session.modified = True
                # call the openai API
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=request.session['messages'],
                    temperature=temperature,
                    max_tokens=1000,
                )
                # format the response
                formatted_response = response['choices'][0]['message']['content']
                # append the response to the messages list
                request.session['messages'].append({"role": "assistant", "content": formatted_response})
                request.session.modified = True
                
                return JsonResponse({
                    'success': True,
                    'response': formatted_response
                })
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'error': str(e)
                }, status=500)
        else:
            # append the prompt to the messages list
            request.session['messages'].append({"role": "user", "content": prompt})
            # set the session as modified
            request.session.modified = True
            # call the openai API
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=request.session['messages'],
                temperature=temperature,
                max_tokens=1000,
            )
            # format the response
            formatted_response = response['choices'][0]['message']['content']
            # append the response to the messages list
            request.session['messages'].append({"role": "assistant", "content": formatted_response})
            request.session.modified = True
            # redirect to the home page
            context = {
                'messages': request.session['messages'],
                'prompt': '',
                'temperature': temperature,
            }
            return redirect('chat:chat.results')
    else:
        # if the request is not a POST request, render the home page
        context = {
            'messages': request.session['messages'],
            'prompt': '',
            'temperature': 0.4,
        }
        return render(request, 'chat/chat-results.html', context)
    

def new_gptchat_view(request):
    # clear the messages list
    request.session.pop('messages', None)
    return redirect('chat:chat.results')

