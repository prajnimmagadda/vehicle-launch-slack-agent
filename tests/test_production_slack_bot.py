import pytest
import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import re

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from production_slack_bot import ProductionSlackBot

class TestProductionSlackBot:
    """Test ProductionSlackBot class"""
    
    @patch('production_slack_bot.ProductionConfig')
    @patch('production_slack_bot.DatabricksClient')
    @patch('production_slack_bot.OpenAIClient')
    @patch('production_slack_bot.FileParser')
    @patch('production_slack_bot.GoogleSheetsDashboard')
    @patch('production_slack_bot.monitoring_manager')
    def test_initialization_success(self, mock_monitoring, mock_dashboard, mock_file_parser, 
                                   mock_openai, mock_databricks, mock_config):
        """Test successful bot initialization"""
        # Mock configuration validation
        mock_config.validate_config.return_value = {'valid': True, 'errors': [], 'warnings': []}
        mock_config.SLACK_BOT_TOKEN = 'test_token'
        mock_config.SLACK_SIGNING_SECRET = 'test_secret'
        
        # Mock Slack app
        with patch('production_slack_bot.App') as mock_app:
            mock_app_instance = Mock()
            mock_app.return_value = mock_app_instance
            
            bot = ProductionSlackBot()
            
            assert bot.app == mock_app_instance
            assert bot.databricks_client is not None
            assert bot.openai_client is not None
            assert bot.file_parser is not None
            assert bot.dashboard_creator is not None
    
    @patch('production_slack_bot.ProductionConfig')
    def test_initialization_config_failure(self, mock_config):
        """Test bot initialization with invalid configuration"""
        mock_config.validate_config.return_value = {
            'valid': False, 
            'errors': ['Missing SLACK_BOT_TOKEN'], 
            'warnings': []
        }
        
        with pytest.raises(ValueError, match="Invalid configuration"):
            ProductionSlackBot()
    
    def test_extract_launch_date_valid(self):
        """Test launch date extraction with valid dates"""
        bot = ProductionSlackBot.__new__(ProductionSlackBot)
        
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
        bot = ProductionSlackBot.__new__(ProductionSlackBot)
        
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
    
    @patch('production_slack_bot.ProductionConfig')
    @patch('production_slack_bot.DatabricksClient')
    @patch('production_slack_bot.OpenAIClient')
    @patch('production_slack_bot.FileParser')
    @patch('production_slack_bot.GoogleSheetsDashboard')
    @patch('production_slack_bot.monitoring_manager')
    def test_register_handlers(self, mock_monitoring, mock_dashboard, mock_file_parser,
                              mock_openai, mock_databricks, mock_config):
        """Test that handlers are registered correctly"""
        mock_config.validate_config.return_value = {'valid': True, 'errors': [], 'warnings': []}
        mock_config.SLACK_BOT_TOKEN = 'test_token'
        mock_config.SLACK_SIGNING_SECRET = 'test_secret'
        
        with patch('production_slack_bot.App') as mock_app:
            mock_app_instance = Mock()
            mock_app.return_value = mock_app_instance
            
            bot = ProductionSlackBot()
            
            # Verify that message decorators were called
            assert mock_app_instance.message.call_count >= 5  # Should have multiple handlers
    
    @patch('production_slack_bot.ProductionConfig')
    @patch('production_slack_bot.DatabricksClient')
    @patch('production_slack_bot.OpenAIClient')
    @patch('production_slack_bot.FileParser')
    @patch('production_slack_bot.GoogleSheetsDashboard')
    @patch('production_slack_bot.monitoring_manager')
    def test_start_stop_methods(self, mock_monitoring, mock_dashboard, mock_file_parser,
                               mock_openai, mock_databricks, mock_config):
        """Test bot start and stop methods"""
        mock_config.validate_config.return_value = {'valid': True, 'errors': [], 'warnings': []}
        mock_config.SLACK_BOT_TOKEN = 'test_token'
        mock_config.SLACK_SIGNING_SECRET = 'test_secret'
        
        with patch('production_slack_bot.App') as mock_app:
            mock_app_instance = Mock()
            mock_app.return_value = mock_app_instance
            
            bot = ProductionSlackBot()
            
            # Test start method
            bot.start()
            mock_app_instance.start.assert_called_once()
            
            # Test stop method
            bot.stop()
            mock_app_instance.stop.assert_called_once()

class TestSlackBotHandlers:
    """Test Slack bot event handlers"""
    
    @patch('production_slack_bot.ProductionConfig')
    @patch('production_slack_bot.DatabricksClient')
    @patch('production_slack_bot.OpenAIClient')
    @patch('production_slack_bot.FileParser')
    @patch('production_slack_bot.GoogleSheetsDashboard')
    @patch('production_slack_bot.monitoring_manager')
    def test_handle_vehicle_program_query(self, mock_monitoring, mock_dashboard, mock_file_parser,
                                         mock_openai, mock_databricks, mock_config):
        """Test vehicle program query handler"""
        mock_config.validate_config.return_value = {'valid': True, 'errors': [], 'warnings': []}
        mock_config.SLACK_BOT_TOKEN = 'test_token'
        mock_config.SLACK_SIGNING_SECRET = 'test_secret'
        
        with patch('production_slack_bot.App') as mock_app:
            mock_app_instance = Mock()
            mock_app.return_value = mock_app_instance
            
            bot = ProductionSlackBot()
            
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
            mock_openai_instance.analyze_program_status.return_value = "Analysis complete"
            bot.openai_client = mock_openai_instance
            
            # Test the handler
            bot._handle_vehicle_program_query(message, say)
            
            # Verify interactions
            mock_databricks_instance.query_vehicle_program_status.assert_called_once_with('2024-03-15')
            mock_openai_instance.analyze_program_status.assert_called_once()
            say.assert_called()
    
    @patch('production_slack_bot.ProductionConfig')
    @patch('production_slack_bot.DatabricksClient')
    @patch('production_slack_bot.OpenAIClient')
    @patch('production_slack_bot.FileParser')
    @patch('production_slack_bot.GoogleSheetsDashboard')
    @patch('production_slack_bot.monitoring_manager')
    def test_handle_help_request(self, mock_monitoring, mock_dashboard, mock_file_parser,
                                mock_openai, mock_databricks, mock_config):
        """Test help request handler"""
        mock_config.validate_config.return_value = {'valid': True, 'errors': [], 'warnings': []}
        mock_config.SLACK_BOT_TOKEN = 'test_token'
        mock_config.SLACK_SIGNING_SECRET = 'test_secret'
        
        with patch('production_slack_bot.App') as mock_app:
            mock_app_instance = Mock()
            mock_app.return_value = mock_app_instance
            
            bot = ProductionSlackBot()
            
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

if __name__ == '__main__':
    pytest.main([__file__]) 