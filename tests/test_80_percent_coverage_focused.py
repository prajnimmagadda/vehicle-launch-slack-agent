import pytest
import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import json
from datetime import datetime, timedelta
from io import BytesIO

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from production_config import ProductionConfig
from database import DatabaseManager, UserSession, BotMetrics
from monitoring import monitoring_manager, MonitoringManager
from slack_bot import VehicleProgramSlackBot
from production_slack_bot import ProductionSlackBot
from file_parser import FileParser
from openai_client import OpenAIClient
from databricks_client import DatabricksClient
from google_sheets_dashboard import GoogleSheetsDashboard

class TestDatabaseManagerFocused:
    """Focused tests for DatabaseManager to improve coverage"""
    
    def test_store_user_session_with_error(self):
        """Test storing user session with database error"""
        db_manager = DatabaseManager()
        
        # Mock session to raise exception
        with patch.object(db_manager, 'get_session') as mock_session:
            mock_session.return_value.__enter__.side_effect = Exception("Database error")
            
            # Should not raise exception, should handle gracefully
            result = db_manager.store_user_session("U123", "2024-03-15", {"data": "test"})
            assert result is None
    
    def test_get_user_session_with_file_data(self):
        """Test getting user session with file data"""
        db_manager = DatabaseManager()
        
        # Mock session with data
        mock_session = Mock()
        mock_user_session = Mock()
        mock_user_session.user_id = "U123"
        mock_user_session.launch_date = "2024-03-15"
        mock_user_session.databricks_data = '{"status": "test"}'
        mock_user_session.file_data = '{"file": "test.xlsx"}'
        mock_user_session.created_at = datetime.now()
        mock_user_session.updated_at = datetime.now()
        mock_user_session.is_active = True
        
        mock_session.query.return_value.filter.return_value.first.return_value = mock_user_session
        
        with patch.object(db_manager, 'get_session') as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session
            
            result = db_manager.get_user_session("U123")
            assert result is not None
            assert result['user_id'] == "U123"
            assert result['file_data'] == {"file": "test.xlsx"}
    
    def test_get_metrics_summary_with_data(self):
        """Test getting metrics summary with actual data"""
        db_manager = DatabaseManager()
        
        # Mock session with metrics data
        mock_session = Mock()
        mock_metrics = [
            Mock(command="vehicle_query", success=True, response_time=1000),
            Mock(command="file_upload", success=True, response_time=2000),
            Mock(command="vehicle_query", success=False, response_time=500)
        ]
        
        mock_session.query.return_value.filter.return_value.all.return_value = mock_metrics
        
        with patch.object(db_manager, 'get_session') as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session
            
            result = db_manager.get_metrics_summary(7)
            assert 'total_commands' in result
            assert result['total_commands'] == 3
    
    def test_cleanup_old_data_with_actual_data(self):
        """Test cleanup with actual data to delete"""
        db_manager = DatabaseManager()
        
        # Mock session with old data
        mock_session = Mock()
        old_date = datetime.now() - timedelta(days=35)
        mock_old_sessions = [
            Mock(created_at=old_date),
            Mock(created_at=old_date),
            Mock(created_at=old_date),
            Mock(created_at=old_date)
        ]
        
        mock_session.query.return_value.filter.return_value.all.return_value = mock_old_sessions
        
        with patch.object(db_manager, 'get_session') as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session
            
            result = db_manager.cleanup_old_data()
            assert result == 4  # Should delete 4 old sessions
    
    def test_health_check_healthy(self):
        """Test health check when database is healthy"""
        db_manager = DatabaseManager()
        
        # Mock successful connection
        with patch.object(db_manager, 'get_session') as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = Mock()
            
            result = db_manager.health_check()
            assert result['status'] == 'healthy'
            assert 'uptime' in result['message']
    
    def test_health_check_no_database(self):
        """Test health check when no database is configured"""
        db_manager = DatabaseManager()
        db_manager.engine = None
        
        result = db_manager.health_check()
        assert result['status'] == 'unavailable'
        assert 'not configured' in result['message']

class TestMonitoringManagerFocused:
    """Focused tests for MonitoringManager to improve coverage"""
    
    def test_track_command_with_failure(self):
        """Test tracking command with failure"""
        monitoring_manager.track_command('test_command', False, 2.5, 'U123')
        
        # Verify command was tracked
        assert 'test_command' in monitoring_manager.command_counter
        assert monitoring_manager.command_counter['test_command']['failure'] >= 1
    
    def test_track_error_with_message(self):
        """Test tracking error with message"""
        monitoring_manager.track_error('test_error', 'Test error message', 'U123')
        
        # Verify error was tracked
        assert 'test_error' in monitoring_manager.error_counter
    
    def test_get_metrics_with_data(self):
        """Test getting metrics with actual data"""
        # Add some test data
        monitoring_manager.track_command('test_cmd', True, 1.0)
        monitoring_manager.track_command('test_cmd', False, 2.0)
        monitoring_manager.track_error('test_error', 'Error message')
        
        metrics = monitoring_manager.get_metrics()
        assert 'commands' in metrics
        assert 'errors' in metrics
        assert 'metrics_server_status' in metrics
    
    def test_get_metrics_summary(self):
        """Test getting metrics summary"""
        # Add test data
        monitoring_manager.track_command('test_cmd', True, 1.0)
        monitoring_manager.track_command('test_cmd', True, 2.0)
        
        summary = monitoring_manager.get_metrics_summary()
        assert 'total_commands' in summary
        assert 'success_rate' in summary
        assert 'uptime_hours' in summary
    
    def test_reset_metrics(self):
        """Test resetting metrics"""
        # Add some data first
        monitoring_manager.track_command('test_cmd', True, 1.0)
        monitoring_manager.track_error('test_error', 'Error')
        
        # Reset metrics
        monitoring_manager.reset_metrics()
        
        # Verify reset
        assert len(monitoring_manager.command_counter) == 0
        assert len(monitoring_manager.error_counter) == 0

class TestSlackBotFocused:
    """Focused tests for SlackBot to improve coverage"""
    
    @patch('slack_bolt.App')
    def test_extract_launch_date_with_invalid_date(self, mock_app):
        """Test launch date extraction with invalid date"""
        # Mock the App to avoid real Slack API calls
        mock_app.return_value = Mock()
        
        # Create bot instance without real Slack initialization
        bot = VehicleProgramSlackBot.__new__(VehicleProgramSlackBot)
        
        # Test invalid date format
        text = "Check vehicle program for 2024-13-45"
        date = bot._extract_launch_date(text)
        assert date is None  # Should return None for invalid date
    
    @patch('slack_bolt.App')
    def test_handle_vehicle_program_query_without_date(self, mock_app):
        """Test vehicle program query without date"""
        # Mock the App to avoid real Slack API calls
        mock_app.return_value = Mock()
        
        # Create bot instance without real Slack initialization
        bot = VehicleProgramSlackBot.__new__(VehicleProgramSlackBot)
        mock_say = Mock()
        message = {'user': 'U123', 'text': '/vehicle'}
        
        bot._handle_vehicle_program_query(message, mock_say)
        
        # Should call say with help message
        mock_say.assert_called_once()
        call_args = mock_say.call_args[0][0]
        assert "Please provide a launch date" in call_args
    
    @patch('slack_bolt.App')
    def test_handle_file_upload_with_valid_file(self, mock_app):
        """Test file upload with valid file"""
        # Mock the App to avoid real Slack API calls
        mock_app.return_value = Mock()
        
        # Create bot instance without real Slack initialization
        bot = VehicleProgramSlackBot.__new__(VehicleProgramSlackBot)
        mock_say = Mock()
        
        # Mock file event
        event = {
            'files': [{'id': 'F123', 'name': 'test.xlsx', 'url_private': 'http://test.com/file'}],
            'user': 'U123'
        }
        
        # Mock file parser
        with patch.object(bot, 'file_parser') as mock_file_parser:
            mock_file_parser.parse_excel_file.return_value = {'status': 'success', 'data': {'test': 'data'}}
            
            bot._handle_file_upload(event, mock_say)
            
            # Verify parse_excel_file was called
            mock_file_parser.parse_excel_file.assert_called_once()
    
    @patch('slack_bolt.App')
    def test_handle_file_upload_with_invalid_file(self, mock_app):
        """Test file upload with invalid file type"""
        # Mock the App to avoid real Slack API calls
        mock_app.return_value = Mock()
        
        # Create bot instance without real Slack initialization
        bot = VehicleProgramSlackBot.__new__(VehicleProgramSlackBot)
        mock_say = Mock()
        
        # Mock file event with invalid file
        event = {
            'files': [{'id': 'F123', 'name': 'test.txt', 'url_private': 'http://test.com/file'}],
            'user': 'U123'
        }
        
        bot._handle_file_upload(event, mock_say)
        
        # Should call say with error message
        mock_say.assert_called_once()
        call_args = mock_say.call_args[0][0]
        assert "unsupported file type" in call_args.lower()
    
    @patch('slack_bolt.App')
    def test_handle_dashboard_request_with_date(self, mock_app):
        """Test dashboard request with date"""
        # Mock the App to avoid real Slack API calls
        mock_app.return_value = Mock()
        
        # Create bot instance without real Slack initialization
        bot = VehicleProgramSlackBot.__new__(VehicleProgramSlackBot)
        mock_say = Mock()
        message = {'user': 'U123', 'text': '/dashboard 2024-03-15'}
        
        # Mock dashboard creator
        with patch.object(bot, 'dashboard_creator') as mock_dashboard:
            mock_dashboard.create_dashboard.return_value = 'https://sheets.google.com/dashboard'
            
            bot._handle_dashboard_request(message, mock_say)
            
            # Verify create_dashboard was called
            mock_dashboard.create_dashboard.assert_called_once()
    
    @patch('slack_bolt.App')
    def test_handle_dashboard_request_without_date(self, mock_app):
        """Test dashboard request without date"""
        # Mock the App to avoid real Slack API calls
        mock_app.return_value = Mock()
        
        # Create bot instance without real Slack initialization
        bot = VehicleProgramSlackBot.__new__(VehicleProgramSlackBot)
        mock_say = Mock()
        message = {'user': 'U123', 'text': '/dashboard'}
        
        bot._handle_dashboard_request(message, mock_say)
        
        # Should call say with help message
        mock_say.assert_called_once()
        call_args = mock_say.call_args[0][0]
        assert "Please provide a launch date" in call_args
    
    @patch('slack_bolt.App')
    def test_handle_help_request(self, mock_app):
        """Test help request handler"""
        # Mock the App to avoid real Slack API calls
        mock_app.return_value = Mock()
        
        # Create bot instance without real Slack initialization
        bot = VehicleProgramSlackBot.__new__(VehicleProgramSlackBot)
        mock_say = Mock()
        message = {'user': 'U123', 'text': '/help'}
        
        bot._handle_help_request(message, mock_say)
        
        # Should call say with help message
        mock_say.assert_called_once()
        call_args = mock_say.call_args[0][0]
        assert "Available commands" in call_args

class TestGoogleSheetsDashboardFocused:
    """Focused tests for GoogleSheetsDashboard to improve coverage"""
    
    @patch('gspread.authorize')
    def test_create_dashboard_success(self, mock_authorize):
        """Test successful dashboard creation"""
        dashboard = GoogleSheetsDashboard()
        
        # Mock gspread response
        mock_spreadsheet = Mock()
        mock_spreadsheet.url = 'https://sheets.google.com/dashboard'
        mock_authorize.return_value.open_by_key.return_value.copy.return_value = mock_spreadsheet
        
        result = dashboard.create_dashboard("2024-03-15")
        assert result == 'https://sheets.google.com/dashboard'
    
    @patch('gspread.authorize')
    def test_create_department_sheets_success(self, mock_authorize):
        """Test successful department sheets creation"""
        dashboard = GoogleSheetsDashboard()
        
        # Mock gspread response
        mock_worksheet = Mock()
        mock_authorize.return_value.open_by_key.return_value.worksheet.return_value = mock_worksheet
        
        departments = ['BOM', 'MP', 'MFE']
        result = dashboard.create_department_sheets(departments)
        assert result is True
    
    @patch('gspread.authorize')
    def test_create_file_data_sheets_with_data(self, mock_authorize):
        """Test creating file data sheets with actual data"""
        dashboard = GoogleSheetsDashboard()
        
        # Mock worksheet
        mock_worksheet = Mock()
        mock_authorize.return_value.open_by_key.return_value.add_worksheet.return_value = mock_worksheet
        
        file_data = {'columns': ['A', 'B'], 'data': [{'A': '1', 'B': '2'}]}
        result = dashboard.create_file_data_sheets(file_data)
        assert result is True
    
    @patch('gspread.authorize')
    def test_create_charts_and_visualizations_success(self, mock_authorize):
        """Test creating charts and visualizations"""
        dashboard = GoogleSheetsDashboard()
        
        # Mock worksheet
        mock_worksheet = Mock()
        mock_authorize.return_value.open_by_key.return_value.add_worksheet.return_value = mock_worksheet
        
        result = dashboard.create_charts_and_visualizations()
        assert result is True
    
    @patch('gspread.authorize')
    def test_format_summary_sheet(self, mock_authorize):
        """Test formatting summary sheet"""
        dashboard = GoogleSheetsDashboard()
        
        # Mock worksheet
        mock_worksheet = Mock()
        mock_authorize.return_value.open_by_key.return_value.worksheet.return_value = mock_worksheet
        
        result = dashboard.format_summary_sheet()
        assert result is True
    
    @patch('gspread.authorize')
    def test_format_department_sheet(self, mock_authorize):
        """Test formatting department sheet"""
        dashboard = GoogleSheetsDashboard()
        
        # Mock worksheet
        mock_worksheet = Mock()
        mock_authorize.return_value.open_by_key.return_value.worksheet.return_value = mock_worksheet
        
        result = dashboard.format_department_sheet('BOM')
        assert result is True
    
    @patch('gspread.authorize')
    def test_update_dashboard_success(self, mock_authorize):
        """Test successful dashboard update"""
        dashboard = GoogleSheetsDashboard()
        
        # Mock gspread response
        mock_spreadsheet = Mock()
        mock_authorize.return_value.open_by_url.return_value = mock_spreadsheet
        
        result = dashboard.update_dashboard('https://sheets.google.com/dashboard', {'new': 'data'})
        assert result is True

class TestFileParserFocused:
    """Focused tests for FileParser to improve coverage"""
    
    def test_parse_excel_file_with_excel(self):
        """Test parsing Excel file"""
        parser = FileParser()
        
        # Create mock Excel file
        mock_file = BytesIO(b'excel_data')
        
        with patch('pandas.read_excel') as mock_read_excel:
            mock_read_excel.return_value = {'Sheet1': Mock()}
            
            result = parser.parse_excel_file(mock_file.read(), 'test.xlsx')
            assert 'file_type' in result
            assert result['file_type'] == 'excel'
    
    def test_parse_google_sheets_with_data(self):
        """Test parsing Google Sheets with data"""
        parser = FileParser()
        
        # Mock Google Sheets response
        with patch('gspread.authorize') as mock_authorize:
            mock_gc = Mock()
            mock_authorize.return_value = mock_gc
            
            mock_spreadsheet = Mock()
            mock_gc.open_by_key.return_value = mock_spreadsheet
            
            mock_worksheet = Mock()
            mock_worksheet.get_all_records.return_value = [{'A': '1', 'B': '2'}]
            mock_worksheet.title = 'Sheet1'
            mock_spreadsheet.worksheets.return_value = [mock_worksheet]
            
            result = parser.parse_google_sheets('test_spreadsheet_id')
            assert 'file_type' in result
            assert result['file_type'] == 'google_sheets'
    
    def test_parse_smartsheet_with_data(self):
        """Test parsing Smartsheet with data"""
        parser = FileParser()
        
        # Mock Smartsheet API response
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = {'data': [{'id': 1, 'name': 'test'}]}
            mock_get.return_value = mock_response
            
            result = parser.parse_smartsheet('test_sheet_id')
            assert 'file_type' in result
            assert result['file_type'] == 'smartsheet'
    
    def test_validate_file_type_with_valid_types(self):
        """Test file type validation with valid types"""
        parser = FileParser()
        
        # Test valid file types
        assert parser.validate_file_type("data.xlsx")
        assert parser.validate_file_type("data.xls")
        assert parser.validate_file_type("data.csv")
        
        # Test invalid file types
        assert not parser.validate_file_type("data.txt")
        assert not parser.validate_file_type("data.pdf")

class TestOpenAIClientFocused:
    """Focused tests for OpenAIClient to improve coverage"""
    
    @patch('openai.OpenAI')
    def test_process_vehicle_program_query_success(self, mock_openai):
        """Test successful vehicle program query processing"""
        client = OpenAIClient()
        
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Analysis complete"
        mock_openai.return_value.chat.completions.create.return_value = mock_response
        
        result = client.process_vehicle_program_query("2024-03-15", {"data": "test"})
        assert result is not None
    
    @patch('openai.OpenAI')
    def test_analyze_program_status_success(self, mock_openai):
        """Test successful program status analysis"""
        client = OpenAIClient()
        
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Analysis complete"
        mock_openai.return_value.chat.completions.create.return_value = mock_response
        
        result = client.analyze_program_status({"data": "test"}, "2024-03-15")
        assert result is not None
    
    @patch('openai.OpenAI')
    def test_generate_recommendations_success(self, mock_openai):
        """Test successful recommendations generation"""
        client = OpenAIClient()
        
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Recommendations: ..."
        mock_openai.return_value.chat.completions.create.return_value = mock_response
        
        result = client.generate_recommendations({"analysis": "test"})
        assert result is not None
    
    @patch('openai.OpenAI')
    def test_analyze_file_data_success(self, mock_openai):
        """Test successful file data analysis"""
        client = OpenAIClient()
        
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "File analysis: ..."
        mock_openai.return_value.chat.completions.create.return_value = mock_response
        
        result = client.analyze_file_data({"data": "test"})
        assert result is not None
    
    def test_validate_response_with_valid_response(self):
        """Test response validation with valid response"""
        client = OpenAIClient()
        
        response = "This is a valid response"
        result = client._validate_response(response)
        assert result == "This is a valid response"
    
    def test_validate_response_with_empty_response(self):
        """Test response validation with empty response"""
        client = OpenAIClient()
        
        response = ""
        with pytest.raises(ValueError, match="Empty response from OpenAI"):
            client._validate_response(response)

class TestDatabricksClientFocused:
    """Focused tests for DatabricksClient to improve coverage"""
    
    @patch('requests.post')
    def test_execute_query_success(self, mock_post):
        """Test successful query execution"""
        client = DatabricksClient()
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'result': {'data': [{'status': 'test'}]}}
        mock_post.return_value = mock_response
        
        result = client.execute_query("SELECT * FROM test")
        assert result is not None
    
    @patch('requests.post')
    def test_execute_query_failure(self, mock_post):
        """Test query execution failure"""
        client = DatabricksClient()
        
        # Mock failed response
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {'error': 'Query failed'}
        mock_post.return_value = mock_response
        
        with pytest.raises(Exception):
            client.execute_query("SELECT * FROM test")
    
    @patch('requests.post')
    def test_query_vehicle_program_status_success(self, mock_post):
        """Test successful vehicle program status query"""
        client = DatabricksClient()
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'result': {'data': [{'department': 'BOM', 'status': 'complete'}]}}
        mock_post.return_value = mock_response
        
        result = client.query_vehicle_program_status("2024-03-15")
        assert result is not None
    
    @patch('plotly.graph_objects.Figure')
    def test_create_visualization_success(self, mock_figure):
        """Test successful visualization creation"""
        client = DatabricksClient()
        
        # Mock plotly
        mock_fig = Mock()
        mock_figure.return_value = mock_fig
        
        result = client.create_visualization([{'data': 'test'}], "2024-03-15")
        assert result is not None

if __name__ == '__main__':
    pytest.main([__file__]) 