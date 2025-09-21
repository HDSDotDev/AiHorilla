from django.urls import path
from . import views

urlpatterns = [
    path('', views.handbook_dashboard, name='handbook-dashboard'),
    path('documents/', views.document_list, name='handbook-documents'),
    path('upload/', views.upload_document, name='handbook-upload'),
    path('chat/', views.chat_api, name='handbook-chat-api'),
    path('history/<uuid:session_id>/', views.chat_history, name='handbook-chat-history'),
    path('new-session/', views.new_chat_session, name='handbook-new-session'),
    path('api-test/', views.api_test, name='handbook-api-test'),
]