import argparse
import csv
import google.auth
import time
from googleapiclient.discovery import build
from src import config
import google.oauth2.id_token
import google.auth.transport.requests
import re
import os

# ANSI escape codes for colors
class Colors:
    RESET = '\033[0m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'

def print_success(message):
    print(f"{Colors.GREEN}{message}{Colors.RESET}")

def print_error(message):
    print(f"{Colors.RED}{message}{Colors.RESET}")

def print_warning(message):
    print(f"{Colors.YELLOW}{message}{Colors.RESET}")

def print_info(message):
    print(f"{Colors.CYAN}{message}{Colors.RESET}")

def print_debug(message):
    print(f"{Colors.MAGENTA}{message}{Colors.RESET}")

def sanitize_project_id_part(part, max_len):
    """Sanitizes a string part for use in a GCP project ID.
    Converts to lowercase, replaces non-alphanumeric (except hyphen) with hyphen,
    removes leading/trailing hyphens, ensures it starts with a letter, and truncates to max_len.
    GCP Project ID rules:
    - Must be 6 to 30 characters long.
    - Must contain only lowercase letters, numbers, or hyphens.
    - Must start with a lowercase letter.
    - Cannot end with a hyphen.
    - Cannot contain colons (handled by replacing with hyphen).
    """
    # Convert to lowercase
    sanitized = part.lower()
    # Replace non-alphanumeric (except hyphen) with hyphen
    sanitized = re.sub(r'[^a-z0-9-]', '-', sanitized)
    # Replace multiple hyphens with a single hyphen
    sanitized = re.sub(r'-+', '-', sanitized)
    # Remove leading/trailing hyphens
    sanitized = sanitized.strip('-')

    # Ensure it starts with a letter (GCP project IDs must start with a lowercase letter)
    if not sanitized or not sanitized[0].isalpha():
        sanitized = 'p' + sanitized  # Prepend 'p' if it doesn't start with a letter

    # Truncate to max_len
    sanitized = sanitized[:max_len]

    # Remove trailing hyphens that might have been introduced by truncation
    sanitized = sanitized.rstrip('-')

    # Ensure it ends with a letter or number
    while sanitized and not sanitized[-1].isalnum():
        sanitized = sanitized[:-1]
    if not sanitized:
        sanitized = 'p' # Fallback if sanitization results in an empty string

    return sanitized

def sanitize_display_name(name):
    """Sanitizes a string for use in a GCP project display name.
    - Can contain letters, numbers, spaces, hyphens, apostrophes, and exclamation points.
    - Must be between 4 and 30 characters.
    """
    # Replace disallowed characters with spaces
    sanitized = re.sub(r'[^a-zA-Z0-9\s\-\'!]', ' ', name)
    # Replace multiple spaces with a single space
    sanitized = re.sub(r'\s+', ' ', sanitized).strip()

    # Truncate if too long, ensuring it's not too short after truncation
    if len(sanitized) > 30:
        sanitized = sanitized[:30].strip()
    if len(sanitized) < 4:
        sanitized = (sanitized + "_display_name_placeholder")[:4] # Ensure minimum length

    return sanitized

def get_credentials():
    """Gets user credentials from the environment and returns them."""
    credentials, project_id = google.auth.default(scopes=['https://www.googleapis.com/auth/userinfo.email', 'https://www.googleapis.com/auth/cloud-platform'])
    user_email = "Unknown User"

    try:
        oauth2_service = build('oauth2', 'v2', credentials=credentials)
        user_info = oauth2_service.userinfo().get().execute()
        if user_info and 'email' in user_info:
            user_email = user_info['email']
    except Exception as e:
        print_warning(f"Warning: Could not retrieve user email from OAuth2 service: {e}")
        if hasattr(credentials, 'service_account_email') and credentials.service_account_email:
            user_email = credentials.service_account_email
        elif hasattr(credentials, 'quota_project_id') and credentials.quota_project_id:
            user_email = f"User Account (Project: {credentials.quota_project_id})"

    return credentials, user_email

    return credentials, user_email

def wait_for_operation(crm_v3, operation_name):
    """Waits for a long-running operation to complete."""
    print_info(f"Waiting for operation {operation_name} to complete...")
    while True:
        operation = crm_v3.operations().get(name=operation_name).execute()
        if operation.get('done'):
            print_success(f"Operation {operation_name} completed.")
            if 'error' in operation:
                print_error(f"Operation failed with error: {operation['error']}")
                raise Exception(f"Operation {operation_name} failed.")
            return operation
        time.sleep(5) # Poll every 5 seconds

def init_project_folders(parent_id, crm_v3, debug_mode=False):
    """Initializes and verifies the project folder structure."""
    print_info(f"Initializing project folders under parent ID: {parent_id}...")

    full_parent_path = None
    # Try as an organization
    try:
        # Attempt to get the organization to verify it exists and we have access
        crm_v3.organizations().get(name=f"organizations/{parent_id}").execute()
        full_parent_path = f"organizations/{parent_id}"
        print_success(f"Parent ID {parent_id} identified as an Organization.")
    except Exception as e_org:
        # If not an organization, try as a folder
        try:
            crm_v3.folders().get(name=f"folders/{parent_id}").execute()
            full_parent_path = f"folders/{parent_id}"
            print_success(f"Parent ID {parent_id} identified as a Folder.")
        except Exception as e_folder:
            raise Exception(f"Parent ID {parent_id} is neither a valid Organization nor Folder ID. "
                            f"Organization check error: {e_org}. Folder check error: {e_folder}")

    if not full_parent_path:
        raise Exception(f"Could not determine type of parent ID: {parent_id}")

    # Now use full_parent_path for all subsequent operations
    # Main Hackathon Playground Users Folder
    main_folder_name = config.MAIN_FOLDER_NAME
    main_folder_id = None
    # Check if main folder exists
    folders = crm_v3.folders().list(parent=full_parent_path).execute().get('folders', [])
    for folder in folders:
        if folder.get('displayName') == main_folder_name:
            main_folder_id = folder.get('name').split('/')[1]
            print_info(f"Found existing main folder: {main_folder_name} (ID: {main_folder_id})")
            break

    if not main_folder_id:
        print_info(f"Creating main folder: {main_folder_name}...")
        body = {'displayName': main_folder_name, 'parent': full_parent_path}
        if debug_mode:
            print_debug(f"DEBUG: API Payload for creating main folder: {body}")
        operation = crm_v3.folders().create(body=body).execute()
        operation_name = operation.get('name')
        wait_for_operation(crm_v3, operation_name)
        main_folder_id = crm_v3.operations().get(name=operation_name).execute().get('response').get('name').split('/')[1]
        print_success(f"Created main folder: {main_folder_name} (ID: {main_folder_id})")

    # Sub-folder for General Attendees
    general_folder_name = config.GENERAL_FOLDER_NAME
    general_folder_id = None
    folders = crm_v3.folders().list(parent=f"folders/{main_folder_id}").execute().get('folders', [])
    for folder in folders:
        if folder.get('displayName') == general_folder_name:
            general_folder_id = folder.get('name').split('/')[1]
            print_info(f"Found existing general attendees folder: {general_folder_name} (ID: {general_folder_id})")
            break

    if not general_folder_id:
        print_info(f"Creating general attendees folder: {general_folder_name}...")
        body = {'displayName': general_folder_name, 'parent': f"folders/{main_folder_id}"}
        if debug_mode:
            print_debug(f"DEBUG: API Payload for creating general attendees folder: {body}")
        operation = crm_v3.folders().create(body=body).execute()
        operation_name = operation.get('name')
        wait_for_operation(crm_v3, operation_name)
        general_folder_id = crm_v3.operations().get(name=operation_name).execute().get('response').get('name').split('/')[1]
        print_success(f"Created general attendees folder: {general_folder_name} (ID: {general_folder_id})")

    # Sub-folder for Hackathon Teams-1
    team1_folder_name = config.TEAM1_FOLDER_NAME
    team1_folder_id = None
    folders = crm_v3.folders().list(parent=f"folders/{main_folder_id}").execute().get('folders', [])
    for folder in folders:
        if folder.get('displayName') == team1_folder_name:
            team1_folder_id = folder.get('name').split('/')[1]
            print_info(f"Found existing hackathon teams-1 folder: {team1_folder_name} (ID: {team1_folder_id})")
            break

    if not team1_folder_id:
        print_info(f"Creating hackathon teams-1 folder: {team1_folder_name}...")
        body = {'displayName': team1_folder_name, 'parent': f"folders/{main_folder_id}"}
        if debug_mode:
            print_debug(f"DEBUG: API Payload for creating hackathon teams-1 folder: {body}")
        operation = crm_v3.folders().create(body=body).execute()
        operation_name = operation.get('name')
        wait_for_operation(crm_v3, operation_name)
        team1_folder_id = crm_v3.operations().get(name=operation_name).execute().get('response').get('name').split('/')[1]
        print_success(f"Created hackathon teams folder: {team1_folder_name} (ID: {team1_folder_id})")

    # Sub-folder for Hackathon Teams-2
    team2_folder_name = config.TEAM2_FOLDER_NAME
    team2_folder_id = None
    folders = crm_v3.folders().list(parent=f"folders/{main_folder_id}").execute().get('folders', [])
    for folder in folders:
        if folder.get('displayName') == team2_folder_name:
            team2_folder_id = folder.get('name').split('/')[1]
            print_info(f"Found existing hackathon teams-2 folder: {team2_folder_name} (ID: {team2_folder_id})")
            break

    if not team2_folder_id:
        print_info(f"Creating hackathon teams-2 folder: {team2_folder_name}...")
        body = {'displayName': team2_folder_name, 'parent': f"folders/{main_folder_id}"}
        if debug_mode:
            print_debug(f"DEBUG: API Payload for creating hackathon teams-2 folder: {body}")
        operation = crm_v3.folders().create(body=body).execute()
        operation_name = operation.get('name')
        wait_for_operation(crm_v3, operation_name)
        team2_folder_id = crm_v3.operations().get(name=operation_name).execute().get('response').get('name').split('/')[1]
        print_success(f"Created hackathon teams folder: {team2_folder_name} (ID: {team2_folder_id})")

    print(main_folder_id, general_folder_id, team1_folder_id, team2_folder_id)
    print_success("Folder initialization complete.")
    return main_folder_id, general_folder_id, team1_folder_id, team2_folder_id

def main():
    pass

def provision_playground_projects(attendees_file, crm_v3, serviceusage_v1, cloudbilling_v1, general_folder_id, debug_mode=False):
    with open(attendees_file, 'r') as f:
        reader = csv.reader(f)
        next(reader)  # Skip header
        for row in reader:
            email = row[0]
            email_prefix = email.split('@')[0]
            sanitized_email_prefix = sanitize_project_id_part(email_prefix, 10)
            # a random string with 5 chars long
            random_string = os.urandom(3).hex() # Generates 6 random hex characters
            project_id_suffix = "" # f"-{random_string}"
            project_id = f"{sanitized_email_prefix}{config.PLAYGROUND_PROJECT_SUFFIX}{project_id_suffix}"
            project_name = sanitize_display_name(f"playground project for {email_prefix}")
            print_info(f'Creating playground project for {email} with name {project_id}...')
            create_project(project_id, project_name, email, crm_v3, serviceusage_v1, cloudbilling_v1, general_folder_id)

def create_project(project_id, project_name, user_email, crm_v3, serviceusage_v1, cloudbilling_v1, parent_folder_id, debug_mode=False):
    parent_folder = f"folders/{parent_folder_id}"
    body = {
        'project_id': project_id,
        'display_name': project_name,
        'parent': parent_folder
    }
    if debug_mode:
        print_debug(f"DEBUG: API Payload for creating project {project_id}: {body}")
    operation = crm_v3.projects().create(body=body).execute()
    print_info(f"Project creation initiated for {project_id}. Operation: {operation['name']}")
    wait_for_operation(crm_v3, operation['name'])
    link_billing_account(project_id, cloudbilling_v1, debug_mode)
    set_iam_policy(project_id, user_email, crm_v3, debug_mode)
    enable_apis(project_id, serviceusage_v1, debug_mode)

def set_iam_policy(project_id, user_email, crm_v3, debug_mode=False):
    admins = config.ADMIN_EMAILS
    resource_name = f"projects/{project_id}"
    policy = crm_v3.projects().getIamPolicy(resource=resource_name, body={}).execute()

    # Add admins as owners
    for admin in admins:
        policy['bindings'].append({
            'role': 'roles/owner',
            'members': [f'user:{admin}']
        })

    # Add user as editor
    policy['bindings'].append({
        'role': 'roles/editor',
        'members': [f'user:{user_email}']
    })

    if debug_mode:
        print_debug(f"DEBUG: API Payload for setting IAM policy for {project_id}: {{'policy': policy}}")
    crm_v3.projects().setIamPolicy(resource=resource_name, body={'policy': policy}).execute()
    print_success(f'IAM policy updated for project {project_id}')

def link_billing_account(project_id, cloudbilling_v1, debug_mode=False):
    billing_account = config.BILLING_ACCOUNT_ID
    project_name = f"projects/{project_id}"
    body = {'billingAccountName': billing_account}
    
    if debug_mode:
        print_debug(f"DEBUG: API Payload for linking billing account for {project_id}: {body}")
    
    cloudbilling_v1.projects().updateBillingInfo(name=project_name, body=body).execute()
    print_success(f'Billing account {billing_account} linked to project {project_id}')


def enable_apis(project_id, serviceusage_v1, debug_mode=False):
    apis_to_enable = config.APIS_TO_ENABLE
    for api in apis_to_enable:
        print_info(f'Enabling {api} for project {project_id}...')
        if debug_mode:
            print_debug(f"DEBUG: API Payload for enabling API {api} for project {project_id}: {{'name': f'projects/{project_id}/services/{api}'}}")
        serviceusage_v1.services().enable(name=f'projects/{project_id}/services/{api}').execute()



def provision_team_projects(teams_file, crm_v3, serviceusage_v1, cloudbilling_v1, team_folder_id, debug_mode=False):
    with open(teams_file, 'r') as f:
        reader = csv.reader(f)
        next(reader)  # Skip header
        for row in reader:
            team_name, team_members_str = row
            team_members = team_members_str.split('|')
            # a random string with 5 chars long
            random_string = os.urandom(3).hex() # Generates 6 random hex characters
            project_id_suffix = "" # f"-{random_string}"
            sanitized_team_name = sanitize_project_id_part(team_name, 6)
            project_id = f'{sanitized_team_name}{config.TEAM_PROJECT_SUFFIX}{project_id_suffix}'
            project_name = sanitize_display_name(f"team project for {team_name}")
            print_info(f'Creating team project for {team_name} with name {project_id}...')
            create_team_project(project_id, project_name, team_members, crm_v3, serviceusage_v1, cloudbilling_v1, team_folder_id)

def create_team_project(project_id, project_name, team_members, crm_v3, serviceusage_v1, cloudbilling_v1, parent_folder_id, debug_mode=False):
    parent_folder = f"folders/{parent_folder_id}"
    body = {
        'project_id': project_id,
        'display_name': project_name,
        'parent': parent_folder
    }
    if debug_mode:
        print_debug(f"DEBUG: API Payload for creating team project {project_id}: {body}")
    operation = crm_v3.projects().create(body=body).execute()
    print_info(f"Project creation initiated for {project_id}. Operation: {operation['name']}")
    wait_for_operation(crm_v3, operation['name'])
    link_billing_account(project_id, cloudbilling_v1, debug_mode)
    set_team_iam_policy(project_id, team_members, crm_v3, debug_mode)
    enable_apis(project_id, serviceusage_v1, debug_mode)

def set_team_iam_policy(project_id, team_members, crm_v3, debug_mode=False):
    admins = config.ADMIN_EMAILS
    resource_name = f"projects/{project_id}"
    policy = crm_v3.projects().getIamPolicy(resource=resource_name, body={}).execute()

    # Add admins as owners
    for admin in admins:
        policy['bindings'].append({
            'role': 'roles/owner',
            'members': [f'user:{admin}']
        })

    # Add team members as editors
    policy['bindings'].append({
        'role': 'roles/editor',
        'members': [f'user:{member}' for member in team_members]
    })

    if debug_mode:
        print_debug(f"DEBUG: API Payload for setting team IAM policy for {project_id}: {{'policy': policy}}")
    crm_v3.projects().setIamPolicy(resource=resource_name, body={'policy': policy}).execute()
    print_success(f'IAM policy updated for project {project_id}')



def check_folder(folder_id, crm_v3):
    """Checks if a folder exists and is accessible."""
    try:
        crm_v3.folders().get(name=f"folders/{folder_id}").execute()
        return True
    except Exception as e:
        print_error(f"Error accessing folder {folder_id}: {e}")
        return False

def list_folders(folder_id, crm_v3):
    """Lists all available folders under MAIN_HACKATHON_FOLDER_ID."""
    try:
        # This is a simplified list command. In a real-world scenario with many folders,
        # you would need to handle pagination.
        folders = crm_v3.folders().list(parent=f"folders/{folder_id}").execute().get('folders', [])
        return folders
    except Exception as e:
        print_error(f"Error listing folders: {e}")
        return []

def list_projects_in_folder(folder_id, crm_v3):
    """Lists all projects within a specific folder."""
    try:
        projects = crm_v3.projects().list(parent=f"folders/{folder_id}").execute().get('projects', [])
        return projects
    except Exception as e:
        print_error(f"Error listing projects in folder {folder_id}: {e}")
        return []

def apply_organization_policies(folder_id, crm_v3, debug_mode=False):
    """Applies the organization policies defined in config.py to a specific folder."""
    print_info(f"Applying organization policies to folder: {folder_id}...")
    parent_folder = f"folders/{folder_id}"

    for constraint, policy_config in config.ORGANIZATION_POLICY.items():
        policy_name = f"{parent_folder}/policies/{constraint.replace('/', '%2F')}"
        print_info(f"Applying policy for constraint: {policy_name}")

        policy = {
            'name': policy_name,
            'spec': policy_config
        }

        if debug_mode:
            print_debug(f"DEBUG: API Payload for setting org policy for {constraint}: {policy}")

        try:
            request = crm_v3.folders().orgPolicies().patch(name=policy_name, body=policy)
            request.execute()
            print_success(f"Successfully applied policy for constraint: {constraint}")
        except Exception as e:
            print_error(f"Error applying policy for constraint {constraint}: {e}")

def revert_organization_policies(folder_id, crm_v3, debug_mode=False):
    """Reverts the organization policies on a specific folder to their default state."""
    print_info(f"Reverting organization policies on folder: {folder_id}...")
    parent_folder = f"folders/{folder_id}"

    for constraint in config.ORGANIZATION_POLICY.keys():
        policy_name = f"{parent_folder}/policies/{constraint.replace('/', '%2F')}"
        print_info(f"Reverting policy for constraint: {policy_name}")

        # To revert, we set a policy that allows all and is not enforced.
        policy = {
            'name': policy_name,
            'spec': {
                'rules': [{'allowAll': True}],
                'inheritFromParent': True, # Reset to inherit from parent
            }
        }

        if debug_mode:
            print_debug(f"DEBUG: API Payload for reverting org policy for {constraint}: {policy}")

        try:
            request = crm_v3.folders().orgPolicies().patch(name=policy_name, body=policy)
            request.execute()
            print_success(f"Successfully reverted policy for constraint: {constraint}")
        except Exception as e:
            print_error(f"Error reverting policy for constraint {constraint}: {e}")


if __name__ == '__main__':
    pass
