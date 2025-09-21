"""
Quick test script for the Handbook AI functionality
Run this after setting up the system to verify everything works
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'horilla.settings')
django.setup()

from handbook.ai_integration import get_ai_response, get_ai_config

def test_ai_functionality():
    """Test the AI integration with sample questions"""
    
    print("?? Testing Handbook AI Integration...")
    print("=" * 50)
    
    # Get AI configuration
    config = get_ai_config()
    print(f"AI Backend: {config.get('backend', 'unknown')}")
    print(f"Max Tokens: {config.get('max_tokens', 'unknown')}")
    print()
    
    # Test questions
    test_questions = [
        "What is the vacation policy?",
        "How do I report sick leave?", 
        "What health insurance benefits are available?",
        "What should I do in an emergency?",
        "How do I file a grievance?"
    ]
    
    for i, question in enumerate(test_questions, 1):
        print(f"Test {i}: {question}")
        print("-" * 30)
        
        try:
            response, docs = get_ai_response(question)
            print(f"Response: {response[:200]}...")
            print(f"Documents found: {len(docs)}")
            if docs:
                print(f"Sources: {', '.join([doc.title for doc in docs])}")
            print()
            
        except Exception as e:
            print(f"Error: {str(e)}")
            print()
    
    print("? AI Testing Complete!")

if __name__ == "__main__":
    test_ai_functionality()