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
    enable_apis,
    set_budget,
    provision_team_projects,
    create_team_project,
    set_team_iam_policy,
    set_team_budget,
)
from config import PLAYGROUND_PROJECT_SUFFIX, TEAM_PROJECT_SUFFIX, PLAYGROUND_PROJECT_BUDGET_USD, TEAM_PROJECT_BUDGET_USD

class TestProjectProvisioning(unittest.TestCase):

    @patch('main.get_credentials')
    @patch('main.build')
    @patch('main.provision_playground_projects')
    @patch('main.provision_team_projects')
    @patch('main.init_project_folders')
    def test_main(self, mock_init_project_folders, mock_team_projects, mock_playground_projects, mock_build, mock_get_credentials):
        mock_crm_v3 = MagicMock()
        mock_billing_v1 = MagicMock()
        mock_serviceusage_v1 = MagicMock()
        mock_build.side_effect = [mock_crm_v3, mock_billing_v1, mock_serviceusage_v1]
        mock_init_project_folders.return_value = ('main_folder_id_mock', 'general_folder_id_mock', 'team_folder_id_mock')

        # Test with --attendees argument
        with patch.object(sys, 'argv', ['main.py', '--attendees', 'attendees.csv']):
            main()
            mock_init_project_folders.assert_called_once_with("organizations/123456789012", mock_crm_v3)
            mock_playground_projects.assert_called_with('attendees.csv', mock_crm_v3, mock_serviceusage_v1, mock_billing_v1, 'general_folder_id_mock')
            mock_team_projects.assert_not_called()

        mock_init_project_folders.reset_mock()
        mock_playground_projects.reset_mock()
        mock_team_projects.reset_mock()
        mock_build.side_effect = [mock_crm_v3, mock_billing_v1, mock_serviceusage_v1]

        # Test with --teams argument
        with patch.object(sys, 'argv', ['main.py', '--teams', 'teams.csv']):
            main()
            mock_init_project_folders.assert_called_once_with("organizations/123456789012", mock_crm_v3)
            mock_playground_projects.assert_not_called()
            mock_team_projects.assert_called_with('teams.csv', mock_crm_v3, mock_serviceusage_v1, mock_billing_v1, 'team_folder_id_mock')

    @patch('builtins.open', new_callable=mock_open, read_data="email\npingda@google.com")
    @patch('main.create_project')
    def test_provision_playground_projects(self, mock_create_project, mock_open):
        provision_playground_projects('attendees.csv', None, None, None, 'general_folder_id_mock')
        mock_create_project.assert_called_with(f'pingda{PLAYGROUND_PROJECT_SUFFIX}', 'pingda@google.com', None, None, None, 'general_folder_id_mock', PLAYGROUND_PROJECT_BUDGET_USD)

    @patch('main.set_iam_policy')
    @patch('main.enable_apis')
    @patch('main.set_budget')
    def test_create_project(self, mock_set_budget, mock_enable_apis, mock_set_iam_policy):
        mock_crm_v3 = MagicMock()
        create_project('test-project', 'user@example.com', mock_crm_v3, None, None, 'parent_folder_id_mock', PLAYGROUND_PROJECT_BUDGET_USD)
        mock_crm_v3.projects().create.assert_called_once()
        mock_set_iam_policy.assert_called_with('test-project', 'user@example.com', mock_crm_v3)
        mock_enable_apis.assert_called_with('test-project', None)
        mock_set_budget.assert_called_with('test-project', None, PLAYGROUND_PROJECT_BUDGET_USD)

    @patch('builtins.open', new_callable=mock_open, read_data="team_name,team_members\nteam_gemini,gemini-pro@google.com")
    @patch('main.create_team_project')
    def test_provision_team_projects(self, mock_create_team_project, mock_open):
        provision_team_projects('teams.csv', None, None, None, 'team_folder_id_mock')
        mock_create_team_project.assert_called_with(f'team_gemini{TEAM_PROJECT_SUFFIX}', ['gemini-pro@google.com'], None, None, None, 'team_folder_id_mock', TEAM_PROJECT_BUDGET_USD)

    @patch('main.set_team_iam_policy')
    @patch('main.enable_apis')
    @patch('main.set_team_budget')
    def test_create_team_project(self, mock_set_team_budget, mock_enable_apis, mock_set_team_iam_policy):
        mock_crm_v3 = MagicMock()
        create_team_project('test-project', ['user@example.com'], mock_crm_v3, None, None, 'parent_folder_id_mock', TEAM_PROJECT_BUDGET_USD)
        mock_crm_v3.projects().create.assert_called_once()
        mock_set_team_iam_policy.assert_called_with('test-project', ['user@example.com'], mock_crm_v3)
        mock_enable_apis.assert_called_with('test-project', None)
        mock_set_team_budget.assert_called_with('test-project', None, TEAM_PROJECT_BUDGET_USD)

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

    def test_enable_apis(self):
        mock_serviceusage_v1 = MagicMock()
        enable_apis('test-project', mock_serviceusage_v1)
        self.assertGreater(mock_serviceusage_v1.services().enable.call_count, 0)

    def test_set_budget(self):
        mock_billing_v1 = MagicMock()
        set_budget('test-project', mock_billing_v1, PLAYGROUND_PROJECT_BUDGET_USD)
        mock_billing_v1.billingAccounts().budgets().create.assert_called_once()

    def test_set_team_budget(self):
        mock_billing_v1 = MagicMock()
        set_team_budget('test-project', mock_billing_v1, TEAM_PROJECT_BUDGET_USD)
        mock_billing_v1.billingAccounts().budgets().create.assert_called_once()

if __name__ == '__main__':
    unittest.main()