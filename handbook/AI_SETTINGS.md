# AI Configuration for Handbook Chat Assistant

## Add these settings to your Django settings.py or environment variables

# Groq AI Configuration (Primary)
GROQ_API_KEY = ''

# AI Backend Configuration
HANDBOOK_AI_BACKEND = 'groq'  # Options: 'groq', 'openai', 'simple'
HANDBOOK_AI_MAX_TOKENS = 700
HANDBOOK_AI_MAX_CONTEXT = 15000

# Alternative AI Services (Optional)
# OPENAI_API_KEY = 'your_openai_api_key_here'

# Add to Django settings.py:
"""
# Handbook AI Configuration
GROQ_API_KEY = env('GROQ_API_KEY', default='')
HANDBOOK_AI_BACKEND = env('HANDBOOK_AI_BACKEND', default='groq')
HANDBOOK_AI_MAX_TOKENS = env.int('HANDBOOK_AI_MAX_TOKENS', default=700)
HANDBOOK_AI_MAX_CONTEXT = env.int('HANDBOOK_AI_MAX_CONTEXT', default=15000)
"""

# Add to .env file:
"""
GROQ_API_KEY=
HANDBOOK_AI_BACKEND=groq
HANDBOOK_AI_MAX_TOKENS=700
HANDBOOK_AI_MAX_CONTEXT=15000
"""