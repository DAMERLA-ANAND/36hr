from pydantic import BaseModel, Field
from typing import List, Optional

class User(BaseModel):
    """user model for database storage, contains user profile details, contains chat history too, applied jobs, saved jobs etc. will be used after everything is completed"""
    pass 


class UserOnboardingRequest(BaseModel):
    """User uploads his resume via the frontend in pdf file or docx file format."""
    filename: str
    

class UserOnboardingResponse(BaseModel):
    """Response backend sends the prsed details for editing and confirmation by the user.
       This model is also used in the confirming onboarding details endpoint.
    """
    name: str
    email: str
    phone: str
    location: str
    skills: List[str]
    experience: List[str]
    profile_summary: str
    # optional fields
    education: Optional[List[str]] = None
    certificationsAndAchievementsAndAwards: Optional[List[str]] = None
    projects: Optional[List[str]] = None
    about: Optional[str] = None


class ChatMessage(BaseModel):
    """Model to represent a chat message in the chat history and chat interface."""
    sender: str  # 'user' or 'bot'
    message: str
    timestamp: Optional[str] = None  # ISO formatted timestamp
class Chat(BaseModel):
    """
    Model to represent a chat session, containing multiple chat messages.
    """
    messages: List[ChatMessage]
    chat_name: str
    # chat id will be handled by the database (ObjectId)
    id: Optional[str] = Field(None, alias="_id")


class ChatHistoryResponseItem(BaseModel):
    """
    Model to represent a single chat history item in the response.
    """
    id: str
    chat_name: str
    chat_id: str

class GetChatHistoryRequest(BaseModel):
    """Request model to get chat history for a user."""
    email: str

class ChatHistoryResponse(BaseModel):
    """Response model for chat history retrieval."""
    chats: List[ChatHistoryResponseItem]

class GetAppliedJobsRequest(BaseModel):
    """Request model to get applied jobs for a user."""
    email: str

class GetAppliedJobsResponseItem(BaseModel):
    """Model to represent a single applied job item in the response."""
    job_id: str
    job_title: str
    company_name: str
    job_link: str

class GetAppliedJobsResponse(BaseModel):
    """Response model for applied jobs retrieval."""
    applied_jobs: List[GetAppliedJobsResponseItem]

class GetSavedJobsRequest(BaseModel):
    """Request model to get saved jobs for a user."""
    email: str

class GetSavedJobsResponseItem(BaseModel):
    """Model to represent a single saved job item in the response."""
    job_id: str
    job_title: str
    company_name: str
    job_link: str

class GetSavedJobsResponse(BaseModel):
    """Response model for saved jobs retrieval."""
    saved_jobs: List[GetSavedJobsResponseItem]

class SaveJobRequest(BaseModel):
    """Request model to save a job for a user."""
    email: str
    job_id: str
    job_title: str
    company_name: str
    job_link: str

class ApplyJobRequest(BaseModel):
    """Request model to apply to a job for a user."""
    email: str
    job_id: str
    job_title: str
    company_name: str
    job_link: str

class UserProfileUpdateRequest(BaseModel):
    """Request model to update user profile details."""
    email: str
    name: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    skills: Optional[List[str]] = None
    experience: Optional[List[str]] = None
    profile_summary: Optional[str] = None
    education: Optional[List[str]] = None
    certificationsAndAchievementsAndAwards: Optional[List[str]] = None
    projects: Optional[List[str]] = None
    about: Optional[str] = None


class ChatMessageRequest(BaseModel):
    """Request model for sending a chat message."""
    email: str
    chat_id: str
    message: str
    selected_job_id: Optional[str] = None  # Optional job ID when user selects a job


class ChatMessageResponse(BaseModel):
    """Response model for chat message containing bot response and optional jobs."""
    message: str
    jobs: Optional[List[dict]] = None  # List of job cards to display
    selected_job_details: Optional[dict] = None  # Detailed job info when a job is selected


class CreateChatRequest(BaseModel):
    """Request model to create a new chat session."""
    email: str


class CreateChatResponse(BaseModel):
    """Response model for creating a new chat session."""
    chat_id: str
    chat_name: str
    initial_message: str


class ChatContext(BaseModel):
    """Model to store chat context for memory management."""
    permanent_context: str  # Minimized resume context created at chat start
    conversation_summary: str = ""  # Rolling summary of all previous messages
    recent_messages: List[dict] = []  # Last 5 in/out message pairs


class GetChatMessagesRequest(BaseModel):
    """Request model to get messages for a specific chat."""
    email: str
    chat_id: str


class GetChatMessagesResponse(BaseModel):
    """Response model for getting chat messages."""
    messages: List[ChatMessage]
    chat_name: str


class JobCardData(BaseModel):
    """Model for job card data sent to frontend."""
    job_id: str
    job_title: str
    employer_name: str
    job_description: str
    job_location: Optional[str] = None
    job_salary: Optional[str] = None
    job_employment_type: Optional[str] = None
    job_apply_link: Optional[str] = None
    job_posted_at: Optional[str] = None
    job_is_remote: Optional[bool] = None
    employer_logo: Optional[str] = None
    job_highlights: Optional[dict] = None
