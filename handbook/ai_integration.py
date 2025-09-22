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
GROQ_API_KEY = getattr(settings, 'GROQ_API_KEY', '')
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
        
        # Score all paragraphs from all documents
        all_paragraphs = []
        for doc in documents:
            if doc.processed_content:
                paragraphs = [p.strip() for p in doc.processed_content.split('\n\n') if p.strip()]
                for p in paragraphs:
                    score = calculate_relevance(keywords, p)
                    if score > 0.01: # Stricter threshold for initial filtering
                        all_paragraphs.append({'score': score, 'text': p, 'doc_title': doc.title})

        # Sort all paragraphs by relevance
        all_paragraphs.sort(key=lambda x: x['score'], reverse=True)

        # Build context from the most relevant paragraphs, avoiding redundancy
        added_paragraphs = set()
        final_paragraphs = []
        doc_titles = set()

        for p_data in all_paragraphs:
            if len(final_paragraphs) < 5: # Limit to top 5 paragraphs overall
                # Simple check to avoid adding very similar paragraphs
                if p_data['text'][:100] not in added_paragraphs:
                    final_paragraphs.append(f"From {p_data['doc_title']}:\n{p_data['text']}")
                    added_paragraphs.add(p_data['text'][:100])
                    doc_titles.add(p_data['doc_title'])
        
        context = "\n\n".join(final_paragraphs)
        relevant_docs = list(doc_titles)

        # Limit context size to avoid API limits
        max_context_chars = 15000
        if len(context) > max_context_chars:
            context = context[:max_context_chars] + "\n...[content truncated]..."
        
        if not context:
             return "I couldn't find any relevant information in the handbook for your question. Please try rephrasing or contact HR.", []

        # Build the AI prompt
        system_prompt = """You are a helpful HR assistant for employees. Answer questions based ONLY on the employee handbook content provided.

Guidelines:
- Provide accurate, helpful answers based on company policies.
- If the information isn't in the handbook, say so clearly.
- Be concise but thorough.
- Use a professional but friendly tone.
- Quote the relevant policy details and procedures directly when possible.
- For complex questions, break down the answer into clear steps.
- Do not invent information. If the context does not contain the answer, state that the information is not available in the provided content."""

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
                source_list = ", ".join(relevant_docs[:3])
                ai_response += f"\n\n?? Sources: {source_list}"
            
            return ai_response, [doc for doc in documents if doc.title in relevant_docs]
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
    if not keywords or not content:
        return 0.0
    
    content_lower = content.lower()
    total_score = 0
    
    # Use a set for faster keyword checking
    keyword_set = set(keywords)
    
    # Find unique words in content to avoid over-counting in very long text
    content_words = set(re.findall(r'\b\w+\b', content_lower))
    
    matched_keywords = keyword_set.intersection(content_words)
    
    if not matched_keywords:
        return 0.0

    # Score based on the presence and weight of keywords
    for keyword in matched_keywords:
        # Weight longer keywords more heavily
        total_score += len(keyword)

    # Normalize score based on the number of unique keywords found vs total keywords
    # This gives a density score.
    relevance = total_score * (len(matched_keywords) / len(keywords))
    
    # Further boost score for paragraphs that contain a high density of keywords
    # This helps shorter, direct paragraphs to stand out.
    content_len = len(content_words)
    if content_len > 0:
        density = len(matched_keywords) / content_len
        if density > 0.1: # Boost if keyword density is high
            relevance *= 1.5

    # Normalize to a 0-1 range (approximate)
    # A perfect match of 10 keywords with average length 5 would be 50 * 1 = 50.
    # A very high relevance score could be around 100. Let's use that as a ceiling.
    return min(relevance / 100.0, 1.0)


def extract_relevant_sections(content: str, keywords: List[str], max_sections: int = 1) -> str:
    """
    Extract the most relevant sections from content based on keywords
    """
    # Split content into paragraphs
    paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
    
    if not paragraphs:
        return ""

    # Score each paragraph
    paragraph_scores = []
    for i, paragraph in enumerate(paragraphs):
        score = calculate_relevance(keywords, paragraph)
        if score > 0:
            paragraph_scores.append((score, i, paragraph))
    
    # Sort by relevance score and take top section
    paragraph_scores.sort(key=lambda x: x[0], reverse=True)
    
    if not paragraph_scores:
        return ""

    # Return the single most relevant paragraph
    top_paragraph = paragraph_scores[0][2]
    
    # Limit paragraph length
    if len(top_paragraph) > 500:
        top_paragraph = top_paragraph[:500] + "..."
            
    return top_paragraph


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
            if relevance > 0.01: # Adjusted threshold
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
        
        # Score all paragraphs from all documents
        all_paragraphs = []
        for doc in documents:
            if doc.processed_content:
                paragraphs = [p.strip() for p in doc.processed_content.split('\n\n') if p.strip()]
                for p in paragraphs:
                    score = calculate_relevance(keywords, p)
                    if score > 0.01:
                        all_paragraphs.append({'score': score, 'text': p, 'doc_title': doc.title})

        # Sort all paragraphs by relevance
        all_paragraphs.sort(key=lambda x: x['score'], reverse=True)

        # Build context from the most relevant paragraphs
        final_paragraphs = []
        doc_titles = set()
        for p_data in all_paragraphs[:5]: # Top 5 paragraphs
            final_paragraphs.append(f"From {p_data['doc_title']}:\n{p_data['text']}")
            doc_titles.add(p_data['doc_title'])
        
        context = "\n\n".join(final_paragraphs)
        relevant_docs = list(doc_titles)

        # Limit context size
        if len(context) > 12000:
            context = context[:12000] + "\n...[content truncated]..."
        
        if not context:
            return "I couldn't find relevant information in the handbook.", []

        system_prompt = """You are a helpful HR assistant. Answer employee questions based only on the handbook content provided. Be accurate, concise, and professional. Quote relevant text where possible."""
        
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
            source_list = ", ".join(relevant_docs[:3])
            bot_response += f"\n\n?? Sources: {source_list}"
        
        return bot_response, [doc for doc in documents if doc.title in relevant_docs]
        
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