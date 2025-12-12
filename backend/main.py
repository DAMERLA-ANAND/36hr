from pydantic import BaseModel, Field
from typing import List, Optional

from jsonschema import ValidationError
import uvicorn
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from models import (
    UserOnboardingRequest, UserOnboardingResponse, User,
    ChatHistoryResponse, ChatHistoryResponseItem,
    GetAppliedJobsResponse, GetAppliedJobsResponseItem,
    GetSavedJobsResponse, GetSavedJobsResponseItem,
    SaveJobRequest, ApplyJobRequest, UserProfileUpdateRequest,
    ChatMessageRequest, ChatMessageResponse,
    CreateChatRequest, CreateChatResponse,
    GetChatMessagesRequest, GetChatMessagesResponse,
    # Interview models
    CreateInterviewRequest, CreateJobInterviewRequest, InterviewResponse,
    GetInterviewsResponse, RegisterCallRequest, RegisterCallResponse,
    CreateInterviewResponseRequest, InterviewResponseData, GetInterviewHistoryResponse,
    SubmitFeedbackRequest, AnalyzeInterviewRequest, InterviewAnalytics,
    UpdateInterviewResponseRequest, InterviewerInfo
)
from bson import ObjectId
import json
from PyPDF2 import PdfReader
import io
import google.generativeai as genai
import logging

from dotenv import load_dotenv
load_dotenv()

from db import db
from gemini_client import model
from chat_service import create_new_chat, process_chat_message, get_chat_messages
# Import interview service
from interview_service import (
    generate_interview_questions,
    create_interview,
    create_job_interview,
    get_interview_by_id,
    get_user_interviews,
    update_interview,
    delete_interview,
    get_all_interviewers,
    get_interviewer_by_id,
    register_retell_call,
    create_interview_response,
    update_interview_response,
    get_response_by_call_id,
    get_interview_responses,
    get_user_interview_history,
    submit_interview_feedback,
    analyze_interview_response
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# user onboarding process

@app.post("/api/onboardFileUpload", response_model=UserOnboardingResponse)
async def onboard_user(request: Request):
    """ The resume file is uploaded by the user via frontend and sent to this endpoint 
        for parsing and extracting details.
        1. the file is parsed using pypdf 2
        2. the parsed text is sent to Gemini 2.5 model along with the onboarding response pydantic model
           for extracting details
        3. the response from Gemini is validated using pydantic model and sent back to 
           frontend for confirmation
    """
    content = await request.body()
    if not content.startswith(b'%PDF-'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    try:
        pdf_reader = PdfReader(io.BytesIO(content))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        
        prompt = f"""
        Extract the following details from the resume text provided below.
        Ensure the output matches the JSON schema provided.
        
        Resume Text:
        {text}
        """

        # Hardcoded schema to avoid Pydantic/Gemini compatibility issues
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "email": {"type": "string"},
                "phone": {"type": "string"},
                "location": {"type": "string"},
                "skills": {"type": "array", "items": {"type": "string"}},
                "experience": {"type": "array", "items": {"type": "string"}},
                "profile_summary": {"type": "string"},
                "education": {"type": "array", "items": {"type": "string"}},
                "certificationsAndAchievementsAndAwards": {"type": "array", "items": {"type": "string"}},
                "projects": {"type": "array", "items": {"type": "string"}},
                "about": {"type": "string"}
            },
            "required": ["name", "email", "phone", "location", "skills", "experience", "profile_summary"]
        }

        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                response_schema=schema
            )
        )
        
        # Clean up the response text if necessary (sometimes it might contain markdown code blocks)
        response_text = response.text
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        
        return UserOnboardingResponse.model_validate_json(response_text.strip())

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/confirmOnboardingDetails")
async def confirm_onboarding_details(onboard_confirmed_details: UserOnboardingResponse):
    """ Once the user confirms the details sent by the backend after parsing the resume,
        this endpoint is called to save the details in the database.
    """
    try:
        user_data = onboard_confirmed_details.model_dump()
        # Check if user already exists? For now, just insert.
        # We might want to use email as a unique identifier.
        existing_user = await db.users.find_one({"email": user_data["email"]})
        if existing_user:
             # Update existing user or raise error? Let's update for now or just return existing.
             # Assuming we want to create a new one or update.
             await db.users.update_one({"email": user_data["email"]}, {"$set": user_data})
             return {"message": "User details updated successfully", "email": user_data["email"]}
        
        # Initialize chat_history for new users
        user_data["chat_history"] = []
        user_data["saved_jobs"] = []
        user_data["applied_jobs"] = []

        result = await db.users.insert_one(user_data)
        return {"message": "User onboarded successfully", "id": str(result.inserted_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

#home page endpoints

@app.get("/api/chatHistoryRequest", response_model=ChatHistoryResponse)
async def chat_history_request(email: str):
    """ Endpoint to handle chat history requests.
        For home page chat history retrieval.
        1. Fetch chat history from the database for the user.
        2. Return the chat history to the frontend.
        3. return only the id, and chat name for listing on home page.
    """
    logger.info(f"Chat history request for email: {email}")
    try:
        user = await db.users.find_one({"email": email})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        chat_history = user.get("chat_history", [])
        response_chats = []
        for chat in chat_history:
            # Handle potential missing fields or different structure
            # Assuming chat object has _id or id
            chat_id = str(chat.get("_id", chat.get("id", "")))
            
            response_chats.append(ChatHistoryResponseItem(
                id=chat_id,
                chat_name=chat.get("chat_name", "New Chat"),
                chat_id=chat_id
            ))
            
        return ChatHistoryResponse(chats=response_chats)
    except Exception as e:
        logger.error(f"Error fetching chat history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/getAppliedJobs", response_model=GetAppliedJobsResponse)
async def get_applied_jobs(email: str):
    """ Endpoint to get applied jobs for the user.
        1. Fetch applied jobs from the database for the user.
        2. Return the applied jobs to the frontend.
    """
    logger.info(f"Get applied jobs request for email: {email}")
    try:
        user = await db.users.find_one({"email": email})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
            
        applied_jobs_data = user.get("applied_jobs", [])
        applied_jobs = []
        for job in applied_jobs_data:
            applied_jobs.append(GetAppliedJobsResponseItem(
                job_id=job.get("job_id"),
                job_title=job.get("job_title"),
                company_name=job.get("company_name"),
                job_link=job.get("job_link")
            ))
            
        return GetAppliedJobsResponse(applied_jobs=applied_jobs)
    except Exception as e:
        logger.error(f"Error fetching applied jobs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/getSavedJobs", response_model=GetSavedJobsResponse)
async def get_saved_jobs(email: str):
    """ Endpoint to get saved jobs for the user.
        1. Fetch saved jobs from the database for the user.
        2. Return the saved jobs to the frontend.
    """
    logger.info(f"Get saved jobs request for email: {email}")
    try:
        user = await db.users.find_one({"email": email})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
            
        saved_jobs_data = user.get("saved_jobs", [])
        saved_jobs = []
        for job in saved_jobs_data:
            saved_jobs.append(GetSavedJobsResponseItem(
                job_id=job.get("job_id"),
                job_title=job.get("job_title"),
                company_name=job.get("company_name"),
                job_link=job.get("job_link")
            ))
            
        return GetSavedJobsResponse(saved_jobs=saved_jobs)
    except Exception as e:
        logger.error(f"Error fetching saved jobs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/saveJob")
async def save_job_endpoint(request: SaveJobRequest):
    """ Endpoint to save a job for the user.
        1. Save the job to the user's saved jobs in the database.
    """
    logger.info(f"Save job request for email: {request.email}, job_id: {request.job_id}")
    try:
        job_data = {
            "job_id": request.job_id,
            "job_title": request.job_title,
            "company_name": request.company_name,
            "job_link": request.job_link
        }
        
        result = await db.users.update_one(
            {"email": request.email},
            {"$addToSet": {"saved_jobs": job_data}}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="User not found")
            
        return {"message": "Job saved successfully"}
    except Exception as e:
        logger.error(f"Error saving job: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/applyJob")
async def apply_job_endpoint(request: ApplyJobRequest):
    """ Endpoint to apply to a job for the user.
        1. Apply to the job via jsearch api.
        2. Save the job to the user's applied jobs in the database.
        3. after user clicks apply, in the job interface, a new tab will open with job link and job applied request popup will appear asking for confirmation
        4. once confirmed the this endpoint will be called to save the applied job in applied category
    """
    logger.info(f"Apply job request for email: {request.email}, job_id: {request.job_id}")
    try:
        # 1. Apply to the job via jsearch api.
        # Note: Actual JSearch API integration for application is not implemented here as per current context.
        # Assuming this endpoint is primarily for tracking the application after user confirmation.
        
        job_data = {
            "job_id": request.job_id,
            "job_title": request.job_title,
            "company_name": request.company_name,
            "job_link": request.job_link
        }
        
        result = await db.users.update_one(
            {"email": request.email},
            {"$addToSet": {"applied_jobs": job_data}}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="User not found")
            
        return {"message": "Job applied successfully"}
    except Exception as e:
        logger.error(f"Error applying job: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/updateUserProfile")
async def update_user_profile(request: UserProfileUpdateRequest):
    """ Endpoint to update user profile details.
        1. Update the user profile details in the database.
    """
    logger.info(f"Update user profile request for email: {request.email}")
    try:
        update_data = request.model_dump(exclude_unset=True)
        email = update_data.pop("email")
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")

        result = await db.users.update_one(
            {"email": email},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="User not found")
            
        return {"message": "User profile updated successfully"}
    except Exception as e:
        logger.error(f"Error updating user profile: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/unsaveJob")
async def unsave_job_endpoint(request: SaveJobRequest):
    """ Endpoint to unsave a job for the user.
        1. Remove the job from the user's saved jobs in the database.
    """
    logger.info(f"Unsave job request for email: {request.email}, job_id: {request.job_id}")
    try:
        job_data = {
            "job_id": request.job_id,
            "job_title": request.job_title,
            "company_name": request.company_name,
            "job_link": request.job_link
        }
        
        result = await db.users.update_one(
            {"email": request.email},
            {"$pull": {"saved_jobs": job_data}}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="User not found")
            
        return {"message": "Job unsaved successfully"}
    except Exception as e:
        logger.error(f"Error unsaving job: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/deleteChatSession")
async def delete_chat_session(email: str, chat_id: str):
    """ Endpoint to delete a chat session for the user.
        1. Remove the chat session from the user's chat history in the database.
    """
    logger.info(f"Delete chat session request for email: {email}, chat_id: {chat_id}")
    try:
        result = await db.users.update_one(
            {"email": email},
            {"$pull": {"chat_history": {"_id": ObjectId(chat_id)}}}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="User not found")
            
        return {"message": "Chat session deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting chat session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Chat endpoints

@app.post("/api/createChat", response_model=CreateChatResponse)
async def create_chat_endpoint(request: CreateChatRequest):
    """
    Create a new chat session for the user.
    1. Creates permanent context from user profile using Gemini
    2. Initializes chat with context and greeting message
    3. Updates user document with new chat
    """
    logger.info(f"Create chat request for email: {request.email}")
    try:
        result = await create_new_chat(request.email)
        
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        
        return CreateChatResponse(
            chat_id=result["chat_id"],
            chat_name=result["chat_name"],
            initial_message=result["initial_message"]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating chat: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/sendMessage", response_model=ChatMessageResponse)
async def send_message_endpoint(request: ChatMessageRequest):
    """
    Send a message to the chatbot and get a response.
    1. Processes user message with context
    2. Uses Gemini with function calling for job search
    3. Returns bot response and optional job cards
    """
    logger.info(f"Send message request for email: {request.email}, chat_id: {request.chat_id}")
    print(f"[MAIN] sendMessage called with email={request.email}, chat_id={request.chat_id}, message={request.message[:50] if request.message else 'None'}...")
    try:
        result = await process_chat_message(
            email=request.email,
            chat_id=request.chat_id,
            user_message=request.message,
            selected_job_id=request.selected_job_id
        )
        print(f"[MAIN] process_chat_message returned: {list(result.keys()) if result else 'None'}")
        
        if "error" in result and result.get("message", "").startswith("User not found"):
            raise HTTPException(status_code=404, detail=result["message"])
        
        response = ChatMessageResponse(
            message=result.get("message", ""),
            jobs=result.get("jobs"),
            selected_job_details=result.get("selected_job_details")
        )
        print(f"[MAIN] Response created successfully")
        return response
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"[MAIN] ERROR in send_message_endpoint: {str(e)}")
        print(f"[MAIN] Traceback:\n{traceback.format_exc()}")
        logger.error(f"Error sending message: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/getChatMessages")
async def get_chat_messages_endpoint(email: str, chat_id: str):
    """
    Get all messages for a specific chat session.
    """
    logger.info(f"Get chat messages request for email: {email}, chat_id: {chat_id}")
    try:
        result = await get_chat_messages(email, chat_id)
        
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting chat messages: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== INTERVIEW ENDPOINTS ====================

class GenerateObjectiveRequest(BaseModel):
    job_title: str
    company_name: str
    job_description: str

@app.post("/api/generateInterviewObjective")
async def generate_interview_objective(request: GenerateObjectiveRequest):
    """
    Generate an interview objective using Gemini AI based on job details.
    This helps users understand what the mock interview will focus on.
    """
    logger.info(f"Generate interview objective for: {request.job_title} at {request.company_name}")
    try:
        prompt = f"""Based on the following job details, generate a concise interview objective (2-3 sentences) 
that describes what skills and topics the mock interview will assess. Focus on key competencies 
needed for the role.

Job Title: {request.job_title}
Company: {request.company_name}
Job Description: {request.job_description[:1500] if request.job_description else 'Not provided'}

Generate ONLY the objective text, no extra formatting or explanation. The objective should:
1. Mention specific technical skills to be assessed
2. Include relevant soft skills for the role
3. Be encouraging and professional in tone

Example format: "This interview will assess your [specific skills] abilities, focusing on [key areas]. 
We'll explore your experience with [technologies/methodologies] and evaluate your [soft skills]."
"""
        
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        
        objective = response.text.strip()
        logger.info(f"Generated objective: {objective[:100]}...")
        
        return {"objective": objective}
    except Exception as e:
        logger.error(f"Error generating interview objective: {str(e)}")
        # Return a default objective on error
        default_objective = f"Practice technical and behavioral interview for the {request.job_title} position at {request.company_name}. Focus on demonstrating relevant skills, problem-solving abilities, and cultural fit."
        return {"objective": default_objective}


@app.get("/api/interviewers")
async def get_interviewers():
    """Get all available AI interviewers."""
    logger.info("Get interviewers request")
    return {"interviewers": get_all_interviewers()}


@app.get("/api/interviewer/{interviewer_id}")
async def get_interviewer(interviewer_id: int):
    """Get a specific interviewer by ID."""
    logger.info(f"Get interviewer request: {interviewer_id}")
    interviewer = get_interviewer_by_id(interviewer_id)
    if not interviewer:
        raise HTTPException(status_code=404, detail="Interviewer not found")
    return interviewer


@app.post("/api/createInterview", response_model=InterviewResponse)
async def create_interview_endpoint(request: CreateInterviewRequest):
    """
    Create a new mock interview session.
    Generates questions based on the objective and optional job context.
    """
    logger.info(f"Create interview request for email: {request.email}")
    try:
        # Generate questions
        context = ""
        if request.job_description:
            context = f"Job: {request.job_title} at {request.company_name}\n{request.job_description}"
        
        generated = await generate_interview_questions(
            name=request.name,
            objective=request.objective,
            context=context,
            number=request.question_count
        )
        
        # Create interview
        interview = await create_interview(
            user_email=request.email,
            name=request.name,
            objective=request.objective,
            interviewer_id=request.interviewer_id,
            questions=generated.get("questions", []),
            description=generated.get("description", ""),
            time_duration=request.time_duration,
            job_id=request.job_id,
            job_title=request.job_title,
            company_name=request.company_name
        )
        
        return InterviewResponse(
            id=interview["id"],
            name=interview["name"],
            description=interview["description"],
            objective=interview["objective"],
            interviewer_id=interview["interviewer_id"],
            questions=interview["questions"],
            question_count=interview["question_count"],
            time_duration=interview["time_duration"],
            is_active=interview["is_active"],
            response_count=interview["response_count"],
            job_id=interview.get("job_id"),
            job_title=interview.get("job_title"),
            company_name=interview.get("company_name"),
            created_at=interview["created_at"],
            url=interview["url"]
        )
    except Exception as e:
        logger.error(f"Error creating interview: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/createJobInterview", response_model=InterviewResponse)
async def create_job_interview_endpoint(request: CreateJobInterviewRequest):
    """
    Create a mock interview tailored to a specific job listing.
    This is the key integration point between job search and interview prep.
    """
    logger.info(f"Create job interview request for email: {request.email}, job: {request.job_title}")
    try:
        interview = await create_job_interview(
            user_email=request.email,
            job_id=request.job_id,
            job_title=request.job_title,
            company_name=request.company_name,
            job_description=request.job_description,
            interviewer_id=request.interviewer_id,
            question_count=request.question_count,
            time_duration=request.time_duration
        )
        
        return InterviewResponse(
            id=interview["id"],
            name=interview["name"],
            description=interview["description"],
            objective=interview["objective"],
            interviewer_id=interview["interviewer_id"],
            questions=interview["questions"],
            question_count=interview["question_count"],
            time_duration=interview["time_duration"],
            is_active=interview["is_active"],
            response_count=interview["response_count"],
            job_id=interview.get("job_id"),
            job_title=interview.get("job_title"),
            company_name=interview.get("company_name"),
            created_at=interview["created_at"],
            url=interview["url"]
        )
    except Exception as e:
        logger.error(f"Error creating job interview: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/interviews", response_model=GetInterviewsResponse)
async def get_user_interviews_endpoint(email: str):
    """Get all interviews for a user."""
    logger.info(f"Get interviews request for email: {email}")
    try:
        interviews = await get_user_interviews(email)
        return GetInterviewsResponse(
            interviews=[
                InterviewResponse(
                    id=i["id"],
                    name=i["name"],
                    description=i.get("description", ""),
                    objective=i["objective"],
                    interviewer_id=i["interviewer_id"],
                    questions=i["questions"],
                    question_count=i["question_count"],
                    time_duration=i["time_duration"],
                    is_active=i["is_active"],
                    response_count=i["response_count"],
                    job_id=i.get("job_id"),
                    job_title=i.get("job_title"),
                    company_name=i.get("company_name"),
                    created_at=i["created_at"],
                    url=i["url"]
                )
                for i in interviews
            ]
        )
    except Exception as e:
        logger.error(f"Error getting interviews: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/interview/{interview_id}")
async def get_interview_endpoint(interview_id: str):
    """Get a specific interview by ID."""
    logger.info(f"Get interview request: {interview_id}")
    try:
        interview = await get_interview_by_id(interview_id)
        if not interview:
            raise HTTPException(status_code=404, detail="Interview not found")
        return interview
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting interview: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/interview/{interview_id}")
async def delete_interview_endpoint(interview_id: str):
    """Delete an interview."""
    logger.info(f"Delete interview request: {interview_id}")
    try:
        success = await delete_interview(interview_id)
        if not success:
            raise HTTPException(status_code=404, detail="Interview not found")
        return {"message": "Interview deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting interview: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/registerCall", response_model=RegisterCallResponse)
async def register_call_endpoint(request: RegisterCallRequest):
    """
    Register a call with Retell AI for voice interview.
    Returns call_id and access_token needed to start the voice call.
    """
    logger.info(f"Register call request for interview: {request.interview_id}")
    try:
        # Get interview details
        interview = await get_interview_by_id(request.interview_id)
        if not interview:
            raise HTTPException(status_code=404, detail="Interview not found")
        
        # Prepare dynamic variables for Retell LLM
        questions_text = "\n".join([f"- {q['question']}" for q in interview.get("questions", [])])
        
        dynamic_data = {
            "candidate_name": request.user_name,
            "candidate_email": request.user_email,
            "interview_name": interview.get("name", "Mock Interview"),
            "interview_objective": interview.get("objective", ""),
            "interview_questions": questions_text
        }
        
        result = await register_retell_call(
            interviewer_id=request.interviewer_id,
            dynamic_data=dynamic_data
        )
        
        # Create interview response record
        await create_interview_response(
            interview_id=request.interview_id,
            name=request.user_name,
            email=request.user_email,
            call_id=result.get("call_id", "")
        )
        
        return RegisterCallResponse(
            call_id=result.get("call_id", ""),
            access_token=result.get("access_token", "")
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registering call: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/updateInterviewResponse")
async def update_interview_response_endpoint(request: UpdateInterviewResponseRequest):
    """Update an interview response (e.g., mark as ended, update duration)."""
    logger.info(f"Update interview response request for call: {request.call_id}")
    try:
        updates = {}
        if request.is_ended is not None:
            updates["is_ended"] = request.is_ended
        if request.duration is not None:
            updates["duration"] = request.duration
        if request.tab_switch_count is not None:
            updates["tab_switch_count"] = request.tab_switch_count
        
        success = await update_interview_response(request.call_id, updates)
        if not success:
            raise HTTPException(status_code=404, detail="Response not found")
        return {"message": "Response updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating response: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/interviewHistory", response_model=GetInterviewHistoryResponse)
async def get_interview_history_endpoint(email: str):
    """Get a user's interview practice history with analytics."""
    logger.info(f"Get interview history request for email: {email}")
    try:
        responses = await get_user_interview_history(email)
        return GetInterviewHistoryResponse(
            responses=[
                InterviewResponseData(
                    id=r["id"],
                    interview_id=r["interview_id"],
                    name=r["name"],
                    email=r["email"],
                    call_id=r["call_id"],
                    candidate_status=r.get("candidate_status", "pending"),
                    duration=r.get("duration", 0),
                    is_analysed=r.get("is_analysed", False),
                    is_ended=r.get("is_ended", False),
                    created_at=r["created_at"],
                    analytics=r.get("analytics"),
                    interview_name=r.get("interview_name"),
                    job_title=r.get("job_title"),
                    company_name=r.get("company_name")
                )
                for r in responses
            ]
        )
    except Exception as e:
        logger.error(f"Error getting interview history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/interviewResponses/{interview_id}")
async def get_interview_responses_endpoint(interview_id: str):
    """Get all responses for a specific interview."""
    logger.info(f"Get interview responses request for interview: {interview_id}")
    try:
        responses = await get_interview_responses(interview_id)
        return {"responses": responses}
    except Exception as e:
        logger.error(f"Error getting interview responses: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/analyzeInterview")
async def analyze_interview_endpoint(request: AnalyzeInterviewRequest):
    """Analyze an interview recording and generate insights."""
    logger.info(f"Analyze interview request for call: {request.call_id}")
    try:
        analytics = await analyze_interview_response(request.call_id)
        if "error" in analytics:
            raise HTTPException(status_code=400, detail=analytics["error"])
        return analytics
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing interview: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/submitInterviewFeedback")
async def submit_feedback_endpoint(request: SubmitFeedbackRequest):
    """Submit feedback for an interview experience."""
    logger.info(f"Submit feedback request for interview: {request.interview_id}")
    try:
        feedback_id = await submit_interview_feedback(
            interview_id=request.interview_id,
            email=request.email,
            feedback=request.feedback,
            satisfaction=request.satisfaction
        )
        return {"message": "Feedback submitted successfully", "feedback_id": feedback_id}
    except Exception as e:
        logger.error(f"Error submitting feedback: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Webhook endpoint for Retell AI callbacks
@app.post("/api/retellWebhook")
async def retell_webhook(request: Request):
    """
    Webhook endpoint for Retell AI to send call events.
    Handles call completion, transcripts, and analysis triggers.
    """
    logger.info("Retell webhook received")
    try:
        body = await request.json()
        event_type = body.get("event")
        call_id = body.get("call_id")
        
        logger.info(f"Retell webhook event: {event_type} for call: {call_id}")
        
        if event_type == "call_ended":
            # Update response as ended
            await update_interview_response(call_id, {
                "is_ended": True,
                "duration": body.get("duration", 0)
            })
            
            # Optionally trigger analysis
            # await analyze_interview_response(call_id)
        
        elif event_type == "call_analyzed":
            # Retell has analyzed the call, store the analysis
            call_analysis = body.get("call_analysis", {})
            await update_interview_response(call_id, {
                "details": body,
                "is_analysed": True
            })
        
        return {"status": "received"}
    except Exception as e:
        logger.error(f"Error processing Retell webhook: {str(e)}")
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    # command to run the app: uvicorn main:app --reload
    uvicorn.run(app, host="0.0.0.0", port=8000)