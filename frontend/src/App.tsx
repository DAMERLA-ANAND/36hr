import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
} from 'react-router-dom';
import { useState, useEffect } from 'react';
import { Toaster } from 'sonner';
import OnboardingPage from './components/OnboardingPage';
import HomePage from './components/HomePage';
import ChatPage from './components/ChatPage';
import ProfilePage from './components/ProfilePage';

export interface UserProfile {
  name: string;
  email: string;
  phone: string;
  location: string;
  skills: string[];
  experience: string[];
  profile_summary: string;
  resumeUploaded: boolean;
  profilePhoto?: string;
  // optional fields
  education?: string[];
  certificationsAndAchievementsAndAwards?: string[];
  projects?: string[];
  about?: string;
}

export interface Job {
  id: string;
  title: string;
  company: string;
  role: string;
  description: string;
  location: string;
  salary: string;
  applyLink?: string;
  postedAt?: string;
  isRemote?: boolean;
  employerLogo?: string;
  highlights?: {
    Qualifications?: string[];
    Responsibilities?: string[];
  };
}

export interface Chat {
  id: string;
  title: string;
  messages: Message[];
  timestamp: Date;
}

export interface Message {
  id: string;
  sender: 'user' | 'bot';
  content: string;
  timestamp: Date;
}

function App() {
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null);
  const [savedJobs, setSavedJobs] = useState<Job[]>([]);
  const [appliedJobs, setAppliedJobs] = useState<Job[]>([]);
  const [chats, setChats] = useState<Chat[]>([]);
  const [isOnboarded, setIsOnboarded] = useState(false);

  useEffect(() => {
    // Load data from localStorage
    const storedProfile = localStorage.getItem('userProfile');
    const storedSavedJobs = localStorage.getItem('savedJobs');
    const storedAppliedJobs = localStorage.getItem('appliedJobs');
    const storedChats = localStorage.getItem('chats');
    const storedOnboarded = localStorage.getItem('isOnboarded');

    if (storedProfile) setUserProfile(JSON.parse(storedProfile));
    if (storedSavedJobs) setSavedJobs(JSON.parse(storedSavedJobs));
    if (storedAppliedJobs) setAppliedJobs(JSON.parse(storedAppliedJobs));
    if (storedChats) {
      const parsedChats = JSON.parse(storedChats);
      // Convert timestamp strings back to Date objects
      parsedChats.forEach((chat: Chat) => {
        chat.timestamp = new Date(chat.timestamp);
        chat.messages.forEach((msg: Message) => {
          msg.timestamp = new Date(msg.timestamp);
        });
      });
      setChats(parsedChats);
    }
    if (storedOnboarded) setIsOnboarded(JSON.parse(storedOnboarded));
  }, []);

  const completeOnboarding = (profile: UserProfile) => {
    setUserProfile(profile);
    setIsOnboarded(true);
    localStorage.setItem('userProfile', JSON.stringify(profile));
    localStorage.setItem('isOnboarded', JSON.stringify(true));
  };

  const updateProfile = (profile: UserProfile) => {
    setUserProfile(profile);
    localStorage.setItem('userProfile', JSON.stringify(profile));
  };

  const saveJob = (job: Job) => {
    const newSavedJobs = [...savedJobs, job];
    setSavedJobs(newSavedJobs);
    localStorage.setItem('savedJobs', JSON.stringify(newSavedJobs));
  };

  const unsaveJob = (job: Job) => {
    const newSavedJobs = savedJobs.filter((j) => j.id !== job.id);
    setSavedJobs(newSavedJobs);
    localStorage.setItem('savedJobs', JSON.stringify(newSavedJobs));
  };

  const applyToJob = (job: Job) => {
    const newAppliedJobs = [...appliedJobs, job];
    setAppliedJobs(newAppliedJobs);
    localStorage.setItem('appliedJobs', JSON.stringify(newAppliedJobs));
  };

  const addChat = (chat: Chat) => {
    const newChats = [chat, ...chats];
    setChats(newChats);
    localStorage.setItem('chats', JSON.stringify(newChats));
  };

  const updateChat = (chatId: string, messages: Message[], title?: string) => {
    const updatedChats = chats.map((chat) =>
      chat.id === chatId ? { ...chat, messages, ...(title && { title }) } : chat
    );
    setChats(updatedChats);
    localStorage.setItem('chats', JSON.stringify(updatedChats));
  };

  const deleteChat = (chatId: string) => {
    const filteredChats = chats.filter((chat) => chat.id !== chatId);
    setChats(filteredChats);
    localStorage.setItem('chats', JSON.stringify(filteredChats));
  };

  const signOut = () => {
    setUserProfile(null);
    setIsOnboarded(false);
    setSavedJobs([]);
    setAppliedJobs([]);
    setChats([]);
    localStorage.clear();
  };

  return (
    <Router>
      <div className='min-h-screen bg-gray-50'>
        <Toaster position='top-center' richColors />
        <Routes>
          <Route
            path='/'
            element={
              !isOnboarded ? (
                <OnboardingPage onComplete={completeOnboarding} />
              ) : (
                <Navigate to='/home' replace />
              )
            }
          />
          <Route
            path='/home'
            element={
              isOnboarded ? (
                <HomePage
                  savedJobs={savedJobs}
                  appliedJobs={appliedJobs}
                  chats={chats}
                  userProfile={userProfile}
                  unsaveJob={unsaveJob}
                  applyToJob={applyToJob}
                  deleteChat={deleteChat}
                />
              ) : (
                <Navigate to='/' replace />
              )
            }
          />
          <Route
            path='/chat/:chatId?'
            element={
              isOnboarded && userProfile ? (
                <ChatPage
                  chats={chats}
                  addChat={addChat}
                  updateChat={updateChat}
                  savedJobs={savedJobs}
                  appliedJobs={appliedJobs}
                  saveJob={saveJob}
                  unsaveJob={unsaveJob}
                  applyToJob={applyToJob}
                  userEmail={userProfile.email}
                />
              ) : (
                <Navigate to='/' replace />
              )
            }
          />
          <Route
            path='/profile'
            element={
              isOnboarded && userProfile ? (
                <ProfilePage
                  userProfile={userProfile}
                  updateProfile={updateProfile}
                  signOut={signOut}
                />
              ) : (
                <Navigate to='/' replace />
              )
            }
          />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
