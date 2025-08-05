import pytest
import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from slack_bot import VehicleProgramSlackBot

class TestVehicleProgramSlackBot:
    """Test VehicleProgramSlackBot class"""
    
    @patch('slack_bot.SLACK_BOT_TOKEN', 'test_token')
    @patch('slack_bot.SLACK_SIGNING_SECRET', 'test_secret')
    @patch('slack_bot.SLACK_APP_TOKEN', 'test_app_token')
    def test_initialization(self):
        """Test Slack bot initialization"""
        with patch('slack_bot.App') as mock_app:
            mock_app_instance = Mock()
            mock_app.return_value = mock_app_instance
            
            bot = VehicleProgramSlackBot()
            
            assert bot.app == mock_app_instance
            assert bot.databricks_client is not None
            assert bot.openai_client is not None
            assert bot.file_parser is not None
            assert bot.dashboard_creator is not None
            assert hasattr(bot, 'user_sessions')
    
    @patch('slack_bot.SLACK_BOT_TOKEN', 'test_token')
    @patch('slack_bot.SLACK_SIGNING_SECRET', 'test_secret')
    @patch('slack_bot.SLACK_APP_TOKEN', 'test_app_token')
    def test_register_handlers(self):
        """Test that handlers are registered correctly"""
        with patch('slack_bot.App') as mock_app:
            mock_app_instance = Mock()
            mock_app.return_value = mock_app_instance
            
            bot = VehicleProgramSlackBot()
            
            # Verify that message decorators were called
            assert mock_app_instance.message.call_count >= 4  # Should have multiple handlers
            assert mock_app_instance.event.call_count >= 1  # Should have file_shared event
    
    def test_extract_launch_date_valid(self):
        """Test launch date extraction with valid dates"""
        bot = VehicleProgramSlackBot.__new__(VehicleProgramSlackBot)
        
        # Test various date formats
        test_cases = [
            ("Check vehicle program for 2024-03-15", "2024-03-15"),
            ("Vehicle launch on 2024-12-31", "2024-12-31"),
            ("Program status 2024-01-01", "2024-01-01"),
            ("/vehicle 2024-06-15", "2024-06-15"),
        ]
        
        for text, expected in test_cases:
            result = bot._extract_launch_date(text)
            assert result == expected
    
    def test_extract_launch_date_invalid(self):
        """Test launch date extraction with invalid dates"""
        bot = VehicleProgramSlackBot.__new__(VehicleProgramSlackBot)
        
        # Test invalid cases
        test_cases = [
            "Check vehicle program",
            "No date here",
            "Invalid date 2024-13-45",
            "Date 2024/03/15",
            "Date 15-03-2024",
        ]
        
        for text in test_cases:
            result = bot._extract_launch_date(text)
            assert result is None
    
    @patch('slack_bot.SLACK_BOT_TOKEN', 'test_token')
    @patch('slack_bot.SLACK_SIGNING_SECRET', 'test_secret')
    @patch('slack_bot.SLACK_APP_TOKEN', 'test_app_token')
    def test_handle_vehicle_program_query_success(self):
        """Test successful vehicle program query handler"""
        with patch('slack_bot.App') as mock_app:
            mock_app_instance = Mock()
            mock_app.return_value = mock_app_instance
            
            bot = VehicleProgramSlackBot()
            
            # Mock message and say
            message = {'text': '/vehicle 2024-03-15', 'user': 'test_user'}
            say = Mock()
            
            # Mock databricks response
            mock_databricks_instance = Mock()
            mock_databricks_instance.query_vehicle_program_status.return_value = {
                'bill_of_material': {'status': 'complete'},
                'master_parts_list': {'status': 'in_progress'}
            }
            bot.databricks_client = mock_databricks_instance
            
            # Mock OpenAI response
            mock_openai_instance = Mock()
            mock_openai_instance.process_vehicle_program_query.return_value = "Analysis complete"
            bot.openai_client = mock_openai_instance
            
            # Test the handler
            bot._handle_vehicle_program_query(message, say)
            
            # Verify interactions
            mock_databricks_instance.query_vehicle_program_status.assert_called_once_with('2024-03-15')
            mock_openai_instance.process_vehicle_program_query.assert_called_once()
            say.assert_called()
    
    @patch('slack_bot.SLACK_BOT_TOKEN', 'test_token')
    @patch('slack_bot.SLACK_SIGNING_SECRET', 'test_secret')
    @patch('slack_bot.SLACK_APP_TOKEN', 'test_app_token')
    def test_handle_vehicle_program_query_no_date(self):
        """Test vehicle program query handler with no date"""
        with patch('slack_bot.App') as mock_app:
            mock_app_instance = Mock()
            mock_app.return_value = mock_app_instance
            
            bot = VehicleProgramSlackBot()
            
            # Mock message and say
            message = {'text': '/vehicle', 'user': 'test_user'}
            say = Mock()
            
            # Test the handler
            bot._handle_vehicle_program_query(message, say)
            
            # Verify help message was sent
            say.assert_called_once()
            call_args = say.call_args[0][0]
            assert 'YYYY-MM-DD' in call_args
    
    @patch('slack_bot.SLACK_BOT_TOKEN', 'test_token')
    @patch('slack_bot.SLACK_SIGNING_SECRET', 'test_secret')
    @patch('slack_bot.SLACK_APP_TOKEN', 'test_app_token')
    def test_handle_vehicle_program_query_exception(self):
        """Test vehicle program query handler with exception"""
        with patch('slack_bot.App') as mock_app:
            mock_app_instance = Mock()
            mock_app.return_value = mock_app_instance
            
            bot = VehicleProgramSlackBot()
            
            # Mock message and say
            message = {'text': '/vehicle 2024-03-15', 'user': 'test_user'}
            say = Mock()
            
            # Mock databricks to raise exception
            mock_databricks_instance = Mock()
            mock_databricks_instance.query_vehicle_program_status.side_effect = Exception("Database error")
            bot.databricks_client = mock_databricks_instance
            
            # Test the handler
            bot._handle_vehicle_program_query(message, say)
            
            # Verify error message was sent
            say.assert_called()
            call_args = say.call_args[0][0]
            assert 'error' in call_args.lower()
    
    @patch('slack_bot.SLACK_BOT_TOKEN', 'test_token')
    @patch('slack_bot.SLACK_SIGNING_SECRET', 'test_secret')
    @patch('slack_bot.SLACK_APP_TOKEN', 'test_app_token')
    def test_handle_upload_request(self):
        """Test upload request handler"""
        with patch('slack_bot.App') as mock_app:
            mock_app_instance = Mock()
            mock_app.return_value = mock_app_instance
            
            bot = VehicleProgramSlackBot()
            
            # Mock message and say
            message = {'text': '/upload', 'user': 'test_user'}
            say = Mock()
            
            # Test the handler
            bot._handle_upload_request(message, say)
            
            # Verify upload instructions were sent
            say.assert_called_once()
            call_args = say.call_args[0][0]
            assert 'upload' in call_args.lower()
            assert 'excel' in call_args.lower()
    
    @patch('slack_bot.SLACK_BOT_TOKEN', 'test_token')
    @patch('slack_bot.SLACK_SIGNING_SECRET', 'test_secret')
    @patch('slack_bot.SLACK_APP_TOKEN', 'test_app_token')
    def test_handle_file_upload_success(self):
        """Test successful file upload handler"""
        with patch('slack_bot.App') as mock_app:
            mock_app_instance = Mock()
            mock_app.return_value = mock_app_instance
            
            bot = VehicleProgramSlackBot()
            
            # Mock event and say
            event = {
                'file': {
                    'id': 'F123456',
                    'name': 'test_data.xlsx',
                    'url_private': 'https://example.com/file.xlsx'
                },
                'user': 'test_user'
            }
            say = Mock()
            
            # Mock file parser
            mock_file_parser = Mock()
            mock_file_parser.parse_excel_file.return_value = {
                'file_type': 'excel',
                'filename': 'test_data.xlsx',
                'sheets': {'BOM': {'data': 'mock_data'}}
            }
            bot.file_parser = mock_file_parser
            
            # Mock OpenAI
            mock_openai_instance = Mock()
            mock_openai_instance.analyze_file_data.return_value = "File analysis complete"
            bot.openai_client = mock_openai_instance
            
            # Test the handler
            bot._handle_file_upload(event, say)
            
            # Verify file was processed
            mock_file_parser.parse_excel_file.assert_called_once()
            mock_openai_instance.analyze_file_data.assert_called_once()
            say.assert_called()
    
    @patch('slack_bot.SLACK_BOT_TOKEN', 'test_token')
    @patch('slack_bot.SLACK_SIGNING_SECRET', 'test_secret')
    @patch('slack_bot.SLACK_APP_TOKEN', 'test_app_token')
    def test_handle_file_upload_invalid_type(self):
        """Test file upload handler with invalid file type"""
        with patch('slack_bot.App') as mock_app:
            mock_app_instance = Mock()
            mock_app.return_value = mock_app_instance
            
            bot = VehicleProgramSlackBot()
            
            # Mock event and say
            event = {
                'file': {
                    'id': 'F123456',
                    'name': 'test_data.txt',
                    'url_private': 'https://example.com/file.txt'
                },
                'user': 'test_user'
            }
            say = Mock()
            
            # Test the handler
            bot._handle_file_upload(event, say)
            
            # Verify error message was sent
            say.assert_called_once()
            call_args = say.call_args[0][0]
            assert 'supported' in call_args.lower()
    
    @patch('slack_bot.SLACK_BOT_TOKEN', 'test_token')
    @patch('slack_bot.SLACK_SIGNING_SECRET', 'test_secret')
    @patch('slack_bot.SLACK_APP_TOKEN', 'test_app_token')
    def test_handle_dashboard_request_success(self):
        """Test successful dashboard request handler"""
        with patch('slack_bot.App') as mock_app:
            mock_app_instance = Mock()
            mock_app.return_value = mock_app_instance
            
            bot = VehicleProgramSlackBot()
            
            # Mock message and say
            message = {'text': '/dashboard 2024-03-15', 'user': 'test_user'}
            say = Mock()
            
            # Mock databricks response
            mock_databricks_instance = Mock()
            mock_databricks_instance.query_vehicle_program_status.return_value = {
                'bill_of_material': {'status': 'complete'},
                'master_parts_list': {'status': 'in_progress'}
            }
            bot.databricks_client = mock_databricks_instance
            
            # Mock dashboard creator
            mock_dashboard_creator = Mock()
            mock_dashboard_creator.create_dashboard.return_value = "https://docs.google.com/spreadsheets/d/test"
            bot.dashboard_creator = mock_dashboard_creator
            
            # Test the handler
            bot._handle_dashboard_request(message, say)
            
            # Verify dashboard was created
            mock_databricks_instance.query_vehicle_program_status.assert_called_once_with('2024-03-15')
            mock_dashboard_creator.create_dashboard.assert_called_once()
            say.assert_called()
    
    @patch('slack_bot.SLACK_BOT_TOKEN', 'test_token')
    @patch('slack_bot.SLACK_SIGNING_SECRET', 'test_secret')
    @patch('slack_bot.SLACK_APP_TOKEN', 'test_app_token')
    def test_handle_dashboard_request_no_date(self):
        """Test dashboard request handler with no date"""
        with patch('slack_bot.App') as mock_app:
            mock_app_instance = Mock()
            mock_app.return_value = mock_app_instance
            
            bot = VehicleProgramSlackBot()
            
            # Mock message and say
            message = {'text': '/dashboard', 'user': 'test_user'}
            say = Mock()
            
            # Test the handler
            bot._handle_dashboard_request(message, say)
            
            # Verify help message was sent
            say.assert_called_once()
            call_args = say.call_args[0][0]
            assert 'YYYY-MM-DD' in call_args
    
    @patch('slack_bot.SLACK_BOT_TOKEN', 'test_token')
    @patch('slack_bot.SLACK_SIGNING_SECRET', 'test_secret')
    @patch('slack_bot.SLACK_APP_TOKEN', 'test_app_token')
    def test_handle_help_request(self):
        """Test help request handler"""
        with patch('slack_bot.App') as mock_app:
            mock_app_instance = Mock()
            mock_app.return_value = mock_app_instance
            
            bot = VehicleProgramSlackBot()
            
            # Mock message and say
            message = {'text': '/help', 'user': 'test_user'}
            say = Mock()
            
            # Test the handler
            bot._handle_help_request(message, say)
            
            # Verify help message was sent
            say.assert_called_once()
            call_args = say.call_args[0][0]
            assert 'vehicle' in call_args.lower()
            assert 'upload' in call_args.lower()
            assert 'dashboard' in call_args.lower()
    
    @patch('slack_bot.SLACK_BOT_TOKEN', 'test_token')
    @patch('slack_bot.SLACK_SIGNING_SECRET', 'test_secret')
    @patch('slack_bot.SLACK_APP_TOKEN', 'test_app_token')
    def test_start_method(self):
        """Test bot start method"""
        with patch('slack_bot.App') as mock_app:
            with patch('slack_bot.SocketModeHandler') as mock_handler:
                mock_app_instance = Mock()
                mock_app.return_value = mock_app_instance
                
                mock_handler_instance = Mock()
                mock_handler.return_value = mock_handler_instance
                
                bot = VehicleProgramSlackBot()
                
                # Test start method
                bot.start()
                
                # Verify handler was created and started
                mock_handler.assert_called_once()
                mock_handler_instance.start.assert_called_once()
    
    @patch('slack_bot.SLACK_BOT_TOKEN', 'test_token')
    @patch('slack_bot.SLACK_SIGNING_SECRET', 'test_secret')
    @patch('slack_bot.SLACK_APP_TOKEN', 'test_app_token')
    def test_start_method_exception(self):
        """Test bot start method with exception"""
        with patch('slack_bot.App') as mock_app:
            with patch('slack_bot.SocketModeHandler') as mock_handler:
                mock_app_instance = Mock()
                mock_app.return_value = mock_app_instance
                
                mock_handler.side_effect = Exception("Startup error")
                
                bot = VehicleProgramSlackBot()
                
                # Test start method with exception
                with pytest.raises(Exception, match="Startup error"):
                    bot.start()

if __name__ == '__main__':
    pytest.main([__file__]) 