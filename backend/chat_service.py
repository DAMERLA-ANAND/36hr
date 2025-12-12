"""
Chat Service for managing chatbot interactions with Gemini API.
Implements function calling for job search and context management.
"""

import os
import json
import logging
from typing import Optional, List, Tuple
from datetime import datetime
import google.generativeai as genai
from google.generativeai import protos
from bson import ObjectId

from db import db
from jsearch_client import search_jobs, get_job_details, extract_job_cards_from_response, extract_job_card_data

logger = logging.getLogger(__name__)

# Configure Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

# System prompt for the career assistant chatbot
SYSTEM_PROMPT = """You are JobBot AI, a friendly and professional career assistant. Your role is to:

1. Help users find relevant jobs based on their profile, skills, and preferences
2. Provide resume correction tips and suggestions
3. Offer interview preparation tips and guidance
4. Help users answer application questions for specific jobs
5. Give career and job-related advice across any domain
6. Suggest AI Mock Interviews for saved or applied jobs

RESPONSE STYLE - VERY IMPORTANT:
- Keep responses SHORT and CONCISE - aim for 2-4 sentences maximum for most responses
- Use bullet points for lists instead of long paragraphs
- Be direct and actionable - get to the point quickly
- Avoid repetitive or verbose explanations
- Only provide detailed responses when specifically asked for in-depth information
- When showing job results, briefly summarize what you found - the job cards will show the details

Guidelines:
- Be conversational, helpful, and encouraging
- Use the user's profile context to provide personalized recommendations
- When searching for jobs, keep the query SIMPLE - don't over-filter
- When a job is selected, provide brief insights about the role
- Offer actionable advice in concise bullet points
- Be supportive but honest
- When a user saves or applies to a job, proactively suggest: "Would you like to practice for this interview? You can try our AI Mock Interview feature for realistic voice-based interview simulation!"

You have access to the following tools:
- search_jobs: Search for job listings based on various criteria
- get_job_details: Get detailed information about a specific job

When users ask about jobs, search with BROAD queries to find more results. Avoid using too many filters.
"""

# Define function declarations for Gemini using proper protobuf types
def get_search_jobs_function():
    """Create the search_jobs function declaration using protos."""
    return protos.FunctionDeclaration(
        name="search_jobs",
        description="Search for job listings. IMPORTANT: Keep queries SIMPLE to find more results. Use minimal filters - only add filters when the user EXPLICITLY asks for them. Start with just the job title/role, add location only if user specifies one.",
        parameters=protos.Schema(
            type=protos.Type.OBJECT,
            properties={
                "query": protos.Schema(
                    type=protos.Type.STRING,
                    description="Keep it SIMPLE: just the job title or role. Examples: 'software developer', 'frontend developer', 'data scientist'. Only add location if user explicitly mentioned one."
                ),
                "country": protos.Schema(
                    type=protos.Type.STRING,
                    description="ISO-3166-1 alpha-2 country code (e.g., 'us', 'uk'). Only use if user specifies a country. Default is 'us'."
                ),
                "date_posted": protos.Schema(
                    type=protos.Type.STRING,
                    description="ONLY use if user asks for recent jobs. Options: 'all', 'today', '3days', 'week', 'month'. Default is 'all'."
                ),
                "employment_types": protos.Schema(
                    type=protos.Type.STRING,
                    description="ONLY use if user explicitly asks for specific employment type. Options: FULLTIME, CONTRACTOR, PARTTIME, INTERN"
                ),
                "job_requirements": protos.Schema(
                    type=protos.Type.STRING,
                    description="ONLY use if user explicitly asks for experience level. Options: under_3_years_experience, more_than_3_years_experience, no_experience, no_degree"
                ),
                "work_from_home": protos.Schema(
                    type=protos.Type.BOOLEAN,
                    description="ONLY set to true if user explicitly asks for remote/work-from-home jobs"
                ),
                "num_pages": protos.Schema(
                    type=protos.Type.INTEGER,
                    description="Number of pages (1-5). Default is 2 to get more results."
                )
            },
            required=["query"]
        )
    )

def get_job_details_function():
    """Create the get_job_details function declaration using protos."""
    return protos.FunctionDeclaration(
        name="get_job_details",
        description="Get detailed information about a specific job by its ID. Use this when a user selects a job or asks for more details about a particular position.",
        parameters=protos.Schema(
            type=protos.Type.OBJECT,
            properties={
                "job_id": protos.Schema(
                    type=protos.Type.STRING,
                    description="The unique identifier of the job to get details for"
                ),
                "country": protos.Schema(
                    type=protos.Type.STRING,
                    description="ISO-3166-1 alpha-2 country code. Default is 'us'."
                )
            },
            required=["job_id"]
        )
    )

# Create the model with function calling capability
def get_chat_model():
    """Get a Gemini model configured for chat with function calling."""
    tools = protos.Tool(
        function_declarations=[
            get_search_jobs_function(),
            get_job_details_function()
        ]
    )
    return genai.GenerativeModel(
        'gemini-2.5-flash',
        tools=[tools],
        system_instruction=SYSTEM_PROMPT
    )


async def create_permanent_context(user_data: dict) -> str:
    """
    Create a minimized permanent context from user profile for the chat session.
    This context will be used throughout the entire chat.
    
    Args:
        user_data: User document from database
    
    Returns:
        Minimized context string
    """
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    # Build user profile summary
    profile_parts = []
    if user_data.get("name"):
        profile_parts.append(f"Name: {user_data['name']}")
    if user_data.get("location"):
        profile_parts.append(f"Location: {user_data['location']}")
    if user_data.get("skills"):
        profile_parts.append(f"Skills: {', '.join(user_data['skills'])}")
    if user_data.get("experience"):
        profile_parts.append(f"Experience: {'; '.join(user_data['experience'])}")
    if user_data.get("education"):
        profile_parts.append(f"Education: {'; '.join(user_data['education'])}")
    if user_data.get("profile_summary"):
        profile_parts.append(f"Profile Summary: {user_data['profile_summary']}")
    if user_data.get("projects"):
        profile_parts.append(f"Projects: {'; '.join(user_data['projects'][:3])}")  # Limit to 3
    if user_data.get("certificationsAndAchievementsAndAwards"):
        certs = user_data['certificationsAndAchievementsAndAwards'][:3]  # Limit to 3
        profile_parts.append(f"Certifications/Awards: {'; '.join(certs)}")
    
    full_profile = "\n".join(profile_parts)
    
    prompt = f"""Create a concise career profile summary (max 200 words) from the following user information. 
Focus on key skills, experience level, and what kind of jobs would suit them. 
This will be used as context for a job search chatbot.

User Profile:
{full_profile}

Create a professional summary that captures the essence of this candidate's profile for job matching purposes."""

    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        logger.error(f"Error creating permanent context: {str(e)}")
        # Fallback to simple summary
        return f"User: {user_data.get('name', 'Unknown')}. Skills: {', '.join(user_data.get('skills', [])[:10])}. Location: {user_data.get('location', 'Not specified')}."


async def summarize_conversation(messages: List[dict]) -> str:
    """
    Create a summary of conversation history.
    
    Args:
        messages: List of message dictionaries
    
    Returns:
        Summary string
    """
    if not messages:
        return ""
    
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    # Format messages for summarization
    conversation_text = "\n".join([
        f"{msg['sender'].upper()}: {msg['message']}" 
        for msg in messages
    ])
    
    prompt = f"""Summarize the following conversation between a user and a job search assistant.
Focus on:
1. What jobs/positions the user is interested in
2. Any preferences mentioned (location, salary, remote, etc.)
3. Key advice or information provided
4. Any jobs that were discussed or selected

Keep the summary concise (max 150 words).

Conversation:
{conversation_text}

Summary:"""

    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        logger.error(f"Error summarizing conversation: {str(e)}")
        return ""


def build_context_prompt(chat_context: dict, current_message: str, selected_job_id: Optional[str] = None) -> str:
    """
    Build the context prompt combining permanent context, summary, and recent messages.
    
    Args:
        chat_context: Chat context dictionary
        current_message: Current user message
        selected_job_id: Optional job ID if user selected a job
    
    Returns:
        Complete context prompt
    """
    parts = []
    
    # Add permanent context (user profile)
    if chat_context.get("permanent_context"):
        parts.append(f"[USER PROFILE]\n{chat_context['permanent_context']}\n")
    
    # Add conversation summary
    if chat_context.get("conversation_summary"):
        parts.append(f"[CONVERSATION HISTORY SUMMARY]\n{chat_context['conversation_summary']}\n")
    
    # Add recent messages (last 5 exchanges)
    if chat_context.get("recent_messages"):
        parts.append("[RECENT CONVERSATION]")
        for msg in chat_context["recent_messages"][-10:]:  # Last 10 messages (5 exchanges)
            parts.append(f"{msg['sender'].upper()}: {msg['message']}")
        parts.append("")
    
    # Add selected job context if applicable
    if selected_job_id:
        parts.append(f"[CONTEXT: User has selected job with ID: {selected_job_id}. Provide insights about this specific job.]\n")
    
    # Add current message
    parts.append(f"[CURRENT MESSAGE]\nUSER: {current_message}")
    
    return "\n".join(parts)


async def execute_function_call(function_name: str, function_args: dict) -> Tuple[dict, Optional[List[dict]]]:
    """
    Execute a function call and return the result.
    
    Args:
        function_name: Name of the function to execute
        function_args: Arguments for the function
    
    Returns:
        Tuple of (function result, job cards if applicable)
    """
    job_cards = None
    
    if function_name == "search_jobs":
        result = await search_jobs(
            query=function_args.get("query", ""),
            num_pages=min(function_args.get("num_pages", 1), 3),  # Limit to 3 pages
            country=function_args.get("country", "us"),
            date_posted=function_args.get("date_posted", "all"),
            employment_types=function_args.get("employment_types"),
            job_requirements=function_args.get("job_requirements"),
            work_from_home=function_args.get("work_from_home", False)
        )
        
        # Extract job cards for frontend
        job_cards = extract_job_cards_from_response(result)
        
        # Create a summary for the model
        jobs_data = result.get("data", [])
        if jobs_data:
            job_summaries = []
            for job in jobs_data[:10]:  # Limit to 10 jobs for context
                summary = f"- {job.get('job_title')} at {job.get('employer_name')} ({job.get('job_location', 'Location not specified')})"
                if job.get('job_salary') or (job.get('job_min_salary') and job.get('job_max_salary')):
                    if job.get('job_min_salary') and job.get('job_max_salary'):
                        summary += f" - ${job['job_min_salary']:,.0f}-${job['job_max_salary']:,.0f}"
                    elif job.get('job_salary'):
                        summary += f" - {job['job_salary']}"
                job_summaries.append(summary)
            
            return {
                "status": "success",
                "total_jobs_found": len(jobs_data),
                "jobs_summary": "\n".join(job_summaries)
            }, job_cards
        else:
            return {
                "status": "no_results",
                "message": "No jobs found matching the search criteria."
            }, []
    
    elif function_name == "get_job_details":
        result = await get_job_details(
            job_id=function_args.get("job_id", ""),
            country=function_args.get("country", "us")
        )
        
        jobs_data = result.get("data", [])
        if jobs_data:
            job = jobs_data[0]
            # Extract detailed info for the model
            job_details = {
                "status": "success",
                "job_title": job.get("job_title"),
                "employer_name": job.get("employer_name"),
                "job_location": job.get("job_location"),
                "job_description": job.get("job_description", "")[:2000],  # Limit description length
                "job_employment_type": job.get("job_employment_type"),
                "job_apply_link": job.get("job_apply_link"),
                "job_highlights": job.get("job_highlights", {}),
                "job_qualifications": job.get("job_highlights", {}).get("Qualifications", []),
                "job_responsibilities": job.get("job_highlights", {}).get("Responsibilities", [])
            }
            
            if job.get("job_min_salary") and job.get("job_max_salary"):
                job_details["salary_range"] = f"${job['job_min_salary']:,.0f} - ${job['job_max_salary']:,.0f} {job.get('job_salary_period', 'yearly')}"
            
            # Return full job details as selected job
            job_card = extract_job_card_data(job)
            return job_details, job_card
        else:
            return {
                "status": "error",
                "message": "Job details not found."
            }, None
    
    return {"status": "error", "message": f"Unknown function: {function_name}"}, None


async def process_chat_message(
    email: str,
    chat_id: str,
    user_message: str,
    selected_job_id: Optional[str] = None
) -> dict:
    """
    Process a chat message and generate a response using Gemini with function calling.
    
    Args:
        email: User's email
        chat_id: Chat session ID
        user_message: User's message
        selected_job_id: Optional job ID if user selected a job
    
    Returns:
        dict with response message, optional job cards, and optional selected job details
    """
    # Fetch user and chat data
    user = await db.users.find_one({"email": email})
    if not user:
        return {"message": "User not found. Please complete onboarding first.", "jobs": None}
    
    # Find the chat in user's chat history
    chat_history = user.get("chat_history", [])
    chat = None
    chat_index = -1
    for i, c in enumerate(chat_history):
        if str(c.get("_id")) == chat_id or str(c.get("id")) == chat_id:
            chat = c
            chat_index = i
            break
    
    if not chat:
        return {"message": "Chat session not found.", "jobs": None}
    
    # Get chat context
    chat_context = chat.get("context", {
        "permanent_context": "",
        "conversation_summary": "",
        "recent_messages": []
    })
    
    # Build the prompt with context
    context_prompt = build_context_prompt(chat_context, user_message, selected_job_id)
    
    # Get selected job details if job_id is provided
    selected_job_details = None
    if selected_job_id:
        job_result = await get_job_details(selected_job_id)
        if job_result.get("data"):
            selected_job_details = extract_job_card_data(job_result["data"][0])
            context_prompt += f"\n\n[Selected Job Details: {selected_job_details.get('job_title')} at {selected_job_details.get('employer_name')}]"
    
    # Create chat model with function calling
    model = get_chat_model()
    
    # Generate response
    try:
        print(f"\n[CHAT_SERVICE] Processing message for email: {email}, chat_id: {chat_id}")
        print(f"[CHAT_SERVICE] User message: {user_message[:100]}...")
        print(f"[CHAT_SERVICE] Selected job ID: {selected_job_id}")
        print(f"[CHAT_SERVICE] Context prompt length: {len(context_prompt)} chars")
        
        # Start a chat session for proper multi-turn with function calling
        chat_session = model.start_chat(enable_automatic_function_calling=False)
        
        # Send initial message
        response = chat_session.send_message(context_prompt)
        print(f"[CHAT_SERVICE] Got response from Gemini")
        
        # Check for function calls
        job_cards = None
        final_response_text = ""
        
        # Handle function calls if present
        if response.candidates[0].content.parts:
            print(f"[CHAT_SERVICE] Response has {len(response.candidates[0].content.parts)} parts")
            
            # Check if there's a function call
            function_call_part = None
            text_response = ""
            
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'function_call') and part.function_call:
                    function_call_part = part.function_call
                elif hasattr(part, 'text') and part.text:
                    text_response += part.text
            
            if function_call_part:
                function_name = function_call_part.name
                print(f"[CHAT_SERVICE] Function call detected: {function_name}")
                
                # Convert args properly - handle MapComposite type
                try:
                    if function_call_part.args:
                        function_args = {key: value for key, value in function_call_part.args.items()}
                    else:
                        function_args = {}
                    print(f"[CHAT_SERVICE] Function args: {function_args}")
                except Exception as arg_error:
                    print(f"[CHAT_SERVICE] Error converting args: {arg_error}")
                    function_args = {}
                
                logger.info(f"Executing function: {function_name} with args: {function_args}")
                
                # Execute the function
                function_result, cards = await execute_function_call(function_name, function_args)
                print(f"[CHAT_SERVICE] Function result status: {function_result.get('status', 'unknown')}")
                
                if function_name == "search_jobs" and cards:
                    job_cards = cards
                    print(f"[CHAT_SERVICE] Got {len(cards)} job cards")
                elif function_name == "get_job_details" and cards:
                    selected_job_details = cards
                    print(f"[CHAT_SERVICE] Got job details")
                
                # Send function result back using chat session
                print(f"[CHAT_SERVICE] Sending function result back to Gemini...")
                function_response_part = protos.Part(
                    function_response=protos.FunctionResponse(
                        name=function_name,
                        response={"result": json.dumps(function_result)}
                    )
                )
                
                # Send the function response through the chat session
                # Pass the Part directly - ChatSession will handle the wrapping
                final_response = chat_session.send_message(function_response_part)
                
                # Extract text from response, handling potential function calls
                try:
                    final_response_text = final_response.text
                except ValueError:
                    # Response might contain another function call, extract any text parts
                    for part in final_response.candidates[0].content.parts:
                        if hasattr(part, 'text') and part.text:
                            final_response_text = part.text
                            break
                    if not final_response_text:
                        final_response_text = "I found the information you requested. Let me know if you need anything else!"
                
                print(f"[CHAT_SERVICE] Got final response: {final_response_text[:100] if final_response_text else 'empty'}...")
            else:
                final_response_text = text_response
                print(f"[CHAT_SERVICE] Got text response: {final_response_text[:100] if final_response_text else 'empty'}...")
        
        if not final_response_text:
            final_response_text = response.text if hasattr(response, 'text') else "I'm here to help you with your job search. What would you like to know?"
        
        # Update chat messages
        timestamp = datetime.utcnow().isoformat()
        new_user_message = {
            "sender": "user",
            "message": user_message,
            "timestamp": timestamp,
            "selected_job_id": selected_job_id
        }
        new_bot_message = {
            "sender": "bot",
            "message": final_response_text,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Update recent messages in context (keep last 10 = 5 exchanges)
        recent_messages = chat_context.get("recent_messages", [])
        recent_messages.extend([new_user_message, new_bot_message])
        if len(recent_messages) > 10:
            # Summarize older messages and update summary
            old_messages = recent_messages[:-10]
            if old_messages:
                current_summary = chat_context.get("conversation_summary", "")
                messages_to_summarize = old_messages
                if current_summary:
                    messages_to_summarize = [{"sender": "system", "message": f"Previous summary: {current_summary}"}] + old_messages
                new_summary = await summarize_conversation(messages_to_summarize)
                chat_context["conversation_summary"] = new_summary
            recent_messages = recent_messages[-10:]
        
        chat_context["recent_messages"] = recent_messages
        
        # Update chat in database
        messages = chat.get("messages", [])
        messages.append({
            "sender": "user",
            "message": user_message,
            "timestamp": timestamp
        })
        messages.append({
            "sender": "bot",
            "message": final_response_text,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Update chat name if it's the first real message
        chat_name = chat.get("chat_name", "New Chat")
        if len(messages) <= 3:  # Initial bot greeting + first user message + response
            chat_name = user_message[:50] + ("..." if len(user_message) > 50 else "")
        
        # Update in database
        await db.users.update_one(
            {"email": email, f"chat_history.{chat_index}._id": chat["_id"]},
            {
                "$set": {
                    f"chat_history.{chat_index}.messages": messages,
                    f"chat_history.{chat_index}.context": chat_context,
                    f"chat_history.{chat_index}.chat_name": chat_name
                }
            }
        )
        
        return {
            "message": final_response_text,
            "jobs": job_cards,
            "selected_job_details": selected_job_details,
            "chat_name": chat_name
        }
        
    except Exception as e:
        import traceback
        print(f"[CHAT_SERVICE] ERROR in process_chat_message: {str(e)}")
        print(f"[CHAT_SERVICE] Error type: {type(e)}")
        print(f"[CHAT_SERVICE] Traceback:\n{traceback.format_exc()}")
        logger.error(f"Error processing chat message: {str(e)}")
        return {
            "message": "I apologize, but I encountered an error. Please try again.",
            "jobs": None,
            "error": str(e)
        }


async def create_new_chat(email: str) -> dict:
    """
    Create a new chat session for a user.
    
    Args:
        email: User's email
    
    Returns:
        dict with chat_id, chat_name, and initial_message
    """
    # Fetch user data
    user = await db.users.find_one({"email": email})
    if not user:
        return {"error": "User not found. Please complete onboarding first."}
    
    # Create permanent context from user profile
    permanent_context = await create_permanent_context(user)
    
    # Generate chat ID
    chat_id = ObjectId()
    
    # Initial bot message
    user_name = user.get("name", "").split()[0] if user.get("name") else "there"
    initial_message = f"""Hello {user_name}! 👋 I'm JobBot AI, your personal career assistant.

I've reviewed your profile and I'm ready to help you with:
• Finding jobs that match your skills and experience
• Resume tips and improvement suggestions
• Interview preparation and guidance
• Answering application questions

What would you like to explore today?"""
    
    # Create chat object
    new_chat = {
        "_id": chat_id,
        "chat_name": "New Job Search",
        "messages": [
            {
                "sender": "bot",
                "message": initial_message,
                "timestamp": datetime.utcnow().isoformat()
            }
        ],
        "context": {
            "permanent_context": permanent_context,
            "conversation_summary": "",
            "recent_messages": []
        },
        "created_at": datetime.utcnow().isoformat()
    }
    
    # Add chat to user's chat history
    await db.users.update_one(
        {"email": email},
        {"$push": {"chat_history": new_chat}}
    )
    
    return {
        "chat_id": str(chat_id),
        "chat_name": "New Job Search",
        "initial_message": initial_message
    }


async def get_chat_messages(email: str, chat_id: str) -> dict:
    """
    Get all messages for a specific chat.
    
    Args:
        email: User's email
        chat_id: Chat session ID
    
    Returns:
        dict with messages and chat_name
    """
    user = await db.users.find_one({"email": email})
    if not user:
        return {"error": "User not found"}
    
    chat_history = user.get("chat_history", [])
    for chat in chat_history:
        if str(chat.get("_id")) == chat_id or str(chat.get("id")) == chat_id:
            return {
                "messages": chat.get("messages", []),
                "chat_name": chat.get("chat_name", "New Chat")
            }
    
    return {"error": "Chat not found"}
