- Project Description - 

This project help user to provision:

* Main Folder for Hackathon Playground Users which contains

** A sub-folder for hackathon general attendees' project as general folder
*** The playground project under folder will be provisioned with allowing some specificed admins as Project Owners and the general attendee will be Project Editor

** A sub-folder for hackathon teams' project as hackathon team folder
*** The team project under folder will be provisioned with allowing some specificed admins as Project Owners and a list of the group of each hackathon team members will be Project Editors as well.

The folders will enforced by org policy by only allows essential Google APIs for GenAI hackathon only and applied corresponding budget control:

* For general folder: $5 per month budget applied for each project within
* For hackathon team folder: $100 per month budget applied for each project within

- Technical Description -

This project will have a CLI internative interface and leverage corresponding API to implement the feature listed above

Each mutable operations will requires user's confirmation before execution with the detail of the API operation command displayed.

This project shall be implemented by python 3.

- Project Flow -

A list of the general attendees will be provided for provision the playground project. Each playground project should contains numbers of the pre-defined admins as Project Owners and the general attendee will be the Project Editor

A list of the hackathon team members will be provided for provision the team project. Each playground project should contains numbers of the pre-defined admins as Project Owners and the team members will be the Project Editors

The format of the input lists will be CSV. 

**CSV Format for Attendees:**
The `attendees.csv` file should have a single column named `email` containing the email addresses of the attendees.

Example `attendees.csv`:
```csv
email
attendee1@example.com
attendee2@example.com
```

**CSV Format for Teams:**
The `teams.csv` file should have two columns: `team_name` for the name of the hackathon team and `team_members` for a comma-separated list of email addresses of the team members.

Example `teams.csv`:
```csv
team_name,team_members
team_alpha,member1@example.com,member2@example.com
team_beta,member3@example.com
```

For the essentials of the API list please generate by your own thinking.

- Naming Convention -

Playground Project: <attendees's email prefix before @>-playground-gcp-25Q3
Team Project: <hackathon team name>-hackathon-team-gcp-25Q3

- Authentication -

Will leverage application-default login credential

- Testing -

This project includes a suite of unit tests to ensure the correctness of the implementation. The tests use Python's `unittest` framework and the `unittest.mock` library to isolate the code from the actual Google Cloud APIs. The tests cover the following scenarios:

*   **Main function:** Verifies that the correct functions are called based on the command-line arguments.
*   **Playground project provisioning:** Ensures that the correct project name is generated and that the project creation function is called with the correct parameters.
*   **Team project provisioning:** Ensures that the correct project name is generated and that the project creation function is called with the correct parameters.
*   **Helper functions:** Verifies that the helper functions for setting IAM policies, enabling APIs, and setting budgets are called with the correct parameters.

- New Features (as of 2025-06-30) -

*   **Interactive CLI:** The project now includes an interactive CLI, which can be started by running `python3 interactive_cli.py`. The interactive CLI supports the following commands:
    *   `init <parent_id>`: Initializes the hackathon folder structure under the given parent (organization or folder ID).
    *   `provision attendees <path_to_csv>`: Provision projects for general attendees.
    *   `provision teams <path_to_csv>`: Provision projects for hackathon teams.
    *   `check folder <folder_id>`: Check if a folder is accessible.
    *   `list folders`: List all available folders.
    *   `list projects <playground|team>`: List projects in the playground or team folder.
    *   `help`: Show the help message.
    *   `exit`: Exit the application.
