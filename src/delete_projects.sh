#!/bin/bash

# A script to find and delete all projects within a given GCP folder.

# --- Configuration ---
# Set to true to skip the final confirmation prompt. Use with caution.
# Example: ./delete_projects.sh 1234567890 --force
FORCE_DELETE=false

# --- Functions ---
print_usage() {
  echo "Usage: $0 <PARENT_FOLDER_ID> [--force]"
  echo "  <PARENT_FOLDER_ID> : The numeric ID of the folder containing the projects to delete."
  echo "  --force              : (Optional) Skip the confirmation prompt and delete immediately."
  exit 1
}

# --- Script Start ---

# Check for help flag
if [[ "$1" == "--help" || "$1" == "-h" ]]; then
  print_usage
fi

# Check if parent folder ID is provided
if [ -z "$1" ]; then
  echo "Error: Parent folder ID is required."
  print_usage
fi

PARENT_FOLDER_ID=$1

# Check for force flag
if [ "$2" == "--force" ]; then
  FORCE_DELETE=true
fi

echo "Fetching projects for parent folder ID: $PARENT_FOLDER_ID..."

# Get a list of project IDs within the specified folder.
PROJECT_IDS=$(gcloud projects list \
  --filter="parent.id=$PARENT_FOLDER_ID AND parent.type=folder" \
  --format="value(projectId)")

# Check if any projects were found
if [ -z "$PROJECT_IDS" ]; then
  echo "No active projects found under folder ID $PARENT_FOLDER_ID."
  exit 0
fi

echo "------------------------------------------------------------------"
echo "The following projects are scheduled for deletion:"
echo "$PROJECT_IDS" | tr ' ' '\n'
echo "------------------------------------------------------------------"

# Confirmation prompt
if [ "$FORCE_DELETE" = false ]; then
  read -p "Are you absolutely sure you want to delete all of these projects? This action cannot be undone. (yes/no) " -r
  echo
  if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
      echo "Deletion cancelled by user."
      exit 1
  fi
else
    echo "--force flag detected. Proceeding with deletion without confirmation."
fi

echo "Starting deletion process..."
for PROJECT_ID in $PROJECT_IDS; do
  echo -n "Requesting deletion for project '$PROJECT_ID'... "
  if gcloud projects delete "$PROJECT_ID" --quiet; then
    echo "SUCCESS"
  else
    echo "FAILED. You may lack permissions or the project may have a lien."
  fi
done

echo "------------------------------------------------------------------"
echo "Deletion process complete."
echo "Note: Projects are marked for deletion and will be fully purged after 30 days."
echo "------------------------------------------------------------------"