from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from handbook.models import HandbookDocument, ChatSession, ChatMessage
import os
from django.conf import settings


class Command(BaseCommand):
    help = 'Setup and test the handbook chat system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--create-sample-data',
            action='store_true',
            help='Create sample chat data for testing',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Setting up Handbook Chat Assistant...')
        )
        
        # Check if models are properly created
        try:
            doc_count = HandbookDocument.objects.count()
            session_count = ChatSession.objects.count()
            message_count = ChatMessage.objects.count()
            
            self.stdout.write(f"? Database models working correctly")
            self.stdout.write(f"  - Documents: {doc_count}")
            self.stdout.write(f"  - Chat Sessions: {session_count}")
            self.stdout.write(f"  - Chat Messages: {message_count}")
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'? Database models error: {str(e)}')
            )
            return
        
        # Check media directory for file uploads
        media_root = settings.MEDIA_ROOT
        handbook_dir = os.path.join(media_root, 'handbook_documents')
        
        if not os.path.exists(handbook_dir):
            os.makedirs(handbook_dir, exist_ok=True)
            self.stdout.write(f"? Created media directory: {handbook_dir}")
        else:
            self.stdout.write(f"? Media directory exists: {handbook_dir}")
        
        # Create sample data if requested
        if options['create_sample_data']:
            self.create_sample_data()
        
        self.stdout.write(
            self.style.SUCCESS('\n?? Handbook Chat Assistant is ready!')
        )
        self.stdout.write(
            'Next steps:\n'
            '1. Access the chat at: /handbook/\n'
            '2. Upload PDF documents at: /handbook/upload/\n'
            '3. Browse documents at: /handbook/documents/\n'
        )

    def create_sample_data(self):
        """Create sample chat data for testing"""
        self.stdout.write("Creating sample data...")
        
        # Get or create a test user
        user, created = User.objects.get_or_create(
            username='handbook_test_user',
            defaults={
                'email': 'test@example.com',
                'first_name': 'Test',
                'last_name': 'User'
            }
        )
        
        if created:
            user.set_password('testpass123')
            user.save()
            self.stdout.write(f"? Created test user: {user.username}")
        
        # Create a sample chat session
        session, created = ChatSession.objects.get_or_create(
            user=user,
            defaults={'session_name': 'Sample Chat Session'}
        )
        
        if created:
            self.stdout.write(f"? Created sample chat session")
            
            # Add sample messages
            ChatMessage.objects.create(
                session=session,
                message_type='user',
                content='What is the company vacation policy?'
            )
            
            ChatMessage.objects.create(
                session=session,
                message_type='bot',
                content='I would be happy to help you with information about the vacation policy. However, I don\'t have any handbook documents uploaded yet. Please ask an administrator to upload the employee handbook PDF documents so I can provide accurate information about company policies.'
            )
            
            ChatMessage.objects.create(
                session=session,
                message_type='user',
                content='How do I request time off?'
            )
            
            ChatMessage.objects.create(
                session=session,
                message_type='bot',
                content='To get information about time off requests, I need access to the employee handbook documents. Once PDF documents are uploaded, I can search through them to provide specific guidance on the time-off request process.'
            )
            
            self.stdout.write(f"? Created sample chat messages")
        
        self.stdout.write(
            self.style.SUCCESS('Sample data created successfully!')
        )