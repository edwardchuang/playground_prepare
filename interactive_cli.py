import sys
import os
import readline # Enables command history
from googleapiclient.discovery import build

# Add the 'src' directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from main import (
    get_credentials,
    provision_playground_projects,
    provision_team_projects,
    check_folder,
    list_folders,
    list_projects_in_folder,
    init_project_folders,
)
from src import config

# Global variables to store folder IDs
main_hackathon_folder_id = config.MAIN_HACKATHON_FOLDER_ID
general_attendees_folder_id = config.GENERAL_ATTENDEES_FOLDER_ID
hackathon_teams_folder_id = config.HACKATHON_TEAMS_FOLDER_ID

debug_mode = False

def print_help():
    """Prints a help message with available commands."""
    print("\nAvailable Commands:")
    print("  init <parent_id>                   - Initialize the hackathon folder structure.")
    print("  provision attendees <path_to_csv>  - Provision projects for general attendees.")
    print("  provision teams <path_to_csv>      - Provision projects for hackathon teams.")
    print("  check folder <folder_id>           - Check if a folder is accessible.")
    print("  list folders                       - List all available folders.")
    print("  list projects <playground|team>    - List projects in the playground or team folder.")
    print("  debug on|off                       - Turn API payload debugging on or off.")
    print("  help                               - Show this help message.")
    print("  exit                               - Exit the application.\n")

def save_folder_ids_to_config():
    """Saves the current folder IDs to src/config.py for persistence."""
    global main_hackathon_folder_id, general_attendees_folder_id, hackathon_teams_folder_id
    
    config_file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'src', 'config.py'))
    
    with open(config_file_path, 'r') as f:
        lines = f.readlines()

    with open(config_file_path, 'w') as f:
        for line in lines:
            if line.startswith('MAIN_HACKATHON_FOLDER_ID ='):
                f.write(f"MAIN_HACKATHON_FOLDER_ID = '{main_hackathon_folder_id}'\n")
            elif line.startswith('GENERAL_ATTENDEES_FOLDER_ID ='):
                f.write(f"GENERAL_ATTENDEES_FOLDER_ID = '{general_attendees_folder_id}'\n")
            elif line.startswith('HACKATHON_TEAMS_FOLDER_ID ='):
                f.write(f"HACKATHON_TEAMS_FOLDER_ID = '{hackathon_teams_folder_id}'\n")
            else:
                f.write(line)
    print("Folder IDs saved to src/config.py.")

def main_loop():
    """The main interactive loop for the CLI."""
    global main_hackathon_folder_id, general_attendees_folder_id, hackathon_teams_folder_id, debug_mode

    # Load folder IDs from config at startup
    main_hackathon_folder_id = config.MAIN_HACKATHON_FOLDER_ID
    general_attendees_folder_id = config.GENERAL_ATTENDEES_FOLDER_ID
    hackathon_teams_folder_id = config.HACKATHON_TEAMS_FOLDER_ID

    print("Welcome to the Hackathon Project Provisioning CLI.")
    print("Type 'help' for a list of commands.")

    # Get credentials and build service clients once at the start
    try:
        credentials, display_name = get_credentials()
        crm_v3 = build('cloudresourcemanager', 'v3', credentials=credentials)
        billing_v1 = build('billingbudgets', 'v1', credentials=credentials)
        serviceusage_v1 = build('serviceusage', 'v1', credentials=credentials)
        print(f"Successfully authenticated with Google Cloud as: {display_name}")
    except Exception as e:
        print(f"Failed to authenticate with Google Cloud: {e}")
        print("Please ensure you have run 'gcloud auth application-default login'.")

    while True:
        try:
            raw_input = input("provisioner> ")
            if not raw_input:
                continue

            parts = raw_input.split()
            command = parts[0].lower()
            args = parts[1:]

            if command in ["exit", "quit"]:
                print("Exiting...")
                break
            elif command == "help":
                print_help()
            elif command == "debug":
                if not args:
                    print("Error: 'debug' requires 'on' or 'off'. Usage: debug on|off")
                    continue
                subcommand = args[0].lower()
                if subcommand == "on":
                    debug_mode = True
                    print("API payload debugging is ON.")
                elif subcommand == "off":
                    debug_mode = False
                    print("API payload debugging is OFF.")
                else:
                    print("Error: Invalid debug subcommand. Use 'on' or 'off'.")
            elif command == "init":
                if not args:
                    print("Error: 'init' requires a parent ID (organization or folder).")
                    continue
                parent_id = args[0]
                try:
                    main_hackathon_folder_id, general_attendees_folder_id, hackathon_teams_folder_id = init_project_folders(parent_id, crm_v3, debug_mode)
                    print(f"Initialized folders: Main: {main_hackathon_folder_id}, General: {general_attendees_folder_id}, Teams: {hackathon_teams_folder_id}")
                    save_folder_ids_to_config()
                except Exception as e:
                    print(f"Error during initialization: {e}")
            elif command == "provision":
                if len(args) < 2:
                    print("Error: 'provision' requires a subcommand (attendees or teams) and a file path.")
                    continue
                
                subcommand = args[0].lower()
                file_path = args[1]

                if not file_path:
                    print(f"Error: 'provision {subcommand}' requires a file path.")
                    continue

                if subcommand == "attendees":
                    if not general_attendees_folder_id:
                        print("Error: General attendees folder not initialized. Please run 'init' first.")
                        continue
                    print(f"Starting provisioning for attendees from {file_path}...")
                    provision_playground_projects(file_path, crm_v3, serviceusage_v1, billing_v1, general_attendees_folder_id, debug_mode)
                    print("Finished provisioning for attendees.")
                elif subcommand == "teams":
                    if not hackathon_teams_folder_id:
                        print("Error: Hackathon teams folder not initialized. Please run 'init' first.")
                        continue
                    print(f"Starting provisioning for teams from {file_path}...")
                    provision_team_projects(file_path, crm_v3, serviceusage_v1, billing_v1, hackathon_teams_folder_id, debug_mode)
                    print("Finished provisioning for teams.")
                else:
                    print(f"Error: Unknown subcommand '{subcommand}' for 'provision'.")
            elif command == "check":
                if len(args) < 2 or args[0].lower() != "folder":
                    print("Error: Usage: check folder <folder_id>")
                    continue
                folder_id = args[1]
                if check_folder(folder_id, crm_v3):
                    print(f"Folder {folder_id} is accessible.")
                else:
                    print(f"Folder {folder_id} is not accessible or does not exist.")

            elif command == "list":
                if not args:
                    print("Error: 'list' requires a subcommand (folders or projects). ")
                    continue
                subcommand = args[0].lower()
                if subcommand == "folders":
                    folders = list_folders(crm_v3)
                    if folders:
                        print("Available Folders:")
                        for folder in folders:
                            print(f"  - {folder['displayName']} ({folder['name']})")
                    else:
                        print("No folders found or an error occurred.")
                elif subcommand == "projects":
                    if len(args) < 2:
                        print("Error: Usage: list projects <playground|team>")
                        continue
                    folder_type = args[1].lower()
                    target_folder_id = None
                    if folder_type == "playground":
                        target_folder_id = general_attendees_folder_id
                    elif folder_type == "team":
                        target_folder_id = hackathon_teams_folder_id
                    else:
                        print("Error: Invalid project type. Use 'playground' or 'team'.")
                        continue

                    if not target_folder_id:
                        print(f"Error: {folder_type} folder not initialized. Please run 'init' first.")
                        continue

                    projects = list_projects_in_folder(target_folder_id, crm_v3)
                    if projects:
                        print(f"Projects in {folder_type} folder ({target_folder_id}):")
                        for project in projects:
                            print(f"  - {project['displayName']} ({project['projectId']})")
                    else:
                        print(f"No projects found in {folder_type} folder or an error occurred.")
                else:
                    print(f"Error: Unknown subcommand '{subcommand}' for 'list'.")
            else:
                print(f"Error: Unknown command '{command}'. Type 'help' for a list of commands.")

        except (KeyboardInterrupt, EOFError):
            print("\nExiting...")
            break
        except FileNotFoundError:
            print(f"Error: The file '{file_path}' was not found.")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    main_loop()