import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Send, Home, Sparkles, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import { Job, Chat, Message } from '../App';
import JobCard from './JobCard';
import {
  createChat,
  sendMessage,
  getChatMessages,
  JobCardData,
} from '../services/api';

interface ChatPageProps {
  chats: Chat[];
  addChat: (chat: Chat) => void;
  updateChat: (chatId: string, messages: Message[], title?: string) => void;
  savedJobs: Job[];
  appliedJobs: Job[];
  saveJob: (job: Job) => void;
  applyToJob: (job: Job) => void;
  userEmail: string;
}

const SUGGESTED_MESSAGES = [
  'Show me frontend developer jobs',
  'Find remote positions',
  'What jobs match my skills?',
  'Show senior level positions',
  'Help me improve my resume',
];

// Convert JobCardData from API to Job type for JobCard component
const convertJobCardDataToJob = (jobData: JobCardData): Job => {
  return {
    id: jobData.job_id,
    title: jobData.job_title,
    company: jobData.employer_name,
    role: jobData.job_employment_type || 'Full-time',
    description: jobData.job_description,
    location: jobData.job_location || 'Not specified',
    salary: jobData.job_salary || 'Not disclosed',
    applyLink: jobData.job_apply_link,
    postedAt: jobData.job_posted_at,
    isRemote: jobData.job_is_remote,
    employerLogo: jobData.employer_logo,
    highlights: jobData.job_highlights,
  };
};

export default function ChatPage({
  chats,
  addChat,
  updateChat,
  savedJobs,
  appliedJobs,
  saveJob,
  applyToJob,
  userEmail,
}: ChatPageProps) {
  const { chatId } = useParams();
  const navigate = useNavigate();
  const [currentChat, setCurrentChat] = useState<Chat | null>(null);
  const [message, setMessage] = useState('');
  const [displayedJobs, setDisplayedJobs] = useState<Job[]>([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [showJobs, setShowJobs] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null);
  const [actualChatId, setActualChatId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const jobsPerPage = 3;

  // Initialize chat
  useEffect(() => {
    const initializeChat = async () => {
      if (!userEmail) {
        toast.error('Please complete onboarding first');
        navigate('/');
        return;
      }

      setIsLoading(true);

      try {
        if (chatId && chatId !== 'new') {
          // Load existing chat
          const existingChat = chats.find((chat) => chat.id === chatId);
          if (existingChat) {
            setCurrentChat(existingChat);
            setActualChatId(chatId);
            // Try to fetch latest messages from server
            try {
              const chatData = await getChatMessages(userEmail, chatId);
              const messages: Message[] = chatData.messages.map(
                (msg, index) => ({
                  id: `msg-${index}`,
                  sender: msg.sender,
                  content: msg.message,
                  timestamp: new Date(msg.timestamp || Date.now()),
                })
              );
              const updatedChat = {
                ...existingChat,
                messages,
                title: chatData.chat_name,
              };
              setCurrentChat(updatedChat);
            } catch (err) {
              // Use cached data if server fails
              console.log('Using cached chat data');
            }
          } else {
            // Chat not found locally, try to fetch from server
            try {
              const chatData = await getChatMessages(userEmail, chatId);
              const messages: Message[] = chatData.messages.map(
                (msg, index) => ({
                  id: `msg-${index}`,
                  sender: msg.sender,
                  content: msg.message,
                  timestamp: new Date(msg.timestamp || Date.now()),
                })
              );
              const newChat: Chat = {
                id: chatId,
                title: chatData.chat_name,
                messages,
                timestamp: new Date(),
              };
              setCurrentChat(newChat);
              setActualChatId(chatId);
              addChat(newChat);
            } catch (err) {
              toast.error('Chat not found');
              navigate('/home');
            }
          }
        } else {
          // Create new chat
          const result = await createChat(userEmail);
          const newChat: Chat = {
            id: result.chat_id,
            title: result.chat_name,
            messages: [
              {
                id: `msg-${Date.now()}`,
                sender: 'bot',
                content: result.initial_message,
                timestamp: new Date(),
              },
            ],
            timestamp: new Date(),
          };
          setCurrentChat(newChat);
          setActualChatId(result.chat_id);
          addChat(newChat);
          // Update URL to include the new chat ID
          navigate(`/chat/${result.chat_id}`, { replace: true });
        }
      } catch (error) {
        console.error('Error initializing chat:', error);
        toast.error('Failed to initialize chat. Please try again.');
      } finally {
        setIsLoading(false);
      }
    };

    initializeChat();
  }, [chatId, userEmail]);

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [currentChat?.messages]);

  const handleSendMessage = async (text?: string) => {
    const messageText = text || message;
    if (!messageText.trim() || !currentChat || !actualChatId || isSending)
      return;

    setIsSending(true);
    setMessage('');

    // Add user message immediately for responsiveness
    const newUserMessage: Message = {
      id: `msg-${Date.now()}`,
      sender: 'user',
      content: messageText,
      timestamp: new Date(),
    };

    const updatedMessages = [...currentChat.messages, newUserMessage];
    setCurrentChat({ ...currentChat, messages: updatedMessages });

    try {
      // Send message to backend
      const response = await sendMessage(
        userEmail,
        actualChatId,
        messageText,
        selectedJobId || undefined
      );

      // Add bot response
      const newBotMessage: Message = {
        id: `msg-${Date.now() + 1}`,
        sender: 'bot',
        content: response.message,
        timestamp: new Date(),
      };

      const messagesWithBot = [...updatedMessages, newBotMessage];

      // Update chat title if it's the first real message
      let newTitle = currentChat.title;
      if (currentChat.messages.length === 1) {
        newTitle =
          messageText.slice(0, 50) + (messageText.length > 50 ? '...' : '');
      }

      const finalChat = {
        ...currentChat,
        messages: messagesWithBot,
        title: newTitle,
      };
      setCurrentChat(finalChat);
      updateChat(actualChatId, messagesWithBot, newTitle);

      // Handle jobs if returned
      if (response.jobs && response.jobs.length > 0) {
        const convertedJobs = response.jobs.map(convertJobCardDataToJob);
        setDisplayedJobs(convertedJobs);
        setShowJobs(true);
        setCurrentPage(1);
        toast.success(`Found ${response.jobs.length} matching jobs!`);
      }

      // Handle selected job details if returned
      if (response.selected_job_details) {
        const selectedJob = convertJobCardDataToJob(
          response.selected_job_details
        );
        console.log('Selected job details:', selectedJob);
      }

      // Clear selected job after sending
      setSelectedJobId(null);
    } catch (error) {
      console.error('Error sending message:', error);
      toast.error('Failed to send message. Please try again.');

      // Remove the user message if sending failed
      setCurrentChat({ ...currentChat, messages: currentChat.messages });
    } finally {
      setIsSending(false);
    }
  };

  const handleChooseJob = (job: Job) => {
    if (!currentChat) return;

    // Set the selected job ID for the next message
    setSelectedJobId(job.id);

    // Automatically send a message about this job
    const chooseMessage = `I'm interested in the ${job.title} position at ${job.company}. Can you tell me more about it and help me prepare for this role?`;
    handleSendMessage(chooseMessage);

    toast.success('Job selected for discussion');
  };

  const totalPages = Math.ceil(displayedJobs.length / jobsPerPage);
  const paginatedJobs = displayedJobs.slice(
    (currentPage - 1) * jobsPerPage,
    currentPage * jobsPerPage
  );

  if (isLoading) {
    return (
      <div className='h-screen flex items-center justify-center bg-gray-50'>
        <div className='text-center'>
          <Loader2 className='w-12 h-12 animate-spin text-blue-600 mx-auto mb-4' />
          <p className='text-gray-600'>Initializing chat...</p>
        </div>
      </div>
    );
  }

  return (
    <div className='h-screen flex flex-col bg-gray-50'>
      {/* Header */}
      <header className='bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between'>
        <h2 className='text-gray-900 font-medium'>
          {currentChat?.title || 'Job Search'}
        </h2>
        <button
          onClick={() => navigate('/home')}
          className='flex items-center gap-2 px-4 py-2 rounded-lg hover:bg-gray-100 transition-colors'>
          <Home className='w-5 h-5' />
          <span>Home</span>
        </button>
      </header>

      {/* Main Content */}
      <div className='flex-1 flex overflow-hidden'>
        {/* Left Side - Chat (40%) */}
        <div className='w-[40%] border-r border-gray-200 bg-white flex flex-col'>
          {/* Messages */}
          <div className='flex-1 overflow-y-auto p-4 space-y-4'>
            {currentChat?.messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex ${
                  msg.sender === 'user' ? 'justify-end' : 'justify-start'
                }`}>
                <div
                  className={`max-w-[85%] px-4 py-3 rounded-2xl ${
                    msg.sender === 'user'
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-900'
                  }`}>
                  {msg.sender === 'bot' && (
                    <div className='flex items-center gap-2 mb-1'>
                      <Sparkles className='w-4 h-4 text-blue-600' />
                      <span className='text-blue-600 text-sm font-medium'>
                        JobBot AI
                      </span>
                    </div>
                  )}
                  <p className='text-sm whitespace-pre-wrap'>{msg.content}</p>
                </div>
              </div>
            ))}

            {/* Typing indicator */}
            {isSending && (
              <div className='flex justify-start'>
                <div className='bg-gray-100 px-4 py-3 rounded-2xl'>
                  <div className='flex items-center gap-2 mb-1'>
                    <Sparkles className='w-4 h-4 text-blue-600' />
                    <span className='text-blue-600 text-sm font-medium'>
                      JobBot AI
                    </span>
                  </div>
                  <div className='flex gap-1'>
                    <div
                      className='w-2 h-2 bg-gray-400 rounded-full animate-bounce'
                      style={{ animationDelay: '0ms' }}
                    />
                    <div
                      className='w-2 h-2 bg-gray-400 rounded-full animate-bounce'
                      style={{ animationDelay: '150ms' }}
                    />
                    <div
                      className='w-2 h-2 bg-gray-400 rounded-full animate-bounce'
                      style={{ animationDelay: '300ms' }}
                    />
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Suggested Messages */}
          {currentChat && currentChat.messages.length <= 2 && !isSending && (
            <div className='px-4 pb-3'>
              <p className='text-gray-500 text-sm mb-2'>Suggested:</p>
              <div className='flex flex-wrap gap-2'>
                {SUGGESTED_MESSAGES.map((suggested, index) => (
                  <button
                    key={index}
                    onClick={() => handleSendMessage(suggested)}
                    className='px-3 py-1.5 bg-gray-100 text-gray-700 rounded-full text-sm hover:bg-gray-200 transition-colors'>
                    {suggested}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Selected Job Indicator */}
          {selectedJobId && (
            <div className='px-4 pb-2'>
              <div className='flex items-center gap-2 text-sm text-blue-600 bg-blue-50 px-3 py-2 rounded-lg'>
                <span>Selected job for discussion</span>
                <button
                  onClick={() => setSelectedJobId(null)}
                  className='text-blue-400 hover:text-blue-600'>
                  ✕
                </button>
              </div>
            </div>
          )}

          {/* Message Input */}
          <div className='p-4 border-t border-gray-200'>
            <div className='flex gap-2'>
              <input
                type='text'
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                onKeyPress={(e) =>
                  e.key === 'Enter' && !isSending && handleSendMessage()
                }
                placeholder='Type your message...'
                disabled={isSending}
                className='flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none disabled:bg-gray-100'
              />
              <button
                onClick={() => handleSendMessage()}
                disabled={isSending || !message.trim()}
                title='Send message'
                className='px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed'>
                {isSending ? (
                  <Loader2 className='w-5 h-5 animate-spin' />
                ) : (
                  <Send className='w-5 h-5' />
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Right Side - Jobs (60%) */}
        <div className='w-[60%] bg-gray-50 flex flex-col'>
          {showJobs && displayedJobs.length > 0 ? (
            <>
              {/* Jobs List */}
              <div className='flex-1 overflow-y-auto p-6'>
                <div className='mb-4'>
                  <h3 className='text-gray-900 font-medium text-lg'>
                    Matching Jobs
                  </h3>
                  <p className='text-gray-600'>
                    Found {displayedJobs.length} opportunities for you
                  </p>
                </div>
                <div className='space-y-4'>
                  {paginatedJobs.map((job) => (
                    <JobCard
                      key={job.id}
                      job={job}
                      onSave={saveJob}
                      onApply={applyToJob}
                      onChoose={handleChooseJob}
                      isSaved={savedJobs.some((j) => j.id === job.id)}
                      isApplied={appliedJobs.some((j) => j.id === job.id)}
                    />
                  ))}
                </div>
              </div>

              {/* Pagination */}
              {totalPages > 1 && (
                <div className='border-t border-gray-200 bg-white px-6 py-4'>
                  <div className='flex items-center justify-between'>
                    <p className='text-gray-600 text-sm'>
                      Showing {(currentPage - 1) * jobsPerPage + 1} -{' '}
                      {Math.min(
                        currentPage * jobsPerPage,
                        displayedJobs.length
                      )}{' '}
                      of {displayedJobs.length} jobs
                    </p>
                    <div className='flex gap-2'>
                      <button
                        onClick={() =>
                          setCurrentPage((prev) => Math.max(1, prev - 1))
                        }
                        disabled={currentPage === 1}
                        className='px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors'>
                        Previous
                      </button>
                      <div className='flex gap-1'>
                        {Array.from(
                          { length: Math.min(totalPages, 5) },
                          (_, i) => i + 1
                        ).map((page) => (
                          <button
                            key={page}
                            onClick={() => setCurrentPage(page)}
                            className={`w-10 h-10 rounded-lg transition-colors ${
                              currentPage === page
                                ? 'bg-blue-600 text-white'
                                : 'bg-white border border-gray-300 hover:bg-gray-50'
                            }`}>
                            {page}
                          </button>
                        ))}
                      </div>
                      <button
                        onClick={() =>
                          setCurrentPage((prev) =>
                            Math.min(totalPages, prev + 1)
                          )
                        }
                        disabled={currentPage === totalPages}
                        className='px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors'>
                        Next
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className='flex-1 flex items-center justify-center'>
              <div className='text-center max-w-md'>
                <div className='w-20 h-20 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4'>
                  <Sparkles className='w-10 h-10 text-blue-600' />
                </div>
                <h3 className='text-gray-900 font-medium text-lg mb-2'>
                  Start chatting to see jobs
                </h3>
                <p className='text-gray-600'>
                  Tell me what kind of job you're looking for and I'll search
                  for matching opportunities. You can also ask for resume tips,
                  interview advice, or career guidance!
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
