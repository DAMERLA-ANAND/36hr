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

// ==================== INTERVIEW API TYPES ====================

export interface InterviewQuestion {
  id: string;
  question: string;
  follow_up_count: number;
}

export interface Interviewer {
  id: number;
  agent_id?: string;
  name: string;
  description: string;
  image: string;
  audio?: string;
  empathy: number;
  exploration: number;
  rapport: number;
  speed: number;
}

export interface Interview {
  id: string;
  name: string;
  description: string;
  objective: string;
  interviewer_id: number;
  questions: InterviewQuestion[];
  question_count: number;
  time_duration: string;
  is_active: boolean;
  response_count: number;
  job_id?: string;
  job_title?: string;
  company_name?: string;
  created_at: string;
  url: string;
}

export interface InterviewResponse {
  id: string;
  interview_id: string;
  name: string;
  email: string;
  call_id: string;
  candidate_status: string;
  duration: number;
  is_analysed: boolean;
  is_ended: boolean;
  created_at: string;
  analytics?: InterviewAnalytics;
  interview_name?: string;
  job_title?: string;
  company_name?: string;
}

export interface InterviewAnalytics {
  overall_score: number;
  communication_score: number;
  technical_score: number;
  strengths: string[];
  improvements: string[];
  notable_quotes: string[];
}

export interface RegisterCallResponse {
  call_id: string;
  access_token: string;
}

// ==================== INTERVIEW API FUNCTIONS ====================

export const getInterviewers = async (): Promise<{ interviewers: Interviewer[] }> => {
  const response = await fetch('/api/interviewers');
  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Failed to get interviewers');
  }
  return response.json();
};

export const createInterview = async (data: {
  email: string;
  name: string;
  objective: string;
  interviewer_id?: number;
  question_count?: number;
  time_duration?: string;
  job_id?: string;
  job_title?: string;
  company_name?: string;
  job_description?: string;
}): Promise<Interview> => {
  const response = await fetch('/api/createInterview', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Failed to create interview');
  }
  return response.json();
};

export const createJobInterview = async (data: {
  email: string;
  job_id: string;
  job_title: string;
  company_name: string;
  job_description: string;
  interviewer_id?: number;
  question_count?: number;
  time_duration?: string;
}): Promise<Interview> => {
  const response = await fetch('/api/createJobInterview', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Failed to create job interview');
  }
  return response.json();
};

export const getUserInterviews = async (
  email: string
): Promise<{ interviews: Interview[] }> => {
  const response = await fetch(`/api/interviews?email=${encodeURIComponent(email)}`);
  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Failed to get interviews');
  }
  return response.json();
};

export const getInterview = async (interviewId: string): Promise<Interview> => {
  const response = await fetch(`/api/interview/${interviewId}`);
  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Failed to get interview');
  }
  return response.json();
};

export const deleteInterview = async (interviewId: string): Promise<{ message: string }> => {
  const response = await fetch(`/api/interview/${interviewId}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Failed to delete interview');
  }
  return response.json();
};

export const registerCall = async (data: {
  interview_id: string;
  interviewer_id: number;
  user_name: string;
  user_email: string;
}): Promise<RegisterCallResponse> => {
  const response = await fetch('/api/registerCall', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Failed to register call');
  }
  return response.json();
};

export const updateInterviewResponse = async (data: {
  call_id: string;
  is_ended?: boolean;
  duration?: number;
  tab_switch_count?: number;
}): Promise<{ message: string }> => {
  const response = await fetch('/api/updateInterviewResponse', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Failed to update response');
  }
  return response.json();
};

export const getInterviewHistory = async (
  email: string
): Promise<{ responses: InterviewResponse[] }> => {
  const response = await fetch(`/api/interviewHistory?email=${encodeURIComponent(email)}`);
  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Failed to get interview history');
  }
  return response.json();
};

export const analyzeInterview = async (
  callId: string
): Promise<InterviewAnalytics> => {
  const response = await fetch('/api/analyzeInterview', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ call_id: callId }),
  });
  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Failed to analyze interview');
  }
  return response.json();
};

export const submitInterviewFeedback = async (data: {
  interview_id: string;
  email: string;
  feedback: string;
  satisfaction: number;
}): Promise<{ message: string; feedback_id: string }> => {
  const response = await fetch('/api/submitInterviewFeedback', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Failed to submit feedback');
  }
  return response.json();
};
