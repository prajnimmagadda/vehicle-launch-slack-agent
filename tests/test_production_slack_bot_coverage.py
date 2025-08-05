import pytest
import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from production_slack_bot import ProductionSlackBot

class TestProductionSlackBotCoverage:
    """Comprehensive tests for production Slack bot to improve coverage"""
    
    @patch('production_slack_bot.SLACK_BOT_TOKEN', 'test_token')
    @patch('production_slack_bot.SLACK_SIGNING_SECRET', 'test_secret')
    @patch('production_slack_bot.SLACK_APP_TOKEN', 'test_app_token')
    @patch('production_slack_bot.OpenAIClient')
    @patch('production_slack_bot.DatabricksClient')
    @patch('production_slack_bot.FileParser')
    @patch('production_slack_bot.GoogleSheetsDashboard')
    @patch('production_slack_bot.DatabaseManager')
    @patch('production_slack_bot.monitoring_manager')
    def test_initialization_success(self, mock_monitoring, mock_db, mock_dashboard, mock_parser, mock_databricks, mock_openai, mock_app):
        """Test production Slack bot initialization success"""
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
        
        mock_db_instance = Mock()
        mock_db.return_value = mock_db_instance
        
        mock_monitoring_instance = Mock()
        mock_monitoring.return_value = mock_monitoring_instance
        
        bot = ProductionSlackBot()
        
        assert bot.app == mock_app_instance
        assert bot.openai_client == mock_openai_instance
        assert bot.databricks_client == mock_databricks_instance
        assert bot.file_parser == mock_parser_instance
        assert bot.dashboard_creator == mock_dashboard_instance
        assert bot.db_manager == mock_db_instance
        assert hasattr(bot, 'user_sessions')
    
    def test_extract_launch_date_malformed(self):
        """Test launch date extraction with malformed dates"""
        bot = ProductionSlackBot.__new__(ProductionSlackBot)
        
        # Test malformed dates that should return None
        test_cases = [
            "2024-13-45",  # Invalid month and day
            "2024-02-30",  # Invalid day for February
            "2024-04-31",  # Invalid day for April
            "2024-00-15",  # Invalid month
            "2024-12-00",  # Invalid day
            "2024-12-32",  # Invalid day
        ]
        
        for text in test_cases:
            result = bot._extract_launch_date(text)
            # These should return None because they're invalid dates
            assert result is None
    
    @patch('production_slack_bot.SLACK_BOT_TOKEN', 'test_token')
    @patch('production_slack_bot.SLACK_SIGNING_SECRET', 'test_secret')
    @patch('production_slack_bot.SLACK_APP_TOKEN', 'test_app_token')
    @patch('production_slack_bot.OpenAIClient')
    @patch('production_slack_bot.DatabricksClient')
    @patch('production_slack_bot.FileParser')
    @patch('production_slack_bot.GoogleSheetsDashboard')
    @patch('production_slack_bot.DatabaseManager')
    @patch('production_slack_bot.monitoring_manager')
    def test_register_handlers(self, mock_monitoring, mock_db, mock_dashboard, mock_parser, mock_databricks, mock_openai, mock_app):
        """Test that handlers are registered correctly"""
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
        
        mock_db_instance = Mock()
        mock_db.return_value = mock_db_instance
        
        mock_monitoring_instance = Mock()
        mock_monitoring.return_value = mock_monitoring_instance
        
        bot = ProductionSlackBot()
        
        # Verify that message decorators were called
        assert mock_app_instance.message.call_count >= 4  # Should have multiple handlers
        assert mock_app_instance.event.call_count >= 1  # Should have file_shared event
    
    @patch('production_slack_bot.SLACK_BOT_TOKEN', 'test_token')
    @patch('production_slack_bot.SLACK_SIGNING_SECRET', 'test_secret')
    @patch('production_slack_bot.SLACK_APP_TOKEN', 'test_app_token')
    @patch('production_slack_bot.OpenAIClient')
    @patch('production_slack_bot.DatabricksClient')
    @patch('production_slack_bot.FileParser')
    @patch('production_slack_bot.GoogleSheetsDashboard')
    @patch('production_slack_bot.DatabaseManager')
    @patch('production_slack_bot.monitoring_manager')
    def test_handle_vehicle_program_query_success(self, mock_monitoring, mock_db, mock_dashboard, mock_parser, mock_databricks, mock_openai, mock_app):
        """Test successful vehicle program query handler"""
        mock_app_instance = Mock()
        mock_app.return_value = mock_app_instance
        
        mock_openai_instance = Mock()
        mock_openai_instance.analyze_program_status.return_value = "Analysis complete"
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
        
        mock_db_instance = Mock()
        mock_db.return_value = mock_db_instance
        
        mock_monitoring_instance = Mock()
        mock_monitoring.return_value = mock_monitoring_instance
        
        bot = ProductionSlackBot()
        
        # Test successful query
        message = {'text': '/vehicle 2024-03-15', 'user': 'test_user'}
        say = Mock()
        
        bot._handle_vehicle_program_query(message, say)
        
        # Verify calls were made
        mock_databricks_instance.query_vehicle_program_status.assert_called_once_with('2024-03-15')
        mock_openai_instance.analyze_program_status.assert_called_once()
        mock_databricks_instance.create_visualization.assert_called_once()
        assert say.call_count >= 1
        
        # Verify session was stored
        assert 'test_user' in bot.user_sessions
        assert bot.user_sessions['test_user']['launch_date'] == '2024-03-15'
    
    @patch('production_slack_bot.SLACK_BOT_TOKEN', 'test_token')
    @patch('production_slack_bot.SLACK_SIGNING_SECRET', 'test_secret')
    @patch('production_slack_bot.SLACK_APP_TOKEN', 'test_app_token')
    @patch('production_slack_bot.OpenAIClient')
    @patch('production_slack_bot.DatabricksClient')
    @patch('production_slack_bot.FileParser')
    @patch('production_slack_bot.GoogleSheetsDashboard')
    @patch('production_slack_bot.DatabaseManager')
    @patch('production_slack_bot.monitoring_manager')
    def test_handle_vehicle_program_query_no_date(self, mock_monitoring, mock_db, mock_dashboard, mock_parser, mock_databricks, mock_openai, mock_app):
        """Test vehicle program query handler with no date"""
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
        
        mock_db_instance = Mock()
        mock_db.return_value = mock_db_instance
        
        mock_monitoring_instance = Mock()
        mock_monitoring.return_value = mock_monitoring_instance
        
        bot = ProductionSlackBot()
        
        # Test query without date
        message = {'text': '/vehicle', 'user': 'test_user'}
        say = Mock()
        
        bot._handle_vehicle_program_query(message, say)
        
        # Verify error message was sent
        say.assert_called_once()
        call_args = say.call_args[0][0]
        assert "Please provide a launch date" in call_args
    
    @patch('production_slack_bot.SLACK_BOT_TOKEN', 'test_token')
    @patch('production_slack_bot.SLACK_SIGNING_SECRET', 'test_secret')
    @patch('production_slack_bot.SLACK_APP_TOKEN', 'test_app_token')
    @patch('production_slack_bot.OpenAIClient')
    @patch('production_slack_bot.DatabricksClient')
    @patch('production_slack_bot.FileParser')
    @patch('production_slack_bot.GoogleSheetsDashboard')
    @patch('production_slack_bot.DatabaseManager')
    @patch('production_slack_bot.monitoring_manager')
    def test_handle_vehicle_program_query_exception(self, mock_monitoring, mock_db, mock_dashboard, mock_parser, mock_databricks, mock_openai, mock_app):
        """Test vehicle program query handler with exception"""
        mock_app_instance = Mock()
        mock_app.return_value = mock_app_instance
        
        mock_openai_instance = Mock()
        mock_openai_instance.analyze_program_status.side_effect = Exception("Test error")
        mock_openai.return_value = mock_openai_instance
        
        mock_databricks_instance = Mock()
        mock_databricks_instance.query_vehicle_program_status.return_value = {}
        mock_databricks.return_value = mock_databricks_instance
        
        mock_parser_instance = Mock()
        mock_parser.return_value = mock_parser_instance
        
        mock_dashboard_instance = Mock()
        mock_dashboard.return_value = mock_dashboard_instance
        
        mock_db_instance = Mock()
        mock_db.return_value = mock_db_instance
        
        mock_monitoring_instance = Mock()
        mock_monitoring.return_value = mock_monitoring_instance
        
        bot = ProductionSlackBot()
        
        message = {'text': '/vehicle 2024-03-15', 'user': 'test_user'}
        say = Mock()
        
        bot._handle_vehicle_program_query(message, say)
        
        # Verify error message was sent
        say.assert_called()
        call_args = say.call_args[0][0]
        assert "Error processing your request" in call_args
    
    @patch('production_slack_bot.SLACK_BOT_TOKEN', 'test_token')
    @patch('production_slack_bot.SLACK_SIGNING_SECRET', 'test_secret')
    @patch('production_slack_bot.SLACK_APP_TOKEN', 'test_app_token')
    @patch('production_slack_bot.OpenAIClient')
    @patch('production_slack_bot.DatabricksClient')
    @patch('production_slack_bot.FileParser')
    @patch('production_slack_bot.GoogleSheetsDashboard')
    @patch('production_slack_bot.DatabaseManager')
    @patch('production_slack_bot.monitoring_manager')
    def test_handle_file_upload_success(self, mock_monitoring, mock_db, mock_dashboard, mock_parser, mock_databricks, mock_openai, mock_app):
        """Test successful file upload handler"""
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
        
        mock_db_instance = Mock()
        mock_db.return_value = mock_db_instance
        
        mock_monitoring_instance = Mock()
        mock_monitoring.return_value = mock_monitoring_instance
        
        bot = ProductionSlackBot()
        
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
    
    @patch('production_slack_bot.SLACK_BOT_TOKEN', 'test_token')
    @patch('production_slack_bot.SLACK_SIGNING_SECRET', 'test_secret')
    @patch('production_slack_bot.SLACK_APP_TOKEN', 'test_app_token')
    @patch('production_slack_bot.OpenAIClient')
    @patch('production_slack_bot.DatabricksClient')
    @patch('production_slack_bot.FileParser')
    @patch('production_slack_bot.GoogleSheetsDashboard')
    @patch('production_slack_bot.DatabaseManager')
    @patch('production_slack_bot.monitoring_manager')
    def test_handle_file_upload_invalid_type(self, mock_monitoring, mock_db, mock_dashboard, mock_parser, mock_databricks, mock_openai, mock_app):
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
        
        mock_db_instance = Mock()
        mock_db.return_value = mock_db_instance
        
        mock_monitoring_instance = Mock()
        mock_monitoring.return_value = mock_monitoring_instance
        
        bot = ProductionSlackBot()
        
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
    
    @patch('production_slack_bot.SLACK_BOT_TOKEN', 'test_token')
    @patch('production_slack_bot.SLACK_SIGNING_SECRET', 'test_secret')
    @patch('production_slack_bot.SLACK_APP_TOKEN', 'test_app_token')
    @patch('production_slack_bot.OpenAIClient')
    @patch('production_slack_bot.DatabricksClient')
    @patch('production_slack_bot.FileParser')
    @patch('production_slack_bot.GoogleSheetsDashboard')
    @patch('production_slack_bot.DatabaseManager')
    @patch('production_slack_bot.monitoring_manager')
    def test_handle_dashboard_request_success(self, mock_monitoring, mock_db, mock_dashboard, mock_parser, mock_databricks, mock_openai, mock_app):
        """Test successful dashboard request handler"""
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
        
        mock_db_instance = Mock()
        mock_db.return_value = mock_db_instance
        
        mock_monitoring_instance = Mock()
        mock_monitoring.return_value = mock_monitoring_instance
        
        bot = ProductionSlackBot()
        
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
    
    @patch('production_slack_bot.SLACK_BOT_TOKEN', 'test_token')
    @patch('production_slack_bot.SLACK_SIGNING_SECRET', 'test_secret')
    @patch('production_slack_bot.SLACK_APP_TOKEN', 'test_app_token')
    @patch('production_slack_bot.OpenAIClient')
    @patch('production_slack_bot.DatabricksClient')
    @patch('production_slack_bot.FileParser')
    @patch('production_slack_bot.GoogleSheetsDashboard')
    @patch('production_slack_bot.DatabaseManager')
    @patch('production_slack_bot.monitoring_manager')
    def test_handle_help_request(self, mock_monitoring, mock_db, mock_dashboard, mock_parser, mock_databricks, mock_openai, mock_app):
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
        
        mock_db_instance = Mock()
        mock_db.return_value = mock_db_instance
        
        mock_monitoring_instance = Mock()
        mock_monitoring.return_value = mock_monitoring_instance
        
        bot = ProductionSlackBot()
        
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
    
    @patch('production_slack_bot.SLACK_BOT_TOKEN', 'test_token')
    @patch('production_slack_bot.SLACK_SIGNING_SECRET', 'test_secret')
    @patch('production_slack_bot.SLACK_APP_TOKEN', 'test_app_token')
    @patch('production_slack_bot.OpenAIClient')
    @patch('production_slack_bot.DatabricksClient')
    @patch('production_slack_bot.FileParser')
    @patch('production_slack_bot.GoogleSheetsDashboard')
    @patch('production_slack_bot.DatabaseManager')
    @patch('production_slack_bot.monitoring_manager')
    def test_handle_app_mention(self, mock_monitoring, mock_db, mock_dashboard, mock_parser, mock_databricks, mock_openai, mock_app):
        """Test app mention handler"""
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
        
        mock_db_instance = Mock()
        mock_db.return_value = mock_db_instance
        
        mock_monitoring_instance = Mock()
        mock_monitoring.return_value = mock_monitoring_instance
        
        bot = ProductionSlackBot()
        
        # Test app mention
        event = {
            'text': '<@U123456> help',
            'user': 'test_user'
        }
        say = Mock()
        
        bot._handle_app_mention(event, say)
        
        # Verify help message was sent
        say.assert_called_once()
        call_args = say.call_args[0][0]
        assert "Vehicle Program Slack Bot - Help" in call_args
    
    @patch('production_slack_bot.SLACK_BOT_TOKEN', 'test_token')
    @patch('production_slack_bot.SLACK_SIGNING_SECRET', 'test_secret')
    @patch('production_slack_bot.SLACK_APP_TOKEN', 'test_app_token')
    @patch('production_slack_bot.OpenAIClient')
    @patch('production_slack_bot.DatabricksClient')
    @patch('production_slack_bot.FileParser')
    @patch('production_slack_bot.GoogleSheetsDashboard')
    @patch('production_slack_bot.DatabaseManager')
    @patch('production_slack_bot.monitoring_manager')
    @patch('production_slack_bot.SocketModeHandler')
    def test_start_stop_methods(self, mock_handler, mock_monitoring, mock_db, mock_dashboard, mock_parser, mock_databricks, mock_openai, mock_app):
        """Test bot start and stop methods"""
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
        
        mock_db_instance = Mock()
        mock_db.return_value = mock_db_instance
        
        mock_monitoring_instance = Mock()
        mock_monitoring.return_value = mock_monitoring_instance
        
        mock_handler_instance = Mock()
        mock_handler.return_value = mock_handler_instance
        
        bot = ProductionSlackBot()
        
        # Test start method
        bot.start()
        
        # Verify handler was created and started
        mock_handler.assert_called_once_with(mock_app_instance, 'test_app_token')
        mock_handler_instance.start.assert_called_once()
        
        # Test stop method
        bot.stop()
        
        # Verify handler was stopped
        mock_handler_instance.stop.assert_called_once()
    
    @patch('production_slack_bot.SLACK_BOT_TOKEN', 'test_token')
    @patch('production_slack_bot.SLACK_SIGNING_SECRET', 'test_secret')
    @patch('production_slack_bot.SLACK_APP_TOKEN', 'test_app_token')
    @patch('production_slack_bot.OpenAIClient')
    @patch('production_slack_bot.DatabricksClient')
    @patch('production_slack_bot.FileParser')
    @patch('production_slack_bot.GoogleSheetsDashboard')
    @patch('production_slack_bot.DatabaseManager')
    @patch('production_slack_bot.monitoring_manager')
    def test_error_handling(self, mock_monitoring, mock_db, mock_dashboard, mock_parser, mock_databricks, mock_openai, mock_app):
        """Test error handling in production bot"""
        mock_app_instance = Mock()
        mock_app.return_value = mock_app_instance
        
        mock_openai_instance = Mock()
        mock_openai_instance.analyze_program_status.side_effect = Exception("Test error")
        mock_openai.return_value = mock_openai_instance
        
        mock_databricks_instance = Mock()
        mock_databricks_instance.query_vehicle_program_status.side_effect = Exception("Databricks error")
        mock_databricks.return_value = mock_databricks_instance
        
        mock_parser_instance = Mock()
        mock_parser.return_value = mock_parser_instance
        
        mock_dashboard_instance = Mock()
        mock_dashboard.return_value = mock_dashboard_instance
        
        mock_db_instance = Mock()
        mock_db.return_value = mock_db_instance
        
        mock_monitoring_instance = Mock()
        mock_monitoring.return_value = mock_monitoring_instance
        
        bot = ProductionSlackBot()
        
        # Test error handling in vehicle program query
        message = {'text': '/vehicle 2024-03-15', 'user': 'test_user'}
        say = Mock()
        
        bot._handle_vehicle_program_query(message, say)
        
        # Verify error message was sent
        say.assert_called()
        call_args = say.call_args[0][0]
        assert "Error processing your request" in call_args
    
    @patch('production_slack_bot.SLACK_BOT_TOKEN', 'test_token')
    @patch('production_slack_bot.SLACK_SIGNING_SECRET', 'test_secret')
    @patch('production_slack_bot.SLACK_APP_TOKEN', 'test_app_token')
    @patch('production_slack_bot.OpenAIClient')
    @patch('production_slack_bot.DatabricksClient')
    @patch('production_slack_bot.FileParser')
    @patch('production_slack_bot.GoogleSheetsDashboard')
    @patch('production_slack_bot.DatabaseManager')
    @patch('production_slack_bot.monitoring_manager')
    def test_logging_integration(self, mock_monitoring, mock_db, mock_dashboard, mock_parser, mock_databricks, mock_openai, mock_app):
        """Test logging integration in production bot"""
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
        
        mock_db_instance = Mock()
        mock_db.return_value = mock_db_instance
        
        mock_monitoring_instance = Mock()
        mock_monitoring.return_value = mock_monitoring_instance
        
        bot = ProductionSlackBot()
        
        # Test that logging is configured
        assert hasattr(bot, 'logger')
        assert bot.logger is not None
    
    @patch('production_slack_bot.SLACK_BOT_TOKEN', 'test_token')
    @patch('production_slack_bot.SLACK_SIGNING_SECRET', 'test_secret')
    @patch('production_slack_bot.SLACK_APP_TOKEN', 'test_app_token')
    @patch('production_slack_bot.OpenAIClient')
    @patch('production_slack_bot.DatabricksClient')
    @patch('production_slack_bot.FileParser')
    @patch('production_slack_bot.GoogleSheetsDashboard')
    @patch('production_slack_bot.DatabaseManager')
    @patch('production_slack_bot.monitoring_manager')
    def test_comprehensive_workflow(self, mock_monitoring, mock_db, mock_dashboard, mock_parser, mock_databricks, mock_openai, mock_app):
        """Test comprehensive workflow in production bot"""
        mock_app_instance = Mock()
        mock_app.return_value = mock_app_instance
        
        mock_openai_instance = Mock()
        mock_openai_instance.analyze_program_status.return_value = "Analysis complete"
        mock_openai_instance.analyze_uploaded_data.return_value = "File analysis complete"
        mock_openai.return_value = mock_openai_instance
        
        mock_databricks_instance = Mock()
        mock_databricks_instance.query_vehicle_program_status.return_value = {
            'bill_of_material': {'status': 'complete'},
            'master_parts_list': {'status': 'in_progress'}
        }
        mock_databricks_instance.create_visualization.return_value = "https://databricks.com/viz"
        mock_databricks.return_value = mock_databricks_instance
        
        mock_parser_instance = Mock()
        mock_parser_instance.validate_file_type.return_value = True
        mock_parser_instance.parse_excel_file.return_value = {'data': 'parsed_data'}
        mock_parser.return_value = mock_parser_instance
        
        mock_dashboard_instance = Mock()
        mock_dashboard_instance.create_dashboard.return_value = "https://sheets.google.com/dashboard"
        mock_dashboard.return_value = mock_dashboard_instance
        
        mock_db_instance = Mock()
        mock_db.return_value = mock_db_instance
        
        mock_monitoring_instance = Mock()
        mock_monitoring.return_value = mock_monitoring_instance
        
        bot = ProductionSlackBot()
        
        # Test complete workflow
        say = Mock()
        
        # 1. Vehicle program query
        message = {'text': '/vehicle 2024-03-15', 'user': 'test_user'}
        bot._handle_vehicle_program_query(message, say)
        
        # 2. File upload
        event = {
            'file': {'name': 'test.xlsx'},
            'user_id': 'test_user'
        }
        bot._handle_file_upload(event, say)
        
        # 3. Dashboard creation
        message = {'user': 'test_user'}
        bot._handle_dashboard_request(message, say)
        
        # Verify all components were called
        mock_databricks_instance.query_vehicle_program_status.assert_called_once()
        mock_openai_instance.analyze_program_status.assert_called_once()
        mock_parser_instance.parse_excel_file.assert_called_once()
        mock_openai_instance.analyze_uploaded_data.assert_called_once()
        mock_dashboard_instance.create_dashboard.assert_called_once()
        
        # Verify session was maintained throughout
        assert 'test_user' in bot.user_sessions
        session = bot.user_sessions['test_user']
        assert session['launch_date'] == '2024-03-15'
        assert 'databricks_data' in session
        assert 'file_data' in session

if __name__ == '__main__':
    pytest.main([__file__]) 