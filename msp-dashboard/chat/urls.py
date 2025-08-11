from django.conf.urls import include
from django.urls import path
from .views import(
    apps_chat_view,
    apps_chatbot_view,
    new_gptchat_view,
    error_handler
)


app_name = "chat"

urlpatterns = [
    path("", view=apps_chat_view, name="chat.chat"),
    path("results/", view=apps_chatbot_view, name="chat.results"),
    path('new_chat/', view=new_gptchat_view, name='chat.new_gptchat'),
    path('404/', view=error_handler, name='chat.error_handler')
]