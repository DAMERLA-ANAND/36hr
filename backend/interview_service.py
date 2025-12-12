"""
Interview Service for AI Mock Interview functionality.
Integrates with Retell AI for voice-based interview simulations.
Uses MongoDB for storing interview data (migrated from Supabase schema).
"""

import os
import json
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from bson import ObjectId
import httpx
import google.generativeai as genai

from db import db

logger = logging.getLogger(__name__)

# Environment variables
RETELL_API_KEY = os.getenv("RETELL_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Configure Gemini for question generation (alternative to OpenAI)
genai.configure(api_key=GEMINI_API_KEY)

# Retell API base URL
RETELL_API_URL = "https://api.retellai.com"

# Default interviewers (matching Supabase interviewer table)
DEFAULT_INTERVIEWERS = [
    {
        "id": 1,
        "agent_id": os.getenv("RETELL_AGENT_ID_1", "agent_ed1114a2461435a6cb630cd771"),
        "name": "Explorer Lisa",
        "description": "Empathetic interviewer who explores your experiences in depth with thoughtful follow-ups",
        "image": "/interviewers/Lisa.png",
        "audio": "Lisa.wav",
        "empathy": 7,
        "exploration": 10,
        "rapport": 7,
        "speed": 5
    },
    {
        "id": 2,
        "agent_id": os.getenv("RETELL_AGENT_ID_2", "agent_d537dae23eb87a23bf6a2bbfc8"),
        "name": "Empathetic Bob",
        "description": "Friendly and understanding interviewer who creates a comfortable interview atmosphere",
        "image": "/interviewers/Bob.png",
        "audio": "Bob.wav",
        "empathy": 10,
        "exploration": 7,
        "rapport": 7,
        "speed": 5
    }
]


# ==================== QUESTION GENERATION ====================

QUESTION_GENERATION_PROMPT = """You are an expert interviewer who crafts insightful questions to evaluate candidates.

Interview Title: {name}
Interview Objective: {objective}
Job Description Context: {context}

Number of questions to be generated: {number}

Follow these detailed guidelines when crafting the questions:
- Focus on evaluating the candidate's technical knowledge and their experience working on relevant projects.
- Include questions designed to assess problem-solving skills through practical examples.
- Soft skills such as communication, teamwork, and adaptability should be addressed.
- Maintain a professional yet approachable tone.
- Ask concise and precise open-ended questions (30 words or less for clarity).

Generate a 50 word or less second-person description about the interview.

Output as JSON with this format:
{{
  "description": "Interview description here...",
  "questions": [
    {{"question": "Question 1 here?"}},
    {{"question": "Question 2 here?"}}
  ]
}}
"""


async def generate_interview_questions(
    name: str,
    objective: str,
    context: str,
    number: int = 5
) -> Dict[str, Any]:
    """
    Generate interview questions using Gemini API.
    
    Args:
        name: Interview title
        objective: Interview objective
        context: Job description or additional context
        number: Number of questions to generate
    
    Returns:
        Dictionary with description and questions
    """
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        prompt = QUESTION_GENERATION_PROMPT.format(
            name=name,
            objective=objective,
            context=context,
            number=number
        )
        
        response = model.generate_content(prompt)
        
        # Parse JSON from response
        response_text = response.text
        # Clean up markdown code blocks if present
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]
        
        result = json.loads(response_text.strip())
        
        # Add IDs to questions
        for i, q in enumerate(result.get("questions", [])):
            q["id"] = str(i + 1)
            q["follow_up_count"] = 2  # Default follow-up count
        
        logger.info(f"Generated {len(result.get('questions', []))} interview questions")
        return result
        
    except Exception as e:
        logger.error(f"Error generating interview questions: {str(e)}")
        # Return default questions on error
        return {
            "description": "A comprehensive interview to assess your skills and experience.",
            "questions": [
                {"id": "1", "question": "Tell me about yourself and your background.", "follow_up_count": 2},
                {"id": "2", "question": "What interests you about this role?", "follow_up_count": 2},
                {"id": "3", "question": "Describe a challenging project you worked on.", "follow_up_count": 2},
                {"id": "4", "question": "How do you handle tight deadlines?", "follow_up_count": 2},
                {"id": "5", "question": "Where do you see yourself in 5 years?", "follow_up_count": 2}
            ]
        }


# ==================== INTERVIEW CRUD OPERATIONS ====================

async def create_interview(
    user_email: str,
    name: str,
    objective: str,
    interviewer_id: int,
    questions: List[Dict],
    description: str,
    time_duration: str = "10",
    job_id: Optional[str] = None,
    job_title: Optional[str] = None,
    company_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a new interview session.
    
    Args:
        user_email: User's email
        name: Interview name
        objective: Interview objective
        interviewer_id: ID of the AI interviewer
        questions: List of interview questions
        description: Interview description
        time_duration: Duration in minutes
        job_id: Optional job ID if interview is for a specific job
        job_title: Optional job title
        company_name: Optional company name
    
    Returns:
        Created interview document
    """
    interview_id = str(ObjectId())
    
    interview_doc = {
        "_id": ObjectId(interview_id),
        "id": interview_id,
        "user_email": user_email,
        "name": name,
        "description": description,
        "objective": objective,
        "interviewer_id": interviewer_id,
        "questions": questions,
        "question_count": len(questions),
        "time_duration": time_duration,
        "is_active": True,
        "is_anonymous": False,
        "response_count": 0,
        "respondents": [],
        "insights": [],
        "quotes": [],
        "theme_color": "#3B82F6",  # Default blue
        "job_id": job_id,
        "job_title": job_title,
        "company_name": company_name,
        "created_at": datetime.utcnow().isoformat(),
        "url": f"/interview/{interview_id}"
    }
    
    await db.interviews.insert_one(interview_doc)
    logger.info(f"Interview created: {interview_id} for user {user_email}")
    
    # Also add interview reference to user's document
    await db.users.update_one(
        {"email": user_email},
        {"$push": {"interviews": {"interview_id": interview_id, "created_at": datetime.utcnow().isoformat()}}}
    )
    
    return interview_doc


async def get_interview_by_id(interview_id: str) -> Optional[Dict[str, Any]]:
    """Get interview by ID."""
    interview = await db.interviews.find_one({"id": interview_id})
    if interview:
        interview["_id"] = str(interview["_id"])
    return interview


async def get_user_interviews(user_email: str) -> List[Dict[str, Any]]:
    """Get all interviews for a user."""
    cursor = db.interviews.find({"user_email": user_email}).sort("created_at", -1)
    interviews = await cursor.to_list(length=100)
    for interview in interviews:
        interview["_id"] = str(interview["_id"])
    return interviews


async def update_interview(interview_id: str, updates: Dict[str, Any]) -> bool:
    """Update an interview."""
    result = await db.interviews.update_one(
        {"id": interview_id},
        {"$set": updates}
    )
    return result.modified_count > 0


async def delete_interview(interview_id: str) -> bool:
    """Delete an interview."""
    result = await db.interviews.delete_one({"id": interview_id})
    return result.deleted_count > 0


# ==================== INTERVIEWER OPERATIONS ====================

def get_all_interviewers() -> List[Dict[str, Any]]:
    """Get all available interviewers."""
    return DEFAULT_INTERVIEWERS


def get_interviewer_by_id(interviewer_id: int) -> Optional[Dict[str, Any]]:
    """Get interviewer by ID."""
    for interviewer in DEFAULT_INTERVIEWERS:
        if interviewer["id"] == interviewer_id:
            return interviewer
    return None


# ==================== RETELL AI INTEGRATION ====================

async def register_retell_call(
    interviewer_id: int,
    dynamic_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Register a call with Retell AI.
    
    Args:
        interviewer_id: ID of the interviewer
        dynamic_data: Dynamic variables for the Retell LLM
    
    Returns:
        Retell call registration response with call_id and access_token
    """
    interviewer = get_interviewer_by_id(interviewer_id)
    
    if not interviewer or not interviewer.get("agent_id"):
        raise ValueError(f"Interviewer {interviewer_id} not found or has no agent_id")
    
    if not RETELL_API_KEY:
        raise ValueError("RETELL_API_KEY is not configured")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{RETELL_API_URL}/v2/create-web-call",
            headers={
                "Authorization": f"Bearer {RETELL_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "agent_id": interviewer["agent_id"],
                "retell_llm_dynamic_variables": dynamic_data
            }
        )
        
        if response.status_code != 200 and response.status_code != 201:
            logger.error(f"Retell API error: {response.text}")
            raise Exception(f"Failed to register call: {response.text}")
        
        result = response.json()
        logger.info(f"Retell call registered: {result.get('call_id')}")
        return result


async def get_retell_call(call_id: str) -> Dict[str, Any]:
    """Get call details from Retell AI."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{RETELL_API_URL}/v2/get-call/{call_id}",
            headers={
                "Authorization": f"Bearer {RETELL_API_KEY}"
            }
        )
        
        if response.status_code != 200:
            logger.error(f"Retell API error getting call: {response.text}")
            raise Exception(f"Failed to get call: {response.text}")
        
        return response.json()


# ==================== RESPONSE/CALL RECORDING OPERATIONS ====================

async def create_interview_response(
    interview_id: str,
    name: str,
    email: str,
    call_id: str
) -> str:
    """
    Create a new interview response record.
    
    Args:
        interview_id: ID of the interview
        name: Respondent's name
        email: Respondent's email
        call_id: Retell call ID
    
    Returns:
        Created response ID
    """
    response_id = str(ObjectId())
    
    response_doc = {
        "_id": ObjectId(response_id),
        "id": response_id,
        "interview_id": interview_id,
        "name": name,
        "email": email,
        "call_id": call_id,
        "candidate_status": "pending",
        "duration": 0,
        "details": None,
        "analytics": None,
        "is_analysed": False,
        "is_ended": False,
        "is_viewed": False,
        "tab_switch_count": 0,
        "created_at": datetime.utcnow().isoformat()
    }
    
    await db.interview_responses.insert_one(response_doc)
    
    # Update interview response count
    await db.interviews.update_one(
        {"id": interview_id},
        {
            "$inc": {"response_count": 1},
            "$push": {"respondents": email}
        }
    )
    
    logger.info(f"Interview response created: {response_id}")
    return response_id


async def update_interview_response(
    call_id: str,
    updates: Dict[str, Any]
) -> bool:
    """Update an interview response by call_id."""
    result = await db.interview_responses.update_one(
        {"call_id": call_id},
        {"$set": updates}
    )
    return result.modified_count > 0


async def get_response_by_call_id(call_id: str) -> Optional[Dict[str, Any]]:
    """Get response by Retell call ID."""
    response = await db.interview_responses.find_one({"call_id": call_id})
    if response:
        response["_id"] = str(response["_id"])
    return response


async def get_interview_responses(interview_id: str) -> List[Dict[str, Any]]:
    """Get all responses for an interview."""
    cursor = db.interview_responses.find({
        "interview_id": interview_id,
        "is_ended": True
    }).sort("created_at", -1)
    
    responses = await cursor.to_list(length=100)
    for response in responses:
        response["_id"] = str(response["_id"])
    return responses


async def get_user_interview_history(user_email: str) -> List[Dict[str, Any]]:
    """Get all interview responses for a user."""
    cursor = db.interview_responses.find({
        "email": user_email
    }).sort("created_at", -1)
    
    responses = await cursor.to_list(length=100)
    
    # Enrich with interview details
    for response in responses:
        response["_id"] = str(response["_id"])
        interview = await get_interview_by_id(response["interview_id"])
        if interview:
            response["interview_name"] = interview.get("name")
            response["job_title"] = interview.get("job_title")
            response["company_name"] = interview.get("company_name")
    
    return responses


# ==================== FEEDBACK OPERATIONS ====================

async def submit_interview_feedback(
    interview_id: str,
    email: str,
    feedback: str,
    satisfaction: int
) -> str:
    """Submit feedback for an interview."""
    feedback_id = str(ObjectId())
    
    feedback_doc = {
        "_id": ObjectId(feedback_id),
        "id": feedback_id,
        "interview_id": interview_id,
        "email": email,
        "feedback": feedback,
        "satisfaction": satisfaction,
        "created_at": datetime.utcnow().isoformat()
    }
    
    await db.interview_feedback.insert_one(feedback_doc)
    logger.info(f"Interview feedback submitted: {feedback_id}")
    return feedback_id


# ==================== ANALYTICS & INSIGHTS ====================

async def analyze_interview_response(call_id: str) -> Dict[str, Any]:
    """
    Analyze an interview response using Gemini.
    
    Args:
        call_id: Retell call ID
    
    Returns:
        Analysis results
    """
    try:
        # Get call details from Retell
        call_details = await get_retell_call(call_id)
        
        transcript = call_details.get("transcript", "")
        
        if not transcript:
            return {"error": "No transcript available"}
        
        # Use Gemini to analyze the interview
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        analysis_prompt = f"""Analyze this interview transcript and provide:
1. Overall performance score (1-10)
2. Communication skills score (1-10)
3. Technical knowledge score (1-10)
4. Key strengths (list 3)
5. Areas for improvement (list 3)
6. Notable quotes from the candidate

Transcript:
{transcript}

Output as JSON:
{{
    "overall_score": 8,
    "communication_score": 7,
    "technical_score": 8,
    "strengths": ["strength1", "strength2", "strength3"],
    "improvements": ["area1", "area2", "area3"],
    "notable_quotes": ["quote1", "quote2"]
}}
"""
        
        response = model.generate_content(analysis_prompt)
        response_text = response.text
        
        # Parse JSON
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]
        
        analytics = json.loads(response_text.strip())
        
        # Update the response record
        await update_interview_response(call_id, {
            "analytics": analytics,
            "is_analysed": True,
            "details": call_details
        })
        
        logger.info(f"Interview analysis completed for call: {call_id}")
        return analytics
        
    except Exception as e:
        logger.error(f"Error analyzing interview: {str(e)}")
        return {"error": str(e)}


# ==================== JOB-SPECIFIC INTERVIEW CREATION ====================

async def create_job_interview(
    user_email: str,
    job_id: str,
    job_title: str,
    company_name: str,
    job_description: str,
    interviewer_id: int = 1,
    question_count: int = 5,
    time_duration: str = "10"
) -> Dict[str, Any]:
    """
    Create a mock interview tailored to a specific job.
    
    Args:
        user_email: User's email
        job_id: Job ID from job search
        job_title: Job title
        company_name: Company name
        job_description: Full job description for context
        interviewer_id: ID of the AI interviewer to use
        question_count: Number of questions to generate
        time_duration: Interview duration in minutes
    
    Returns:
        Created interview document
    """
    # Get user profile for context
    user = await db.users.find_one({"email": user_email})
    
    user_context = ""
    if user:
        skills = user.get("skills", [])
        experience = user.get("experience", [])
        user_context = f"\nCandidate skills: {', '.join(skills)}\nCandidate experience: {', '.join(experience)}"
    
    # Generate questions based on job
    interview_name = f"{job_title} at {company_name}"
    objective = f"Assess candidate's fit for {job_title} position at {company_name}"
    context = f"Job Description:\n{job_description}\n{user_context}"
    
    generated = await generate_interview_questions(
        name=interview_name,
        objective=objective,
        context=context,
        number=question_count
    )
    
    # Create the interview
    interview = await create_interview(
        user_email=user_email,
        name=interview_name,
        objective=objective,
        interviewer_id=interviewer_id,
        questions=generated.get("questions", []),
        description=generated.get("description", ""),
        time_duration=time_duration,
        job_id=job_id,
        job_title=job_title,
        company_name=company_name
    )
    
    return interview
