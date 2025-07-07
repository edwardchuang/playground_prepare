#!/bin/bash

# A script to find and delete all subfolders within a given GCP folder.

# --- Configuration ---
# Set to true to skip the final confirmation prompt. Use with caution.
# Example: ./delete_subfolders.sh 1234567890 --force
FORCE_DELETE=false

# --- Functions ---
print_usage() {
  echo "Usage: $0 <PARENT_FOLDER_ID> [--force]"
  echo "  <PARENT_FOLDER_ID> : The numeric ID of the folder containing the subfolders to delete."
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

echo "Fetching subfolders for parent folder ID: $PARENT_FOLDER_ID..."

# Get a list of subfolders with their display names and IDs.
# The query ensures we only get ACTIVE folders. Folders being deleted are in state DELETE_REQUESTED.
SUBFOLDERS_INFO=$(gcloud resource-manager folders list \
  --folder="$PARENT_FOLDER_ID" \
  --format="table[no-heading](name, displayName)")

echo $SUBFOLDERS_INFO

# Check if any subfolders were found
if [ -z "$SUBFOLDERS_INFO" ]; then
  echo "No active subfolders found under folder ID $PARENT_FOLDER_ID."
  exit 0
fi

echo "------------------------------------------------------------------"
echo "The following subfolders are scheduled for deletion:"
echo "$SUBFOLDERS_INFO"
echo "------------------------------------------------------------------"

# Confirmation prompt
if [ "$FORCE_DELETE" = false ]; then
  read -p "Are you absolutely sure you want to delete all of these folders? This action cannot be undone. (yes/no) " -r
  echo
  if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
      echo "Deletion cancelled by user."
      exit 1
  fi
else
    echo "--force flag detected. Proceeding with deletion without confirmation."
fi

echo "Starting deletion process..."
while IFS= read -r line; do
  # Each line is "folders/ID  DisplayName"
  FOLDER_NAME=$(echo "$line" | awk '{print $1}') # e.g., folders/12345
  FOLDER_ID=$(basename "$FOLDER_NAME")
  DISPLAY_NAME=$(echo "$line" | awk '{$1=""; print $0}' | xargs) # The rest of the line

  echo -n "Deleting folder '$DISPLAY_NAME' (ID: $FOLDER_ID)... "
  
  # The delete command can fail if the folder is not empty.
  # gcloud will return a non-zero exit code.
  if gcloud resource-manager folders delete "$FOLDER_ID" --quiet; then
    echo "SUCCESS"
  else
    echo "FAILED. The folder might not be empty or you may lack permissions."
  fi
done <<< "$SUBFOLDERS_INFO"

# delete parent folder 
echo "Attempting to delete the parent folder $PARENT_FOLDER_ID..."
if gcloud resource-manager folders delete "$PARENT_FOLDER_ID" --quiet; then
  echo "Parent folder $PARENT_FOLDER_ID deletion requested successfully."
else
  echo "Failed to request deletion of parent folder $PARENT_FOLDER_ID. It might not be empty, or you may lack permissions."
fi

echo "------------------------------------------------------------------"
echo "Deletion process complete."
echo "Note: Folders enter a 'DELETE_REQUESTED' state and will be purged after 30 days."
echo "------------------------------------------------------------------"