import sys
import os
import readline # Enables command history
from googleapiclient.discovery import build

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
    apply_organization_policies,
    revert_organization_policies,
)
from src import config

# Global variables to store folder IDs
main_hackathon_folder_id = config.MAIN_HACKATHON_FOLDER_ID
general_attendees_folder_id = config.GENERAL_ATTENDEES_FOLDER_ID
hackathon_teams_folder_id = config.HACKATHON_TEAMS_FOLDER_ID

debug_mode = False

def print_help():
    """Prints a help message with available commands."""
    print_info("\nAvailable Commands:")
    print_info("  init <parent_id>                   - Initialize the hackathon folder structure.")
    print_info("  provision attendees <path_to_csv>  - Provision projects for general attendees.")
    print_info("  provision teams <path_to_csv>      - Provision projects for hackathon teams.")
    print_info("  check folder <folder_id>           - Check if a folder is accessible.")
    print_info("  list folders                       - List all available folders.")
    print_info("  list projects <playground|team>    - List projects in the playground or team folder.")
    print_info("  apply-policies <folder_id>         - Apply organization policies to a folder.")
    print_info("  revert-policies <folder_id>        - Revert organization policies on a folder.")
    print_info("  debug on|off                       - Turn API payload debugging on or off.")
    print_info("  help                               - Show this help message.")
    print_info("  exit                               - Exit the application.\n")

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
    print_success("Folder IDs saved to src/config.py.")

def main_loop():
    """The main interactive loop for the CLI."""
    global main_hackathon_folder_id, general_attendees_folder_id, hackathon_teams_folder_id, debug_mode

    # Load folder IDs from config at startup
    main_hackathon_folder_id = config.MAIN_HACKATHON_FOLDER_ID
    general_attendees_folder_id = config.GENERAL_ATTENDEES_FOLDER_ID
    hackathon_teams_folder_id = config.HACKATHON_TEAMS_FOLDER_ID

    print_info("Welcome to the Hackathon Project Provisioning CLI.")
    print_info("Type 'help' for a list of commands.")

    # Get credentials and build service clients once at the start
    try:
        credentials, display_name = get_credentials()
        crm_v3 = build('cloudresourcemanager', 'v3', credentials=credentials)
        serviceusage_v1 = build('serviceusage', 'v1', credentials=credentials)
        cloudbilling_v1 = build('cloudbilling', 'v1', credentials=credentials)
        print_success(f"Successfully authenticated with Google Cloud as: {display_name}")
    except Exception as e:
        print_error(f"Failed to authenticate with Google Cloud: {e}")
        print_warning("Please ensure you have run 'gcloud auth application-default login'.")

    while True:
        try:
            raw_input = input("provisioner> ")
            if not raw_input:
                continue

            parts = raw_input.split()
            command = parts[0].lower()
            args = parts[1:]

            if command in ["exit", "quit"]:
                print_info("Exiting...")
                break
            elif command == "help":
                print_help()
            elif command == "debug":
                if not args:
                    print_error("Error: 'debug' requires 'on' or 'off'. Usage: debug on|off")
                    continue
                subcommand = args[0].lower()
                if subcommand == "on":
                    debug_mode = True
                    print_info("API payload debugging is ON.")
                elif subcommand == "off":
                    debug_mode = False
                    print_info("API payload debugging is OFF.")
                else:
                    print_error("Error: Invalid debug subcommand. Use 'on' or 'off'.")
            elif command == "init":
                if not args:
                    print_error("Error: 'init' requires a parent ID (organization or folder).")
                    continue
                parent_id = args[0]
                try:
                    main_hackathon_folder_id, general_attendees_folder_id, hackathon_teams_folder_id = init_project_folders(parent_id, crm_v3, debug_mode)
                    print_success(f"Initialized folders: Main: {main_hackathon_folder_id}, General: {general_attendees_folder_id}, Teams: {hackathon_teams_folder_id}")
                    save_folder_ids_to_config()
                except Exception as e:
                    print_error(f"Error during initialization: {e}")
            elif command == "provision":
                if len(args) < 2:
                    print_error("Error: 'provision' requires a subcommand (attendees or teams) and a file path.")
                    continue
                
                subcommand = args[0].lower()
                file_path = args[1]

                if not file_path:
                    print_error(f"Error: 'provision {subcommand}' requires a file path.")
                    continue

                if subcommand == "attendees":
                    if not general_attendees_folder_id:
                        print_error("Error: General attendees folder not initialized. Please run 'init' first.")
                        continue
                    print_info(f"Starting provisioning for attendees from {file_path}...")
                    provision_playground_projects(file_path, crm_v3, serviceusage_v1, cloudbilling_v1, general_attendees_folder_id, debug_mode)
                    print_success("Finished provisioning for attendees.")
                elif subcommand == "teams":
                    if not hackathon_teams_folder_id:
                        print_error("Error: Hackathon teams folder not initialized. Please run 'init' first.")
                        continue
                    print_info(f"Starting provisioning for teams from {file_path}...")
                    provision_team_projects(file_path, crm_v3, serviceusage_v1, cloudbilling_v1, hackathon_teams_folder_id, debug_mode)
                    print_success("Finished provisioning for teams.")
                else:
                    print_error(f"Error: Unknown subcommand '{subcommand}' for 'provision'.")
            elif command == "check":
                if len(args) < 2 or args[0].lower() != "folder":
                    print_error("Error: Usage: check folder <folder_id>")
                    continue
                folder_id = args[1]
                if check_folder(folder_id, crm_v3):
                    print_success(f"Folder {folder_id} is accessible.")
                else:
                    print_error(f"Folder {folder_id} is not accessible or does not exist.")

            elif command == "list":
                if not args:
                    print_error("Error: 'list' requires a subcommand (folders or projects). ")
                    continue
                subcommand = args[0].lower()
                if subcommand == "folders":
                    folders = list_folders(crm_v3)
                    if folders:
                        print_info("Available Folders:")
                        for folder in folders:
                            print_info(f"  - {folder['displayName']} ({folder['name']})")
                    else:
                        print_warning("No folders found or an error occurred.")
                elif subcommand == "projects":
                    if len(args) < 2:
                        print_error("Error: Usage: list projects <playground|team>")
                        continue
                    folder_type = args[1].lower()
                    target_folder_id = None
                    if folder_type == "playground":
                        target_folder_id = general_attendees_folder_id
                    elif folder_type == "team":
                        target_folder_id = hackathon_teams_folder_id
                    else:
                        print_error("Error: Invalid project type. Use 'playground' or 'team'.")
                        continue

                    if not target_folder_id:
                        print_error(f"Error: {folder_type} folder not initialized. Please run 'init' first.")
                        continue

                    projects = list_projects_in_folder(target_folder_id, crm_v3)
                    if projects:
                        print_info(f"Projects in {folder_type} folder ({target_folder_id}):")
                        for project in projects:
                            print_info(f"  - {project['displayName']} ({project['projectId']})")
                    else:
                        print_warning(f"No projects found in {folder_type} folder or an error occurred.")
                else:
                    print_error(f"Error: Unknown subcommand '{subcommand}' for 'list'.")
            elif command == "apply-policies":
                if not args:
                    print_error("Error: 'apply-policies' requires a folder ID.")
                    continue
                folder_id = args[0]
                try:
                    apply_organization_policies(folder_id, crm_v3, debug_mode)
                    print_success(f"Successfully applied organization policies to folder {folder_id}.")
                except Exception as e:
                    print_error(f"Error applying organization policies: {e}")
            elif command == "revert-policies":
                if not args:
                    print_error("Error: 'revert-policies' requires a folder ID.")
                    continue
                folder_id = args[0]
                try:
                    revert_organization_policies(folder_id, crm_v3, debug_mode)
                    print_success(f"Successfully reverted organization policies on folder {folder_id}.")
                except Exception as e:
                    print_error(f"Error reverting organization policies: {e}")
            else:
                print_error(f"Error: Unknown command '{command}'. Type 'help' for a list of commands.")

        except (KeyboardInterrupt, EOFError):
            print_info("\nExiting...")
            break
        except FileNotFoundError:
            print_error(f"Error: The file '{file_path}' was not found.")
        except Exception as e:
            print_error(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    main_loop()