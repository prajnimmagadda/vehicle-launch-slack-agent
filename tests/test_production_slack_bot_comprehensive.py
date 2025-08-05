import pytest
import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from production_slack_bot import ProductionSlackBot

class TestProductionSlackBotComprehensive:
    """Comprehensive tests for ProductionSlackBot"""
    
    def setup_method(self):
        """Setup test method"""
        self.mock_app = Mock()
        self.mock_say = Mock()
        self.mock_ack = Mock()
        self.mock_client = Mock()
        
    @patch('production_slack_bot.App')
    @patch('production_slack_bot.ProductionConfig')
    def test_initialization_success(self, mock_config, mock_app):
        """Test successful bot initialization"""
        mock_app.return_value = self.mock_app
        mock_config.get_logging_config.return_value = {'version': 1}
        
        bot = ProductionSlackBot()
        
        assert bot.app is not None
        assert bot.openai_client is not None
        assert bot.databricks_client is not None
        assert bot.file_parser is not None
        assert bot.dashboard is not None
        mock_app.assert_called_once()
    
    @patch('production_slack_bot.App')
    @patch('production_slack_bot.ProductionConfig')
    def test_initialization_failure(self, mock_config, mock_app):
        """Test bot initialization failure"""
        mock_app.side_effect = Exception("App initialization failed")
        mock_config.get_logging_config.return_value = {'version': 1}
        
        with pytest.raises(Exception):
            ProductionSlackBot()
    
    def test_extract_launch_date_valid(self):
        """Test valid launch date extraction"""
        bot = ProductionSlackBot.__new__(ProductionSlackBot)
        
        text = "Check vehicle program for 2024-03-15"
        date = bot._extract_launch_date(text)
        
        assert date == "2024-03-15"
    
    def test_extract_launch_date_invalid(self):
        """Test invalid launch date extraction"""
        bot = ProductionSlackBot.__new__(ProductionSlackBot)
        
        text = "Check vehicle program"
        date = bot._extract_launch_date(text)
        
        assert date is None
    
    def test_extract_launch_date_malformed(self):
        """Test malformed date extraction"""
        bot = ProductionSlackBot.__new__(ProductionSlackBot)
        
        text = "Check vehicle program for 2024-13-45"
        date = bot._extract_launch_date(text)
        
        assert date is None
    
    @patch('production_slack_bot.App')
    @patch('production_slack_bot.ProductionConfig')
    def test_register_handlers(self, mock_config, mock_app):
        """Test handler registration"""
        mock_app.return_value = self.mock_app
        mock_config.get_logging_config.return_value = {'version': 1}
        
        bot = ProductionSlackBot()
        bot.register_handlers()
        
        # Verify handlers were registered
        self.mock_app.message.assert_called()
        self.mock_app.event.assert_called()
    
    @patch('production_slack_bot.App')
    @patch('production_slack_bot.ProductionConfig')
    def test_handle_vehicle_program_query_success(self, mock_config, mock_app):
        """Test successful vehicle program query handling"""
        mock_app.return_value = self.mock_app
        mock_config.get_logging_config.return_value = {'version': 1}
        
        bot = ProductionSlackBot()
        
        # Mock dependencies
        bot.openai_client = Mock()
        bot.openai_client.process_vehicle_program_query.return_value = "Analysis complete"
        
        bot.databricks_client = Mock()
        bot.databricks_client.execute_query.return_value = {'data': 'test'}
        
        # Mock message event
        message = Mock()
        message.text = "Check vehicle program for 2024-03-15"
        message.channel = "C123"
        message.user = "U123"
        
        bot._handle_vehicle_program_query(message, self.mock_say)
        
        # Verify OpenAI was called
        bot.openai_client.process_vehicle_program_query.assert_called_once()
        self.mock_say.assert_called_once()
    
    @patch('production_slack_bot.App')
    @patch('production_slack_bot.ProductionConfig')
    def test_handle_vehicle_program_query_no_date(self, mock_config, mock_app):
        """Test vehicle program query without date"""
        mock_app.return_value = self.mock_app
        mock_config.get_logging_config.return_value = {'version': 1}
        
        bot = ProductionSlackBot()
        
        # Mock message event
        message = Mock()
        message.text = "Check vehicle program"
        message.channel = "C123"
        message.user = "U123"
        
        bot._handle_vehicle_program_query(message, self.mock_say)
        
        # Verify error message was sent
        self.mock_say.assert_called_once()
        call_args = self.mock_say.call_args[0][0]
        assert "Please provide a launch date" in call_args
    
    @patch('production_slack_bot.App')
    @patch('production_slack_bot.ProductionConfig')
    def test_handle_vehicle_program_query_exception(self, mock_config, mock_app):
        """Test vehicle program query with exception"""
        mock_app.return_value = self.mock_app
        mock_config.get_logging_config.return_value = {'version': 1}
        
        bot = ProductionSlackBot()
        
        # Mock dependencies to raise exception
        bot.databricks_client = Mock()
        bot.databricks_client.execute_query.side_effect = Exception("Database error")
        
        # Mock message event
        message = Mock()
        message.text = "Check vehicle program for 2024-03-15"
        message.channel = "C123"
        message.user = "U123"
        
        bot._handle_vehicle_program_query(message, self.mock_say)
        
        # Verify error message was sent
        self.mock_say.assert_called_once()
        call_args = self.mock_say.call_args[0][0]
        assert "error" in call_args.lower()
    
    @patch('production_slack_bot.App')
    @patch('production_slack_bot.ProductionConfig')
    def test_handle_file_upload_success(self, mock_config, mock_app):
        """Test successful file upload handling"""
        mock_app.return_value = self.mock_app
        mock_config.get_logging_config.return_value = {'version': 1}
        
        bot = ProductionSlackBot()
        
        # Mock file parser
        bot.file_parser = Mock()
        bot.file_parser.parse_file.return_value = {'status': 'success', 'data': 'test'}
        
        # Mock message event
        message = Mock()
        message.files = [{'url_private': 'https://example.com/file.xlsx', 'name': 'test.xlsx'}]
        message.channel = "C123"
        message.user = "U123"
        
        bot._handle_file_upload(message, self.mock_say)
        
        # Verify file parser was called
        bot.file_parser.parse_file.assert_called_once()
        self.mock_say.assert_called_once()
    
    @patch('production_slack_bot.App')
    @patch('production_slack_bot.ProductionConfig')
    def test_handle_file_upload_invalid_type(self, mock_config, mock_app):
        """Test file upload with invalid file type"""
        mock_app.return_value = self.mock_app
        mock_config.get_logging_config.return_value = {'version': 1}
        
        bot = ProductionSlackBot()
        
        # Mock message event with invalid file
        message = Mock()
        message.files = [{'url_private': 'https://example.com/file.txt', 'name': 'test.txt'}]
        message.channel = "C123"
        message.user = "U123"
        
        bot._handle_file_upload(message, self.mock_say)
        
        # Verify error message was sent
        self.mock_say.assert_called_once()
        call_args = self.mock_say.call_args[0][0]
        assert "unsupported file type" in call_args.lower()
    
    @patch('production_slack_bot.App')
    @patch('production_slack_bot.ProductionConfig')
    def test_handle_file_upload_no_files(self, mock_config, mock_app):
        """Test file upload with no files"""
        mock_app.return_value = self.mock_app
        mock_config.get_logging_config.return_value = {'version': 1}
        
        bot = ProductionSlackBot()
        
        # Mock message event with no files
        message = Mock()
        message.files = []
        message.channel = "C123"
        message.user = "U123"
        
        bot._handle_file_upload(message, self.mock_say)
        
        # Verify error message was sent
        self.mock_say.assert_called_once()
        call_args = self.mock_say.call_args[0][0]
        assert "no files" in call_args.lower()
    
    @patch('production_slack_bot.App')
    @patch('production_slack_bot.ProductionConfig')
    def test_handle_dashboard_request_success(self, mock_config, mock_app):
        """Test successful dashboard request handling"""
        mock_app.return_value = self.mock_app
        mock_config.get_logging_config.return_value = {'version': 1}
        
        bot = ProductionSlackBot()
        
        # Mock dashboard
        bot.dashboard = Mock()
        bot.dashboard.create_dashboard.return_value = "https://docs.google.com/spreadsheets/d/test"
        
        # Mock databricks client
        bot.databricks_client = Mock()
        bot.databricks_client.execute_query.return_value = {'data': 'test'}
        
        # Mock message event
        message = Mock()
        message.text = "Create dashboard for 2024-03-15"
        message.channel = "C123"
        message.user = "U123"
        
        bot._handle_dashboard_request(message, self.mock_say)
        
        # Verify dashboard was created
        bot.dashboard.create_dashboard.assert_called_once()
        self.mock_say.assert_called_once()
    
    @patch('production_slack_bot.App')
    @patch('production_slack_bot.ProductionConfig')
    def test_handle_dashboard_request_no_date(self, mock_config, mock_app):
        """Test dashboard request without date"""
        mock_app.return_value = self.mock_app
        mock_config.get_logging_config.return_value = {'version': 1}
        
        bot = ProductionSlackBot()
        
        # Mock message event
        message = Mock()
        message.text = "Create dashboard"
        message.channel = "C123"
        message.user = "U123"
        
        bot._handle_dashboard_request(message, self.mock_say)
        
        # Verify error message was sent
        self.mock_say.assert_called_once()
        call_args = self.mock_say.call_args[0][0]
        assert "Please provide a launch date" in call_args
    
    @patch('production_slack_bot.App')
    @patch('production_slack_bot.ProductionConfig')
    def test_handle_help_request(self, mock_config, mock_app):
        """Test help request handling"""
        mock_app.return_value = self.mock_app
        mock_config.get_logging_config.return_value = {'version': 1}
        
        bot = ProductionSlackBot()
        
        # Mock message event
        message = Mock()
        message.channel = "C123"
        message.user = "U123"
        
        bot._handle_help_request(message, self.mock_say)
        
        # Verify help message was sent
        self.mock_say.assert_called_once()
        call_args = self.mock_say.call_args[0][0]
        assert "help" in call_args.lower() or "commands" in call_args.lower()
    
    @patch('production_slack_bot.App')
    @patch('production_slack_bot.ProductionConfig')
    def test_handle_app_mention(self, mock_config, mock_app):
        """Test app mention handling"""
        mock_app.return_value = self.mock_app
        mock_config.get_logging_config.return_value = {'version': 1}
        
        bot = ProductionSlackBot()
        
        # Mock message event
        message = Mock()
        message.text = "<@U123> help"
        message.channel = "C123"
        message.user = "U123"
        
        bot._handle_app_mention(message, self.mock_say)
        
        # Verify response was sent
        self.mock_say.assert_called_once()
    
    @patch('production_slack_bot.App')
    @patch('production_slack_bot.ProductionConfig')
    def test_start_stop_methods(self, mock_config, mock_app):
        """Test bot start and stop methods"""
        mock_app.return_value = self.mock_app
        mock_config.get_logging_config.return_value = {'version': 1}
        
        bot = ProductionSlackBot()
        
        # Test start method
        with patch('production_slack_bot.SocketModeHandler') as mock_handler:
            mock_handler_instance = Mock()
            mock_handler.return_value = mock_handler_instance
            
            bot.start()
            
            mock_handler.assert_called_once()
            mock_handler_instance.start.assert_called_once()
        
        # Test stop method
        bot.stop()
        
        # Verify cleanup was performed
        assert True  # If we get here, no exceptions were raised
    
    @patch('production_slack_bot.App')
    @patch('production_slack_bot.ProductionConfig')
    def test_error_handling(self, mock_config, mock_app):
        """Test error handling in bot"""
        mock_app.return_value = self.mock_app
        mock_config.get_logging_config.return_value = {'version': 1}
        
        bot = ProductionSlackBot()
        
        # Mock message event
        message = Mock()
        message.text = "Check vehicle program for 2024-03-15"
        message.channel = "C123"
        message.user = "U123"
        
        # Mock exception in databricks client
        bot.databricks_client = Mock()
        bot.databricks_client.execute_query.side_effect = Exception("Test error")
        
        # This should not raise an exception
        bot._handle_vehicle_program_query(message, self.mock_say)
        
        # Verify error message was sent
        self.mock_say.assert_called_once()
        call_args = self.mock_say.call_args[0][0]
        assert "error" in call_args.lower()
    
    @patch('production_slack_bot.App')
    @patch('production_slack_bot.ProductionConfig')
    def test_logging_integration(self, mock_config, mock_app):
        """Test logging integration"""
        mock_app.return_value = self.mock_app
        mock_config.get_logging_config.return_value = {'version': 1}
        
        bot = ProductionSlackBot()
        
        # Mock message event
        message = Mock()
        message.text = "Check vehicle program for 2024-03-15"
        message.channel = "C123"
        message.user = "U123"
        
        # Mock dependencies
        bot.openai_client = Mock()
        bot.openai_client.process_vehicle_program_query.return_value = "Analysis complete"
        
        bot.databricks_client = Mock()
        bot.databricks_client.execute_query.return_value = {'data': 'test'}
        
        # This should log the command
        bot._handle_vehicle_program_query(message, self.mock_say)
        
        # Verify the method completed without exceptions
        assert True
    
    @patch('production_slack_bot.App')
    @patch('production_slack_bot.ProductionConfig')
    def test_comprehensive_workflow(self, mock_config, mock_app):
        """Test comprehensive workflow"""
        mock_app.return_value = self.mock_app
        mock_config.get_logging_config.return_value = {'version': 1}
        
        bot = ProductionSlackBot()
        
        # Mock all dependencies
        bot.openai_client = Mock()
        bot.openai_client.process_vehicle_program_query.return_value = "Analysis complete"
        
        bot.databricks_client = Mock()
        bot.databricks_client.execute_query.return_value = {'data': 'test'}
        
        bot.file_parser = Mock()
        bot.file_parser.parse_file.return_value = {'status': 'success', 'data': 'test'}
        
        bot.dashboard = Mock()
        bot.dashboard.create_dashboard.return_value = "https://docs.google.com/spreadsheets/d/test"
        
        # Test multiple commands
        message1 = Mock()
        message1.text = "Check vehicle program for 2024-03-15"
        message1.channel = "C123"
        message1.user = "U123"
        
        message2 = Mock()
        message2.text = "Create dashboard for 2024-03-15"
        message2.channel = "C123"
        message2.user = "U123"
        
        message3 = Mock()
        message3.text = "help"
        message3.channel = "C123"
        message3.user = "U123"
        
        # Execute commands
        bot._handle_vehicle_program_query(message1, self.mock_say)
        bot._handle_dashboard_request(message2, self.mock_say)
        bot._handle_help_request(message3, self.mock_say)
        
        # Verify all commands were processed
        assert self.mock_say.call_count == 3

if __name__ == '__main__':
    pytest.main([__file__]) 