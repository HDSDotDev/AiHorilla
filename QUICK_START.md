# ?? Quick Start Guide - Handbook AI Chat Assistant

## ?? Final Setup Steps

### 1. **AI Configuration** 
The Groq API key is already configured in the code:
```
API Key: REMOVED_GROQ_API_KEY
Model: meta-llama/llama-4-scout-17b-16e-instruct
```

### 2. **Upload Sample Handbook**
1. Convert `Employee_Handbook_Complete.md` to PDF (use any online converter)
2. Or create your own company handbook PDF
3. Upload via: `/handbook/upload/`

### 3. **Test the System**
```bash
# Run the test script
python test_ai.py

# Or test via web interface
# Navigate to: http://127.0.0.1:8000/handbook/
```

### 4. **Sample Questions to Try**
- "What is the vacation policy?"
- "How do I request time off?"
- "What are the company core values?"
- "How do I report workplace harassment?"
- "What should I do in a fire emergency?"
- "What health insurance do we have?"
- "When are performance reviews?"

## ?? You're Ready!

The handbook chat assistant is now **fully functional** with:
- ? Advanced AI responses via Groq
- ? Professional HR chat interface  
- ? Document upload and management
- ? Source attribution and citations
- ? Mobile-responsive design
- ? Sidebar integration with Horilla

**Navigate to `/handbook/` and start chatting with your AI-powered HR assistant!**

---

## ??? Troubleshooting

**If AI responses aren't working:**
1. Check internet connection
2. Verify Groq API key is valid
3. Upload a handbook PDF first
4. Try the fallback: Change `HANDBOOK_AI_BACKEND = 'simple'` in settings

**If templates aren't loading:**
- Already fixed! Templates now extend `index.html` correctly

**If sidebar isn't showing:**
- Already configured! "Handbook" should appear in the left navigation

The system is production-ready and fully tested! ??