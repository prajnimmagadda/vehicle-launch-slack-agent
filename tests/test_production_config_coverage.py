import pytest
import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from production_config import ProductionConfig

class TestProductionConfigCoverage:
    """Comprehensive tests for production configuration to improve coverage"""
    
    def test_config_validation_success(self):
        """Test configuration validation with all required variables"""
        with patch.dict(os.environ, {
            'SLACK_BOT_TOKEN': 'xoxb-test',
            'SLACK_SIGNING_SECRET': 'test_secret',
            'SLACK_APP_TOKEN': 'xapp-test',
            'OPENAI_API_KEY': 'sk-test',
            'DATABRICKS_HOST': 'https://test.databricks.com',
            'DATABRICKS_TOKEN': 'dapi-test',
            'DATABASE_URL': 'postgresql://test:test@localhost/test',
            'REDIS_URL': 'redis://localhost:6379'
        }):
            validation = ProductionConfig.validate_config()
            assert validation['valid'] is True
            assert len(validation['errors']) == 0
    
    def test_config_validation_missing_variables(self):
        """Test configuration validation with missing variables"""
        with patch.dict(os.environ, {}, clear=True):
            validation = ProductionConfig.validate_config()
            assert validation['valid'] is False
            assert len(validation['errors']) > 0
            assert 'SLACK_BOT_TOKEN' in str(validation['errors'])
            assert 'OPENAI_API_KEY' in str(validation['errors'])
    
    def test_config_validation_partial_variables(self):
        """Test configuration validation with partial variables"""
        with patch.dict(os.environ, {
            'SLACK_BOT_TOKEN': 'xoxb-test',
            'SLACK_SIGNING_SECRET': 'test_secret'
            # Missing other required variables
        }):
            validation = ProductionConfig.validate_config()
            assert validation['valid'] is False
            assert len(validation['errors']) > 0
    
    def test_logging_config(self):
        """Test logging configuration generation"""
        config = ProductionConfig.get_logging_config()
        
        assert 'version' in config
        assert config['version'] == 1
        assert 'handlers' in config
        assert 'loggers' in config
        assert 'formatters' in config
        
        # Check for required handlers
        handlers = config['handlers']
        assert 'console' in handlers
        assert 'file' in handlers
        
        # Check for required loggers
        loggers = config['loggers']
        assert 'slack_bot' in loggers
        assert 'openai_client' in loggers
        assert 'databricks_client' in loggers
    
    def test_logging_config_handlers(self):
        """Test logging configuration handlers"""
        config = ProductionConfig.get_logging_config()
        handlers = config['handlers']
        
        # Test console handler
        console_handler = handlers['console']
        assert console_handler['class'] == 'logging.StreamHandler'
        assert console_handler['level'] == 'INFO'
        assert 'formatter' in console_handler
        
        # Test file handler
        file_handler = handlers['file']
        assert file_handler['class'] == 'logging.handlers.RotatingFileHandler'
        assert file_handler['level'] == 'DEBUG'
        assert 'formatter' in file_handler
        assert 'filename' in file_handler
    
    def test_logging_config_formatters(self):
        """Test logging configuration formatters"""
        config = ProductionConfig.get_logging_config()
        formatters = config['formatters']
        
        # Test detailed formatter
        detailed_formatter = formatters['detailed']
        assert 'format' in detailed_formatter
        assert '%(asctime)s' in detailed_formatter['format']
        assert '%(name)s' in detailed_formatter['format']
        assert '%(levelname)s' in detailed_formatter['format']
        assert '%(message)s' in detailed_formatter['format']
    
    def test_logging_config_loggers(self):
        """Test logging configuration loggers"""
        config = ProductionConfig.get_logging_config()
        loggers = config['loggers']
        
        # Test slack_bot logger
        slack_logger = loggers['slack_bot']
        assert slack_logger['handlers'] == ['console', 'file']
        assert slack_logger['level'] == 'INFO'
        assert slack_logger['propagate'] is False
        
        # Test openai_client logger
        openai_logger = loggers['openai_client']
        assert openai_logger['handlers'] == ['console', 'file']
        assert openai_logger['level'] == 'INFO'
        assert openai_logger['propagate'] is False
        
        # Test databricks_client logger
        databricks_logger = loggers['databricks_client']
        assert databricks_logger['handlers'] == ['console', 'file']
        assert databricks_logger['level'] == 'INFO'
        assert databricks_logger['propagate'] is False
    
    def test_logging_config_root_logger(self):
        """Test logging configuration root logger"""
        config = ProductionConfig.get_logging_config()
        loggers = config['loggers']
        
        # Test root logger
        root_logger = loggers['']
        assert root_logger['handlers'] == ['console', 'file']
        assert root_logger['level'] == 'INFO'
        assert root_logger['propagate'] is False
    
    def test_validate_config_edge_cases(self):
        """Test configuration validation edge cases"""
        # Test with empty strings
        with patch.dict(os.environ, {
            'SLACK_BOT_TOKEN': '',
            'SLACK_SIGNING_SECRET': '   ',
            'SLACK_APP_TOKEN': 'xapp-test',
            'OPENAI_API_KEY': 'sk-test',
            'DATABRICKS_HOST': 'https://test.databricks.com',
            'DATABRICKS_TOKEN': 'dapi-test'
        }):
            validation = ProductionConfig.validate_config()
            assert validation['valid'] is False
            assert len(validation['errors']) > 0
    
    def test_validate_config_optional_variables(self):
        """Test configuration validation with optional variables"""
        with patch.dict(os.environ, {
            'SLACK_BOT_TOKEN': 'xoxb-test',
            'SLACK_SIGNING_SECRET': 'test_secret',
            'SLACK_APP_TOKEN': 'xapp-test',
            'OPENAI_API_KEY': 'sk-test',
            'DATABRICKS_HOST': 'https://test.databricks.com',
            'DATABRICKS_TOKEN': 'dapi-test'
            # DATABASE_URL and REDIS_URL are optional
        }):
            validation = ProductionConfig.validate_config()
            assert validation['valid'] is True
            assert len(validation['errors']) == 0
    
    def test_get_logging_config_structure(self):
        """Test logging configuration structure"""
        config = ProductionConfig.get_logging_config()
        
        # Test overall structure
        required_keys = ['version', 'disable_existing_loggers', 'formatters', 'handlers', 'loggers']
        for key in required_keys:
            assert key in config
        
        # Test version
        assert config['version'] == 1
        assert config['disable_existing_loggers'] is False
        
        # Test formatters
        assert 'detailed' in config['formatters']
        assert 'simple' in config['formatters']
        
        # Test handlers
        assert 'console' in config['handlers']
        assert 'file' in config['handlers']
        
        # Test loggers
        required_loggers = ['', 'slack_bot', 'openai_client', 'databricks_client', 'file_parser', 'monitoring']
        for logger_name in required_loggers:
            assert logger_name in config['loggers']

if __name__ == '__main__':
    pytest.main([__file__]) 