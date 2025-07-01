# Configuration for Hackathon Project Provisioning CLI

# List of admin emails who will be Project Owners
ADMIN_EMAILS = [
    'admin1@example.com',
    'admin2@example.com'
]

# Your Google Cloud Billing Account ID (e.g., 'billingAccounts/012345-6789AB-CDEF01')
BILLING_ACCOUNT_ID = 'billingAccounts/YOUR_BILLING_ACCOUNT_ID'

# Default budget amount for playground projects (per month in USD)
PLAYGROUND_PROJECT_BUDGET_USD = 5

# Default budget amount for team projects (per month in USD)
TEAM_PROJECT_BUDGET_USD = 100

# List of Google APIs to enable for new projects
APIS_TO_ENABLE = [
    'aiplatform.googleapis.com',
    'storage.googleapis.com',
    'bigquery.googleapis.com',
    'cloudfunctions.googleapis.com',
    'run.googleapis.com',
    'logging.googleapis.com',
    'monitoring.googleapis.com',
    'iam.googleapis.com',
    'cloudresourcemanager.googleapis.com',
    'serviceusage.googleapis.com',
    'cloudbilling.googleapis.com',
]

# Folder names
MAIN_FOLDER_NAME = "Hackathon Playground Users"
GENERAL_FOLDER_NAME = "General Attendees"
TEAM_FOLDER_NAME = "Hackathon Teams"

# Project Naming Conventions
PLAYGROUND_PROJECT_SUFFIX = "-playground-gcp-25Q3"
TEAM_PROJECT_SUFFIX = "-hackathon-team-gcp-25Q3"
