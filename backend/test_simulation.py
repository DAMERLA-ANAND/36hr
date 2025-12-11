import requests
import os
import json

# Base URL of the running backend server
BASE_URL = "http://localhost:8000"

# Path to the resume file
RESUME_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "23501a4412_Resume.pdf")

def print_step(step_name):
    print(f"\n{'='*20} {step_name} {'='*20}")

def test_simulation():
    # Check if resume exists
    if not os.path.exists(RESUME_PATH):
        print(f"Error: Resume file not found at {RESUME_PATH}")
        return

    # 1. Onboard User (Upload Resume)
    print_step("1. Uploading Resume")
    url = f"{BASE_URL}/api/onboardFileUpload"
    files = {'file': open(RESUME_PATH, 'rb')}
    
    # Note: The endpoint expects the body to be the raw PDF content, not multipart/form-data with 'file' key
    # based on: content = await request.body() and if not content.startswith(b'%PDF-')
    # So we send data=file_content
    
    with open(RESUME_PATH, 'rb') as f:
        pdf_content = f.read()
        
    response = requests.post(url, data=pdf_content)
    
    if response.status_code != 200:
        print(f"Failed to upload resume: {response.status_code} - {response.text}")
        return
    
    onboarding_data = response.json()
    print("Onboarding Data Received:")
    print(json.dumps(onboarding_data, indent=2))
    
    # 2. Confirm Onboarding Details
    print_step("2. Confirming Onboarding Details")
    confirm_url = f"{BASE_URL}/api/confirmOnboardingDetails"
    
    # Ensure required fields are present (mocking if extraction failed for some reason)
    if not onboarding_data.get("email"):
        onboarding_data["email"] = "simulation_test@example.com"
    if not onboarding_data.get("name"):
        onboarding_data["name"] = "Simulation User"
        
    response = requests.post(confirm_url, json=onboarding_data)
    
    if response.status_code != 200:
        print(f"Failed to confirm details: {response.status_code} - {response.text}")
        return
        
    print("Confirmation Response:", response.json())
    user_email = onboarding_data["email"]
    
    # 3. Update User Profile
    print_step("3. Updating User Profile")
    update_url = f"{BASE_URL}/api/updateUserProfile"
    update_payload = {
        "email": user_email,
        "about": "This is an updated about section from the simulation test."
    }
    
    response = requests.post(update_url, json=update_payload)
    if response.status_code == 200:
        print("Profile Updated Successfully:", response.json())
    else:
        print(f"Failed to update profile: {response.status_code} - {response.text}")

    # 4. Get Chat History
    print_step("4. Fetching Chat History")
    chat_history_url = f"{BASE_URL}/api/chatHistoryRequest"
    response = requests.get(chat_history_url, params={"email": user_email})
    
    if response.status_code == 200:
        print("Chat History:", response.json())
    else:
        print(f"Failed to get chat history: {response.status_code} - {response.text}")

    # 5. Save a Job
    print_step("5. Saving a Job")
    save_job_url = f"{BASE_URL}/api/saveJob"
    job_payload = {
        "email": user_email,
        "job_id": "sim_job_123",
        "job_title": "Simulation Engineer",
        "company_name": "Sim Corp",
        "job_link": "http://simcorp.com/jobs/123"
    }
    
    response = requests.post(save_job_url, json=job_payload)
    if response.status_code == 200:
        print("Job Saved:", response.json())
    else:
        print(f"Failed to save job: {response.status_code} - {response.text}")

    # 6. Get Saved Jobs
    print_step("6. Fetching Saved Jobs")
    get_saved_url = f"{BASE_URL}/api/getSavedJobs"
    response = requests.get(get_saved_url, params={"email": user_email})
    
    if response.status_code == 200:
        print("Saved Jobs:", response.json())
    else:
        print(f"Failed to get saved jobs: {response.status_code} - {response.text}")

    # 7. Apply to a Job
    print_step("7. Applying to a Job")
    apply_job_url = f"{BASE_URL}/api/applyJob"
    apply_payload = {
        "email": user_email,
        "job_id": "sim_job_456",
        "job_title": "Senior Simulation Architect",
        "company_name": "Sim Corp",
        "job_link": "http://simcorp.com/jobs/456"
    }
    
    response = requests.post(apply_job_url, json=apply_payload)
    if response.status_code == 200:
        print("Job Applied:", response.json())
    else:
        print(f"Failed to apply to job: {response.status_code} - {response.text}")

    # 8. Get Applied Jobs
    print_step("8. Fetching Applied Jobs")
    get_applied_url = f"{BASE_URL}/api/getAppliedJobs"
    response = requests.get(get_applied_url, params={"email": user_email})
    
    if response.status_code == 200:
        print("Applied Jobs:", response.json())
    else:
        print(f"Failed to get applied jobs: {response.status_code} - {response.text}")

if __name__ == "__main__":
    print("Starting Simulation Test...")
    print(f"Target Server: {BASE_URL}")
    print(f"Resume File: {RESUME_PATH}")
    try:
        test_simulation()
    except requests.exceptions.ConnectionError:
        print("\nError: Could not connect to the server.")
        print("Make sure the backend server is running on http://localhost:8000")
        print("Run: uvicorn main:app --reload")
