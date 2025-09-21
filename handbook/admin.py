from django.contrib import admin
from .models import HandbookDocument, ChatSession, ChatMessage


@admin.register(HandbookDocument)
class HandbookDocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'uploaded_by', 'uploaded_at', 'is_active']
    list_filter = ['is_active', 'uploaded_at', 'uploaded_by']
    search_fields = ['title', 'description']
    readonly_fields = ['uploaded_at', 'updated_at', 'processed_content']
    
    fieldsets = [
        ('Document Information', {
            'fields': ['title', 'description', 'document', 'is_active']
        }),
        ('Upload Details', {
            'fields': ['uploaded_by', 'uploaded_at', 'updated_at'],
            'classes': ['collapse']
        }),
        ('Processed Content', {
            'fields': ['processed_content'],
            'classes': ['collapse']
        })
    ]


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'session_name', 'created_at', 'is_active']
    list_filter = ['is_active', 'created_at', 'user']
    search_fields = ['user__username', 'session_name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['session', 'message_type', 'content_preview', 'created_at']
    list_filter = ['message_type', 'created_at', 'session__user']
    search_fields = ['content', 'session__user__username']
    readonly_fields = ['created_at']
    
    def content_preview(self, obj):
        return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content Preview'
