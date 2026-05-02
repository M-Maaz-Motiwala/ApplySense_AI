#!/usr/bin/env bash

set -euo pipefail

echo "=========================================="
echo " ApplySense AI - Jane Smith Workflow      "
echo "=========================================="
echo ""

# 1. Update the user profile with the provided CV details
echo "[1/4] Seeding database with Jane Smith's diverse profile..."
docker compose exec -T backend python scripts/seed_jane_smith.py
echo ""

# 2. Run the main workflow script targeting the AI/ML Engineer Job
echo "[2/4] Executing the resume & cover letter generation workflow..."
# We pass AUTO_APPROVE=1 so the workflow doesn't pause for manual approval.
# Using AI/ML Engineer job ID
export USER_EMAIL="jane@example.com"
export USER_PASSWORD="password123"
export JOB_ID="4596ca94-3241-4b47-90a8-17ea53df5523"
export AUTO_APPROVE=1
./scripts/applysense_workflow.sh
echo ""

# 3. Fetching the generated artifacts path
echo "[3/4] Locating generated artifacts..."
echo "The generated Cover Letter and Resume PDF will be available in the following directory:"
echo "./backend/generated/resumes/"
echo ""
echo "[4/4] Workflow Complete."
