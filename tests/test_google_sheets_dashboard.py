import pytest
import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from google_sheets_dashboard import GoogleSheetsDashboard

class TestGoogleSheetsDashboard:
    """Test Google Sheets Dashboard functionality"""
    
    def setup_method(self):
        """Setup test method"""
        self.mock_credentials = Mock()
        self.mock_service = Mock()
        self.mock_spreadsheet = Mock()
        
    @patch('google_sheets_dashboard.service_account.Credentials.from_service_account_file')
    @patch('google_sheets_dashboard.build')
    def test_initialization_success(self, mock_build, mock_credentials):
        """Test successful dashboard initialization"""
        mock_credentials.return_value = self.mock_credentials
        mock_build.return_value = self.mock_service
        
        dashboard = GoogleSheetsDashboard()
        
        assert dashboard.service is not None
        mock_credentials.assert_called_once()
        mock_build.assert_called_once()
    
    @patch('google_sheets_dashboard.service_account.Credentials.from_service_account_file')
    def test_initialization_failure(self, mock_credentials):
        """Test dashboard initialization failure"""
        mock_credentials.side_effect = Exception("Credentials error")
        
        with pytest.raises(Exception):
            GoogleSheetsDashboard()
    
    @patch('google_sheets_dashboard.service_account.Credentials.from_service_account_file')
    @patch('google_sheets_dashboard.build')
    def test_create_dashboard_success(self, mock_build, mock_credentials):
        """Test successful dashboard creation"""
        mock_credentials.return_value = self.mock_credentials
        mock_build.return_value = self.mock_service
        
        # Mock spreadsheet creation
        mock_spreadsheet = Mock()
        mock_spreadsheet.get.return_value.execute.return_value = {
            'spreadsheetId': 'test_id',
            'properties': {'title': 'Test Dashboard'}
        }
        self.mock_service.spreadsheets.return_value = mock_spreadsheet
        
        dashboard = GoogleSheetsDashboard()
        result = dashboard.create_dashboard("Test Dashboard")
        
        assert result['spreadsheetId'] == 'test_id'
        mock_spreadsheet.create.assert_called_once()
    
    @patch('google_sheets_dashboard.service_account.Credentials.from_service_account_file')
    @patch('google_sheets_dashboard.build')
    def test_create_dashboard_with_template(self, mock_build, mock_credentials):
        """Test dashboard creation with template"""
        mock_credentials.return_value = self.mock_credentials
        mock_build.return_value = self.mock_service
        
        # Mock template copying
        mock_drive_service = Mock()
        mock_drive_service.files.return_value.copy.return_value.execute.return_value = {
            'id': 'copied_id'
        }
        self.mock_service.files.return_value = mock_drive_service
        
        dashboard = GoogleSheetsDashboard()
        result = dashboard.create_dashboard_with_template("Test Dashboard", "template_id")
        
        assert result['id'] == 'copied_id'
    
    @patch('google_sheets_dashboard.service_account.Credentials.from_service_account_file')
    @patch('google_sheets_dashboard.build')
    def test_create_summary_sheet(self, mock_build, mock_credentials):
        """Test summary sheet creation"""
        mock_credentials.return_value = self.mock_credentials
        mock_build.return_value = self.mock_service
        
        # Mock sheet operations
        mock_spreadsheet = Mock()
        mock_spreadsheet.batchUpdate.return_value.execute.return_value = {
            'replies': [{'addSheet': {'properties': {'title': 'Summary'}}}]
        }
        self.mock_service.spreadsheets.return_value = mock_spreadsheet
        
        dashboard = GoogleSheetsDashboard()
        result = dashboard.create_summary_sheet("test_id")
        
        assert result is not None
        mock_spreadsheet.batchUpdate.assert_called_once()
    
    @patch('google_sheets_dashboard.service_account.Credentials.from_service_account_file')
    @patch('google_sheets_dashboard.build')
    def test_create_department_sheets(self, mock_build, mock_credentials):
        """Test department sheets creation"""
        mock_credentials.return_value = self.mock_credentials
        mock_build.return_value = self.mock_service
        
        # Mock sheet operations
        mock_spreadsheet = Mock()
        mock_spreadsheet.batchUpdate.return_value.execute.return_value = {
            'replies': [{'addSheet': {'properties': {'title': 'BOM'}}}]
        }
        self.mock_service.spreadsheets.return_value = mock_spreadsheet
        
        dashboard = GoogleSheetsDashboard()
        departments = ['BOM', 'MPL', 'MFE']
        result = dashboard.create_department_sheets("test_id", departments)
        
        assert result is not None
        mock_spreadsheet.batchUpdate.assert_called_once()
    
    @patch('google_sheets_dashboard.service_account.Credentials.from_service_account_file')
    @patch('google_sheets_dashboard.build')
    def test_create_file_data_sheets(self, mock_build, mock_credentials):
        """Test file data sheets creation"""
        mock_credentials.return_value = self.mock_credentials
        mock_build.return_value = self.mock_service
        
        # Mock sheet operations
        mock_spreadsheet = Mock()
        mock_spreadsheet.batchUpdate.return_value.execute.return_value = {
            'replies': [{'addSheet': {'properties': {'title': 'File Data'}}}]
        }
        self.mock_service.spreadsheets.return_value = mock_spreadsheet
        
        dashboard = GoogleSheetsDashboard()
        file_data = {'file1.xlsx': {'data': 'test'}}
        result = dashboard.create_file_data_sheets("test_id", file_data)
        
        assert result is not None
        mock_spreadsheet.batchUpdate.assert_called_once()
    
    @patch('google_sheets_dashboard.service_account.Credentials.from_service_account_file')
    @patch('google_sheets_dashboard.build')
    def test_create_file_data_sheets_no_data(self, mock_build, mock_credentials):
        """Test file data sheets creation with no data"""
        mock_credentials.return_value = self.mock_credentials
        mock_build.return_value = self.mock_service
        
        dashboard = GoogleSheetsDashboard()
        result = dashboard.create_file_data_sheets("test_id", {})
        
        assert result is None
    
    @patch('google_sheets_dashboard.service_account.Credentials.from_service_account_file')
    @patch('google_sheets_dashboard.build')
    def test_create_charts_and_visualizations(self, mock_build, mock_credentials):
        """Test charts and visualizations creation"""
        mock_credentials.return_value = self.mock_credentials
        mock_build.return_value = self.mock_service
        
        # Mock chart creation
        mock_spreadsheet = Mock()
        mock_spreadsheet.batchUpdate.return_value.execute.return_value = {
            'replies': [{'addChart': {'chart': {'chartId': 1}}}]
        }
        self.mock_service.spreadsheets.return_value = mock_spreadsheet
        
        dashboard = GoogleSheetsDashboard()
        result = dashboard.create_charts_and_visualizations("test_id")
        
        assert result is not None
        mock_spreadsheet.batchUpdate.assert_called_once()
    
    @patch('google_sheets_dashboard.service_account.Credentials.from_service_account_file')
    @patch('google_sheets_dashboard.build')
    def test_format_summary_sheet(self, mock_build, mock_credentials):
        """Test summary sheet formatting"""
        mock_credentials.return_value = self.mock_credentials
        mock_build.return_value = self.mock_service
        
        # Mock formatting operations
        mock_spreadsheet = Mock()
        mock_spreadsheet.batchUpdate.return_value.execute.return_value = {
            'replies': [{'updateCells': {}}]
        }
        self.mock_service.spreadsheets.return_value = mock_spreadsheet
        
        dashboard = GoogleSheetsDashboard()
        result = dashboard.format_summary_sheet("test_id")
        
        assert result is not None
        mock_spreadsheet.batchUpdate.assert_called_once()
    
    @patch('google_sheets_dashboard.service_account.Credentials.from_service_account_file')
    @patch('google_sheets_dashboard.build')
    def test_format_department_sheet(self, mock_build, mock_credentials):
        """Test department sheet formatting"""
        mock_credentials.return_value = self.mock_credentials
        mock_build.return_value = self.mock_service
        
        # Mock formatting operations
        mock_spreadsheet = Mock()
        mock_spreadsheet.batchUpdate.return_value.execute.return_value = {
            'replies': [{'updateCells': {}}]
        }
        self.mock_service.spreadsheets.return_value = mock_spreadsheet
        
        dashboard = GoogleSheetsDashboard()
        result = dashboard.format_department_sheet("test_id", "BOM")
        
        assert result is not None
        mock_spreadsheet.batchUpdate.assert_called_once()
    
    @patch('google_sheets_dashboard.service_account.Credentials.from_service_account_file')
    @patch('google_sheets_dashboard.build')
    def test_update_dashboard(self, mock_build, mock_credentials):
        """Test dashboard update"""
        mock_credentials.return_value = self.mock_credentials
        mock_build.return_value = self.mock_service
        
        # Mock update operations
        mock_spreadsheet = Mock()
        mock_spreadsheet.values.return_value.update.return_value.execute.return_value = {
            'updatedCells': 10
        }
        self.mock_service.spreadsheets.return_value = mock_spreadsheet
        
        dashboard = GoogleSheetsDashboard()
        data = [['Header1', 'Header2'], ['Data1', 'Data2']]
        result = dashboard.update_dashboard("test_id", "Summary!A1", data)
        
        assert result['updatedCells'] == 10
        mock_spreadsheet.values.return_value.update.assert_called_once()
    
    @patch('google_sheets_dashboard.service_account.Credentials.from_service_account_file')
    @patch('google_sheets_dashboard.build')
    def test_get_sheet_data(self, mock_build, mock_credentials):
        """Test getting sheet data"""
        mock_credentials.return_value = self.mock_credentials
        mock_build.return_value = self.mock_service
        
        # Mock data retrieval
        mock_spreadsheet = Mock()
        mock_spreadsheet.values.return_value.get.return_value.execute.return_value = {
            'values': [['Header1', 'Header2'], ['Data1', 'Data2']]
        }
        self.mock_service.spreadsheets.return_value = mock_spreadsheet
        
        dashboard = GoogleSheetsDashboard()
        result = dashboard.get_sheet_data("test_id", "Summary!A1:B2")
        
        assert result == [['Header1', 'Header2'], ['Data1', 'Data2']]
        mock_spreadsheet.values.return_value.get.assert_called_once()
    
    @patch('google_sheets_dashboard.service_account.Credentials.from_service_account_file')
    @patch('google_sheets_dashboard.build')
    def test_create_dashboard_comprehensive(self, mock_build, mock_credentials):
        """Test comprehensive dashboard creation"""
        mock_credentials.return_value = self.mock_credentials
        mock_build.return_value = self.mock_service
        
        # Mock all operations
        mock_spreadsheet = Mock()
        mock_spreadsheet.get.return_value.execute.return_value = {
            'spreadsheetId': 'test_id',
            'properties': {'title': 'Test Dashboard'}
        }
        mock_spreadsheet.batchUpdate.return_value.execute.return_value = {
            'replies': [{'addSheet': {'properties': {'title': 'Summary'}}}]
        }
        mock_spreadsheet.values.return_value.update.return_value.execute.return_value = {
            'updatedCells': 5
        }
        self.mock_service.spreadsheets.return_value = mock_spreadsheet
        
        dashboard = GoogleSheetsDashboard()
        
        # Test full dashboard creation
        result = dashboard.create_dashboard("Test Dashboard")
        assert result['spreadsheetId'] == 'test_id'
        
        # Test adding summary sheet
        summary_result = dashboard.create_summary_sheet("test_id")
        assert summary_result is not None
        
        # Test updating data
        data = [['Test', 'Data']]
        update_result = dashboard.update_dashboard("test_id", "Summary!A1", data)
        assert update_result['updatedCells'] == 5

if __name__ == '__main__':
    pytest.main([__file__]) 