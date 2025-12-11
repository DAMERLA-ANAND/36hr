"""
Comprehensive Chatbot Simulation Test
=====================================
This test file simulates a real-world conversation flow to test all chatbot endpoints
and features including:
- Creating new chats
- Sending messages with context retention
- Job search via function calling
- Job selection and follow-up questions
- Resume tips and career advice
- Context management (permanent context, summaries, recent messages)
- Getting chat messages and history

Run with: python test_chatbot_simulation.py
Make sure the backend server is running: uvicorn main:app --reload
"""

import requests
import json
import time
import os
from datetime import datetime

# Base URL of the running backend server
BASE_URL = "http://localhost:8000"

# Test user email - should exist in database (run test_simulation.py first to create user)
TEST_USER_EMAIL = None  # Will be set after onboarding

# Color codes for pretty printing
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}  {text}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.END}\n")

def print_step(step_num, text):
    print(f"\n{Colors.CYAN}{Colors.BOLD}[Step {step_num}] {text}{Colors.END}")
    print(f"{Colors.CYAN}{'-'*50}{Colors.END}")

def print_user_message(msg):
    print(f"{Colors.GREEN}👤 USER: {msg}{Colors.END}")

def print_bot_response(msg):
    # Truncate long responses for readability
    if len(msg) > 500:
        msg = msg[:500] + "... [truncated]"
    print(f"{Colors.BLUE}🤖 BOT: {msg}{Colors.END}")

def print_jobs_found(jobs):
    if jobs:
        print(f"{Colors.YELLOW}📋 JOBS FOUND: {len(jobs)} positions{Colors.END}")
        for i, job in enumerate(jobs[:3], 1):  # Show first 3
            print(f"   {i}. {job.get('job_title', 'N/A')} at {job.get('employer_name', 'N/A')}")
            if job.get('job_location'):
                print(f"      📍 {job.get('job_location')}")
            if job.get('job_salary'):
                print(f"      💰 {job.get('job_salary')}")
        if len(jobs) > 3:
            print(f"   ... and {len(jobs) - 3} more jobs")

def print_error(msg):
    print(f"{Colors.RED}❌ ERROR: {msg}{Colors.END}")

def print_success(msg):
    print(f"{Colors.GREEN}✅ {msg}{Colors.END}")

def print_info(msg):
    print(f"{Colors.YELLOW}ℹ️  {msg}{Colors.END}")

# Resume file path
RESUME_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "23501a4412_Resume.pdf")


def setup_test_user():
    """Create a test user by uploading a resume and confirming onboarding."""
    global TEST_USER_EMAIL
    
    print_header("SETTING UP TEST USER")
    
    # Check if resume exists, if not create a mock user
    if os.path.exists(RESUME_PATH):
        print_info(f"Found resume at: {RESUME_PATH}")
        
        # Upload resume
        print_step("0.1", "Uploading Resume")
        with open(RESUME_PATH, 'rb') as f:
            pdf_content = f.read()
        
        response = requests.post(f"{BASE_URL}/api/onboardFileUpload", data=pdf_content)
        
        if response.status_code == 200:
            onboarding_data = response.json()
            print_success("Resume parsed successfully")
            TEST_USER_EMAIL = onboarding_data.get("email", "chatbot_test@example.com")
        else:
            print_error(f"Failed to parse resume: {response.status_code}")
            # Use mock data
            onboarding_data = create_mock_user_data()
            TEST_USER_EMAIL = onboarding_data["email"]
    else:
        print_info("Resume not found, using mock user data")
        onboarding_data = create_mock_user_data()
        TEST_USER_EMAIL = onboarding_data["email"]
    
    # Confirm onboarding
    print_step("0.2", "Confirming Onboarding Details")
    response = requests.post(f"{BASE_URL}/api/confirmOnboardingDetails", json=onboarding_data)
    
    if response.status_code == 200:
        print_success(f"User created/updated: {TEST_USER_EMAIL}")
    else:
        print_info(f"Note: {response.status_code} - {response.text}")
    
    return TEST_USER_EMAIL


def create_mock_user_data():
    """Create mock user data for testing."""
    return {
        "name": "Alex Johnson",
        "email": "alex.johnson.chattest@example.com",
        "phone": "+1-555-0123",
        "location": "San Francisco, CA",
        "skills": [
            "Python", "JavaScript", "React", "Node.js", "TypeScript",
            "AWS", "Docker", "PostgreSQL", "MongoDB", "Git",
            "REST APIs", "GraphQL", "Machine Learning", "Agile"
        ],
        "experience": [
            "Senior Software Engineer at TechCorp (2021-2024): Led development of microservices architecture, mentored 5 junior developers",
            "Software Engineer at StartupXYZ (2019-2021): Built React frontend and Node.js backend for SaaS platform",
            "Junior Developer at WebAgency (2017-2019): Full-stack web development using JavaScript and Python"
        ],
        "profile_summary": "Experienced full-stack developer with 7+ years of experience building scalable web applications. Expert in Python, JavaScript, and cloud technologies. Passionate about clean code and mentoring.",
        "education": [
            "M.S. Computer Science, Stanford University, 2017",
            "B.S. Computer Science, UC Berkeley, 2015"
        ],
        "projects": [
            "Open-source contribution to React ecosystem with 500+ GitHub stars",
            "Built real-time analytics dashboard processing 1M+ events/day"
        ],
        "certificationsAndAchievementsAndAwards": [
            "AWS Solutions Architect Professional",
            "Google Cloud Professional Data Engineer"
        ]
    }


def test_create_chat(email):
    """Test creating a new chat session."""
    print_step(1, "Creating New Chat Session")
    
    response = requests.post(
        f"{BASE_URL}/api/createChat",
        json={"email": email}
    )
    
    if response.status_code == 200:
        data = response.json()
        chat_id = data.get("chat_id")
        initial_message = data.get("initial_message")
        
        print_success(f"Chat created with ID: {chat_id}")
        print_bot_response(initial_message)
        return chat_id
    else:
        print_error(f"Failed to create chat: {response.status_code} - {response.text}")
        return None


def test_send_message(email, chat_id, message, selected_job_id=None):
    """Test sending a message and receiving a response."""
    print_user_message(message)
    
    payload = {
        "email": email,
        "chat_id": chat_id,
        "message": message
    }
    if selected_job_id:
        payload["selected_job_id"] = selected_job_id
        print_info(f"Selected job ID: {selected_job_id}")
    
    start_time = time.time()
    response = requests.post(f"{BASE_URL}/api/sendMessage", json=payload)
    elapsed = time.time() - start_time
    
    if response.status_code == 200:
        data = response.json()
        bot_message = data.get("message", "")
        jobs = data.get("jobs")
        selected_job = data.get("selected_job_details")
        
        print_bot_response(bot_message)
        print_info(f"Response time: {elapsed:.2f}s")
        
        if jobs:
            print_jobs_found(jobs)
        
        if selected_job:
            print_info(f"Selected job details received: {selected_job.get('job_title')}")
        
        return data
    else:
        print_error(f"Failed to send message: {response.status_code} - {response.text}")
        return None


def test_get_chat_messages(email, chat_id):
    """Test getting all messages from a chat."""
    print_step("X", "Fetching Chat Messages")
    
    response = requests.get(
        f"{BASE_URL}/api/getChatMessages",
        params={"email": email, "chat_id": chat_id}
    )
    
    if response.status_code == 200:
        data = response.json()
        messages = data.get("messages", [])
        chat_name = data.get("chat_name", "Unknown")
        
        print_success(f"Retrieved {len(messages)} messages from chat: {chat_name}")
        return data
    else:
        print_error(f"Failed to get messages: {response.status_code} - {response.text}")
        return None


def test_get_chat_history(email):
    """Test getting chat history for user."""
    print_step("X", "Fetching Chat History")
    
    response = requests.get(
        f"{BASE_URL}/api/chatHistoryRequest",
        params={"email": email}
    )
    
    if response.status_code == 200:
        data = response.json()
        chats = data.get("chats", [])
        print_success(f"Found {len(chats)} chats in history")
        for chat in chats[:5]:
            print(f"   - {chat.get('chat_name', 'Unnamed')} (ID: {chat.get('chat_id', 'N/A')[:8]}...)")
        return data
    else:
        print_error(f"Failed to get chat history: {response.status_code} - {response.text}")
        return None


def run_conversation_simulation():
    """Run a comprehensive conversation simulation."""
    
    print_header("CHATBOT SIMULATION TEST")
    print(f"Server: {BASE_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Setup test user
    email = setup_test_user()
    if not email:
        print_error("Failed to setup test user")
        return
    
    # Small delay to let the database settle
    time.sleep(1)
    
    # ============================================
    # CONVERSATION 1: Job Search Flow
    # ============================================
    print_header("CONVERSATION 1: Job Search Flow")
    
    chat_id = test_create_chat(email)
    if not chat_id:
        return
    
    time.sleep(1)
    
    # Message 1: Greeting and asking for jobs
    print_step(2, "User asks about job opportunities")
    response = test_send_message(
        email, chat_id,
        "Hi! I'm looking for software engineering jobs. Can you help me find some positions that match my skills?"
    )
    time.sleep(2)
    
    # Message 2: More specific request
    print_step(3, "User specifies preferences")
    response = test_send_message(
        email, chat_id,
        "I'd prefer remote positions. Also, I'm particularly interested in Python or full-stack roles. Can you search for those?"
    )
    time.sleep(2)
    
    # Message 3: Ask about specific technologies
    print_step(4, "User asks about specific tech stack")
    response = test_send_message(
        email, chat_id,
        "Do you have any jobs that require React and Node.js? I have a lot of experience with those technologies."
    )
    time.sleep(2)
    
    # Store a job ID if we got jobs
    selected_job_id = None
    if response and response.get("jobs"):
        selected_job_id = response["jobs"][0].get("job_id")
    
    # Message 4: Select a job (if we have one)
    if selected_job_id:
        print_step(5, "User selects a job for more details")
        response = test_send_message(
            email, chat_id,
            "I'm interested in the first job you showed me. Can you tell me more about it and how I should prepare?",
            selected_job_id=selected_job_id
        )
        time.sleep(2)
        
        # Message 5: Ask about resume tips for this job
        print_step(6, "User asks for resume tips")
        response = test_send_message(
            email, chat_id,
            "Based on this job's requirements, what should I highlight in my resume? Any specific improvements you'd suggest?"
        )
        time.sleep(2)
        
        # Message 6: Interview preparation
        print_step(7, "User asks for interview tips")
        response = test_send_message(
            email, chat_id,
            "If I get an interview for this position, what kind of questions should I expect? Can you help me prepare?"
        )
        time.sleep(2)
    
    # Message 7: Application questions
    print_step(8, "User asks about application questions")
    response = test_send_message(
        email, chat_id,
        "The application asks 'Why do you want to work here?' - how should I answer this for a tech company?"
    )
    time.sleep(2)
    
    # Message 8: Career advice
    print_step(9, "User asks for general career advice")
    response = test_send_message(
        email, chat_id,
        "I've been a developer for 7 years. Should I consider moving into management or stay technical? What's your advice?"
    )
    time.sleep(2)
    
    # ============================================
    # Verify chat messages were stored
    # ============================================
    print_header("VERIFYING CHAT STORAGE")
    test_get_chat_messages(email, chat_id)
    
    # ============================================
    # CONVERSATION 2: Different Job Search
    # ============================================
    print_header("CONVERSATION 2: Different Domain Search")
    
    chat_id_2 = test_create_chat(email)
    if not chat_id_2:
        return
    
    time.sleep(1)
    
    # Message 1: Different type of search
    print_step(10, "User searches for different role")
    response = test_send_message(
        email, chat_id_2,
        "I'm considering a career change to data science. What data scientist positions are available for someone with my software engineering background?"
    )
    time.sleep(2)
    
    # Message 2: Experience requirements
    print_step(11, "User asks about requirements")
    response = test_send_message(
        email, chat_id_2,
        "What skills would I need to learn to transition from software engineering to data science? Do these jobs require a lot of ML experience?"
    )
    time.sleep(2)
    
    # Message 3: Salary comparison
    print_step(12, "User asks about salary")
    response = test_send_message(
        email, chat_id_2,
        "How do data science salaries compare to software engineering? Should I expect a pay cut during the transition?"
    )
    time.sleep(2)
    
    # ============================================
    # CONVERSATION 3: Long Context Test
    # ============================================
    print_header("CONVERSATION 3: Long Context Memory Test")
    
    chat_id_3 = test_create_chat(email)
    if not chat_id_3:
        return
    
    time.sleep(1)
    
    # Series of messages to test context retention
    messages = [
        "I'm Alex, a senior developer with 7 years experience in Python and JavaScript.",
        "I'm currently based in San Francisco but open to relocation.",
        "My salary expectation is around $180k to $200k for a senior role.",
        "I prefer working at mid-size companies, not too big and not too small.",
        "Remote work is very important to me, ideally fully remote.",
        "I'm most interested in companies working on developer tools or AI.",
        "Based on everything I've told you, what jobs would you recommend?",
        "Can you summarize what you know about my preferences so far?",
        "Now search for jobs that match all my criteria we discussed.",
        "What's the most important thing I should highlight in my applications based on my background?"
    ]
    
    for i, msg in enumerate(messages, 13):
        print_step(i, f"Message {i-12}/10 - Testing context retention")
        response = test_send_message(email, chat_id_3, msg)
        time.sleep(2)
    
    # ============================================
    # Final Verification
    # ============================================
    print_header("FINAL VERIFICATION")
    
    # Get all chat history
    test_get_chat_history(email)
    
    # Get messages from the long conversation
    print_step("Final", "Verifying long conversation storage")
    result = test_get_chat_messages(email, chat_id_3)
    if result:
        msg_count = len(result.get("messages", []))
        print_success(f"Long conversation has {msg_count} messages stored")
        
        # Check if context was summarized (should have fewer recent messages but retain summary)
        print_info("Context management is working if the bot remembered preferences from early messages")
    
    print_header("SIMULATION COMPLETE")
    print(f"""
{Colors.GREEN}Summary:{Colors.END}
- Created 3 chat sessions
- Tested job search functionality
- Tested job selection and follow-up
- Tested resume and interview tips
- Tested career advice
- Tested long conversation context retention
- Verified message storage

{Colors.YELLOW}Note:{Colors.END} 
- Check the bot responses to ensure they reference user profile context
- Job search results depend on JSearch API availability and RAPIDAPI_KEY
- Context summarization kicks in after 5 message exchanges
""")


def test_individual_endpoint(endpoint_name):
    """Test a specific endpoint."""
    email = setup_test_user()
    
    if endpoint_name == "create_chat":
        test_create_chat(email)
    elif endpoint_name == "chat_history":
        test_get_chat_history(email)
    elif endpoint_name == "send_message":
        chat_id = test_create_chat(email)
        if chat_id:
            test_send_message(email, chat_id, "Hello, can you help me find a job?")
    else:
        print_error(f"Unknown endpoint: {endpoint_name}")


if __name__ == "__main__":
    import sys
    
    print(f"""
{Colors.HEADER}╔════════════════════════════════════════════════════════════╗
║        CHATBOT ENDPOINT SIMULATION TEST                    ║
║        Tests all chatbot features with real conversations  ║
╚════════════════════════════════════════════════════════════╝{Colors.END}
    """)
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/docs", timeout=5)
        print_success(f"Server is running at {BASE_URL}")
    except requests.exceptions.ConnectionError:
        print_error(f"Cannot connect to server at {BASE_URL}")
        print_info("Make sure the backend is running: uvicorn main:app --reload")
        sys.exit(1)
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        endpoint = sys.argv[1]
        test_individual_endpoint(endpoint)
    else:
        # Run full simulation
        try:
            run_conversation_simulation()
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}Test interrupted by user{Colors.END}")
        except Exception as e:
            print_error(f"Unexpected error: {str(e)}")
            import traceback
            traceback.print_exc()
