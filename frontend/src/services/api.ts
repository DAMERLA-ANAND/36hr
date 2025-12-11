import { UserProfile } from '../App';

// Types for chat API
export interface JobCardData {
  job_id: string;
  job_title: string;
  employer_name: string;
  job_description: string;
  job_location?: string;
  job_salary?: string;
  job_employment_type?: string;
  job_apply_link?: string;
  job_posted_at?: string;
  job_is_remote?: boolean;
  employer_logo?: string;
  job_highlights?: {
    Qualifications?: string[];
    Responsibilities?: string[];
  };
}

export interface CreateChatResponse {
  chat_id: string;
  chat_name: string;
  initial_message: string;
}

export interface ChatMessageResponse {
  message: string;
  jobs?: JobCardData[];
  selected_job_details?: JobCardData;
}

export interface ChatMessage {
  sender: 'user' | 'bot';
  message: string;
  timestamp?: string;
  selected_job_id?: string;
}

export interface GetChatMessagesResponse {
  messages: ChatMessage[];
  chat_name: string;
}

export const uploadResume = async (file: File): Promise<UserProfile> => {
  const response = await fetch('/api/onboardFileUpload', {
    method: 'POST',
    body: file,
    headers: {
      // Content-Type is automatically set by fetch when body is a File/Blob
      // but for raw binary we might need to be careful.
      // The backend expects raw bytes, not multipart/form-data.
    },
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Failed to upload resume');
  }

  return response.json();
};

export const confirmOnboarding = async (
  data: UserProfile
): Promise<{ message: string; id?: string }> => {
  const response = await fetch('/api/confirmOnboardingDetails', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Failed to confirm onboarding details');
  }

  return response.json();
};

// Chat API functions

export const createChat = async (
  email: string
): Promise<CreateChatResponse> => {
  const response = await fetch('/api/createChat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email }),
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Failed to create chat');
  }

  return response.json();
};

export const sendMessage = async (
  email: string,
  chatId: string,
  message: string,
  selectedJobId?: string
): Promise<ChatMessageResponse> => {
  const response = await fetch('/api/sendMessage', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      email,
      chat_id: chatId,
      message,
      selected_job_id: selectedJobId,
    }),
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Failed to send message');
  }

  return response.json();
};

export const getChatMessages = async (
  email: string,
  chatId: string
): Promise<GetChatMessagesResponse> => {
  const response = await fetch(
    `/api/getChatMessages?email=${encodeURIComponent(
      email
    )}&chat_id=${encodeURIComponent(chatId)}`
  );

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Failed to get chat messages');
  }

  return response.json();
};

export const getChatHistory = async (
  email: string
): Promise<{
  chats: Array<{ id: string; chat_name: string; chat_id: string }>;
}> => {
  const response = await fetch(
    `/api/chatHistoryRequest?email=${encodeURIComponent(email)}`
  );

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Failed to get chat history');
  }

  return response.json();
};

export const deleteChatSession = async (
  email: string,
  chatId: string
): Promise<{ message: string }> => {
  const response = await fetch(
    `/api/deleteChatSession?email=${encodeURIComponent(
      email
    )}&chat_id=${encodeURIComponent(chatId)}`,
    {
      method: 'POST',
    }
  );

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Failed to delete chat session');
  }

  return response.json();
};
