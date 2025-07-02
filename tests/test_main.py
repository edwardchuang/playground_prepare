import unittest
from unittest.mock import patch, MagicMock, call, mock_open
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from main import (
    main,
    provision_playground_projects,
    create_project,
    set_iam_policy,
    link_billing_account,
    enable_apis,
    provision_team_projects,
    create_team_project,
    set_team_iam_policy,
)
from config import PLAYGROUND_PROJECT_SUFFIX, TEAM_PROJECT_SUFFIX

class TestProjectProvisioning(unittest.TestCase):

    @patch('main.get_credentials')
    @patch('main.build')
    @patch('main.provision_playground_projects')
    @patch('main.provision_team_projects')
    @patch('main.init_project_folders')
    def test_main(self, mock_init_project_folders, mock_team_projects, mock_playground_projects, mock_build, mock_get_credentials):
        mock_crm_v3 = MagicMock()
        mock_crm_v3.organizations().get.return_value.execute.return_value = {'name': 'organizations/123456789012'}
        mock_crm_v3.folders().get.return_value.execute.return_value = {'name': 'folders/123456789012'}
        mock_serviceusage_v1 = MagicMock()
        mock_cloudbilling_v1 = MagicMock()
        mock_build.side_effect = [mock_crm_v3, mock_serviceusage_v1, mock_cloudbilling_v1]
        mock_init_project_folders.return_value = ('main_folder_id_mock', 'general_folder_id_mock', 'team_folder_id_mock')

        # Test with --attendees argument
        with patch.object(sys, 'argv', ['main.py', '--attendees', 'attendees.csv']):
            main()
            mock_init_project_folders.assert_called_once_with("organizations/123456789012", mock_crm_v3, debug_mode=False)
            mock_playground_projects.assert_called_with('attendees.csv', mock_crm_v3, mock_serviceusage_v1, mock_cloudbilling_v1, 'general_folder_id_mock', debug_mode=False)
            mock_team_projects.assert_not_called()

        mock_init_project_folders.reset_mock()
        mock_playground_projects.reset_mock()
        mock_team_projects.reset_mock()
        mock_build.side_effect = [mock_crm_v3, mock_serviceusage_v1, mock_cloudbilling_v1]

        # Test with --teams argument
        with patch.object(sys, 'argv', ['main.py', '--teams', 'teams.csv']):
            main()
            mock_init_project_folders.assert_called_once_with("organizations/123456789012", mock_crm_v3, debug_mode=False)
            mock_playground_projects.assert_not_called()
            mock_team_projects.assert_called_with('teams.csv', mock_crm_v3, mock_serviceusage_v1, mock_cloudbilling_v1, 'team_folder_id_mock', debug_mode=False)

    @patch('builtins.open', new_callable=mock_open, read_data="email\npingda@google.com")
    @patch('main.create_project')
    def test_provision_playground_projects(self, mock_create_project, mock_open):
        with patch('os.urandom') as mock_urandom:
            mock_urandom.return_value.hex.return_value = '576363'
            provision_playground_projects('attendees.csv', None, None, 'general_folder_id_mock', False)
            mock_create_project.assert_called_with('pingda-sbox-gcp-25q3-576363', 'playground project for pingda', 'pingda@google.com', None, None, 'general_folder_id_mock', False)

    @patch('main.set_iam_policy')
    @patch('main.link_billing_account')
    @patch('main.enable_apis')
    
    def test_create_project(self, mock_enable_apis, mock_link_billing_account, mock_set_iam_policy):
        mock_crm_v3 = MagicMock()
        mock_serviceusage_v1 = MagicMock()
        mock_cloudbilling_v1 = MagicMock()
        create_project('test-project','test-project', 'user@example.com', mock_crm_v3, mock_serviceusage_v1, mock_cloudbilling_v1, 'parent_folder_id_mock', False)
        mock_crm_v3.projects().create.assert_called_once()
        mock_set_iam_policy.assert_called_with('test-project', 'user@example.com', mock_crm_v3, False)
        mock_link_billing_account.assert_called_with('test-project', mock_cloudbilling_v1, False)
        mock_enable_apis.assert_called_with('test-project', mock_serviceusage_v1, False)

    @patch('builtins.open', new_callable=mock_open, read_data="team_name,team_members\nteam_gemini,gemini-pro@google.com")
    @patch('main.create_team_project')
    def test_provision_team_projects(self, mock_create_team_project, mock_open):
        provision_team_projects('teams.csv', None, None, 'team_folder_id_mock', False)
        mock_create_team_project.assert_called_with('team-g-team-gcp-25q3', 'team project for team_gemini', ['gemini-pro@google.com'], None, None, 'team_folder_id_mock', False)

    @patch('main.set_team_iam_policy')
    @patch('main.link_billing_account')
    @patch('main.enable_apis')
    
    def test_create_team_project(self, mock_enable_apis, mock_link_billing_account, mock_set_team_iam_policy):
        mock_crm_v3 = MagicMock()
        mock_serviceusage_v1 = MagicMock()
        mock_cloudbilling_v1 = MagicMock()
        create_team_project('test-project', 'test-project', ['user@example.com'], mock_crm_v3, mock_serviceusage_v1, mock_cloudbilling_v1, 'parent_folder_id_mock', False)
        mock_crm_v3.projects().create.assert_called_once()
        mock_set_team_iam_policy.assert_called_with('test-project', ['user@example.com'], mock_crm_v3, False)
        mock_link_billing_account.assert_called_with('test-project', mock_cloudbilling_v1, False)
        mock_enable_apis.assert_called_with('test-project', mock_serviceusage_v1, False)

    def test_set_iam_policy(self):
        mock_crm_v3 = MagicMock()
        mock_crm_v3.projects().getIamPolicy.return_value.execute.return_value = {'bindings': []}
        set_iam_policy('test-project', 'user@example.com', mock_crm_v3)
        mock_crm_v3.projects().setIamPolicy.assert_called_once()

    def test_set_team_iam_policy(self):
        mock_crm_v3 = MagicMock()
        mock_crm_v3.projects().getIamPolicy.return_value.execute.return_value = {'bindings': []}
        set_team_iam_policy('test-project', ['user@example.com'], mock_crm_v3)
        mock_crm_v3.projects().setIamPolicy.assert_called_once()

    def test_link_billing_account(self):
        mock_cloudbilling_v1 = MagicMock()
        link_billing_account('test-project', mock_cloudbilling_v1)
        mock_cloudbilling_v1.projects().updateBillingInfo.assert_called_once()

    def test_enable_apis(self):
        mock_serviceusage_v1 = MagicMock()
        enable_apis('test-project', mock_serviceusage_v1)
        self.assertGreater(mock_serviceusage_v1.services().enable.call_count, 0)

    

if __name__ == '__main__':
    unittest.main()