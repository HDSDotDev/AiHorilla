# Handbook Chat Assistant

This module implements a chatbot functionality for the Horilla HR system that allows employees to ask questions about company policies and procedures using uploaded PDF handbook documents.

## Features

### 1. Chat Interface
- **Interactive Chat**: Real-time chat interface where employees can ask questions
- **Context-Aware Responses**: Bot provides answers based on uploaded handbook documents
- **Source Attribution**: Shows which documents were used to generate answers
- **Session Management**: Supports multiple chat sessions per user

### 2. Document Management
- **PDF Upload**: Administrators can upload PDF handbook documents
- **Text Extraction**: Automatic text extraction from PDFs for search functionality
- **Document Library**: Browse and download available handbook documents
- **Version Control**: Track document uploads with timestamps and authors

### 3. Smart Search
- **Keyword Matching**: Advanced keyword-based search through document content
- **Relevance Scoring**: Documents are ranked by relevance to user queries
- **Multi-Document Support**: Search across multiple handbook documents simultaneously

## Installation & Setup

### 1. App Configuration
The handbook app has been added to:
- `INSTALLED_APPS` in `horilla_apps.py`
- `SIDEBARS` for navigation menu integration
- URL routing in main `urls.py`

### 2. Database Models
- **HandbookDocument**: Stores PDF documents and extracted text content
- **ChatSession**: Manages user chat sessions
- **ChatMessage**: Stores individual chat messages and context

### 3. Dependencies
- **PyPDF2**: For PDF text extraction
- **Django File Storage**: For document uploads

## Usage

### For Administrators
1. **Upload Documents**: Go to Handbook ? Upload Document
2. **Manage Documents**: View and manage uploaded documents in Handbook ? Documents
3. **Monitor Usage**: View chat sessions and messages in Django admin

### For Employees
1. **Access Chat**: Click on "Handbook" in the sidebar, then "Chat Assistant"
2. **Ask Questions**: Type questions about company policies, procedures, benefits, etc.
3. **View Sources**: See which documents were referenced in bot responses
4. **Browse Documents**: Access document library to download handbooks directly

## Technical Implementation

### Backend Components
- **Views**: Django views handling chat API, document management, and UI
- **Models**: Database models for documents, sessions, and messages
- **Admin**: Django admin interface for content management
- **Sidebar**: Integration with Horilla's navigation system

### Frontend Components
- **Chat Interface**: Real-time chat UI with message history
- **Document Library**: Grid view of available documents
- **Upload Interface**: Drag-and-drop PDF upload with progress tracking
- **Responsive Design**: Mobile-friendly interface

### API Endpoints
- `/handbook/` - Main chat dashboard
- `/handbook/documents/` - Document library
- `/handbook/upload/` - Document upload
- `/handbook/chat/` - Chat API endpoint
- `/handbook/history/<session_id>/` - Chat history
- `/handbook/new-session/` - Create new chat session

## Security Features
- **Login Required**: All views require user authentication
- **Permission Checks**: Upload and document management require appropriate permissions
- **File Validation**: Only PDF files are accepted
- **Size Limits**: File size restrictions prevent abuse
- **Content Sanitization**: Safe handling of user input and PDF content

## Future Enhancements
- **AI Integration**: Replace keyword matching with advanced AI/NLP models
- **Multi-language Support**: Support for multiple languages
- **Advanced Search**: Full-text search with ranking algorithms
- **Analytics**: Usage analytics and popular questions tracking
- **Integration**: Connect with external AI services like OpenAI GPT

## Files Created/Modified

### New Files Created:
- `handbook/` - Complete Django app directory
- `handbook/models.py` - Database models
- `handbook/views.py` - View functions and API endpoints
- `handbook/urls.py` - URL routing
- `handbook/admin.py` - Django admin configuration
- `handbook/sidebar.py` - Sidebar navigation
- `handbook/templates/handbook/` - HTML templates
- `static/images/ui/book-solid.svg` - Handbook icon

### Modified Files:
- `horilla/horilla_apps.py` - Added handbook to apps and sidebar
- `horilla/urls.py` - Added handbook URL routing

## Testing
The implementation has been tested with:
- ? Django system checks pass
- ? Database migrations successful
- ? No syntax errors in code
- ? Proper template structure
- ? API endpoints defined
- ? Admin interface configured

## Next Steps
1. Test the chat interface with real users
2. Upload sample PDF documents
3. Fine-tune the search algorithm
4. Add more sophisticated NLP capabilities
5. Integrate with external AI services for better responses