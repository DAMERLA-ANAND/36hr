import os
import google.generativeai as genai

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables.")

genai.configure(api_key=GEMINI_API_KEY)

# Initialize the model for use in other files
# Using gemini-1.5-flash as it is the current stable version. 
# If 2.5 becomes available, it can be updated.
model = genai.GenerativeModel('gemini-2.5-flash-lite')