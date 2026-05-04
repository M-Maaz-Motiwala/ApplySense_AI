import httpx
import time
import json
import sys

BASE_URL = "http://localhost:8000/api/v1"

def test_workflow(email, password):
    print(f"\n--- Testing Workflow for {email} ---")
    
    # 1. Login
    print("[1] Logging in...")
    try:
        response = httpx.post(f"{BASE_URL}/auth/login", json={"email": email, "password": password}, timeout=10.0)
        response.raise_for_status()
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("Success: Token acquired.")
    except Exception as e:
        print(f"Error logging in: {e}")
        return

    # 2. Trigger Job Ingestion
    print("[2] Triggering job ingestion...")
    try:
        response = httpx.post(f"{BASE_URL}/jobs/refresh", headers=headers, timeout=10.0)
        response.raise_for_status()
        task_id = response.json()["task_id"]
        print(f"Success: Task {task_id} triggered.")
    except Exception as e:
        print(f"Error triggering ingestion: {e}")
        return

    # 3. Poll for completion
    print("[3] Waiting for task completion (polling)...")
    status = "PENDING"
    max_retries = 100 # Increased to allow for thorough search + scraping
    retry_count = 0
    while status not in ["COMPLETED", "FAILED"] and retry_count < max_retries:
        time.sleep(5)
        try:
            response = httpx.get(f"{BASE_URL}/tasks/{task_id}", headers=headers, timeout=10.0)
            data = response.json()
            status = data["status"]
            print(f"Task status: {status}")
            if status == "COMPLETED":
                print(f"Ingestion result: {json.dumps(data['result'], indent=2)}")
                break
        except Exception as e:
            print(f"Error polling task: {e}")
        retry_count += 1

    if status != "COMPLETED":
        print("Error: Task did not complete successfully.")
        return

    # 4. Fetch Jobs and Matches
    print("[4] Checking ingested jobs and match insights...")
    try:
        response = httpx.get(f"{BASE_URL}/jobs", headers=headers, timeout=10.0)
        jobs = response.json()
        print(f"Found {len(jobs)} jobs in database.")
        
        if jobs:
            sample_job = jobs[0]
            print(f"Sample Job: {sample_job['title']} at {sample_job['company']}")
            
            # Check match
            match_response = httpx.get(f"{BASE_URL}/jobs/{sample_job['id']}/match", headers=headers, timeout=15.0)
            match_data = match_response.json()
            print(f"Match Score for {email}: {match_data['score']}%")
            print(f"Reasoning: {match_data['explanation'][:100]}...")
            
    except Exception as e:
        print(f"Error fetching jobs/matches: {e}")

if __name__ == "__main__":
    # Test for Jane Smith
    test_workflow("jane@example.com", "password123")
    
    # # Test for John Doe (Commented out for faster testing)
    test_workflow("john@example.com", "password123")
