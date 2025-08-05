import pytest
import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import tempfile
import json

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from production_config import ProductionConfig
from database import DatabaseManager
from monitoring import monitoring_manager
from file_parser import FileParser
from openai_client import OpenAIClient
from start_bot import validate_environment

class TestProductionConfigFinal:
    """Final comprehensive tests for production configuration"""
    
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
        assert 'slack_bolt' in loggers
        assert 'openai' in loggers
    
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
        
        # Test standard formatter
        standard_formatter = formatters['standard']
        assert 'format' in standard_formatter
        assert '%(asctime)s' in standard_formatter['format']
    
    def test_logging_config_loggers(self):
        """Test logging configuration loggers"""
        config = ProductionConfig.get_logging_config()
        loggers = config['loggers']
        
        # Test root logger
        root_logger = loggers['']
        assert root_logger['handlers'] == ['console', 'file']
        assert 'level' in root_logger
        assert root_logger['propagate'] is False
        
        # Test slack_bolt logger
        slack_logger = loggers['slack_bolt']
        assert slack_logger['handlers'] == ['console', 'file']
        assert slack_logger['level'] == 'INFO'
        assert slack_logger['propagate'] is False
        
        # Test openai logger
        openai_logger = loggers['openai']
        assert openai_logger['handlers'] == ['console', 'file']
        assert openai_logger['level'] == 'INFO'
        assert openai_logger['propagate'] is False
    
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
        assert 'standard' in config['formatters']
        
        # Test handlers
        assert 'console' in config['handlers']
        assert 'file' in config['handlers']
        
        # Test loggers
        required_loggers = ['', 'slack_bolt', 'openai']
        for logger_name in required_loggers:
            assert logger_name in config['loggers']

class TestDatabaseFinal:
    """Final comprehensive tests for database manager"""
    
    def test_database_manager_initialization(self):
        """Test database manager initialization"""
        db_manager = DatabaseManager()
        assert db_manager.engine is None  # No DATABASE_URL in test environment
    
    def test_health_check_no_database(self):
        """Test health check when no database is available"""
        db_manager = DatabaseManager()
        health = db_manager.health_check()
        assert health['status'] == 'unavailable'
        assert 'Database not configured' in health['message']
    
    def test_get_session_no_database(self):
        """Test getting session when no database is available"""
        db_manager = DatabaseManager()
        session = db_manager.get_session()
        # Should return a context manager even without database
        assert session is not None
    
    def test_bot_metrics_model_minimal(self):
        """Test bot metrics model creation"""
        from database import BotMetrics
        
        # Test creating a minimal bot metrics instance
        metrics = BotMetrics(
            command_name='test_command',
            user_id='test_user',
            success=True,
            execution_time=1.0
        )
        
        assert metrics.command_name == 'test_command'
        assert metrics.user_id == 'test_user'
        assert metrics.success is True
        assert metrics.execution_time == 1.0

class TestMonitoringFinal:
    """Final comprehensive tests for monitoring manager"""
    
    def test_monitoring_manager_exists(self):
        """Test that monitoring manager exists"""
        assert monitoring_manager is not None
        assert hasattr(monitoring_manager, 'start_time')
    
    def test_monitoring_manager_methods(self):
        """Test monitoring manager methods"""
        # Reset metrics for testing
        monitoring_manager.reset_metrics()
        
        # Test tracking commands
        monitoring_manager.track_command('test_command', True, 1.0)
        monitoring_manager.track_command('test_command2', False, 2.0)
        
        # Test tracking errors
        monitoring_manager.track_error('test_error', 'Test error message')
        
        # Test getting metrics
        metrics = monitoring_manager.get_metrics()
        assert isinstance(metrics, dict)
        assert 'commands' in metrics
        assert 'errors' in metrics
    
    def test_monitoring_get_uptime(self):
        """Test monitoring uptime calculation"""
        uptime = monitoring_manager.get_uptime()
        assert isinstance(uptime, str)
        assert 'days' in uptime or 'hours' in uptime or 'minutes' in uptime
    
    def test_monitoring_get_metrics(self):
        """Test getting monitoring metrics"""
        metrics = monitoring_manager.get_metrics()
        assert isinstance(metrics, dict)
        assert 'commands' in metrics
        assert 'errors' in metrics
        assert 'metrics_server_status' in metrics
        assert 'start_time' in metrics
    
    def test_monitoring_reset_metrics(self):
        """Test resetting monitoring metrics"""
        # Track some data first
        monitoring_manager.track_command('test_command', True, 1.0)
        monitoring_manager.track_error('test_error', 'Test error')
        
        # Reset metrics
        monitoring_manager.reset_metrics()
        
        # Check that metrics are reset
        metrics = monitoring_manager.get_metrics()
        assert metrics['commands'] == {}
        assert metrics['errors'] == {}

class TestIntegrationFinal:
    """Final integration tests"""
    
    def test_monitoring_integration(self):
        """Test monitoring integration"""
        # Reset metrics
        monitoring_manager.reset_metrics()
        
        # Track some commands
        monitoring_manager.track_command('test_command', True, 1.0)
        monitoring_manager.track_command('test_command2', False, 2.0)
        monitoring_manager.track_error('test_error', 'Test error message')
        
        # Get metrics
        metrics = monitoring_manager.get_metrics()
        assert 'commands' in metrics
        assert 'errors' in metrics
        
        # Check that commands were tracked
        commands = metrics['commands']
        assert len(commands) > 0
    
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
        # Test with no client (test environment)
        with patch('openai_client.OPENAI_API_KEY', 'test-key'):
            client = OpenAIClient()
            assert client.client is None
            
            # Test processing without client
            result = client.process_vehicle_program_query('2024-03-15', {})
            assert "OpenAI client not configured" in result
    
    def test_comprehensive_workflow(self):
        """Test comprehensive workflow"""
        # Test configuration validation
        with patch.dict(os.environ, {
            'SLACK_BOT_TOKEN': 'xoxb-test',
            'SLACK_SIGNING_SECRET': 'test_secret',
            'SLACK_APP_TOKEN': 'xapp-test',
            'OPENAI_API_KEY': 'sk-test',
            'DATABRICKS_HOST': 'https://test.databricks.com',
            'DATABRICKS_TOKEN': 'dapi-test'
        }):
            validation = ProductionConfig.validate_config()
            assert validation['valid'] is True
        
        # Test monitoring
        monitoring_manager.reset_metrics()
        monitoring_manager.track_command('test_command', True, 1.0)
        metrics = monitoring_manager.get_metrics()
        assert 'commands' in metrics
        
        # Test file parser
        parser = FileParser()
        assert parser.validate_file_type('test.xlsx')
        assert not parser.validate_file_type('test.txt')
        
        # Test database manager
        db_manager = DatabaseManager()
        health = db_manager.health_check()
        assert 'status' in health
        assert 'message' in health

class TestErrorHandlingFinal:
    """Final error handling tests"""
    
    def test_file_parser_error_handling(self):
        """Test file parser error handling"""
        parser = FileParser()
        
        # Test with invalid file type
        with pytest.raises(ValueError):
            parser.parse_excel_file(b"invalid data", "test.txt")
    
    def test_openai_client_error_handling(self):
        """Test OpenAI client error handling"""
        with patch('openai_client.OPENAI_API_KEY', 'test-key'):
            client = OpenAIClient()
            
            # Test analyze_program_status with no client
            result = client.analyze_program_status({}, '2024-03-15')
            assert "encountered an error" in result
    
    def test_database_error_handling(self):
        """Test database error handling"""
        db_manager = DatabaseManager()
        
        # Test health check with no database
        health = db_manager.health_check()
        assert health['status'] == 'unavailable'
        
        # Test get session with no database
        session = db_manager.get_session()
        assert session is not None  # Should return context manager

class TestEdgeCasesFinal:
    """Final edge case tests"""
    
    def test_empty_data_handling(self):
        """Test handling of empty data"""
        # Test monitoring with no data
        monitoring_manager.reset_metrics()
        metrics = monitoring_manager.get_metrics()
        assert metrics['commands'] == {}
        assert metrics['errors'] == {}
    
    def test_none_values_handling(self):
        """Test handling of None values"""
        with patch('openai_client.OPENAI_API_KEY', 'test-key'):
            client = OpenAIClient()
            
            # Test with None values
            result = client._validate_response(None)
            assert "No response received" in result
    
    def test_large_data_handling(self):
        """Test handling of large data sets"""
        # Test monitoring with many commands
        monitoring_manager.reset_metrics()
        
        for i in range(100):
            monitoring_manager.track_command(f'command_{i}', True, 1.0)
        
        metrics = monitoring_manager.get_metrics()
        assert 'commands' in metrics

class TestStartBotFinal:
    """Final tests for start_bot.py"""
    
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

if __name__ == '__main__':
    pytest.main([__file__]) 