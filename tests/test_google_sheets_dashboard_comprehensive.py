import pytest
import unittest
from unittest.mock import Mock, patch, MagicMock, call
import sys
import os
import json
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from google_sheets_dashboard import GoogleSheetsDashboard

class TestGoogleSheetsDashboardComprehensive:
    """Comprehensive tests for GoogleSheetsDashboard"""
    
    def setup_method(self):
        """Set up test fixtures"""
        with patch('google_sheets_dashboard.GOOGLE_SHEETS_CREDENTIALS_FILE', '/path/to/credentials.json'), \
             patch('google_sheets_dashboard.GOOGLE_SHEETS_SCOPES', ['https://www.googleapis.com/auth/spreadsheets']), \
             patch('google_sheets_dashboard.DASHBOARD_TEMPLATE_ID', 'template_id_123'):
            
            # Mock external dependencies
            with patch('google_sheets_dashboard.Credentials') as mock_credentials, \
                 patch('google_sheets_dashboard.build') as mock_build, \
                 patch('google_sheets_dashboard.gspread') as mock_gspread:
                
                # Configure mocks
                mock_creds = Mock()
                mock_credentials.from_service_account_file.return_value = mock_creds
                
                mock_service = Mock()
                mock_build.return_value = mock_service
                
                mock_gc = Mock()
                mock_gspread.authorize.return_value = mock_gc
                
                self.dashboard = GoogleSheetsDashboard()
    
    def test_initialization_success(self):
        """Test successful dashboard initialization"""
        assert self.dashboard.creds is not None
        assert self.dashboard.service is not None
    
    def test_initialization_no_credentials_file(self):
        """Test initialization without credentials file"""
        with patch('google_sheets_dashboard.GOOGLE_SHEETS_CREDENTIALS_FILE', None):
            dashboard = GoogleSheetsDashboard()
            
            assert dashboard.creds is None
            assert dashboard.service is None
    
    def test_initialization_credentials_error(self):
        """Test initialization with credentials error"""
        with patch('google_sheets_dashboard.GOOGLE_SHEETS_CREDENTIALS_FILE', '/invalid/path.json'):
            with patch('google_sheets_dashboard.Credentials') as mock_credentials:
                mock_credentials.from_service_account_file.side_effect = Exception("Credentials error")
                
                dashboard = GoogleSheetsDashboard()
                
                assert dashboard.creds is None
                assert dashboard.service is None
    
    def test_create_dashboard_success(self):
        """Test successful dashboard creation"""
        # Mock spreadsheet creation
        mock_dashboard = Mock()
        mock_dashboard.url = "https://sheets.google.com/dashboard"
        
        with patch('google_sheets_dashboard.gspread') as mock_gspread:
            mock_gc = Mock()
            mock_gspread.authorize.return_value = mock_gc
            mock_gc.create.return_value = mock_dashboard
            
            # Mock sheet creation methods
            with patch.object(self.dashboard, '_create_summary_sheet') as mock_summary, \
                 patch.object(self.dashboard, '_create_department_sheets') as mock_dept, \
                 patch.object(self.dashboard, '_create_file_data_sheets') as mock_file, \
                 patch.object(self.dashboard, '_create_charts_and_visualizations') as mock_charts:
                
                databricks_data = {
                    'BOM': {'status': 'success', 'data': [{'part': 'P001', 'status': 'complete'}]},
                    'MP': {'status': 'success', 'data': [{'part': 'P002', 'status': 'pending'}]}
                }
                file_data = {'file': 'data'}
                launch_date = '2024-03-15'
                
                result = self.dashboard.create_dashboard(databricks_data, file_data, launch_date)
                
                assert result == "https://sheets.google.com/dashboard"
                mock_summary.assert_called_once()
                mock_dept.assert_called_once()
                mock_file.assert_called_once()
                mock_charts.assert_called_once()
    
    def test_create_dashboard_with_template(self):
        """Test dashboard creation with template"""
        mock_template = Mock()
        mock_dashboard = Mock()
        mock_dashboard.url = "https://sheets.google.com/dashboard"
        mock_template.copy.return_value = mock_dashboard
        
        with patch('google_sheets_dashboard.gspread') as mock_gspread:
            mock_gc = Mock()
            mock_gspread.authorize.return_value = mock_gc
            mock_gc.open_by_key.return_value = mock_template
            
            with patch.object(self.dashboard, '_create_summary_sheet') as mock_summary, \
                 patch.object(self.dashboard, '_create_department_sheets') as mock_dept, \
                 patch.object(self.dashboard, '_create_file_data_sheets') as mock_file, \
                 patch.object(self.dashboard, '_create_charts_and_visualizations') as mock_charts:
                
                databricks_data = {'BOM': {'status': 'success', 'data': []}}
                launch_date = '2024-03-15'
                
                result = self.dashboard.create_dashboard(databricks_data, None, launch_date)
                
                assert result == "https://sheets.google.com/dashboard"
                mock_template.copy.assert_called_once_with(title=f"Vehicle Program Dashboard - {launch_date}")
    
    def test_create_dashboard_no_credentials(self):
        """Test dashboard creation without credentials"""
        self.dashboard.creds = None
        
        with pytest.raises(Exception, match="Google credentials not configured"):
            self.dashboard.create_dashboard({}, None, '2024-03-15')
    
    def test_create_dashboard_creation_error(self):
        """Test dashboard creation with error"""
        with patch('google_sheets_dashboard.gspread') as mock_gspread:
            mock_gc = Mock()
            mock_gspread.authorize.return_value = mock_gc
            mock_gc.create.side_effect = Exception("Creation error")
            
            with pytest.raises(Exception, match="Creation error"):
                self.dashboard.create_dashboard({}, None, '2024-03-15')
    
    def test_create_summary_sheet_success(self):
        """Test successful summary sheet creation"""
        mock_dashboard = Mock()
        mock_summary_sheet = Mock()
        mock_dashboard.worksheet.return_value = mock_summary_sheet
        mock_dashboard.worksheets.return_value = [Mock(title='Summary')]
        
        databricks_data = {
            'BOM': {
                'status': 'success',
                'summary': {
                    'total_items': 100,
                    'completed': 75,
                    'pending': 20,
                    'overdue': 5
                }
            },
            'MP': {
                'status': 'success',
                'summary': {
                    'total_items': 50,
                    'completed': 30,
                    'pending': 15,
                    'overdue': 5
                }
            }
        }
        file_data = {'file': 'data'}
        launch_date = '2024-03-15'
        
        with patch.object(self.dashboard, '_format_summary_sheet') as mock_format:
            self.dashboard._create_summary_sheet(mock_dashboard, databricks_data, file_data, launch_date)
            
            # Verify data was written
            mock_summary_sheet.update.assert_called()
            mock_format.assert_called_once_with(mock_summary_sheet)
    
    def test_create_summary_sheet_new_sheet(self):
        """Test summary sheet creation with new sheet"""
        mock_dashboard = Mock()
        mock_summary_sheet = Mock()
        mock_dashboard.worksheet.side_effect = Exception("Sheet not found")
        mock_dashboard.worksheets.return_value = []
        mock_dashboard.add_worksheet.return_value = mock_summary_sheet
        
        databricks_data = {'BOM': {'status': 'success', 'summary': {}}}
        launch_date = '2024-03-15'
        
        with patch.object(self.dashboard, '_format_summary_sheet') as mock_format:
            self.dashboard._create_summary_sheet(mock_dashboard, databricks_data, None, launch_date)
            
            # Verify new sheet was created
            mock_dashboard.add_worksheet.assert_called_once_with(title='Summary', rows=50, cols=20)
            mock_format.assert_called_once_with(mock_summary_sheet)
    
    def test_create_department_sheets_success(self):
        """Test successful department sheets creation"""
        mock_dashboard = Mock()
        mock_dept_sheet = Mock()
        mock_dashboard.add_worksheet.return_value = mock_dept_sheet
        
        databricks_data = {
            'BOM': {
                'status': 'success',
                'data': [
                    {'part_number': 'P001', 'status': 'complete', 'completion_perc': 100},
                    {'part_number': 'P002', 'status': 'pending', 'completion_perc': 50}
                ]
            },
            'MP': {
                'status': 'success',
                'data': [
                    {'part_number': 'P003', 'status': 'complete', 'completion_perc': 100}
                ]
            }
        }
        
        with patch.object(self.dashboard, '_format_department_sheet') as mock_format:
            self.dashboard._create_department_sheets(mock_dashboard, databricks_data)
            
            # Verify sheets were created for each department
            assert mock_dashboard.add_worksheet.call_count == 2
            assert mock_format.call_count == 2
    
    def test_create_department_sheets_no_data(self):
        """Test department sheets creation with no data"""
        mock_dashboard = Mock()
        databricks_data = {}
        
        with patch.object(self.dashboard, '_format_department_sheet') as mock_format:
            self.dashboard._create_department_sheets(mock_dashboard, databricks_data)
            
            # Should not create any sheets
            mock_dashboard.add_worksheet.assert_not_called()
            mock_format.assert_not_called()
    
    def test_create_file_data_sheets_with_data(self):
        """Test file data sheets creation with data"""
        mock_dashboard = Mock()
        mock_file_sheet = Mock()
        mock_dashboard.add_worksheet.return_value = mock_file_sheet
        
        file_data = {
            'file_type': 'excel',
            'data': {
                'columns': ['part_number', 'status', 'completion_perc'],
                'rows': [
                    {'part_number': 'P001', 'status': 'complete', 'completion_perc': 100},
                    {'part_number': 'P002', 'status': 'pending', 'completion_perc': 50}
                ]
            }
        }
        
        with patch.object(self.dashboard, '_format_summary_sheet') as mock_format:
            self.dashboard._create_file_data_sheets(mock_dashboard, file_data)
            
            # Verify sheet was created
            mock_dashboard.add_worksheet.assert_called_once_with(title='File Data', rows=100, cols=20)
            mock_format.assert_called_once_with(mock_file_sheet)
    
    def test_create_file_data_sheets_no_data(self):
        """Test file data sheets creation with no data"""
        mock_dashboard = Mock()
        file_data = None
        
        with patch.object(self.dashboard, '_format_summary_sheet') as mock_format:
            self.dashboard._create_file_data_sheets(mock_dashboard, file_data)
            
            # Should not create sheet
            mock_dashboard.add_worksheet.assert_not_called()
            mock_format.assert_not_called()
    
    def test_create_charts_and_visualizations_success(self):
        """Test successful charts and visualizations creation"""
        mock_dashboard = Mock()
        mock_chart_sheet = Mock()
        mock_dashboard.add_worksheet.return_value = mock_chart_sheet
        
        databricks_data = {
            'BOM': {
                'status': 'success',
                'summary': {
                    'total_items': 100,
                    'completed': 75,
                    'pending': 20,
                    'overdue': 5
                }
            }
        }
        file_data = {'file': 'data'}
        
        self.dashboard._create_charts_and_visualizations(mock_dashboard, databricks_data, file_data)
        
        # Verify chart sheet was created
        mock_dashboard.add_worksheet.assert_called_once_with(title='Charts & Visualizations', rows=50, cols=20)
    
    def test_format_summary_sheet(self):
        """Test summary sheet formatting"""
        mock_sheet = Mock()
        
        self.dashboard._format_summary_sheet(mock_sheet)
        
        # Verify formatting was applied
        mock_sheet.format.assert_called()
    
    def test_format_department_sheet(self):
        """Test department sheet formatting"""
        mock_sheet = Mock()
        department = 'BOM'
        
        self.dashboard._format_department_sheet(mock_sheet, department)
        
        # Verify formatting was applied
        mock_sheet.format.assert_called()
    
    def test_update_dashboard_success(self):
        """Test successful dashboard update"""
        dashboard_url = "https://sheets.google.com/dashboard"
        new_data = {'BOM': {'status': 'success', 'data': []}}
        
        with patch('google_sheets_dashboard.gspread') as mock_gspread:
            mock_gc = Mock()
            mock_gspread.authorize.return_value = mock_gc
            mock_dashboard = Mock()
            mock_gc.open_by_url.return_value = mock_dashboard
            
            with patch.object(self.dashboard, '_create_summary_sheet') as mock_summary, \
                 patch.object(self.dashboard, '_create_department_sheets') as mock_dept:
                
                self.dashboard.update_dashboard(dashboard_url, new_data)
                
                # Verify dashboard was opened and updated
                mock_gc.open_by_url.assert_called_once_with(dashboard_url)
                mock_summary.assert_called_once()
                mock_dept.assert_called_once()
    
    def test_update_dashboard_error(self):
        """Test dashboard update with error"""
        dashboard_url = "https://sheets.google.com/dashboard"
        new_data = {'BOM': {'status': 'success', 'data': []}}
        
        with patch('google_sheets_dashboard.gspread') as mock_gspread:
            mock_gc = Mock()
            mock_gspread.authorize.return_value = mock_gc
            mock_gc.open_by_url.side_effect = Exception("Update error")
            
            with pytest.raises(Exception, match="Update error"):
                self.dashboard.update_dashboard(dashboard_url, new_data)
    
    def test_get_sheet_data_success(self):
        """Test successful sheet data retrieval"""
        sheet_url = "https://sheets.google.com/dashboard"
        
        with patch('google_sheets_dashboard.gspread') as mock_gspread:
            mock_gc = Mock()
            mock_gspread.authorize.return_value = mock_gc
            mock_dashboard = Mock()
            mock_gc.open_by_url.return_value = mock_dashboard
            mock_sheet = Mock()
            mock_dashboard.worksheet.return_value = mock_sheet
            mock_sheet.get_all_records.return_value = [
                {'part_number': 'P001', 'status': 'complete'},
                {'part_number': 'P002', 'status': 'pending'}
            ]
            
            result = self.dashboard.get_sheet_data(sheet_url, 'Summary')
            
            assert result is not None
            assert len(result) == 2
            assert result[0]['part_number'] == 'P001'
    
    def test_get_sheet_data_error(self):
        """Test sheet data retrieval with error"""
        sheet_url = "https://sheets.google.com/dashboard"
        
        with patch('google_sheets_dashboard.gspread') as mock_gspread:
            mock_gc = Mock()
            mock_gspread.authorize.return_value = mock_gc
            mock_gc.open_by_url.side_effect = Exception("Data retrieval error")
            
            with pytest.raises(Exception, match="Data retrieval error"):
                self.dashboard.get_sheet_data(sheet_url, 'Summary')
    
    def test_error_handling_comprehensive(self):
        """Test comprehensive error handling"""
        # Test various error scenarios
        error_scenarios = [
            (Exception("General error"), "general"),
            (ConnectionError("Network error"), "network"),
            (ValueError("Invalid data"), "data"),
            (TimeoutError("Timeout"), "timeout")
        ]
        
        for exception, error_type in error_scenarios:
            with patch('google_sheets_dashboard.gspread') as mock_gspread:
                mock_gc = Mock()
                mock_gspread.authorize.return_value = mock_gc
                mock_gc.create.side_effect = exception
                
                with pytest.raises(Exception):
                    self.dashboard.create_dashboard({}, None, '2024-03-15')
    
    def test_performance_metrics(self):
        """Test performance of dashboard operations"""
        import time
        
        mock_dashboard = Mock()
        mock_dashboard.url = "https://sheets.google.com/dashboard"
        
        with patch('google_sheets_dashboard.gspread') as mock_gspread:
            mock_gc = Mock()
            mock_gspread.authorize.return_value = mock_gc
            mock_gc.create.return_value = mock_dashboard
            
            with patch.object(self.dashboard, '_create_summary_sheet'), \
                 patch.object(self.dashboard, '_create_department_sheets'), \
                 patch.object(self.dashboard, '_create_file_data_sheets'), \
                 patch.object(self.dashboard, '_create_charts_and_visualizations'):
                
                databricks_data = {'BOM': {'status': 'success', 'data': []}}
                launch_date = '2024-03-15'
                
                start_time = time.time()
                
                result = self.dashboard.create_dashboard(databricks_data, None, launch_date)
                
                end_time = time.time()
                
                # Verify operation completed in reasonable time
                duration = end_time - start_time
                assert duration < 5.0  # Should complete within 5 seconds
                assert result == "https://sheets.google.com/dashboard"
    
    def test_data_validation(self):
        """Test data validation in dashboard creation"""
        # Test with valid data
        valid_databricks_data = {
            'BOM': {
                'status': 'success',
                'summary': {
                    'total_items': 100,
                    'completed': 75,
                    'pending': 20,
                    'overdue': 5
                },
                'data': [
                    {'part_number': 'P001', 'status': 'complete', 'completion_perc': 100}
                ]
            }
        }
        
        mock_dashboard = Mock()
        mock_dashboard.url = "https://sheets.google.com/dashboard"
        
        with patch('google_sheets_dashboard.gspread') as mock_gspread:
            mock_gc = Mock()
            mock_gspread.authorize.return_value = mock_gc
            mock_gc.create.return_value = mock_dashboard
            
            with patch.object(self.dashboard, '_create_summary_sheet') as mock_summary, \
                 patch.object(self.dashboard, '_create_department_sheets') as mock_dept, \
                 patch.object(self.dashboard, '_create_file_data_sheets') as mock_file, \
                 patch.object(self.dashboard, '_create_charts_and_visualizations') as mock_charts:
                
                result = self.dashboard.create_dashboard(valid_databricks_data, None, '2024-03-15')
                
                assert result == "https://sheets.google.com/dashboard"
                mock_summary.assert_called_once()
                mock_dept.assert_called_once()
                mock_file.assert_called_once()
                mock_charts.assert_called_once()
    
    def test_edge_cases(self):
        """Test edge cases in dashboard operations"""
        # Test with empty data
        empty_databricks_data = {}
        empty_file_data = None
        
        mock_dashboard = Mock()
        mock_dashboard.url = "https://sheets.google.com/dashboard"
        
        with patch('google_sheets_dashboard.gspread') as mock_gspread:
            mock_gc = Mock()
            mock_gspread.authorize.return_value = mock_gc
            mock_gc.create.return_value = mock_dashboard
            
            with patch.object(self.dashboard, '_create_summary_sheet') as mock_summary, \
                 patch.object(self.dashboard, '_create_department_sheets') as mock_dept, \
                 patch.object(self.dashboard, '_create_file_data_sheets') as mock_file, \
                 patch.object(self.dashboard, '_create_charts_and_visualizations') as mock_charts:
                
                result = self.dashboard.create_dashboard(empty_databricks_data, empty_file_data, '2024-03-15')
                
                assert result == "https://sheets.google.com/dashboard"
                mock_summary.assert_called_once()
                mock_dept.assert_called_once()
                mock_file.assert_called_once()
                mock_charts.assert_called_once()
        
        # Test with None values
        with patch('google_sheets_dashboard.gspread') as mock_gspread:
            mock_gc = Mock()
            mock_gspread.authorize.return_value = mock_gc
            mock_gc.create.return_value = mock_dashboard
            
            with patch.object(self.dashboard, '_create_summary_sheet') as mock_summary, \
                 patch.object(self.dashboard, '_create_department_sheets') as mock_dept, \
                 patch.object(self.dashboard, '_create_file_data_sheets') as mock_file, \
                 patch.object(self.dashboard, '_create_charts_and_visualizations') as mock_charts:
                
                result = self.dashboard.create_dashboard(None, None, None)
                
                assert result == "https://sheets.google.com/dashboard"
                mock_summary.assert_called_once()
                mock_dept.assert_called_once()
                mock_file.assert_called_once()
                mock_charts.assert_called_once()

if __name__ == '__main__':
    pytest.main([__file__]) 