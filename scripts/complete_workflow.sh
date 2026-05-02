#!/usr/bin/env bash

set -euo pipefail

echo "=========================================="
echo " ApplySense AI - Complete Workflow Script "
echo "=========================================="
echo ""

# 1. Update the user profile with the provided CV details
echo "[1/4] Seeding database with John Doe's resume profile..."
docker compose exec -T backend python scripts/seed_john_doe.py
echo ""

# 2. Run the main workflow script (assuming JOB_ID is already exported or we let the script pick the first one)
echo "[2/4] Executing the resume & cover letter generation workflow..."
# We pass AUTO_APPROVE=1 so the workflow doesn't pause for manual approval.
export AUTO_APPROVE=1
./scripts/applysense_workflow.sh
echo ""

# 3. Fetching the generated artifacts path
# Wait for the Celery worker to finish processing the PDF and cover letter.
echo "[3/4] Locating generated artifacts..."
# Since the workflow script outputs the Application ID, the files should be available in the backend/generated/resumes directory.
echo "The generated Cover Letter and Resume PDF will be available in the following directory:"
echo "./backend/generated/resumes/"
echo ""
echo "[4/4] Workflow Complete."
