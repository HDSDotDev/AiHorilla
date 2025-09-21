from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.contrib import messages
from django.urls import reverse
from django.conf import settings
import json
import PyPDF2
import io
import re

from .models import HandbookDocument, ChatSession, ChatMessage
from .ai_integration import get_ai_response, get_ai_config


@login_required
def handbook_dashboard(request):
    """
    Dashboard view for handbook chat interface
    """
    # Get or create a chat session for the user
    chat_session, created = ChatSession.objects.get_or_create(
        user=request.user,
        is_active=True,
        defaults={'session_name': 'Default Session'}
    )
    
    # Get recent chat messages
    messages = ChatMessage.objects.filter(session=chat_session)[:50]
    
    # Get available documents
    documents = HandbookDocument.objects.filter(is_active=True)
    
    # Get AI configuration
    ai_config = get_ai_config()
    
    context = {
        'chat_session': chat_session,
        'messages': messages,
        'documents': documents,
        'ai_backend': ai_config.get('backend', 'groq'),
    }
    
    return render(request, 'handbook/dashboard.html', context)


@login_required
def document_list(request):
    """
    List all handbook documents
    """
    documents = HandbookDocument.objects.filter(is_active=True)
    paginator = Paginator(documents, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
    }
    
    return render(request, 'handbook/document_list.html', context)


@login_required
def upload_document(request):
    """
    Upload a new handbook document
    """
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        document = request.FILES.get('document')
        
        if title and document:
            # Extract text content from PDF
            try:
                content = extract_pdf_content(document)
                
                handbook_doc = HandbookDocument.objects.create(
                    title=title,
                    description=description,
                    document=document,
                    uploaded_by=request.user,
                    processed_content=content
                )
                
                messages.success(request, f'Document "{title}" uploaded successfully!')
                return redirect('handbook-documents')
                
            except Exception as e:
                messages.error(request, f'Error processing PDF: {str(e)}')
        else:
            messages.error(request, 'Please provide both title and document.')
    
    return render(request, 'handbook/upload_document.html')


def extract_pdf_content(pdf_file):
    """
    Extract text content from uploaded PDF file
    """
    content = ""
    try:
        pdf_file.seek(0)  # Reset file pointer
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            content += page.extract_text() + "\n"
            
    except Exception as e:
        raise Exception(f"Could not extract text from PDF: {str(e)}")
    
    return content


@csrf_exempt
@login_required
def chat_api(request):
    """
    API endpoint for chat functionality with AI integration
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_message = data.get('message', '').strip()
            session_id = data.get('session_id')
            
            if not user_message:
                return JsonResponse({'error': 'Message is required'}, status=400)
            
            # Get or create chat session
            if session_id:
                try:
                    chat_session = ChatSession.objects.get(id=session_id, user=request.user)
                except ChatSession.DoesNotExist:
                    chat_session = ChatSession.objects.create(
                        user=request.user,
                        session_name='Chat Session'
                    )
            else:
                chat_session = ChatSession.objects.create(
                    user=request.user,
                    session_name='Chat Session'
                )
            
            # Save user message
            user_chat_message = ChatMessage.objects.create(
                session=chat_session,
                message_type='user',
                content=user_message
            )
            
            # Generate bot response using AI integration
            ai_config = get_ai_config()
            ai_backend = ai_config.get('backend', 'groq')
            
            try:
                bot_response, relevant_docs = get_ai_response(user_message, backend=ai_backend)
            except Exception as e:
                # Fallback to simple response if AI fails
                bot_response = f"I apologize, but I'm experiencing technical difficulties. Please try again later or contact HR directly. Error: {str(e)}"
                relevant_docs = []
            
            # Save bot message
            bot_chat_message = ChatMessage.objects.create(
                session=chat_session,
                message_type='bot',
                content=bot_response
            )
            
            # Associate relevant documents with the bot message
            if relevant_docs:
                bot_chat_message.context_documents.set(relevant_docs)
            
            return JsonResponse({
                'success': True,
                'session_id': str(chat_session.id),
                'bot_response': bot_response,
                'user_message_id': str(user_chat_message.id),
                'bot_message_id': str(bot_chat_message.id),
                'relevant_documents': [
                    {'title': doc.title, 'id': str(doc.id)} 
                    for doc in relevant_docs
                ],
                'ai_backend': ai_backend
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Only POST method allowed'}, status=405)


def generate_bot_response(user_message):
    """
    Simple keyword-based response generation (fallback method)
    This is kept as a fallback when AI services are unavailable
    """
    # Get all active documents
    documents = HandbookDocument.objects.filter(is_active=True)
    
    # Simple keyword matching
    user_message_lower = user_message.lower()
    keywords = re.findall(r'\b\w+\b', user_message_lower)
    
    relevant_docs = []
    relevant_content = []
    
    for doc in documents:
        if doc.processed_content:
            content_lower = doc.processed_content.lower()
            score = 0
            
            # Count keyword matches
            for keyword in keywords:
                if len(keyword) > 3:  # Only consider words longer than 3 characters
                    score += content_lower.count(keyword)
            
            if score > 0:
                relevant_docs.append(doc)
                # Extract relevant sections (simplified)
                sentences = re.split(r'[.!?]+', doc.processed_content)
                relevant_sentences = []
                
                for sentence in sentences:
                    sentence_lower = sentence.lower()
                    if any(keyword in sentence_lower for keyword in keywords if len(keyword) > 3):
                        relevant_sentences.append(sentence.strip())
                
                if relevant_sentences:
                    relevant_content.extend(relevant_sentences[:3])  # Take top 3 relevant sentences
    
    # Generate response
    if relevant_content:
        response = "Based on the employee handbook, here's what I found:\n\n"
        for i, content in enumerate(relevant_content[:5], 1):
            if content:
                response += f"{i}. {content}\n\n"
        
        if relevant_docs:
            response += f"This information was found in: {', '.join([doc.title for doc in relevant_docs[:3]])}"
    else:
        response = ("I couldn't find specific information about that in the employee handbook. "
                   "You might want to try rephrasing your question or contact HR directly for more details.")
    
    return response, relevant_docs


@login_required  
def chat_history(request, session_id):
    """
    Get chat history for a specific session
    """
    session = get_object_or_404(ChatSession, id=session_id, user=request.user)
    messages = ChatMessage.objects.filter(session=session)
    
    messages_data = []
    for message in messages:
        message_data = {
            'id': str(message.id),
            'type': message.message_type,
            'content': message.content,
            'created_at': message.created_at.isoformat(),
        }
        
        if message.message_type == 'bot' and message.context_documents.exists():
            message_data['documents'] = [
                {'title': doc.title, 'id': str(doc.id)}
                for doc in message.context_documents.all()
            ]
        
        messages_data.append(message_data)
    
    return JsonResponse({
        'session_id': str(session.id),
        'messages': messages_data
    })


@login_required
def new_chat_session(request):
    """
    Create a new chat session
    """
    if request.method == 'POST':
        # Mark current session as inactive
        ChatSession.objects.filter(user=request.user, is_active=True).update(is_active=False)
        
        # Create new session
        new_session = ChatSession.objects.create(
            user=request.user,
            session_name=f"Chat {ChatSession.objects.filter(user=request.user).count() + 1}"
        )
        
        return JsonResponse({
            'success': True,
            'session_id': str(new_session.id),
            'redirect_url': reverse('handbook-dashboard')
        })
    
    return JsonResponse({'error': 'Only POST method allowed'}, status=405)


@login_required
def api_test(request):
    """
    Test endpoint for AI API functionality
    """
    if request.method == 'POST':
        test_question = request.POST.get('question', 'What is the vacation policy?')
        ai_config = get_ai_config()
        
        try:
            response, docs = get_ai_response(test_question, backend=ai_config.get('backend', 'groq'))
            return JsonResponse({
                'success': True,
                'question': test_question,
                'response': response,
                'backend': ai_config.get('backend'),
                'documents_found': len(docs)
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e),
                'backend': ai_config.get('backend')
            })
    
    return JsonResponse({'error': 'Only POST method allowed'}, status=405)
