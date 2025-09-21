"""
handbook/ai_integration.py

Enhanced AI integration with Groq API for better handbook responses.
This replaces the simple keyword matching with advanced AI capabilities.
"""

import os
import json
import re
from typing import List, Tuple, Optional
from django.conf import settings
import requests
from .models import HandbookDocument

# Groq API Configuration
GROQ_API_KEY = getattr(settings, 'GROQ_API_KEY', 'REMOVED_GROQ_API_KEY')
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"

def generate_groq_response(user_message: str, max_tokens: int = 700) -> Tuple[str, List]:
    """
    Generate response using Groq AI with handbook context
    """
    try:
        if not GROQ_API_KEY or GROQ_API_KEY == 'your_groq_api_key_here':
            return "Groq API key not configured. Please set GROQ_API_KEY in settings.", []
        
        # Get relevant documents
        documents = HandbookDocument.objects.filter(is_active=True)
        
        # Build context from relevant documents
        context = ""
        relevant_docs = []
        
        user_message_lower = user_message.lower()
        keywords = extract_keywords(user_message_lower)
        
        for doc in documents:
            if doc.processed_content:
                content_lower = doc.processed_content.lower()
                # Enhanced relevance check
                relevance_score = calculate_relevance(keywords, content_lower)
                
                if relevance_score > 0.1:  # Threshold for relevance
                    relevant_docs.append(doc)
                    # Extract most relevant sections
                    relevant_sections = extract_relevant_sections(
                        doc.processed_content, keywords, max_sections=3
                    )
                    context += f"\n\nFrom {doc.title}:\n{relevant_sections}"
        
        # Limit context size to avoid API limits
        max_context_chars = 15000
        if len(context) > max_context_chars:
            context = context[:max_context_chars] + "\n...[content truncated]..."
        
        # Build the AI prompt
        system_prompt = """You are a helpful HR assistant for employees. Answer questions based ONLY on the employee handbook content provided. 

Guidelines:
- Provide accurate, helpful answers based on company policies
- If information isn't in the handbook, say so clearly
- Be concise but thorough
- Use a professional but friendly tone
- Include relevant policy details and procedures
- For complex questions, break down the answer into clear steps"""

        user_prompt = f"""Employee Handbook Content:
{context}

Employee Question: {user_message}

Please provide a helpful answer based on the handbook information above. If the specific information isn't available in the handbook, mention that and suggest contacting HR for clarification."""

        # Make API request to Groq
        headers = {
            'Authorization': f'Bearer {GROQ_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'model': GROQ_MODEL,
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt}
            ],
            'temperature': 0.2,
            'max_tokens': max_tokens
        }
        
        response = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        response_data = response.json()
        
        if 'choices' in response_data and len(response_data['choices']) > 0:
            ai_response = response_data['choices'][0]['message']['content'].strip()
            
            # Add source attribution
            if relevant_docs:
                source_list = ", ".join([doc.title for doc in relevant_docs[:3]])
                ai_response += f"\n\n?? Sources: {source_list}"
            
            return ai_response, relevant_docs
        else:
            return "I apologize, but I couldn't generate a response. Please try rephrasing your question.", []
        
    except requests.exceptions.RequestException as e:
        return f"I'm experiencing technical difficulties connecting to the AI service. Please try again later or contact HR directly. Error: {str(e)}", []
    except Exception as e:
        return f"An error occurred while processing your question: {str(e)}", []


def extract_keywords(text: str) -> List[str]:
    """
    Extract meaningful keywords from user query
    """
    # Remove common stop words
    stop_words = {
        'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', 'your', 'yours',
        'yourself', 'yourselves', 'he', 'him', 'his', 'himself', 'she', 'her', 'hers',
        'herself', 'it', 'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves',
        'what', 'which', 'who', 'whom', 'this', 'that', 'these', 'those', 'am', 'is', 'are',
        'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does',
        'did', 'doing', 'a', 'an', 'the', 'and', 'but', 'if', 'or', 'because', 'as', 'until',
        'while', 'of', 'at', 'by', 'for', 'with', 'through', 'during', 'before', 'after',
        'above', 'below', 'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under', 'again',
        'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all',
        'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor',
        'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 's', 't', 'can', 'will',
        'just', 'don', 'should', 'now', 'get', 'could', 'would'
    }
    
    # Extract words and filter
    words = re.findall(r'\b\w+\b', text.lower())
    keywords = [word for word in words if len(word) > 2 and word not in stop_words]
    
    return keywords


def calculate_relevance(keywords: List[str], content: str) -> float:
    """
    Calculate relevance score between keywords and content
    """
    if not keywords:
        return 0.0
    
    content_lower = content.lower()
    total_score = 0
    
    for keyword in keywords:
        # Count occurrences of the keyword
        count = content_lower.count(keyword)
        if count > 0:
            # Weight longer keywords more heavily
            weight = len(keyword) / 10.0
            total_score += count * weight
    
    # Normalize by content length and keyword count
    max_possible_score = len(keywords) * len(content) / 1000
    return min(total_score / max_possible_score if max_possible_score > 0 else 0, 1.0)


def extract_relevant_sections(content: str, keywords: List[str], max_sections: int = 3) -> str:
    """
    Extract the most relevant sections from content based on keywords
    """
    # Split content into paragraphs
    paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
    
    # Score each paragraph
    paragraph_scores = []
    for i, paragraph in enumerate(paragraphs):
        score = calculate_relevance(keywords, paragraph)
        paragraph_scores.append((score, i, paragraph))
    
    # Sort by relevance score and take top sections
    paragraph_scores.sort(key=lambda x: x[0], reverse=True)
    
    selected_sections = []
    for score, _, paragraph in paragraph_scores[:max_sections]:
        if score > 0:
            # Limit paragraph length
            if len(paragraph) > 500:
                paragraph = paragraph[:500] + "..."
            selected_sections.append(paragraph)
    
    return "\n\n".join(selected_sections)


def search_handbook_semantic(query: str, limit: int = 5) -> List[dict]:
    """
    Semantic search through handbook documents
    """
    documents = HandbookDocument.objects.filter(is_active=True)
    keywords = extract_keywords(query.lower())
    
    results = []
    for doc in documents:
        if doc.processed_content:
            relevance = calculate_relevance(keywords, doc.processed_content.lower())
            if relevance > 0:
                relevant_excerpt = extract_relevant_sections(
                    doc.processed_content, keywords, max_sections=1
                )
                results.append({
                    'document': doc,
                    'relevance': relevance,
                    'excerpt': relevant_excerpt[:300] + "..." if len(relevant_excerpt) > 300 else relevant_excerpt
                })
    
    # Sort by relevance and return top results
    results.sort(key=lambda x: x['relevance'], reverse=True)
    return results[:limit]


# Alternative AI backends for comparison

def generate_openai_response(user_message: str, max_tokens: int = 500) -> Tuple[str, List]:
    """
    Generate response using OpenAI GPT model (for comparison)
    """
    try:
        import openai
        
        openai_api_key = getattr(settings, 'OPENAI_API_KEY', None)
        if not openai_api_key:
            return "OpenAI API key not configured.", []
        
        openai.api_key = openai_api_key
        
        # Get relevant documents
        documents = HandbookDocument.objects.filter(is_active=True)
        
        # Build context from relevant documents (similar to Groq implementation)
        context = ""
        relevant_docs = []
        
        user_message_lower = user_message.lower()
        keywords = extract_keywords(user_message_lower)
        
        for doc in documents:
            if doc.processed_content:
                relevance = calculate_relevance(keywords, doc.processed_content.lower())
                if relevance > 0.1:
                    relevant_docs.append(doc)
                    relevant_sections = extract_relevant_sections(
                        doc.processed_content, keywords, max_sections=2
                    )
                    context += f"\n\nFrom {doc.title}:\n{relevant_sections}"
        
        # Limit context size
        if len(context) > 12000:
            context = context[:12000] + "\n...[content truncated]..."
        
        system_prompt = """You are a helpful HR assistant. Answer employee questions based only on the handbook content provided. Be accurate, concise, and professional."""
        
        user_prompt = f"""Employee Handbook Context:
{context}

Employee Question: {user_message}

Provide a helpful answer based on the handbook information."""
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=max_tokens,
            temperature=0.3
        )
        
        bot_response = response.choices[0].message.content.strip()
        
        if relevant_docs:
            source_list = ", ".join([doc.title for doc in relevant_docs[:3]])
            bot_response += f"\n\n?? Sources: {source_list}"
        
        return bot_response, relevant_docs
        
    except ImportError:
        return "OpenAI integration not available. Please install the openai package.", []
    except Exception as e:
        return f"Error generating OpenAI response: {str(e)}", []


# Main function to get AI response using configured backend
def get_ai_response(user_message: str, backend: str = 'groq') -> Tuple[str, List]:
    """
    Main function to get AI response using different backends
    
    Available backends:
    - 'groq': Groq AI API (default, fast and efficient)
    - 'openai': OpenAI GPT integration  
    - 'simple': Fallback to simple keyword matching
    """
    
    if backend == 'groq':
        return generate_groq_response(user_message)
    elif backend == 'openai':
        return generate_openai_response(user_message)
    else:
        # Fall back to the simple method from views.py
        from .views import generate_bot_response
        return generate_bot_response(user_message)


# Configuration for Django settings
def get_ai_config():
    """
    Get AI configuration from Django settings
    """
    return {
        'backend': getattr(settings, 'HANDBOOK_AI_BACKEND', 'groq'),
        'groq_api_key': getattr(settings, 'GROQ_API_KEY', ''),
        'openai_api_key': getattr(settings, 'OPENAI_API_KEY', ''),
        'max_tokens': getattr(settings, 'HANDBOOK_AI_MAX_TOKENS', 700),
        'max_context_length': getattr(settings, 'HANDBOOK_AI_MAX_CONTEXT', 15000),
    }