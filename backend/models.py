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


# ==================== INTERVIEW MODELS ====================

class InterviewQuestion(BaseModel):
    """Model for interview question."""
    id: str
    question: str
    follow_up_count: int = 2


class InterviewerInfo(BaseModel):
    """Model for AI interviewer information."""
    id: int
    agent_id: Optional[str] = None
    name: str
    description: str
    image: str
    audio: Optional[str] = None
    empathy: int
    exploration: int
    rapport: int
    speed: int


class CreateInterviewRequest(BaseModel):
    """Request model to create a new interview."""
    email: str
    name: str
    objective: str
    interviewer_id: int = 1
    question_count: int = 5
    time_duration: str = "10"
    # Optional job-specific fields
    job_id: Optional[str] = None
    job_title: Optional[str] = None
    company_name: Optional[str] = None
    job_description: Optional[str] = None


class CreateJobInterviewRequest(BaseModel):
    """Request model to create an interview for a specific job."""
    email: str
    job_id: str
    job_title: str
    company_name: str
    job_description: str
    interviewer_id: int = 1
    question_count: int = 5
    time_duration: str = "10"


class InterviewResponse(BaseModel):
    """Response model for interview data."""
    id: str
    name: str
    description: str
    objective: str
    interviewer_id: int
    questions: List[InterviewQuestion]
    question_count: int
    time_duration: str
    is_active: bool
    response_count: int
    job_id: Optional[str] = None
    job_title: Optional[str] = None
    company_name: Optional[str] = None
    created_at: str
    url: str


class GetInterviewsResponse(BaseModel):
    """Response model for getting user's interviews."""
    interviews: List[InterviewResponse]


class RegisterCallRequest(BaseModel):
    """Request model to register a Retell call."""
    interview_id: str
    interviewer_id: int
    user_name: str
    user_email: str
    # Dynamic variables for Retell LLM
    interview_name: Optional[str] = None
    interview_questions: Optional[str] = None


class RegisterCallResponse(BaseModel):
    """Response model for Retell call registration."""
    call_id: str
    access_token: str


class CreateInterviewResponseRequest(BaseModel):
    """Request model to create an interview response record."""
    interview_id: str
    name: str
    email: str
    call_id: str


class InterviewResponseData(BaseModel):
    """Model for interview response/recording data."""
    id: str
    interview_id: str
    name: str
    email: str
    call_id: str
    candidate_status: str
    duration: int
    is_analysed: bool
    is_ended: bool
    created_at: str
    analytics: Optional[dict] = None
    interview_name: Optional[str] = None
    job_title: Optional[str] = None
    company_name: Optional[str] = None


class GetInterviewHistoryResponse(BaseModel):
    """Response model for user's interview history."""
    responses: List[InterviewResponseData]


class SubmitFeedbackRequest(BaseModel):
    """Request model to submit interview feedback."""
    interview_id: str
    email: str
    feedback: str
    satisfaction: int  # 1-5 rating


class AnalyzeInterviewRequest(BaseModel):
    """Request model to analyze an interview."""
    call_id: str


class InterviewAnalytics(BaseModel):
    """Model for interview analytics."""
    overall_score: int
    communication_score: int
    technical_score: int
    strengths: List[str]
    improvements: List[str]
    notable_quotes: List[str]


class UpdateInterviewResponseRequest(BaseModel):
    """Request model to update interview response."""
    call_id: str
    is_ended: Optional[bool] = None
    duration: Optional[int] = None
    tab_switch_count: Optional[int] = None
