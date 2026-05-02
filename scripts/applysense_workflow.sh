#!/usr/bin/env bash

set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8000}"
USER_EMAIL="${USER_EMAIL:-john@example.com}"
USER_PASSWORD="${USER_PASSWORD:-SecurePass@123}"
JOB_ID="${JOB_ID:-}"
AUTO_APPROVE="${AUTO_APPROVE:-0}"
MAX_ATTEMPTS="${MAX_ATTEMPTS:-30}"
SLEEP_SECONDS="${SLEEP_SECONDS:-3}"

json_get() {
  python3 -c 'import json,sys; data=json.load(sys.stdin); path=sys.argv[1].split(".");
value=data
for part in path:
    value=value[part]
print(value)' "$1"
}

login_response=$(curl -s -X POST "$BASE_URL/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$USER_EMAIL\",\"password\":\"$USER_PASSWORD\"}")
USER_TOKEN=$(printf '%s' "$login_response" | python3 -c 'import json,sys; print(json.load(sys.stdin)["access_token"])')

echo "Authenticated as $USER_EMAIL"

if [[ -z "$JOB_ID" ]]; then
  jobs_json=$(curl -s -X GET "$BASE_URL/api/v1/jobs" \
    -H "Authorization: Bearer $USER_TOKEN")
  JOB_ID=$(printf '%s' "$jobs_json" | python3 -c '
import json, sys
jobs = json.load(sys.stdin)
if not jobs:
    raise SystemExit("No jobs available. Seed jobs first with the admin webhook endpoint.")
print(jobs[0]["id"])
')
  echo "Selected first available job: $JOB_ID"
fi

export JOB_ID

match_json=$(curl -s -X GET "$BASE_URL/api/v1/jobs/$JOB_ID/match" \
  -H "Authorization: Bearer $USER_TOKEN")
echo "Match result: $match_json"

existing_count=$(curl -s -X GET "$BASE_URL/api/v1/applications" \
  -H "Authorization: Bearer $USER_TOKEN" | python3 -c '
import json, sys, os
job_id = os.environ["JOB_ID"]
applications = json.load(sys.stdin)
print(sum(1 for app in applications if app.get("job_id") == job_id))
')

export EXISTING_COUNT="$existing_count"

generation_response=$(curl -s -X POST "$BASE_URL/api/v1/jobs/$JOB_ID/generate-application" \
  -H "Authorization: Bearer $USER_TOKEN")
CELERY_TASK_ID=$(printf '%s' "$generation_response" | python3 -c 'import json,sys; print(json.load(sys.stdin)["task_id"])')

echo "Triggered generation: $generation_response"
echo "Celery task id: $CELERY_TASK_ID"
echo "Waiting for application creation..."

APPLICATION_ID=""
for attempt in $(seq 1 "$MAX_ATTEMPTS"); do
  applications_json=$(curl -s -X GET "$BASE_URL/api/v1/applications" \
    -H "Authorization: Bearer $USER_TOKEN")
  candidate_id=$(printf '%s' "$applications_json" | python3 -c '
import json, os, sys
job_id = os.environ["JOB_ID"]
existing_count = int(os.environ["EXISTING_COUNT"])
applications = [app for app in json.load(sys.stdin) if app.get("job_id") == job_id]
if len(applications) <= existing_count:
    print("")
else:
    applications.sort(key=lambda item: item.get("last_updated", ""), reverse=True)
    print(applications[0]["id"])
')
  if [[ -n "$candidate_id" ]]; then
    APPLICATION_ID="$candidate_id"
    echo "Application created: $APPLICATION_ID"
    break
  fi

  echo "  attempt $attempt/$MAX_ATTEMPTS: not ready yet"
  sleep "$SLEEP_SECONDS"
done

if [[ -z "$APPLICATION_ID" ]]; then
  echo "Timed out waiting for application creation. Check worker logs for the celery task id: $CELERY_TASK_ID"
  exit 1
fi

echo "Previewing generated application..."
curl -s -X GET "$BASE_URL/api/v1/applications/$APPLICATION_ID/preview-resume" \
  -H "Authorization: Bearer $USER_TOKEN" | python3 -m json.tool

if [[ "$AUTO_APPROVE" == "1" ]]; then
  echo "Approving application..."
  curl -s -X POST "$BASE_URL/api/v1/applications/$APPLICATION_ID/approve" \
    -H "Authorization: Bearer $USER_TOKEN" | python3 -m json.tool
else
  echo "Application is left in PENDING_APPROVAL. Set AUTO_APPROVE=1 to approve automatically."
fi
