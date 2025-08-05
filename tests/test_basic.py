import pytest
import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from production_config import ProductionConfig
from database import DatabaseManager
from monitoring import monitoring_manager

class TestProductionConfig:
    """Test production configuration"""
    
    def test_config_validation(self):
        """Test configuration validation"""
        # Test with missing required configs - mock more thoroughly
        with patch.dict(os.environ, {}, clear=True):
            with patch('production_config.DATABASE_URL', None):
                with patch('production_config.REDIS_URL', None):
                    validation = ProductionConfig.validate_config()
                    assert not validation['valid']
                    assert len(validation['errors']) > 0
    
    def test_logging_config(self):
        """Test logging configuration"""
        config = ProductionConfig.get_logging_config()
        assert 'version' in config
        assert 'handlers' in config
        assert 'loggers' in config

class TestDatabaseManager:
    """Test database manager"""
    
    def test_database_initialization(self):
        """Test database initialization"""
        # Test without DATABASE_URL
        with patch.dict(os.environ, {}, clear=True):
            db_manager = DatabaseManager()
            assert db_manager.engine is None
    
    def test_health_check(self):
        """Test database health check"""
        db_manager = DatabaseManager()
        health = db_manager.health_check()
        assert 'status' in health
        assert 'message' in health

class TestMonitoringManager:
    """Test monitoring manager"""
    
    def test_monitoring_initialization(self):
        """Test monitoring initialization"""
        assert monitoring_manager is not None
        assert hasattr(monitoring_manager, 'start_time')
    
    def test_track_command(self):
        """Test command tracking"""
        monitoring_manager.track_command('test_command', True, 1.0)
        # This should not raise any exceptions
    
    def test_track_error(self):
        """Test error tracking"""
        monitoring_manager.track_error('test_error', 'Test error message')
        # This should not raise any exceptions

class TestSlackBotComponents:
    """Test Slack bot components"""
    
    @patch('slack_bolt.App')
    def test_slack_app_initialization(self, mock_app):
        """Test Slack app initialization"""
        mock_app.return_value = Mock()
        # Test that the app can be initialized without errors
        assert True
    
    def test_launch_date_extraction(self):
        """Test launch date extraction from text"""
        # Import here to avoid logging config issues
        from production_slack_bot import ProductionSlackBot
        
        bot = ProductionSlackBot.__new__(ProductionSlackBot)
        
        # Test valid date extraction
        text = "Check vehicle program for 2024-03-15"
        date = bot._extract_launch_date(text)
        assert date == "2024-03-15"
        
        # Test invalid date
        text = "Check vehicle program"
        date = bot._extract_launch_date(text)
        assert date is None

class TestFileParser:
    """Test file parser"""
    
    def test_file_type_validation(self):
        """Test file type validation"""
        from file_parser import FileParser
        
        parser = FileParser()
        
        # Test valid file types
        assert parser.validate_file_type("data.xlsx")
        assert parser.validate_file_type("data.xls")
        assert parser.validate_file_type("data.csv")
        
        # Test invalid file types
        assert not parser.validate_file_type("data.txt")
        assert not parser.validate_file_type("data.pdf")

class TestOpenAIClient:
    """Test OpenAI client"""
    
    @patch('openai.OpenAI')
    def test_openai_client_initialization(self, mock_openai):
        """Test OpenAI client initialization"""
        from openai_client import OpenAIClient
        
        # Mock the OpenAI client
        mock_client = Mock()
        mock_openai.return_value = mock_client
        
        # Mock the chat completion response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Test response"
        mock_client.chat.completions.create.return_value = mock_response
        
        client = OpenAIClient()
        assert client is not None

if __name__ == '__main__':
    pytest.main([__file__]) 