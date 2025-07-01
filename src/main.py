import argparse
import csv
import google.auth
import time
from googleapiclient.discovery import build
from src import config

def get_credentials():
    """Gets user credentials from the environment."""
    credentials, project_id = google.auth.default()
    return credentials

def wait_for_operation(crm_v3, operation_name):
    """Waits for a long-running operation to complete."""
    print(f"Waiting for operation {operation_name} to complete...")
    while True:
        operation = crm_v3.operations().get(name=operation_name).execute()
        if operation.get('done'):
            print(f"Operation {operation_name} completed.")
            if 'error' in operation:
                print(f"Operation failed with error: {operation['error']}")
                raise Exception(f"Operation {operation_name} failed.")
            return operation
        time.sleep(5) # Poll every 5 seconds

def init_project_folders(parent_id, crm_v3):
    """Initializes and verifies the project folder structure."""
    print(f"Initializing project folders under parent ID: {parent_id}...")

    # Main Hackathon Playground Users Folder
    main_folder_name = config.MAIN_FOLDER_NAME
    main_folder_id = None
    # Check if main folder exists
    folders = crm_v3.folders().list(parent=f"organizations/{parent_id}" if "organizations" in parent_id else f"folders/{parent_id}").execute().get('folders', [])
    for folder in folders:
        if folder.get('displayName') == main_folder_name:
            main_folder_id = folder.get('name').split('/')[1]
            print(f"Found existing main folder: {main_folder_name} (ID: {main_folder_id})")
            break

    if not main_folder_id:
        print(f"Creating main folder: {main_folder_name}...")
        operation = crm_v3.folders().create(body={'displayName': main_folder_name, 'parent': f"organizations/{parent_id}" if "organizations" in parent_id else f"folders/{parent_id}"}).execute()
        operation_name = operation.get('name')
        wait_for_operation(crm_v3, operation_name)
        main_folder_id = crm_v3.operations().get(name=operation_name).execute().get('response').get('name').split('/')[1]
        print(f"Created main folder: {main_folder_name} (ID: {main_folder_id})")

    # Sub-folder for General Attendees
    general_folder_name = config.GENERAL_FOLDER_NAME
    general_folder_id = None
    folders = crm_v3.folders().list(parent=f"folders/{main_folder_id}").execute().get('folders', [])
    for folder in folders:
        if folder.get('displayName') == general_folder_name:
            general_folder_id = folder.get('name').split('/')[1]
            print(f"Found existing general attendees folder: {general_folder_name} (ID: {general_folder_id})")
            break

    if not general_folder_id:
        print(f"Creating general attendees folder: {general_folder_name}...")
        operation = crm_v3.folders().create(body={'displayName': general_folder_name, 'parent': f"folders/{main_folder_id}"}).execute()
        operation_name = operation.get('name')
        wait_for_operation(crm_v3, operation_name)
        general_folder_id = crm_v3.operations().get(name=operation_name).execute().get('response').get('name').split('/')[1]
        print(f"Created general attendees folder: {general_folder_name} (ID: {general_folder_id})")

    # Sub-folder for Hackathon Teams
    team_folder_name = config.TEAM_FOLDER_NAME
    team_folder_id = None
    folders = crm_v3.folders().list(parent=f"folders/{main_folder_id}").execute().get('folders', [])
    for folder in folders:
        if folder.get('displayName') == team_folder_name:
            team_folder_id = folder.get('name').split('/')[1]
            print(f"Found existing hackathon teams folder: {team_folder_name} (ID: {team_folder_id})")
            break

    if not team_folder_id:
        print(f"Creating hackathon teams folder: {team_folder_name}...")
        operation = crm_v3.folders().create(body={'displayName': team_folder_name, 'parent': f"folders/{main_folder_id}"}).execute()
        operation_name = operation.get('name')
        wait_for_operation(crm_v3, operation_name)
        team_folder_id = crm_v3.operations().get(name=operation_name).execute().get('response').get('name').split('/')[1]
        print(f"Created hackathon teams folder: {team_folder_name} (ID: {team_folder_id})")

    print("Folder initialization complete.")
    return main_folder_id, general_folder_id, team_folder_id

def main():
    pass

def provision_playground_projects(attendees_file, crm_v3, serviceusage_v1, billing_v1, general_folder_id):
    with open(attendees_file, 'r') as f:
        reader = csv.reader(f)
        next(reader)  # Skip header
        for row in reader:
            email = row[0]
            project_name = f"{email.split('@')[0]}{config.PLAYGROUND_PROJECT_SUFFIX}"
            print(f'Creating playground project for {email} with name {project_name}...')
            create_project(project_name, email, crm_v3, serviceusage_v1, billing_v1, general_folder_id, config.PLAYGROUND_PROJECT_BUDGET_USD)

def create_project(project_name, user_email, crm_v3, serviceusage_v1, billing_v1, parent_folder_id, budget_amount):
    parent_folder = f"folders/{parent_folder_id}"
    operation = crm_v3.projects().create(body={
        'project_id': project_name,
        'parent': parent_folder
    }).execute()
    print(f"Project creation initiated for {project_name}. Operation: {operation['name']}")
    wait_for_operation(crm_v3, operation['name'])
    set_iam_policy(project_name, user_email, crm_v3)
    enable_apis(project_name, serviceusage_v1)
    set_budget(project_name, billing_v1, budget_amount)

def set_iam_policy(project_id, user_email, crm_v3):
    admins = config.ADMIN_EMAILS
    policy = crm_v3.projects().getIamPolicy(resource=project_id, body={}).execute()

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

    crm_v3.projects().setIamPolicy(resource=project_id, body={'policy': policy}).execute()
    print(f'IAM policy updated for project {project_id}')

def enable_apis(project_id, serviceusage_v1):
    apis_to_enable = config.APIS_TO_ENABLE
    for api in apis_to_enable:
        print(f'Enabling {api} for project {project_id}...')
        serviceusage_v1.services().enable(name=f'projects/{project_id}/services/{api}').execute()

def set_budget(project_id, billing_v1, budget_amount):
    billing_account = config.BILLING_ACCOUNT_ID
    budget = {
        'displayName': f'{project_id}-budget',
        'budgetFilter': {
            'projects': [f'projects/{project_id}']
        },
        'amount': {
            'specifiedAmount': {
                'currencyCode': 'USD',
                'units': str(budget_amount)
            }
        },
        'thresholdRules': [
            {'thresholdPercent': 0.5, 'spendBasis': 'CURRENT_SPEND'},
            {'thresholdPercent': 0.9, 'spendBasis': 'CURRENT_SPEND'},
            {'thresholdPercent': 1.0, 'spendBasis': 'CURRENT_SPEND'}
        ]
    }
    billing_v1.billingAccounts().budgets().create(parent=billing_account, body=budget).execute()
    print(f'Budget set for project {project_id}')

def provision_team_projects(teams_file, crm_v3, serviceusage_v1, billing_v1, team_folder_id):
    with open(teams_file, 'r') as f:
        reader = csv.reader(f)
        next(reader)  # Skip header
        for row in reader:
            team_name, team_members_str = row
            team_members = team_members_str.split(',')
            project_name = f'{team_name}{config.TEAM_PROJECT_SUFFIX}'
            print(f'Creating team project for {team_name} with name {project_name}...')
            create_team_project(project_name, team_members, crm_v3, serviceusage_v1, billing_v1, team_folder_id, config.TEAM_PROJECT_BUDGET_USD)

def create_team_project(project_name, team_members, crm_v3, serviceusage_v1, billing_v1, parent_folder_id, budget_amount):
    parent_folder = f"folders/{parent_folder_id}"
    operation = crm_v3.projects().create(body={
        'project_id': project_name,
        'parent': parent_folder
    }).execute()
    print(f"Project creation initiated for {project_name}. Operation: {operation['name']}")
    wait_for_operation(crm_v3, operation['name'])
    set_team_iam_policy(project_name, team_members, crm_v3)
    enable_apis(project_name, serviceusage_v1)
    set_team_budget(project_name, billing_v1, budget_amount)

def set_team_iam_policy(project_id, team_members, crm_v3):
    admins = config.ADMIN_EMAILS
    policy = crm_v3.projects().getIamPolicy(resource=project_id, body={}).execute()

    # Add admins as owners
    for admin in admins:
        policy['bindings'].append({
            'role': 'roles/owner',
            'members': [f'user:{admin}']
        })

    # Add team members as editors
    policy['bindings'].append({
        'role': 'roles/editor',
        'members': [f'group:{member}' for member in team_members]
    })

    crm_v3.projects().setIamPolicy(resource=project_id, body={'policy': policy}).execute()
    print(f'IAM policy updated for project {project_id}')

def set_team_budget(project_id, billing_v1, budget_amount):
    billing_account = config.BILLING_ACCOUNT_ID
    budget = {
        'displayName': f'{project_id}-budget',
        'budgetFilter': {
            'projects': [f'projects/{project_id}']
        },
        'amount': {
            'specifiedAmount': {
                'currencyCode': 'USD',
                'units': str(budget_amount)
            }
        },
        'thresholdRules': [
            {'thresholdPercent': 0.5, 'spendBasis': 'CURRENT_SPEND'},
            {'thresholdPercent': 0.9, 'spendBasis': 'CURRENT_SPEND'},
            {'thresholdPercent': 1.0, 'spendBasis': 'CURRENT_SPEND'}
        ]
    }
    billing_v1.billingAccounts().budgets().create(parent=billing_account, body=budget).execute()
    print(f'Budget set for project {project_id}')

def check_folder(folder_id, crm_v3):
    """Checks if a folder exists and is accessible."""
    try:
        crm_v3.folders().get(name=f"folders/{folder_id}").execute()
        return True
    except Exception as e:
        print(f"Error accessing folder {folder_id}: {e}")
        return False

def list_folders(crm_v3):
    """Lists all available folders."""
    try:
        # This is a simplified list command. In a real-world scenario with many folders,
        # you would need to handle pagination.
        folders = crm_v3.folders().list().execute().get('folders', [])
        return folders
    except Exception as e:
        print(f"Error listing folders: {e}")
        return []

def list_projects_in_folder(folder_id, crm_v3):
    """Lists all projects within a specific folder."""
    try:
        query = f"parent.type:folder parent.id:{folder_id}"
        projects = crm_v3.projects().list(query=query).execute().get('projects', [])
        return projects
    except Exception as e:
        print(f"Error listing projects in folder {folder_id}: {e}")
        return []

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Provision Google Cloud projects for a hackathon.')
    parser.add_argument('--attendees', help='Path to the attendees CSV file.')
    parser.add_argument('--teams', help='Path to the teams CSV file.')
    args = parser.parse_args()

    credentials = get_credentials()
    crm_v3 = build('cloudresourcemanager', 'v3', credentials=credentials)
    billing_v1 = build('billingbudgets', 'v1', credentials=credentials)
    serviceusage_v1 = build('serviceusage', 'v1', credentials=credentials)

    if args.attendees:
        provision_playground_projects(args.attendees, crm_v3, serviceusage_v1, billing_v1)

    if args.teams:
        provision_team_projects(args.teams, crm_v3, serviceusage_v1, billing_v1)
