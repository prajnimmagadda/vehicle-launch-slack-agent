import pytest
import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import tempfile
import json

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from slack_bot import VehicleProgramSlackBot
from openai_client import OpenAIClient
from file_parser import FileParser
from databricks_client import DatabricksClient
from database import DatabaseManager
from monitoring import monitoring_manager
from production_config import ProductionConfig
from start_bot import validate_environment

class TestSlackBotCoverage:
    """Comprehensive tests for Slack bot to improve coverage"""
    
    @patch('slack_bot.SLACK_BOT_TOKEN', 'test_token')
    @patch('slack_bot.SLACK_SIGNING_SECRET', 'test_secret')
    @patch('slack_bot.SLACK_APP_TOKEN', 'test_app_token')
    @patch('slack_bot.OpenAIClient')
    @patch('slack_bot.DatabricksClient')
    @patch('slack_bot.FileParser')
    @patch('slack_bot.GoogleSheetsDashboard')
    def test_initialization_with_mocks(self, mock_dashboard, mock_parser, mock_databricks, mock_openai, mock_app):
        """Test Slack bot initialization with all dependencies mocked"""
        mock_app_instance = Mock()
        mock_app.return_value = mock_app_instance
        
        mock_openai_instance = Mock()
        mock_openai.return_value = mock_openai_instance
        
        mock_databricks_instance = Mock()
        mock_databricks.return_value = mock_databricks_instance
        
        mock_parser_instance = Mock()
        mock_parser.return_value = mock_parser_instance
        
        mock_dashboard_instance = Mock()
        mock_dashboard.return_value = mock_dashboard_instance
        
        bot = VehicleProgramSlackBot()
        
        assert bot.app == mock_app_instance
        assert bot.openai_client == mock_openai_instance
        assert bot.databricks_client == mock_databricks_instance
        assert bot.file_parser == mock_parser_instance
        assert bot.dashboard_creator == mock_dashboard_instance
        assert hasattr(bot, 'user_sessions')
        assert isinstance(bot.user_sessions, dict)
    
    def test_extract_launch_date_edge_cases(self):
        """Test launch date extraction with edge cases"""
        bot = VehicleProgramSlackBot.__new__(VehicleProgramSlackBot)
        
        # Test edge cases
        test_cases = [
            ("", None),
            ("2024-13-45", "2024-13-45"),  # Invalid date but matches pattern
            ("Date: 2024-03-15 and time", "2024-03-15"),
            ("Multiple dates: 2024-01-01 and 2024-02-02", "2024-01-01"),  # First match
            ("No date here", None),
            ("2024-03-15", "2024-03-15"),
            ("Launch on 2024-12-31", "2024-12-31"),
        ]
        
        for text, expected in test_cases:
            result = bot._extract_launch_date(text)
            assert result == expected
    
    @patch('slack_bot.SLACK_BOT_TOKEN', 'test_token')
    @patch('slack_bot.SLACK_SIGNING_SECRET', 'test_secret')
    @patch('slack_bot.SLACK_APP_TOKEN', 'test_app_token')
    @patch('slack_bot.OpenAIClient')
    @patch('slack_bot.DatabricksClient')
    @patch('slack_bot.FileParser')
    @patch('slack_bot.GoogleSheetsDashboard')
    def test_handle_vehicle_program_query_comprehensive(self, mock_dashboard, mock_parser, mock_databricks, mock_openai, mock_app):
        """Test vehicle program query handler with comprehensive mocking"""
        mock_app_instance = Mock()
        mock_app.return_value = mock_app_instance
        
        mock_openai_instance = Mock()
        mock_openai_instance.process_vehicle_program_query.return_value = "Analysis complete"
        mock_openai.return_value = mock_openai_instance
        
        mock_databricks_instance = Mock()
        mock_databricks_instance.query_vehicle_program_status.return_value = {
            'bill_of_material': {'status': 'complete'},
            'master_parts_list': {'status': 'in_progress'}
        }
        mock_databricks_instance.create_visualization.return_value = "https://databricks.com/viz"
        mock_databricks.return_value = mock_databricks_instance
        
        mock_parser_instance = Mock()
        mock_parser.return_value = mock_parser_instance
        
        mock_dashboard_instance = Mock()
        mock_dashboard.return_value = mock_dashboard_instance
        
        bot = VehicleProgramSlackBot()
        
        # Test successful query
        message = {'text': '/vehicle 2024-03-15', 'user': 'test_user'}
        say = Mock()
        
        bot._handle_vehicle_program_query(message, say)
        
        # Verify calls were made
        mock_databricks_instance.query_vehicle_program_status.assert_called_once_with('2024-03-15')
        mock_openai_instance.process_vehicle_program_query.assert_called_once()
        mock_databricks_instance.create_visualization.assert_called_once()
        assert say.call_count >= 1
        
        # Verify session was stored
        assert 'test_user' in bot.user_sessions
        assert bot.user_sessions['test_user']['launch_date'] == '2024-03-15'
    
    @patch('slack_bot.SLACK_BOT_TOKEN', 'test_token')
    @patch('slack_bot.SLACK_SIGNING_SECRET', 'test_secret')
    @patch('slack_bot.SLACK_APP_TOKEN', 'test_app_token')
    @patch('slack_bot.OpenAIClient')
    @patch('slack_bot.DatabricksClient')
    @patch('slack_bot.FileParser')
    @patch('slack_bot.GoogleSheetsDashboard')
    def test_handle_vehicle_program_query_exception_handling(self, mock_dashboard, mock_parser, mock_databricks, mock_openai, mock_app):
        """Test vehicle program query handler with exception handling"""
        mock_app_instance = Mock()
        mock_app.return_value = mock_app_instance
        
        mock_openai_instance = Mock()
        mock_openai_instance.process_vehicle_program_query.side_effect = Exception("Test error")
        mock_openai.return_value = mock_openai_instance
        
        mock_databricks_instance = Mock()
        mock_databricks_instance.query_vehicle_program_status.return_value = {}
        mock_databricks.return_value = mock_databricks_instance
        
        mock_parser_instance = Mock()
        mock_parser.return_value = mock_parser_instance
        
        mock_dashboard_instance = Mock()
        mock_dashboard.return_value = mock_dashboard_instance
        
        bot = VehicleProgramSlackBot()
        
        message = {'text': '/vehicle 2024-03-15', 'user': 'test_user'}
        say = Mock()
        
        bot._handle_vehicle_program_query(message, say)
        
        # Verify error message was sent
        say.assert_called()
        call_args = say.call_args[0][0]
        assert "Error processing your request" in call_args
    
    @patch('slack_bot.SLACK_BOT_TOKEN', 'test_token')
    @patch('slack_bot.SLACK_SIGNING_SECRET', 'test_secret')
    @patch('slack_bot.SLACK_APP_TOKEN', 'test_app_token')
    @patch('slack_bot.OpenAIClient')
    @patch('slack_bot.DatabricksClient')
    @patch('slack_bot.FileParser')
    @patch('slack_bot.GoogleSheetsDashboard')
    def test_handle_upload_request_comprehensive(self, mock_dashboard, mock_parser, mock_databricks, mock_openai, mock_app):
        """Test upload request handler comprehensively"""
        mock_app_instance = Mock()
        mock_app.return_value = mock_app_instance
        
        mock_openai_instance = Mock()
        mock_openai_instance.generate_file_upload_instructions.return_value = "Upload instructions"
        mock_openai.return_value = mock_openai_instance
        
        mock_databricks_instance = Mock()
        mock_databricks.return_value = mock_databricks_instance
        
        mock_parser_instance = Mock()
        mock_parser.return_value = mock_parser_instance
        
        mock_dashboard_instance = Mock()
        mock_dashboard.return_value = mock_dashboard_instance
        
        bot = VehicleProgramSlackBot()
        
        # Test different upload types
        test_cases = [
            ("/upload excel", "excel"),
            ("/upload google", "google_sheets"),
            ("/upload smartsheet", "smartsheet"),
            ("/upload", None),  # Default case
        ]
        
        for text, expected_type in test_cases:
            message = {'text': text}
            say = Mock()
            
            bot._handle_upload_request(message, say)
            
            if expected_type:
                mock_openai_instance.generate_file_upload_instructions.assert_called_with(expected_type)
            else:
                # Should call say with default instructions
                say.assert_called()
    
    @patch('slack_bot.SLACK_BOT_TOKEN', 'test_token')
    @patch('slack_bot.SLACK_SIGNING_SECRET', 'test_secret')
    @patch('slack_bot.SLACK_APP_TOKEN', 'test_app_token')
    @patch('slack_bot.OpenAIClient')
    @patch('slack_bot.DatabricksClient')
    @patch('slack_bot.FileParser')
    @patch('slack_bot.GoogleSheetsDashboard')
    def test_handle_file_upload_comprehensive(self, mock_dashboard, mock_parser, mock_databricks, mock_openai, mock_app):
        """Test file upload handler comprehensively"""
        mock_app_instance = Mock()
        mock_app.return_value = mock_app_instance
        
        mock_openai_instance = Mock()
        mock_openai_instance.analyze_uploaded_data.return_value = "File analysis complete"
        mock_openai.return_value = mock_openai_instance
        
        mock_databricks_instance = Mock()
        mock_databricks.return_value = mock_databricks_instance
        
        mock_parser_instance = Mock()
        mock_parser_instance.validate_file_type.return_value = True
        mock_parser_instance.parse_excel_file.return_value = {'data': 'parsed_data'}
        mock_parser.return_value = mock_parser_instance
        
        mock_dashboard_instance = Mock()
        mock_dashboard.return_value = mock_dashboard_instance
        
        bot = VehicleProgramSlackBot()
        
        # Set up user session
        bot.user_sessions['test_user'] = {
            'launch_date': '2024-03-15',
            'databricks_data': {'test': 'data'},
            'last_query': '2024-03-15'
        }
        
        # Test successful file upload
        event = {
            'file': {'name': 'test.xlsx'},
            'user_id': 'test_user'
        }
        say = Mock()
        
        bot._handle_file_upload(event, say)
        
        # Verify calls were made
        mock_parser_instance.validate_file_type.assert_called_once_with('test.xlsx')
        mock_parser_instance.parse_excel_file.assert_called_once()
        mock_openai_instance.analyze_uploaded_data.assert_called_once()
        assert say.call_count >= 1
        
        # Verify session was updated
        assert 'file_data' in bot.user_sessions['test_user']
    
    @patch('slack_bot.SLACK_BOT_TOKEN', 'test_token')
    @patch('slack_bot.SLACK_SIGNING_SECRET', 'test_secret')
    @patch('slack_bot.SLACK_APP_TOKEN', 'test_app_token')
    @patch('slack_bot.OpenAIClient')
    @patch('slack_bot.DatabricksClient')
    @patch('slack_bot.FileParser')
    @patch('slack_bot.GoogleSheetsDashboard')
    def test_handle_file_upload_no_session(self, mock_dashboard, mock_parser, mock_databricks, mock_openai, mock_app):
        """Test file upload handler when user has no session"""
        mock_app_instance = Mock()
        mock_app.return_value = mock_app_instance
        
        mock_openai_instance = Mock()
        mock_openai.return_value = mock_openai_instance
        
        mock_databricks_instance = Mock()
        mock_databricks.return_value = mock_databricks_instance
        
        mock_parser_instance = Mock()
        mock_parser.return_value = mock_parser_instance
        
        mock_dashboard_instance = Mock()
        mock_dashboard.return_value = mock_dashboard_instance
        
        bot = VehicleProgramSlackBot()
        
        # Test file upload without session
        event = {
            'file': {'name': 'test.xlsx'},
            'user_id': 'unknown_user'
        }
        say = Mock()
        
        bot._handle_file_upload(event, say)
        
        # Verify error message was sent
        say.assert_called_once()
        call_args = say.call_args[0][0]
        assert "Please first query a vehicle program" in call_args
    
    @patch('slack_bot.SLACK_BOT_TOKEN', 'test_token')
    @patch('slack_bot.SLACK_SIGNING_SECRET', 'test_secret')
    @patch('slack_bot.SLACK_APP_TOKEN', 'test_app_token')
    @patch('slack_bot.OpenAIClient')
    @patch('slack_bot.DatabricksClient')
    @patch('slack_bot.FileParser')
    @patch('slack_bot.GoogleSheetsDashboard')
    def test_handle_file_upload_invalid_type(self, mock_dashboard, mock_parser, mock_databricks, mock_openai, mock_app):
        """Test file upload handler with invalid file type"""
        mock_app_instance = Mock()
        mock_app.return_value = mock_app_instance
        
        mock_openai_instance = Mock()
        mock_openai.return_value = mock_openai_instance
        
        mock_databricks_instance = Mock()
        mock_databricks.return_value = mock_databricks_instance
        
        mock_parser_instance = Mock()
        mock_parser_instance.validate_file_type.return_value = False
        mock_parser.return_value = mock_parser_instance
        
        mock_dashboard_instance = Mock()
        mock_dashboard.return_value = mock_dashboard_instance
        
        bot = VehicleProgramSlackBot()
        
        # Set up user session
        bot.user_sessions['test_user'] = {
            'launch_date': '2024-03-15',
            'databricks_data': {'test': 'data'},
            'last_query': '2024-03-15'
        }
        
        # Test invalid file type
        event = {
            'file': {'name': 'test.txt'},
            'user_id': 'test_user'
        }
        say = Mock()
        
        bot._handle_file_upload(event, say)
        
        # Verify error message was sent
        say.assert_called_once()
        call_args = say.call_args[0][0]
        assert "Unsupported file type" in call_args
    
    @patch('slack_bot.SLACK_BOT_TOKEN', 'test_token')
    @patch('slack_bot.SLACK_SIGNING_SECRET', 'test_secret')
    @patch('slack_bot.SLACK_APP_TOKEN', 'test_app_token')
    @patch('slack_bot.OpenAIClient')
    @patch('slack_bot.DatabricksClient')
    @patch('slack_bot.FileParser')
    @patch('slack_bot.GoogleSheetsDashboard')
    def test_handle_dashboard_request_comprehensive(self, mock_dashboard, mock_parser, mock_databricks, mock_openai, mock_app):
        """Test dashboard request handler comprehensively"""
        mock_app_instance = Mock()
        mock_app.return_value = mock_app_instance
        
        mock_openai_instance = Mock()
        mock_openai.return_value = mock_openai_instance
        
        mock_databricks_instance = Mock()
        mock_databricks.return_value = mock_databricks_instance
        
        mock_parser_instance = Mock()
        mock_parser.return_value = mock_parser_instance
        
        mock_dashboard_instance = Mock()
        mock_dashboard_instance.create_dashboard.return_value = "https://sheets.google.com/dashboard"
        mock_dashboard.return_value = mock_dashboard_instance
        
        bot = VehicleProgramSlackBot()
        
        # Set up user session
        bot.user_sessions['test_user'] = {
            'launch_date': '2024-03-15',
            'databricks_data': {'test': 'data'},
            'file_data': {'uploaded': 'data'},
            'last_query': '2024-03-15'
        }
        
        # Test dashboard creation
        message = {'user': 'test_user'}
        say = Mock()
        
        bot._handle_dashboard_request(message, say)
        
        # Verify dashboard was created
        mock_dashboard_instance.create_dashboard.assert_called_once_with(
            databricks_data={'test': 'data'},
            file_data={'uploaded': 'data'},
            launch_date='2024-03-15'
        )
        assert say.call_count >= 1
    
    @patch('slack_bot.SLACK_BOT_TOKEN', 'test_token')
    @patch('slack_bot.SLACK_SIGNING_SECRET', 'test_secret')
    @patch('slack_bot.SLACK_APP_TOKEN', 'test_app_token')
    @patch('slack_bot.OpenAIClient')
    @patch('slack_bot.DatabricksClient')
    @patch('slack_bot.FileParser')
    @patch('slack_bot.GoogleSheetsDashboard')
    def test_handle_dashboard_request_no_session(self, mock_dashboard, mock_parser, mock_databricks, mock_openai, mock_app):
        """Test dashboard request handler when user has no session"""
        mock_app_instance = Mock()
        mock_app.return_value = mock_app_instance
        
        mock_openai_instance = Mock()
        mock_openai.return_value = mock_openai_instance
        
        mock_databricks_instance = Mock()
        mock_databricks.return_value = mock_databricks_instance
        
        mock_parser_instance = Mock()
        mock_parser.return_value = mock_parser_instance
        
        mock_dashboard_instance = Mock()
        mock_dashboard.return_value = mock_dashboard_instance
        
        bot = VehicleProgramSlackBot()
        
        # Test dashboard request without session
        message = {'user': 'unknown_user'}
        say = Mock()
        
        bot._handle_dashboard_request(message, say)
        
        # Verify error message was sent
        say.assert_called_once()
        call_args = say.call_args[0][0]
        assert "Please first query a vehicle program" in call_args
    
    @patch('slack_bot.SLACK_BOT_TOKEN', 'test_token')
    @patch('slack_bot.SLACK_SIGNING_SECRET', 'test_secret')
    @patch('slack_bot.SLACK_APP_TOKEN', 'test_app_token')
    @patch('slack_bot.OpenAIClient')
    @patch('slack_bot.DatabricksClient')
    @patch('slack_bot.FileParser')
    @patch('slack_bot.GoogleSheetsDashboard')
    def test_handle_help_request(self, mock_dashboard, mock_parser, mock_databricks, mock_openai, mock_app):
        """Test help request handler"""
        mock_app_instance = Mock()
        mock_app.return_value = mock_app_instance
        
        mock_openai_instance = Mock()
        mock_openai.return_value = mock_openai_instance
        
        mock_databricks_instance = Mock()
        mock_databricks.return_value = mock_databricks_instance
        
        mock_parser_instance = Mock()
        mock_parser.return_value = mock_parser_instance
        
        mock_dashboard_instance = Mock()
        mock_dashboard.return_value = mock_dashboard_instance
        
        bot = VehicleProgramSlackBot()
        
        message = {'user': 'test_user'}
        say = Mock()
        
        bot._handle_help_request(message, say)
        
        # Verify help message was sent
        say.assert_called_once()
        call_args = say.call_args[0][0]
        assert "Vehicle Program Slack Bot - Help" in call_args
        assert "/vehicle" in call_args
        assert "/upload" in call_args
        assert "/dashboard" in call_args
    
    @patch('slack_bot.SLACK_BOT_TOKEN', 'test_token')
    @patch('slack_bot.SLACK_SIGNING_SECRET', 'test_secret')
    @patch('slack_bot.SLACK_APP_TOKEN', 'test_app_token')
    @patch('slack_bot.OpenAIClient')
    @patch('slack_bot.DatabricksClient')
    @patch('slack_bot.FileParser')
    @patch('slack_bot.GoogleSheetsDashboard')
    @patch('slack_bot.SocketModeHandler')
    def test_start_method_success(self, mock_handler, mock_dashboard, mock_parser, mock_databricks, mock_openai, mock_app):
        """Test bot start method success"""
        mock_app_instance = Mock()
        mock_app.return_value = mock_app_instance
        
        mock_openai_instance = Mock()
        mock_openai.return_value = mock_openai_instance
        
        mock_databricks_instance = Mock()
        mock_databricks.return_value = mock_databricks_instance
        
        mock_parser_instance = Mock()
        mock_parser.return_value = mock_parser_instance
        
        mock_dashboard_instance = Mock()
        mock_dashboard.return_value = mock_dashboard_instance
        
        mock_handler_instance = Mock()
        mock_handler.return_value = mock_handler_instance
        
        bot = VehicleProgramSlackBot()
        
        bot.start()
        
        # Verify handler was created and started
        mock_handler.assert_called_once_with(mock_app_instance, 'test_app_token')
        mock_handler_instance.start.assert_called_once()
    
    @patch('slack_bot.SLACK_BOT_TOKEN', 'test_token')
    @patch('slack_bot.SLACK_SIGNING_SECRET', 'test_secret')
    @patch('slack_bot.SLACK_APP_TOKEN', 'test_app_token')
    @patch('slack_bot.OpenAIClient')
    @patch('slack_bot.DatabricksClient')
    @patch('slack_bot.FileParser')
    @patch('slack_bot.GoogleSheetsDashboard')
    @patch('slack_bot.SocketModeHandler')
    def test_start_method_exception(self, mock_handler, mock_dashboard, mock_parser, mock_databricks, mock_openai, mock_app):
        """Test bot start method with exception"""
        mock_app_instance = Mock()
        mock_app.return_value = mock_app_instance
        
        mock_openai_instance = Mock()
        mock_openai.return_value = mock_openai_instance
        
        mock_databricks_instance = Mock()
        mock_databricks.return_value = mock_databricks_instance
        
        mock_parser_instance = Mock()
        mock_parser.return_value = mock_parser_instance
        
        mock_dashboard_instance = Mock()
        mock_dashboard.return_value = mock_dashboard_instance
        
        mock_handler.side_effect = Exception("Startup error")
        
        bot = VehicleProgramSlackBot()
        
        with pytest.raises(Exception):
            bot.start()

class TestOpenAIClientCoverage:
    """Comprehensive tests for OpenAI client to improve coverage"""
    
    @patch('openai_client.OPENAI_API_KEY', 'test-key')
    def test_openai_client_initialization(self):
        """Test OpenAI client initialization"""
        client = OpenAIClient()
        assert client.api_key == 'test-key'
        assert client.client is None  # No real API key
    
    @patch('openai_client.OPENAI_API_KEY', 'sk-real-key')
    @patch('openai_client.openai.OpenAI')
    def test_openai_client_with_real_key(self, mock_openai):
        """Test OpenAI client with real API key"""
        mock_client = Mock()
        mock_openai.return_value = mock_client
        
        client = OpenAIClient()
        assert client.client == mock_client
    
    @patch('openai_client.OPENAI_API_KEY', 'test-key')
    def test_get_system_prompt(self):
        """Test system prompt generation"""
        client = OpenAIClient()
        prompt = client._get_system_prompt()
        assert "vehicle program" in prompt.lower()
        assert "analysis" in prompt.lower()
    
    @patch('openai_client.OPENAI_API_KEY', 'test-key')
    def test_create_analysis_prompt(self):
        """Test analysis prompt creation"""
        client = OpenAIClient()
        launch_date = "2024-03-15"
        databricks_data = {"test": "data"}
        
        prompt = client._create_analysis_prompt(launch_date, databricks_data)
        assert launch_date in prompt
        assert "test" in prompt
    
    @patch('openai_client.OPENAI_API_KEY', 'test-key')
    def test_create_recommendation_prompt(self):
        """Test recommendation prompt creation"""
        client = OpenAIClient()
        analysis_data = {"status": "incomplete", "issues": ["missing parts"]}
        
        prompt = client._create_recommendation_prompt(analysis_data)
        assert "recommendations" in prompt.lower()
        assert "missing parts" in prompt
    
    @patch('openai_client.OPENAI_API_KEY', 'test-key')
    def test_create_file_analysis_prompt(self):
        """Test file analysis prompt creation"""
        client = OpenAIClient()
        file_data = {"columns": ["part_id"], "data": [{"part_id": "P001"}]}
        
        prompt = client._create_file_analysis_prompt(file_data)
        assert "file data" in prompt.lower()
        assert "P001" in prompt
    
    @patch('openai_client.OPENAI_API_KEY', 'test-key')
    def test_create_upload_prompt(self):
        """Test upload prompt creation"""
        client = OpenAIClient()
        missing_data = {"departments": ["BOM", "MPL"]}
        
        prompt = client._create_upload_prompt(missing_data)
        assert "upload" in prompt.lower()
        assert "BOM" in prompt
    
    @patch('openai_client.OPENAI_API_KEY', 'test-key')
    def test_create_combined_analysis_prompt(self):
        """Test combined analysis prompt creation"""
        client = OpenAIClient()
        databricks_data = {"bom": {"status": "complete"}}
        file_data = {"columns": ["part_id"], "data": []}
        
        prompt = client._create_combined_analysis_prompt(databricks_data, file_data)
        assert "combined" in prompt.lower()
        assert "complete" in prompt
    
    @patch('openai_client.OPENAI_API_KEY', 'test-key')
    def test_validate_response(self):
        """Test response validation"""
        client = OpenAIClient()
        
        # Test valid response
        valid_response = "This is a valid analysis response."
        result = client._validate_response(valid_response)
        assert result == valid_response
        
        # Test empty response
        empty_response = ""
        result = client._validate_response(empty_response)
        assert "No response received" in result
        
        # Test None response
        result = client._validate_response(None)
        assert "No response received" in result

class TestFileParserCoverage:
    """Comprehensive tests for file parser to improve coverage"""
    
    def test_parse_google_sheet(self):
        """Test Google Sheets parsing"""
        parser = FileParser()
        
        # Mock Google Sheets API response
        mock_sheet_data = {
            'values': [
                ['part_id', 'description', 'status'],
                ['P001', 'Engine Block', 'complete'],
                ['P002', 'Transmission', 'in_progress']
            ]
        }
        
        with patch.object(parser, '_get_google_sheet_data', return_value=mock_sheet_data):
            result = parser.parse_google_sheet('test_sheet_id')
            
            assert 'columns' in result
            assert 'data' in result
            assert result['columns'] == ['part_id', 'description', 'status']
            assert len(result['data']) == 2
    
    def test_parse_smartsheet(self):
        """Test Smartsheet parsing"""
        parser = FileParser()
        
        # Mock Smartsheet API response
        mock_sheet_data = {
            'rows': [
                {'cells': [{'value': 'P001'}, {'value': 'Engine Block'}, {'value': 'complete'}]},
                {'cells': [{'value': 'P002'}, {'value': 'Transmission'}, {'value': 'in_progress'}]}
            ]
        }
        
        with patch.object(parser, '_get_smartsheet_data', return_value=mock_sheet_data):
            result = parser.parse_smartsheet('test_sheet_id')
            
            assert 'columns' in result
            assert 'data' in result
            assert len(result['data']) == 2
    
    def test_generate_summary(self):
        """Test summary generation"""
        parser = FileParser()
        
        data = {
            'columns': ['part_id', 'status', 'completion_perc'],
            'data': [
                {'part_id': 'P001', 'status': 'complete', 'completion_perc': 100},
                {'part_id': 'P002', 'status': 'in_progress', 'completion_perc': 75}
            ]
        }
        
        summary = parser.generate_summary(data)
        
        assert 'total_parts' in summary
        assert 'completion_percentages' in summary
        assert 'departments_found' in summary
        assert summary['total_parts'] == 2

class TestDatabaseCoverage:
    """Comprehensive tests for database manager to improve coverage"""
    
    def test_database_manager_initialization(self):
        """Test database manager initialization"""
        db_manager = DatabaseManager()
        assert db_manager.engine is None  # No DATABASE_URL in test environment
    
    def test_health_check_no_database(self):
        """Test health check when no database is available"""
        db_manager = DatabaseManager()
        health = db_manager.health_check()
        assert health['status'] == 'unavailable'
        assert 'No database connection' in health['message']
    
    def test_get_session_no_database(self):
        """Test getting session when no database is available"""
        db_manager = DatabaseManager()
        session = db_manager.get_session()
        assert session is None
    
    def test_save_command_log_no_database(self):
        """Test saving command log when no database is available"""
        db_manager = DatabaseManager()
        result = db_manager.save_command_log('test_command', 'test_user', True, 1.0)
        assert result is None
    
    def test_save_error_log_no_database(self):
        """Test saving error log when no database is available"""
        db_manager = DatabaseManager()
        result = db_manager.save_error_log('test_error', 'Test error message')
        assert result is None
    
    def test_get_command_stats_no_database(self):
        """Test getting command stats when no database is available"""
        db_manager = DatabaseManager()
        stats = db_manager.get_command_stats()
        assert stats == {}
    
    def test_get_error_stats_no_database(self):
        """Test getting error stats when no database is available"""
        db_manager = DatabaseManager()
        stats = db_manager.get_error_stats()
        assert stats == {}
    
    def test_cleanup_old_logs_no_database(self):
        """Test cleanup when no database is available"""
        db_manager = DatabaseManager()
        result = db_manager.cleanup_old_logs()
        assert result is None

class TestMonitoringCoverage:
    """Comprehensive tests for monitoring manager to improve coverage"""
    
    def test_monitoring_manager_exists(self):
        """Test that monitoring manager exists"""
        assert monitoring_manager is not None
        assert hasattr(monitoring_manager, 'start_time')
    
    def test_monitoring_get_stats(self):
        """Test getting monitoring stats"""
        # Reset stats for testing
        monitoring_manager.reset_metrics()
        
        stats = monitoring_manager.get_stats()
        assert 'total_commands' in stats
        assert 'total_errors' in stats
        assert 'uptime' in stats
    
    def test_monitoring_get_metrics(self):
        """Test getting monitoring metrics"""
        metrics = monitoring_manager.get_metrics()
        assert isinstance(metrics, dict)
        assert 'commands_processed' in metrics
        assert 'errors_encountered' in metrics

class TestIntegrationCoverage:
    """Integration tests to improve coverage"""
    
    def test_monitoring_integration(self):
        """Test monitoring integration"""
        # Reset metrics
        monitoring_manager.reset_metrics()
        
        # Track some commands
        monitoring_manager.track_command('test_command', True, 1.0)
        monitoring_manager.track_command('test_command2', False, 2.0)
        monitoring_manager.track_error('test_error', 'Test error message')
        
        # Get stats
        stats = monitoring_manager.get_stats()
        assert stats['total_commands'] == 2
        assert stats['total_errors'] == 1
    
    def test_file_parser_integration(self):
        """Test file parser integration"""
        parser = FileParser()
        
        # Test file type validation
        assert parser.validate_file_type('test.xlsx')
        assert parser.validate_file_type('test.xls')
        assert parser.validate_file_type('test.csv')
        assert not parser.validate_file_type('test.txt')
        assert not parser.validate_file_type('test.pdf')
    
    def test_openai_client_integration(self):
        """Test OpenAI client integration"""
        client = OpenAIClient()
        
        # Test with no client (test environment)
        result = client.process_vehicle_program_query('2024-03-15', {})
        assert "OpenAI client not configured" in result

class TestErrorHandlingCoverage:
    """Error handling tests to improve coverage"""
    
    def test_file_parser_error_handling(self):
        """Test file parser error handling"""
        parser = FileParser()
        
        # Test with invalid file type
        with pytest.raises(ValueError):
            parser.parse_excel_file(b"invalid data", "test.txt")
    
    def test_openai_client_error_handling(self):
        """Test OpenAI client error handling"""
        client = OpenAIClient()
        
        # Test analyze_program_status with no client
        result = client.analyze_program_status({}, '2024-03-15')
        assert "encountered an error" in result

class TestEdgeCasesCoverage:
    """Edge case tests to improve coverage"""
    
    def test_empty_data_handling(self):
        """Test handling of empty data"""
        parser = FileParser()
        
        empty_data = {
            'columns': [],
            'data': []
        }
        
        summary = parser.generate_summary(empty_data)
        assert summary['total_parts'] == 0
        assert len(summary['completion_percentages']) == 0
    
    def test_none_values_handling(self):
        """Test handling of None values"""
        client = OpenAIClient()
        
        # Test with None values
        result = client._validate_response(None)
        assert "No response received" in result
    
    def test_large_data_handling(self):
        """Test handling of large data sets"""
        parser = FileParser()
        
        # Create large dataset
        large_data = {
            'columns': ['part_id', 'status'],
            'data': [{'part_id': f'P{i:03d}', 'status': 'complete'} for i in range(1000)]
        }
        
        summary = parser.generate_summary(large_data)
        assert summary['total_parts'] == 1000

if __name__ == '__main__':
    pytest.main([__file__]) 