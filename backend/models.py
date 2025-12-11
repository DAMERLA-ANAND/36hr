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

class ChatHistoryResponse(BaseModel):
    """Response model for chat history retrieval."""
    chats: List[ChatHistoryResponseItem]
