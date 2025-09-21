from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator
import uuid


class HandbookDocument(models.Model):
    """
    Model for storing employee handbook documents (PDFs)
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    document = models.FileField(
        upload_to='handbook_documents/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf'])]
    )
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    processed_content = models.TextField(blank=True, null=True)  # Extracted text content
    
    class Meta:
        ordering = ['-uploaded_at']
        
    def __str__(self):
        return self.title


class ChatSession(models.Model):
    """
    Model for storing chat sessions between users and the handbook chatbot
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    session_name = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-updated_at']
        
    def __str__(self):
        return f"Chat Session - {self.user.username} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"


class ChatMessage(models.Model):
    """
    Model for storing individual messages in chat sessions
    """
    MESSAGE_TYPES = [
        ('user', 'User'),
        ('bot', 'Bot'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    message_type = models.CharField(max_length=4, choices=MESSAGE_TYPES)
    content = models.TextField()
    context_documents = models.ManyToManyField(HandbookDocument, blank=True)  # Documents used as context
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
        
    def __str__(self):
        return f"{self.get_message_type_display()}: {self.content[:50]}..."
