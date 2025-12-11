import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Send, Home, Sparkles } from 'lucide-react';
import { toast } from 'sonner';
import { Job, Chat, Message } from '../App';
import JobCard from './JobCard';

interface ChatPageProps {
  chats: Chat[];
  addChat: (chat: Chat) => void;
  updateChat: (chatId: string, messages: Message[]) => void;
  savedJobs: Job[];
  appliedJobs: Job[];
  saveJob: (job: Job) => void;
  applyToJob: (job: Job) => void;
}

const MOCK_JOBS: Job[] = [
  {
    id: 'job-1',
    title: 'Senior Software Engineer',
    company: 'TechCorp Inc.',
    role: 'Full Stack Developer',
    description: 'We are seeking an experienced Senior Software Engineer to join our dynamic team. You will work on cutting-edge technologies including React, Node.js, and cloud services. Responsibilities include designing scalable systems, mentoring junior developers, and collaborating with cross-functional teams.',
    location: 'San Francisco, CA',
    salary: '$150k - $200k',
  },
  {
    id: 'job-2',
    title: 'Frontend Developer',
    company: 'StartupHub',
    role: 'React Specialist',
    description: 'Join our fast-growing startup as a Frontend Developer. Build beautiful, responsive user interfaces using React, TypeScript, and modern CSS. Work closely with designers and backend engineers to create seamless user experiences.',
    location: 'Remote',
    salary: '$120k - $160k',
  },
  {
    id: 'job-3',
    title: 'Full Stack Engineer',
    company: 'DataFlow Systems',
    role: 'JavaScript Developer',
    description: 'Looking for a versatile Full Stack Engineer proficient in both frontend and backend development. Technologies include React, Node.js, PostgreSQL, and AWS. You will be building data visualization tools and RESTful APIs.',
    location: 'New York, NY',
    salary: '$140k - $180k',
  },
  {
    id: 'job-4',
    title: 'React Native Developer',
    company: 'MobileFirst Co.',
    role: 'Mobile App Developer',
    description: 'Create amazing mobile experiences with React Native. Build cross-platform apps for iOS and Android. Experience with Redux, mobile UI/UX patterns, and app deployment required.',
    location: 'Austin, TX',
    salary: '$130k - $170k',
  },
  {
    id: 'job-5',
    title: 'JavaScript Engineer',
    company: 'CloudWorks',
    role: 'Backend Developer',
    description: 'Join our backend team to build scalable microservices. Work with Node.js, Express, MongoDB, and Docker. Focus on API design, system architecture, and performance optimization.',
    location: 'Seattle, WA',
    salary: '$135k - $175k',
  },
  {
    id: 'job-6',
    title: 'UI/UX Engineer',
    company: 'DesignTech',
    role: 'Frontend Developer',
    description: 'Combine your design sensibility with technical skills. Build pixel-perfect interfaces using React, CSS-in-JS, and animation libraries. Collaborate with product designers to implement design systems.',
    location: 'Los Angeles, CA',
    salary: '$125k - $165k',
  },
];

const SUGGESTED_MESSAGES = [
  'Show me frontend developer jobs',
  'Find remote positions',
  'What jobs match my skills?',
  'Show senior level positions',
  'Find jobs in San Francisco',
];

const BOT_RESPONSES = [
  "I'd be happy to help you find the perfect job! Let me search our database...",
  "Great choice! I'm finding jobs that match your criteria...",
  "Let me look for positions that fit your profile...",
  "Searching for opportunities that align with your skills...",
];

export default function ChatPage({
  chats,
  addChat,
  updateChat,
  savedJobs,
  appliedJobs,
  saveJob,
  applyToJob,
}: ChatPageProps) {
  const { chatId } = useParams();
  const navigate = useNavigate();
  const [currentChat, setCurrentChat] = useState<Chat | null>(null);
  const [message, setMessage] = useState('');
  const [displayedJobs, setDisplayedJobs] = useState<Job[]>([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [showJobs, setShowJobs] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const jobsPerPage = 3;

  useEffect(() => {
    if (chatId) {
      const existingChat = chats.find((chat) => chat.id === chatId);
      if (existingChat) {
        setCurrentChat(existingChat);
        // Show jobs if there are enough messages
        if (existingChat.messages.length >= 2) {
          setShowJobs(true);
          setDisplayedJobs(MOCK_JOBS);
        }
      } else {
        // Create new chat
        const newChat: Chat = {
          id: chatId,
          title: 'New Job Search',
          messages: [
            {
              id: `msg-${Date.now()}`,
              sender: 'bot',
              content: 'Hello! I\'m your AI job search assistant. How can I help you find your dream job today?',
              timestamp: new Date(),
            },
          ],
          timestamp: new Date(),
        };
        setCurrentChat(newChat);
        addChat(newChat);
      }
    }
  }, [chatId, chats]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [currentChat?.messages]);

  const handleSendMessage = (text?: string) => {
    const messageText = text || message;
    if (!messageText.trim() || !currentChat) return;

    const newUserMessage: Message = {
      id: `msg-${Date.now()}`,
      sender: 'user',
      content: messageText,
      timestamp: new Date(),
    };

    const updatedMessages = [...currentChat.messages, newUserMessage];
    if (currentChat.messages.length === 1) {
      const updatedChat = {
        ...currentChat,
        title: messageText.slice(0, 50) + (messageText.length > 50 ? '...' : ''),
        messages: updatedMessages,
      };
      setCurrentChat(updatedChat);
      updateChat(currentChat.id, updatedMessages);
    } else {
      setCurrentChat({ ...currentChat, messages: updatedMessages });
      updateChat(currentChat.id, updatedMessages);
    }

    setMessage('');

    // Bot response after delay
    setTimeout(() => {
      const botResponse = BOT_RESPONSES[Math.floor(Math.random() * BOT_RESPONSES.length)];
      const newBotMessage: Message = {
        id: `msg-${Date.now() + 1}`,
        sender: 'bot',
        content: botResponse,
        timestamp: new Date(),
      };

      const messagesWithBot = [...updatedMessages, newBotMessage];
      setCurrentChat({ ...currentChat, messages: messagesWithBot });
      updateChat(currentChat.id, messagesWithBot);

      // Show jobs after second exchange
      if (updatedMessages.length >= 2) {
        setTimeout(() => {
          setShowJobs(true);
          setDisplayedJobs(MOCK_JOBS);
          toast.success(`Found ${MOCK_JOBS.length} matching jobs!`);
        }, 500);
      }
    }, 1000);
  };

  const handleChooseJob = (job: Job) => {
    if (!currentChat) return;
    
    const newMessage: Message = {
      id: `msg-${Date.now()}`,
      sender: 'bot',
      content: `Great choice! The ${job.title} position at ${job.company} looks like an excellent fit. Would you like me to help you prepare your application?`,
      timestamp: new Date(),
    };
    
    const updatedMessages = [...currentChat.messages, newMessage];
    setCurrentChat({ ...currentChat, messages: updatedMessages });
    updateChat(currentChat.id, updatedMessages);
    toast.success('Job selected for discussion');
  };

  const totalPages = Math.ceil(displayedJobs.length / jobsPerPage);
  const paginatedJobs = displayedJobs.slice(
    (currentPage - 1) * jobsPerPage,
    currentPage * jobsPerPage
  );

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
        <h2 className="text-gray-900">{currentChat?.title || 'Job Search'}</h2>
        <button
          onClick={() => navigate('/home')}
          className="flex items-center gap-2 px-4 py-2 rounded-lg hover:bg-gray-100 transition-colors"
        >
          <Home className="w-5 h-5" />
          <span>Home</span>
        </button>
      </header>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Side - Chat (40%) */}
        <div className="w-[40%] border-r border-gray-200 bg-white flex flex-col">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {currentChat?.messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[85%] px-4 py-3 rounded-2xl ${
                    msg.sender === 'user'
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-900'
                  }`}
                >
                  {msg.sender === 'bot' && (
                    <div className="flex items-center gap-2 mb-1">
                      <Sparkles className="w-4 h-4 text-blue-600" />
                      <span className="text-blue-600 text-sm">JobBot AI</span>
                    </div>
                  )}
                  <p className="text-sm">{msg.content}</p>
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          {/* Suggested Messages */}
          {currentChat && currentChat.messages.length <= 2 && (
            <div className="px-4 pb-3">
              <p className="text-gray-500 text-sm mb-2">Suggested:</p>
              <div className="flex flex-wrap gap-2">
                {SUGGESTED_MESSAGES.map((suggested, index) => (
                  <button
                    key={index}
                    onClick={() => handleSendMessage(suggested)}
                    className="px-3 py-1.5 bg-gray-100 text-gray-700 rounded-full text-sm hover:bg-gray-200 transition-colors"
                  >
                    {suggested}
                  </button>
                ))}
              </div>
            </div>
          )}

          {}
          <div className="p-4 border-t border-gray-200">
            <div className="flex gap-2">
              <input
                type="text"
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                placeholder="Type your message..."
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
              />
              <button
                onClick={() => handleSendMessage()}
                title="Send message"
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                <Send className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>

        {}
        <div className="w-[60%] bg-gray-50 flex flex-col">
          {showJobs ? (
            <>
              {/* Jobs List */}
              <div className="flex-1 overflow-y-auto p-6">
                <div className="mb-4">
                  <h3 className="text-gray-900">Matching Jobs</h3>
                  <p className="text-gray-600">Found {displayedJobs.length} opportunities for you</p>
                </div>
                <div className="space-y-4">
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
                <div className="border-t border-gray-200 bg-white px-6 py-4">
                  <div className="flex items-center justify-between">
                    <p className="text-gray-600 text-sm">
                      Showing {(currentPage - 1) * jobsPerPage + 1} -{' '}
                      {Math.min(currentPage * jobsPerPage, displayedJobs.length)} of{' '}
                      {displayedJobs.length} jobs
                    </p>
                    <div className="flex gap-2">
                      <button
                        onClick={() => setCurrentPage((prev) => Math.max(1, prev - 1))}
                        disabled={currentPage === 1}
                        className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                      >
                        Previous
                      </button>
                      <div className="flex gap-1">
                        {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => (
                          <button
                            key={page}
                            onClick={() => setCurrentPage(page)}
                            className={`w-10 h-10 rounded-lg transition-colors ${
                              currentPage === page
                                ? 'bg-blue-600 text-white'
                                : 'bg-white border border-gray-300 hover:bg-gray-50'
                            }`}
                          >
                            {page}
                          </button>
                        ))}
                      </div>
                      <button
                        onClick={() => setCurrentPage((prev) => Math.min(totalPages, prev + 1))}
                        disabled={currentPage === totalPages}
                        className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                      >
                        Next
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center">
                <div className="w-20 h-20 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Sparkles className="w-10 h-10 text-blue-600" />
                </div>
                <h3 className="text-gray-900 mb-2">Start chatting to see jobs</h3>
                <p className="text-gray-600">
                  Tell me what kind of job you're looking for and I'll show you matching opportunities
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}