import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Mic,
  MicOff,
  Phone,
  PhoneOff,
  Clock,
  AlertTriangle,
  CheckCircle,
  XCircle,
  ArrowLeft,
  Play,
  MessageSquare,
} from 'lucide-react';
import { toast } from 'sonner';
import { UserProfile } from '../App';
import {
  Interview,
  Interviewer,
  InterviewAnalytics,
  getInterview,
  getInterviewers,
  registerCall,
  updateInterviewResponse,
  analyzeInterview,
} from '../services/api';

// Note: You'll need to install retell-client-js-sdk
// npm install retell-client-js-sdk

interface InterviewRoomPageProps {
  userProfile: UserProfile | null;
}

export default function InterviewRoomPage({ userProfile }: InterviewRoomPageProps) {
  const { interviewId } = useParams<{ interviewId: string }>();
  const navigate = useNavigate();
  
  const [interview, setInterview] = useState<Interview | null>(null);
  const [interviewer, setInterviewer] = useState<Interviewer | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isStarted, setIsStarted] = useState(false);
  const [isEnded, setIsEnded] = useState(false);
  const [isCalling, setIsCalling] = useState(false);
  const [callId, setCallId] = useState<string>('');
  
  // Timer state
  const [time, setTime] = useState(0);
  const [maxTime, setMaxTime] = useState(600); // 10 minutes in seconds
  
  // Transcript state
  const [lastInterviewerResponse, setLastInterviewerResponse] = useState('');
  const [lastUserResponse, setLastUserResponse] = useState('');
  const [activeTurn, setActiveTurn] = useState<'agent' | 'user' | ''>('');
  
  // Tab switch detection
  const [tabSwitchCount, setTabSwitchCount] = useState(0);
  const [showTabWarning, setShowTabWarning] = useState(false);
  
  // Analysis state
  const [analysis, setAnalysis] = useState<InterviewAnalytics | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [showAnalysis, setShowAnalysis] = useState(false);
  
  // Retell Web Client reference
  const webClientRef = useRef<any>(null);

  useEffect(() => {
    if (interviewId) {
      loadInterview();
    }
  }, [interviewId]);

  // Timer effect
  useEffect(() => {
    let intervalId: NodeJS.Timeout;
    if (isCalling) {
      intervalId = setInterval(() => {
        setTime((prev) => {
          if (prev >= maxTime) {
            handleEndCall();
            return prev;
          }
          return prev + 1;
        });
      }, 1000);
    }
    return () => clearInterval(intervalId);
  }, [isCalling, maxTime]);

  // Tab switch detection
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.hidden && isCalling) {
        setTabSwitchCount((prev) => prev + 1);
        setShowTabWarning(true);
        toast.warning('Tab switch detected!', {
          description: 'Please stay on this page during the interview.',
        });
      } else {
        setShowTabWarning(false);
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
  }, [isCalling]);

  const loadInterview = async () => {
    if (!interviewId) return;
    
    setIsLoading(true);
    try {
      const [interviewData, interviewersData] = await Promise.all([
        getInterview(interviewId),
        getInterviewers(),
      ]);
      
      setInterview(interviewData);
      setMaxTime(parseInt(interviewData.time_duration) * 60);
      
      const matchingInterviewer = interviewersData.interviewers.find(
        (i) => i.id === interviewData.interviewer_id
      );
      setInterviewer(matchingInterviewer || null);
    } catch (error) {
      console.error('Error loading interview:', error);
      toast.error('Failed to load interview');
      navigate('/interview-prep');
    } finally {
      setIsLoading(false);
    }
  };

  const initializeRetellClient = async () => {
    try {
      // Dynamic import of Retell SDK
      const { RetellWebClient } = await import('retell-client-js-sdk');
      webClientRef.current = new RetellWebClient();
      
      // Set up event listeners
      webClientRef.current.on('call_started', () => {
        console.log('Call started');
        setIsCalling(true);
      });

      webClientRef.current.on('call_ended', () => {
        console.log('Call ended');
        setIsCalling(false);
        setIsEnded(true);
      });

      webClientRef.current.on('agent_start_talking', () => {
        setActiveTurn('agent');
      });

      webClientRef.current.on('agent_stop_talking', () => {
        setActiveTurn('');
      });

      webClientRef.current.on('update', (update: any) => {
        if (update.transcript) {
          const transcript = update.transcript;
          transcript.forEach((item: any) => {
            if (item.role === 'agent') {
              setLastInterviewerResponse(item.content);
            } else if (item.role === 'user') {
              setLastUserResponse(item.content);
            }
          });
        }
      });

      webClientRef.current.on('error', (error: any) => {
        console.error('Retell error:', error);
        toast.error('Connection error occurred');
      });

      return true;
    } catch (error) {
      console.error('Failed to initialize Retell client:', error);
      return false;
    }
  };

  const handleStartCall = async () => {
    if (!interview || !userProfile) return;
    
    try {
      setIsStarted(true);
      
      // Initialize Retell client
      const initialized = await initializeRetellClient();
      if (!initialized) {
        toast.error('Failed to initialize voice call');
        setIsStarted(false);
        return;
      }
      
      // Register call with backend
      const callResponse = await registerCall({
        interview_id: interview.id,
        interviewer_id: interview.interviewer_id,
        user_name: userProfile.name,
        user_email: userProfile.email,
      });
      
      setCallId(callResponse.call_id);
      
      // Start the Retell call
      if (webClientRef.current) {
        await webClientRef.current.startCall({
          accessToken: callResponse.access_token,
        });
      }
      
      toast.success('Interview started!');
    } catch (error) {
      console.error('Error starting call:', error);
      toast.error('Failed to start interview');
      setIsStarted(false);
    }
  };

  const handleEndCall = async () => {
    try {
      if (webClientRef.current) {
        webClientRef.current.stopCall();
      }
      
      // Update response with final data
      if (callId) {
        await updateInterviewResponse({
          call_id: callId,
          is_ended: true,
          duration: time,
          tab_switch_count: tabSwitchCount,
        });
      }
      
      setIsCalling(false);
      setIsEnded(true);
      toast.success('Interview completed!');
    } catch (error) {
      console.error('Error ending call:', error);
    }
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const getTimeProgress = () => {
    return (time / maxTime) * 100;
  };

  if (isLoading) {
    return (
      <div style={{ minHeight: '100vh', backgroundColor: '#111827', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white"></div>
      </div>
    );
  }

  if (!interview) {
    return (
      <div style={{ minHeight: '100vh', backgroundColor: '#111827', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#ffffff' }}>
        <p style={{ color: '#ffffff' }}>Interview not found</p>
      </div>
    );
  }

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#111827', color: '#ffffff' }}>
      {/* Tab Switch Warning Overlay */}
      {showTabWarning && (
        <div style={{ position: 'fixed', inset: 0, backgroundColor: 'rgba(127, 29, 29, 0.9)', zIndex: 50, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <div className="text-center">
            <AlertTriangle className="w-16 h-16 mx-auto mb-4" style={{ color: '#f87171' }} />
            <h2 className="text-2xl font-bold mb-2" style={{ color: '#ffffff' }}>Tab Switch Detected!</h2>
            <p className="mb-4" style={{ color: '#fecaca' }}>
              Please stay on this page during the interview.
            </p>
            <p style={{ color: '#fca5a5' }}>Tab switches: {tabSwitchCount}</p>
          </div>
        </div>
      )}

      {/* Header */}
      <header style={{ backgroundColor: '#1f2937', borderBottom: '1px solid #374151', position: 'sticky', top: 0, zIndex: 10 }}>
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={() => !isCalling && navigate('/interview-prep')}
              disabled={isCalling}
              style={{ backgroundColor: '#374151', border: '1px solid #4b5563' }}
              className="p-2.5 hover:bg-gray-600 rounded-lg transition-colors disabled:opacity-50"
              title="Back to Interview Prep"
            >
              <ArrowLeft className="w-5 h-5" style={{ color: '#ffffff' }} />
            </button>
            <button
              onClick={() => !isCalling && navigate('/home')}
              disabled={isCalling}
              className="px-4 py-2.5 bg-blue-600 hover:bg-blue-700 font-medium rounded-lg transition-colors disabled:opacity-50 text-sm"
              style={{ color: '#ffffff' }}
            >
              🏠 Home
            </button>
            <div>
              <h1 className="font-semibold text-lg" style={{ color: '#ffffff' }}>{interview.name}</h1>
              {interview.job_title && (
                <p className="text-sm" style={{ color: '#d1d5db' }}>
                  {interview.job_title} at {interview.company_name}
                </p>
              )}
            </div>
          </div>
          
          {/* Timer */}
          {isStarted && (
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2 px-4 py-2 rounded-lg" style={{ backgroundColor: '#374151' }}>
                <Clock className="w-4 h-4" style={{ color: '#9ca3af' }} />
                <span className="font-mono text-lg" style={{ color: '#ffffff' }}>{formatTime(time)}</span>
                <span style={{ color: '#9ca3af' }}>/</span>
                <span className="font-mono" style={{ color: '#9ca3af' }}>{formatTime(maxTime)}</span>
              </div>
              <div className="w-32 h-2 rounded-full overflow-hidden" style={{ backgroundColor: '#374151' }}>
                <div
                  className={`h-full transition-all duration-1000 ${
                    getTimeProgress() > 80 ? 'bg-red-500' : 'bg-blue-500'
                  }`}
                  style={{ width: `${getTimeProgress()}%` }}
                />
              </div>
            </div>
          )}
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-8">
        {!isStarted ? (
          // Pre-interview screen
          <div className="text-center max-w-2xl mx-auto">
            {/* Interviewer Info */}
            {interviewer && (
              <div className="mb-8">
                <div className="w-24 h-24 bg-gradient-to-br from-purple-500 to-indigo-600 rounded-full mx-auto mb-4 flex items-center justify-center text-3xl font-bold" style={{ color: '#ffffff' }}>
                  {interviewer.name.charAt(0)}
                </div>
                <h2 className="text-2xl font-bold" style={{ color: '#ffffff' }}>{interviewer.name}</h2>
                <p className="text-lg" style={{ color: '#d1d5db' }}>{interviewer.description}</p>
              </div>
            )}

            {/* Interview Details */}
            <div className="rounded-xl p-6 mb-8 text-left" style={{ backgroundColor: '#1f2937', border: '1px solid #374151' }}>
              <h3 className="font-bold text-lg mb-4 flex items-center gap-2" style={{ color: '#ffffff' }}>
                <MessageSquare className="w-5 h-5" style={{ color: '#60a5fa' }} />
                Interview Questions ({interview.question_count})
              </h3>
              <ul className="space-y-3">
                {interview.questions.map((q, i) => (
                  <li key={q.id} className="flex items-start gap-3">
                    <span className="flex-shrink-0 w-6 h-6 bg-blue-600 rounded-full flex items-center justify-center text-xs font-bold" style={{ color: '#ffffff' }}>
                      {i + 1}
                    </span>
                    <span className="text-base" style={{ color: '#ffffff' }}>{q.question}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Instructions */}
            <div className="rounded-xl p-6 mb-8 text-left" style={{ backgroundColor: '#1f2937', border: '1px solid #374151' }}>
              <h3 className="font-bold text-lg mb-3" style={{ color: '#ffffff' }}>Instructions</h3>
              <ul className="space-y-2 text-base" style={{ color: '#e5e7eb' }}>
                <li>• Make sure your microphone is working properly</li>
                <li>• Find a quiet place with minimal background noise</li>
                <li>• Speak clearly and at a normal pace</li>
                <li>• Stay on this page during the interview</li>
                <li>• The interview will automatically end after {interview.time_duration} minutes</li>
              </ul>
            </div>

            {/* Start Button */}
            <button
              onClick={handleStartCall}
              className="flex items-center gap-3 px-10 py-5 bg-gradient-to-r from-green-500 to-emerald-600 text-white rounded-xl hover:from-green-600 hover:to-emerald-700 transition-all mx-auto text-xl font-semibold shadow-lg hover:shadow-xl border-2 border-green-400"
            >
              <Play className="w-7 h-7" />
              Start Interview
            </button>
          </div>
        ) : isEnded ? (
          // Post-interview screen
          <div className="text-center max-w-2xl mx-auto">
            <div className="w-24 h-24 bg-green-500/20 rounded-full mx-auto mb-6 flex items-center justify-center">
              <CheckCircle className="w-12 h-12 text-green-500" />
            </div>
            <h2 className="text-2xl font-bold mb-2" style={{ color: '#ffffff' }}>Interview Completed!</h2>
            <p className="mb-8 text-lg" style={{ color: '#d1d5db' }}>
              Great job! {analysis ? 'Here are your results.' : 'Click "View Analysis" to see your performance insights.'}
            </p>

            {/* Summary */}
            <div className="rounded-xl p-6 mb-8 text-left" style={{ backgroundColor: '#1f2937', border: '1px solid #374151' }}>
              <h3 className="font-bold text-lg mb-4" style={{ color: '#ffffff' }}>Session Summary</h3>
              <div className="grid grid-cols-3 gap-4">
                <div className="text-center">
                  <p className="text-2xl font-bold" style={{ color: '#60a5fa' }}>{formatTime(time)}</p>
                  <p className="text-sm" style={{ color: '#d1d5db' }}>Duration</p>
                </div>
                <div className="text-center">
                  <p className="text-2xl font-bold" style={{ color: '#60a5fa' }}>{interview.question_count}</p>
                  <p className="text-sm" style={{ color: '#d1d5db' }}>Questions</p>
                </div>
                <div className="text-center">
                  <p className="text-2xl font-bold" style={{ color: tabSwitchCount > 0 ? '#f87171' : '#4ade80' }}>
                    {tabSwitchCount}
                  </p>
                  <p className="text-sm" style={{ color: '#d1d5db' }}>Tab Switches</p>
                </div>
              </div>
            </div>

            {/* Analysis Results */}
            {analysis && (
              <div className="rounded-xl p-6 mb-8 text-left" style={{ backgroundColor: '#1f2937', border: '1px solid #374151' }}>
                <h3 className="font-bold text-lg mb-4" style={{ color: '#ffffff' }}>📊 Performance Analysis</h3>
                
                {/* Scores */}
                <div className="grid grid-cols-3 gap-4 mb-6">
                  <div className="text-center p-4 rounded-lg" style={{ backgroundColor: '#374151' }}>
                    <p className="text-3xl font-bold" style={{ color: '#4ade80' }}>{analysis.overall_score}/10</p>
                    <p className="text-sm" style={{ color: '#d1d5db' }}>Overall Score</p>
                  </div>
                  <div className="text-center p-4 rounded-lg" style={{ backgroundColor: '#374151' }}>
                    <p className="text-3xl font-bold" style={{ color: '#60a5fa' }}>{analysis.communication_score}/10</p>
                    <p className="text-sm" style={{ color: '#d1d5db' }}>Communication</p>
                  </div>
                  <div className="text-center p-4 rounded-lg" style={{ backgroundColor: '#374151' }}>
                    <p className="text-3xl font-bold" style={{ color: '#a78bfa' }}>{analysis.technical_score}/10</p>
                    <p className="text-sm" style={{ color: '#d1d5db' }}>Technical</p>
                  </div>
                </div>

                {/* Strengths */}
                <div className="mb-4">
                  <h4 className="font-semibold mb-2" style={{ color: '#4ade80' }}>✓ Strengths</h4>
                  <ul className="space-y-1">
                    {analysis.strengths.map((s, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm" style={{ color: '#e5e7eb' }}>
                        <span style={{ color: '#4ade80' }}>•</span> {s}
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Improvements */}
                <div className="mb-4">
                  <h4 className="font-semibold mb-2" style={{ color: '#fbbf24' }}>→ Areas for Improvement</h4>
                  <ul className="space-y-1">
                    {analysis.improvements.map((s, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm" style={{ color: '#e5e7eb' }}>
                        <span style={{ color: '#fbbf24' }}>•</span> {s}
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Notable Quotes */}
                {analysis.notable_quotes && analysis.notable_quotes.length > 0 && (
                  <div>
                    <h4 className="font-semibold mb-2" style={{ color: '#60a5fa' }}>💬 Notable Responses</h4>
                    <div className="space-y-2">
                      {analysis.notable_quotes.map((q, i) => (
                        <p key={i} className="text-sm italic p-2 rounded" style={{ backgroundColor: '#374151', color: '#d1d5db' }}>
                          "{q}"
                        </p>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            <div className="flex gap-4 justify-center flex-wrap">
              {!analysis && callId && (
                <button
                  onClick={async () => {
                    if (!callId) return;
                    setIsAnalyzing(true);
                    try {
                      const result = await analyzeInterview(callId);
                      setAnalysis(result);
                      toast.success('Analysis complete!');
                    } catch (error) {
                      console.error('Error analyzing interview:', error);
                      toast.error('Analysis not available yet. Please try again in a few moments.');
                    } finally {
                      setIsAnalyzing(false);
                    }
                  }}
                  disabled={isAnalyzing}
                  className="px-6 py-3 bg-gradient-to-r from-green-500 to-emerald-600 text-white font-medium rounded-lg hover:from-green-600 hover:to-emerald-700 transition-all border border-green-400 shadow-md disabled:opacity-50"
                >
                  {isAnalyzing ? (
                    <>
                      <span className="inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></span>
                      Analyzing...
                    </>
                  ) : '📊 View Analysis'}
                </button>
              )}
              <button
                onClick={() => navigate('/home')}
                className="px-6 py-3 bg-gradient-to-r from-gray-600 to-gray-700 text-white font-medium rounded-lg hover:from-gray-700 hover:to-gray-800 transition-all border border-gray-500 shadow-md"
              >
                🏠 Home
              </button>
              <button
                onClick={() => navigate('/interview-prep')}
                className="px-6 py-3 bg-gradient-to-r from-purple-500 to-indigo-600 text-white font-medium rounded-lg hover:from-purple-600 hover:to-indigo-700 transition-all border border-purple-400 shadow-md"
              >
                Back to Dashboard
              </button>
              <button
                onClick={() => {
                  setIsStarted(false);
                  setIsEnded(false);
                  setTime(0);
                  setTabSwitchCount(0);
                  setAnalysis(null);
                }}
                className="px-6 py-3 bg-gradient-to-r from-blue-500 to-cyan-600 text-white font-medium rounded-lg hover:from-blue-600 hover:to-cyan-700 transition-all border border-blue-400 shadow-md"
              >
                Practice Again
              </button>
            </div>
          </div>
        ) : (
          // Active interview screen
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Main Interview Area */}
            <div className="lg:col-span-2 space-y-6">
              {/* Interviewer Response */}
              <div className="rounded-xl p-6" style={{ backgroundColor: '#1f2937', border: '1px solid #374151' }}>
                <div className="flex items-center gap-3 mb-4">
                  <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold ${activeTurn === 'agent' ? 'bg-green-500 animate-pulse' : 'bg-gray-600'}`} style={{ color: '#ffffff' }}>
                    {interviewer?.name.charAt(0) || 'I'}
                  </div>
                  <div>
                    <p className="font-medium" style={{ color: '#ffffff' }}>{interviewer?.name || 'Interviewer'}</p>
                    <p className="text-sm" style={{ color: '#d1d5db' }}>
                      {activeTurn === 'agent' ? 'Speaking...' : 'Listening'}
                    </p>
                  </div>
                </div>
                <p className="min-h-[60px] text-lg leading-relaxed" style={{ color: '#ffffff' }}>
                  {lastInterviewerResponse || 'Waiting for interviewer...'}
                </p>
              </div>

              {/* User Response */}
              <div className="rounded-xl p-6" style={{ backgroundColor: '#1f2937', border: '1px solid #374151' }}>
                <div className="flex items-center gap-3 mb-4">
                  <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold ${activeTurn === 'user' ? 'bg-blue-500 animate-pulse' : 'bg-gray-600'}`} style={{ color: '#ffffff' }}>
                    {userProfile?.name.charAt(0) || 'Y'}
                  </div>
                  <div>
                    <p className="font-medium" style={{ color: '#ffffff' }}>You</p>
                    <p className="text-sm" style={{ color: '#d1d5db' }}>
                      {activeTurn === 'user' ? 'Speaking...' : 'Your turn'}
                    </p>
                  </div>
                </div>
                <p className="min-h-[60px] text-lg leading-relaxed" style={{ color: '#ffffff' }}>
                  {lastUserResponse || 'Start speaking...'}
                </p>
              </div>

              {/* Call Controls */}
              <div className="flex justify-center gap-6">
                <button
                  onClick={handleEndCall}
                  className="flex items-center gap-3 px-10 py-4 bg-gradient-to-r from-red-500 to-rose-600 text-white rounded-xl hover:from-red-600 hover:to-rose-700 transition-all font-semibold shadow-lg hover:shadow-xl border-2 border-red-400 text-lg"
                >
                  <PhoneOff className="w-6 h-6" />
                  End Interview
                </button>
              </div>
            </div>

            {/* Sidebar - Questions */}
            <div className="rounded-xl p-6 h-fit sticky top-24" style={{ backgroundColor: '#1f2937', border: '1px solid #374151' }}>
              <h3 className="font-bold text-lg mb-4 flex items-center gap-2" style={{ color: '#ffffff' }}>
                <MessageSquare className="w-5 h-5" style={{ color: '#60a5fa' }} />
                Questions
              </h3>
              <ul className="space-y-3">
                {interview.questions.map((q, i) => (
                  <li key={q.id} className="flex items-start gap-3">
                    <span className="flex-shrink-0 w-5 h-5 bg-blue-600 rounded-full flex items-center justify-center text-xs font-bold" style={{ color: '#ffffff' }}>
                      {i + 1}
                    </span>
                    <span className="text-sm" style={{ color: '#ffffff' }}>{q.question}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
