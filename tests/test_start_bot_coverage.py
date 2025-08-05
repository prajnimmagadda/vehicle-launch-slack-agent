import pytest
import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from start_bot import validate_environment

class TestStartBotCoverage:
    """Comprehensive tests for start_bot.py to improve coverage"""
    
    def test_validate_environment_all_variables_present(self):
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
    
    def test_validate_environment_empty_variables(self):
        """Test environment validation with empty variables"""
        with patch.dict(os.environ, {
            'SLACK_BOT_TOKEN': '',
            'SLACK_SIGNING_SECRET': '   ',
            'SLACK_APP_TOKEN': 'xapp-test',
            'OPENAI_API_KEY': 'sk-test',
            'DATABRICKS_HOST': 'https://test.databricks.com',
            'DATABRICKS_TOKEN': 'dapi-test'
        }):
            result = validate_environment()
            assert result is False
    
    def test_validate_environment_whitespace_variables(self):
        """Test environment validation with whitespace-only variables"""
        with patch.dict(os.environ, {
            'SLACK_BOT_TOKEN': '   ',
            'SLACK_SIGNING_SECRET': '\t\n',
            'SLACK_APP_TOKEN': 'xapp-test',
            'OPENAI_API_KEY': 'sk-test',
            'DATABRICKS_HOST': 'https://test.databricks.com',
            'DATABRICKS_TOKEN': 'dapi-test'
        }):
            result = validate_environment()
            assert result is False
    
    def test_validate_environment_required_variables_list(self):
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
    
    def test_validate_environment_specific_variable_validation(self):
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
            
            # Missing DATABRICKS_TOKEN
            ({
                'SLACK_BOT_TOKEN': 'xoxb-test',
                'SLACK_SIGNING_SECRET': 'test_secret',
                'SLACK_APP_TOKEN': 'xapp-test',
                'OPENAI_API_KEY': 'sk-test',
                'DATABRICKS_HOST': 'https://test.databricks.com'
            }, False),
            
            # Missing SLACK_SIGNING_SECRET
            ({
                'SLACK_BOT_TOKEN': 'xoxb-test',
                'SLACK_APP_TOKEN': 'xapp-test',
                'OPENAI_API_KEY': 'sk-test',
                'DATABRICKS_HOST': 'https://test.databricks.com',
                'DATABRICKS_TOKEN': 'dapi-test'
            }, False),
            
            # Missing SLACK_APP_TOKEN
            ({
                'SLACK_BOT_TOKEN': 'xoxb-test',
                'SLACK_SIGNING_SECRET': 'test_secret',
                'OPENAI_API_KEY': 'sk-test',
                'DATABRICKS_HOST': 'https://test.databricks.com',
                'DATABRICKS_TOKEN': 'dapi-test'
            }, False),
        ]
        
        for env_vars, should_succeed in test_cases:
            with patch.dict(os.environ, env_vars):
                result = validate_environment()
                assert result == should_succeed
    
    def test_validate_environment_edge_cases(self):
        """Test environment validation edge cases"""
        # Test with None values (should not happen in real environment)
        with patch.dict(os.environ, {
            'SLACK_BOT_TOKEN': None,
            'SLACK_SIGNING_SECRET': 'test_secret',
            'SLACK_APP_TOKEN': 'xapp-test',
            'OPENAI_API_KEY': 'sk-test',
            'DATABRICKS_HOST': 'https://test.databricks.com',
            'DATABRICKS_TOKEN': 'dapi-test'
        }):
            result = validate_environment()
            assert result is False
        
        # Test with very long values
        long_value = 'x' * 1000
        with patch.dict(os.environ, {
            'SLACK_BOT_TOKEN': long_value,
            'SLACK_SIGNING_SECRET': long_value,
            'SLACK_APP_TOKEN': long_value,
            'OPENAI_API_KEY': long_value,
            'DATABRICKS_HOST': long_value,
            'DATABRICKS_TOKEN': long_value
        }):
            result = validate_environment()
            assert result is True
    
    def test_validate_environment_special_characters(self):
        """Test environment validation with special characters"""
        with patch.dict(os.environ, {
            'SLACK_BOT_TOKEN': 'xoxb-test!@#$%^&*()',
            'SLACK_SIGNING_SECRET': 'test_secret!@#$%^&*()',
            'SLACK_APP_TOKEN': 'xapp-test!@#$%^&*()',
            'OPENAI_API_KEY': 'sk-test!@#$%^&*()',
            'DATABRICKS_HOST': 'https://test.databricks.com!@#$%^&*()',
            'DATABRICKS_TOKEN': 'dapi-test!@#$%^&*()'
        }):
            result = validate_environment()
            assert result is True
    
    def test_validate_environment_unicode_characters(self):
        """Test environment validation with unicode characters"""
        with patch.dict(os.environ, {
            'SLACK_BOT_TOKEN': 'xoxb-test-🚗',
            'SLACK_SIGNING_SECRET': 'test_secret-🤖',
            'SLACK_APP_TOKEN': 'xapp-test-📊',
            'OPENAI_API_KEY': 'sk-test-🔍',
            'DATABRICKS_HOST': 'https://test.databricks.com-📈',
            'DATABRICKS_TOKEN': 'dapi-test-✅'
        }):
            result = validate_environment()
            assert result is True

if __name__ == '__main__':
    pytest.main([__file__]) 