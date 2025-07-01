# Hackathon Project Provisioning CLI

This project provides a Command Line Interface (CLI) tool to automate the provisioning of Google Cloud Platform (GCP) projects for hackathon attendees and teams. It ensures proper folder structure, IAM policies, budget controls, and essential API enablement for GenAI hackathons.

## Features

*   **Main Folder Provisioning:** Creates main folders for general attendees and hackathon teams.
*   **Project Provisioning:**
    *   **General Attendees:** Provisions individual GCP projects for each attendee with specified admins as Project Owners and the attendee as Project Editor. A $5/month budget is applied per project.
    *   **Hackathon Teams:** Provisions GCP projects for each team with specified admins as Project Owners and team members as Project Editors. A $100/month budget is applied per project.
*   **Org Policy Enforcement:** Enforces essential Google APIs for GenAI hackathons and applies budget controls.
*   **Interactive CLI:** A user-friendly interactive CLI for managing the provisioning process.

## Technical Details

The project is implemented in Python 3 and leverages Google Cloud APIs for provisioning. All mutable operations require user confirmation before execution, displaying the detailed API operation command.

## Project Flow

The tool takes CSV files as input for attendees and teams to automate project creation.

### CSV Format for Attendees:

The `attendees.csv` file should have a single column named `email` containing the email addresses of the attendees.

Example `attendees.csv`:
```csv
email
attendee1@example.com
attendee2@example.com
```

### CSV Format for Teams:

The `teams.csv` file should have two columns: `team_name` for the name of the hackathon team and `team_members` for a comma-separated list of email addresses of the team members.

Example `teams.csv`:
```csv
team_name,team_members
team_alpha,member1@example.com,member2@example.com
team_beta,member3@example.com
```

## Naming Convention

*   **Playground Project:** `<attendees's email prefix before @>-playground-gcp-25Q3`
*   **Team Project:** `<hackathon team name>-hackathon-team-gcp-25Q3`

## Authentication

The project leverages application-default login credentials for authentication with Google Cloud.

## Testing

The project includes a suite of unit tests using Python's `unittest` framework and `unittest.mock` to ensure correctness and isolate API calls.

## Interactive CLI Usage

To start the interactive CLI, run:

```bash
python3 interactive_cli.py
```

The CLI supports the following commands:

*   `init <parent_id>`: Initializes the hackathon folder structure under the given parent (organization or folder ID).
*   `provision attendees <path_to_csv>`: Provision projects for general attendees.
*   `provision teams <path_to_csv>`: Provision projects for hackathon teams.
*   `check folder <folder_id>`: Check if a folder is accessible.
*   `list folders`: List all available folders.
*   `list projects <playground|team>`: List projects in the playground or team folder.
*   `help`: Show the help message.
*   `exit`: Exit the application.
