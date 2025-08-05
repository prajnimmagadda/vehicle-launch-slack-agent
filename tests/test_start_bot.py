import pytest
import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from start_bot import main, validate_environment

class TestStartBot:
    """Test start_bot module"""
    
    def test_validate_environment_success(self):
        """Test environment validation with all required variables"""
        with patch.dict(os.environ, {
            'SLACK_BOT_TOKEN': 'xoxb-test',
            'SLACK_SIGNING_SECRET': 'test_secret',
            'SLACK_APP_TOKEN': 'xapp-test',
            'OPENAI_API_KEY': 'sk-test',
            'DATABRICKS_HOST': 'https://test.databricks.com',
            'DATABRICKS_TOKEN': 'dapi-test'
        }):
            result = validate_environment()
            assert result is True
    
    def test_validate_environment_missing_variables(self):
        """Test environment validation with missing variables"""
        with patch.dict(os.environ, {}, clear=True):
            result = validate_environment()
            assert result is False
    
    def test_validate_environment_partial_variables(self):
        """Test environment validation with partial variables"""
        with patch.dict(os.environ, {
            'SLACK_BOT_TOKEN': 'xoxb-test',
            'SLACK_SIGNING_SECRET': 'test_secret'
            # Missing other required variables
        }):
            result = validate_environment()
            assert result is False
    
    @patch('start_bot.VehicleProgramSlackBot')
    def test_main_success(self, mock_slack_bot):
        """Test successful main function execution"""
        with patch('start_bot.validate_environment') as mock_validate:
            with patch('start_bot.load_dotenv') as mock_load_dotenv:
                # Mock the bot
                mock_bot_instance = Mock()
                mock_slack_bot.return_value = mock_bot_instance
                
                # Mock successful validation
                mock_validate.return_value = True
                
                main()
                
                # Verify setup was called
                mock_load_dotenv.assert_called_once()
                mock_validate.assert_called_once()
                mock_slack_bot.assert_called_once()
                mock_bot_instance.start.assert_called_once()
    
    @patch('start_bot.VehicleProgramSlackBot')
    def test_main_validation_failure(self, mock_slack_bot):
        """Test main function with validation failure"""
        with patch('start_bot.validate_environment') as mock_validate:
            with patch('start_bot.load_dotenv') as mock_load_dotenv:
                with patch('start_bot.sys') as mock_sys:
                    # Mock validation failure
                    mock_validate.return_value = False
                    
                    main()
                    
                    # Verify bot was not created
                    mock_slack_bot.assert_not_called()
                    mock_sys.exit.assert_called_once_with(1)
    
    @patch('start_bot.VehicleProgramSlackBot')
    def test_main_bot_creation_failure(self, mock_slack_bot):
        """Test main function with bot creation failure"""
        with patch('start_bot.validate_environment') as mock_validate:
            with patch('start_bot.load_dotenv') as mock_load_dotenv:
                with patch('start_bot.sys') as mock_sys:
                    # Mock successful validation
                    mock_validate.return_value = True
                    
                    # Mock bot creation failure
                    mock_slack_bot.side_effect = Exception("Bot creation failed")
                    
                    main()
                    
                    # Verify setup and validation were called
                    mock_load_dotenv.assert_called_once()
                    mock_validate.assert_called_once()
                    mock_sys.exit.assert_called_once_with(1)
    
    @patch('start_bot.VehicleProgramSlackBot')
    def test_main_bot_start_failure(self, mock_slack_bot):
        """Test main function with bot start failure"""
        with patch('start_bot.validate_environment') as mock_validate:
            with patch('start_bot.load_dotenv') as mock_load_dotenv:
                with patch('start_bot.sys') as mock_sys:
                    # Mock successful validation
                    mock_validate.return_value = True
                    
                    # Mock the bot
                    mock_bot_instance = Mock()
                    mock_bot_instance.start.side_effect = Exception("Start failed")
                    mock_slack_bot.return_value = mock_bot_instance
                    
                    main()
                    
                    # Verify bot was created but start failed
                    mock_slack_bot.assert_called_once()
                    mock_bot_instance.start.assert_called_once()
                    mock_sys.exit.assert_called_once_with(1)
    
    def test_environment_variable_validation(self):
        """Test specific environment variable validation"""
        test_cases = [
            # Valid cases
            ({
                'SLACK_BOT_TOKEN': 'xoxb-test',
                'SLACK_SIGNING_SECRET': 'test_secret',
                'SLACK_APP_TOKEN': 'xapp-test',
                'OPENAI_API_KEY': 'sk-test',
                'DATABRICKS_HOST': 'https://test.databricks.com',
                'DATABRICKS_TOKEN': 'dapi-test'
            }, True),
            
            # Missing SLACK_BOT_TOKEN
            ({
                'SLACK_SIGNING_SECRET': 'test_secret',
                'SLACK_APP_TOKEN': 'xapp-test',
                'OPENAI_API_KEY': 'sk-test',
                'DATABRICKS_HOST': 'https://test.databricks.com',
                'DATABRICKS_TOKEN': 'dapi-test'
            }, False),
            
            # Missing OPENAI_API_KEY
            ({
                'SLACK_BOT_TOKEN': 'xoxb-test',
                'SLACK_SIGNING_SECRET': 'test_secret',
                'SLACK_APP_TOKEN': 'xapp-test',
                'DATABRICKS_HOST': 'https://test.databricks.com',
                'DATABRICKS_TOKEN': 'dapi-test'
            }, False),
            
            # Missing DATABRICKS_HOST
            ({
                'SLACK_BOT_TOKEN': 'xoxb-test',
                'SLACK_SIGNING_SECRET': 'test_secret',
                'SLACK_APP_TOKEN': 'xapp-test',
                'OPENAI_API_KEY': 'sk-test',
                'DATABRICKS_TOKEN': 'dapi-test'
            }, False),
        ]
        
        for env_vars, should_succeed in test_cases:
            with patch.dict(os.environ, env_vars):
                result = validate_environment()
                assert result == should_succeed
    
    def test_required_environment_variables(self):
        """Test that all required environment variables are checked"""
        required_vars = [
            'SLACK_BOT_TOKEN',
            'SLACK_SIGNING_SECRET', 
            'SLACK_APP_TOKEN',
            'OPENAI_API_KEY',
            'DATABRICKS_HOST',
            'DATABRICKS_TOKEN'
        ]
        
        # Test with each variable missing individually
        for missing_var in required_vars:
            env_vars = {
                'SLACK_BOT_TOKEN': 'xoxb-test',
                'SLACK_SIGNING_SECRET': 'test_secret',
                'SLACK_APP_TOKEN': 'xapp-test',
                'OPENAI_API_KEY': 'sk-test',
                'DATABRICKS_HOST': 'https://test.databricks.com',
                'DATABRICKS_TOKEN': 'dapi-test'
            }
            del env_vars[missing_var]
            
            with patch.dict(os.environ, env_vars):
                result = validate_environment()
                assert result is False

if __name__ == '__main__':
    pytest.main([__file__]) 