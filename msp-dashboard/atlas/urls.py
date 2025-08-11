from django.urls import path
from .views import atlas_chatbot
urlpatterns = [
    path("chatbot/", atlas_chatbot, name="atlas_chatbot"),
]
