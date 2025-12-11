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
    GetChatMessagesRequest, GetChatMessagesResponse
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



if __name__ == "__main__":
    # command to run the app: uvicorn main:app --reload
    uvicorn.run(app, host="0.0.0.0", port=8000)