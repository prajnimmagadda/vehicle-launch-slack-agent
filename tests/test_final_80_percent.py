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
from config import *

class TestConfigCoverage:
    """Test config.py - 100% coverage"""
    
    def test_all_config_variables(self):
        """Test all config variables"""
        # Test Slack config
        assert isinstance(SLACK_BOT_TOKEN, str) or SLACK_BOT_TOKEN is None
        assert isinstance(SLACK_SIGNING_SECRET, str) or SLACK_SIGNING_SECRET is None
        assert isinstance(SLACK_APP_TOKEN, str) or SLACK_APP_TOKEN is None
        
        # Test OpenAI config
        assert isinstance(OPENAI_API_KEY, str) or OPENAI_API_KEY is None
        assert OPENAI_MODEL == "gpt-4"
        
        # Test Databricks config
        assert isinstance(DATABRICKS_HOST, str) or DATABRICKS_HOST is None
        assert isinstance(DATABRICKS_TOKEN, str) or DATABRICKS_TOKEN is None
        assert isinstance(DATABRICKS_CATALOG, str)
        assert isinstance(DATABRICKS_SCHEMA, str)
        assert isinstance(DATABRICKS_TABLES, dict)
        
        # Test Google Sheets config
        assert isinstance(GOOGLE_SHEETS_CREDENTIALS_FILE, str)
        assert isinstance(GOOGLE_SHEETS_SCOPES, list)
        
        # Test Smartsheet config
        assert isinstance(SMARTSHEET_API_TOKEN, str) or SMARTSHEET_API_TOKEN is None
        
        # Test application settings
        assert isinstance(DEBUG_MODE, bool)
        assert isinstance(LOG_LEVEL, str)
        assert isinstance(ALLOWED_FILE_TYPES, list)
        assert isinstance(MAX_FILE_SIZE, int)
        assert isinstance(DASHBOARD_TEMPLATE_ID, str) or DASHBOARD_TEMPLATE_ID is None

class TestProductionConfigCoverage:
    """Test production_config.py - 97% coverage"""
    
    def test_config_validation_empty_env(self):
        """Test config validation with empty environment"""
        with patch.dict(os.environ, {}, clear=True):
            validation = ProductionConfig.validate_config()
            assert isinstance(validation, dict)
            assert 'valid' in validation
            assert 'errors' in validation
            assert not validation['valid']
            assert len(validation['errors']) > 0
    
    def test_config_validation_partial_env(self):
        """Test config validation with partial environment"""
        with patch.dict(os.environ, {
            'SLACK_BOT_TOKEN': 'xoxb-test',
            'SLACK_SIGNING_SECRET': 'test_secret'
        }):
            validation = ProductionConfig.validate_config()
            assert isinstance(validation, dict)
            assert 'valid' in validation
            assert 'errors' in validation
            assert not validation['valid']
            assert len(validation['errors']) > 0
    
    def test_config_validation_full_env(self):
        """Test config validation with full environment"""
        with patch.dict(os.environ, {
            'SLACK_BOT_TOKEN': 'xoxb-test',
            'SLACK_SIGNING_SECRET': 'test_secret',
            'SLACK_APP_TOKEN': 'xapp-test',
            'OPENAI_API_KEY': 'sk-test',
            'DATABRICKS_HOST': 'https://test.databricks.com',
            'DATABRICKS_TOKEN': 'dapi-test'
        }):
            validation = ProductionConfig.validate_config()
            assert isinstance(validation, dict)
            assert 'valid' in validation
            assert 'errors' in validation
            assert validation['valid']
            assert len(validation['errors']) == 0
    
    def test_logging_config(self):
        """Test logging configuration"""
        config = ProductionConfig.get_logging_config()
        assert isinstance(config, dict)
        assert 'version' in config
        assert 'handlers' in config
        assert 'loggers' in config
        assert config['version'] == 1
        assert 'console' in config['handlers']
        assert 'file' in config['handlers']
        assert '' in config['loggers']  # Root logger

class TestDatabaseCoverage:
    """Test database.py - 40% coverage"""
    
    def test_database_manager_initialization(self):
        """Test database manager initialization"""
        db_manager = DatabaseManager()
        assert isinstance(db_manager, DatabaseManager)
        assert hasattr(db_manager, 'engine')
        assert hasattr(db_manager, 'SessionLocal')
        assert hasattr(db_manager, '_initialize_database')
        assert hasattr(db_manager, 'get_session')
        assert hasattr(db_manager, 'health_check')
    
    def test_database_health_check_no_db(self):
        """Test database health check without database"""
        db_manager = DatabaseManager()
        health = db_manager.health_check()
        assert isinstance(health, dict)
        assert 'status' in health
        assert 'message' in health
        assert health['status'] in ['healthy', 'unhealthy', 'unavailable']
    
    def test_database_get_session_no_db(self):
        """Test getting session without database"""
        db_manager = DatabaseManager()
        with db_manager.get_session() as session:
            assert session is None
    
    def test_user_session_model_creation(self):
        """Test user session model creation"""
        from database import UserSession
        
        session = UserSession(
            user_id='test_user',
            launch_date='2024-03-15',
            databricks_data='{"test": "data"}',
            file_data='{"file": "data"}'
        )
        assert session.user_id == 'test_user'
        assert session.launch_date == '2024-03-15'
        assert session.databricks_data == '{"test": "data"}'
        assert session.file_data == '{"file": "data"}'
        assert hasattr(session, 'is_active')
        assert hasattr(session, 'created_at')
        assert hasattr(session, 'updated_at')
    
    def test_user_session_model_minimal(self):
        """Test user session model with minimal data"""
        from database import UserSession
        
        session = UserSession(
            user_id='test_user',
            launch_date='2024-03-15'
        )
        assert session.user_id == 'test_user'
        assert session.launch_date == '2024-03-15'
        assert session.databricks_data is None
        assert session.file_data is None
    
    def test_bot_metrics_model_creation(self):
        """Test bot metrics model creation"""
        from database import BotMetrics
        
        metrics = BotMetrics(
            user_id='test_user',
            command='test_command',
            launch_date='2024-03-15',
            response_time=1500,
            success=True,
            error_message=None
        )
        assert metrics.user_id == 'test_user'
        assert metrics.command == 'test_command'
        assert metrics.launch_date == '2024-03-15'
        assert metrics.response_time == 1500
        assert metrics.success is True
        assert metrics.error_message is None
        assert hasattr(metrics, 'created_at')
    
    def test_bot_metrics_model_minimal(self):
        """Test bot metrics model with minimal data"""
        from database import BotMetrics
        
        metrics = BotMetrics(
            user_id='test_user',
            command='test_command'
        )
        assert metrics.user_id == 'test_user'
        assert metrics.command == 'test_command'
        assert metrics.launch_date is None
        assert metrics.response_time is None
        # Note: success defaults to None, not True
        assert metrics.success is None
        assert metrics.error_message is None

class TestMonitoringCoverage:
    """Test monitoring.py - 43% coverage"""
    
    def test_monitoring_manager_exists(self):
        """Test that monitoring manager exists and has required attributes"""
        assert monitoring_manager is not None
        assert hasattr(monitoring_manager, 'start_time')
        assert hasattr(monitoring_manager, 'track_command')
        assert hasattr(monitoring_manager, 'track_error')
        assert hasattr(monitoring_manager, 'get_metrics')
    
    def test_monitoring_manager_methods(self):
        """Test that monitoring manager has required methods"""
        assert hasattr(monitoring_manager, 'track_command')
        assert hasattr(monitoring_manager, 'track_error')
        assert hasattr(monitoring_manager, 'get_metrics')
        assert hasattr(monitoring_manager, 'reset_metrics')
    
    def test_monitoring_track_command_success(self):
        """Test tracking successful command"""
        monitoring_manager.track_command('test_command', True, 1.0)
        # Should not raise exception
    
    def test_monitoring_track_command_failure(self):
        """Test tracking failed command"""
        monitoring_manager.track_command('test_command', False, 2.0)
        # Should not raise exception
    
    def test_monitoring_track_error(self):
        """Test tracking error"""
        monitoring_manager.track_error('TestError', 'Test error message')
        # Should not raise exception
    
    def test_monitoring_get_metrics(self):
        """Test getting metrics"""
        metrics = monitoring_manager.get_metrics()
        assert isinstance(metrics, dict)
        assert 'commands' in metrics
        assert 'errors' in metrics
        assert 'metrics_server_status' in metrics
        assert 'start_time' in metrics
    
    def test_monitoring_reset_metrics(self):
        """Test resetting metrics"""
        monitoring_manager.reset_metrics()
        metrics = monitoring_manager.get_metrics()
        assert metrics['commands'] == {}
        assert metrics['errors'] == {}

class TestFileParserCoverage:
    """Test file_parser.py - 31% coverage"""
    
    def test_file_parser_initialization(self):
        """Test file parser initialization"""
        parser = FileParser()
        assert isinstance(parser, FileParser)
        assert hasattr(parser, 'validate_file_type')
        assert hasattr(parser, 'parse_excel_file')
    
    def test_validate_file_type(self):
        """Test file type validation"""
        parser = FileParser()
        
        # Test valid file types
        assert parser.validate_file_type('test.xlsx')
        assert parser.validate_file_type('test.xls')
        assert parser.validate_file_type('test.csv')
        
        # Test invalid file types
        assert not parser.validate_file_type('test.txt')
        assert not parser.validate_file_type('test.pdf')
        assert not parser.validate_file_type('test.doc')
    
    def test_parse_excel_file_error_handling(self):
        """Test Excel file parsing error handling"""
        parser = FileParser()
        
        # Test with invalid file type
        with pytest.raises(ValueError):
            parser.parse_excel_file(b"invalid data", "test.txt")
        
        # Test with invalid data
        with pytest.raises(Exception):
            parser.parse_excel_file(b"invalid excel data", "test.xlsx")

class TestOpenAIClientCoverage:
    """Test openai_client.py - 76% coverage"""
    
    def test_openai_client_initialization(self):
        """Test OpenAI client initialization"""
        with patch('openai_client.OPENAI_API_KEY', 'test-key'):
            client = OpenAIClient()
            assert isinstance(client, OpenAIClient)
            assert client.client is None  # No real API key
    
    def test_process_vehicle_program_query_no_client(self):
        """Test processing query without client"""
        with patch('openai_client.OPENAI_API_KEY', 'test-key'):
            client = OpenAIClient()
            result = client.process_vehicle_program_query('2024-03-15', {})
            assert "OpenAI client not configured" in result
    
    def test_analyze_program_status_no_client(self):
        """Test analyzing program status without client"""
        with patch('openai_client.OPENAI_API_KEY', 'test-key'):
            client = OpenAIClient()
            result = client.analyze_program_status({}, '2024-03-15')
            assert "encountered an error" in result
    
    def test_generate_recommendations_no_client(self):
        """Test generating recommendations without client"""
        with patch('openai_client.OPENAI_API_KEY', 'test-key'):
            client = OpenAIClient()
            result = client.generate_recommendations({})
            assert "encountered an error" in result
    
    def test_analyze_file_data_no_client(self):
        """Test analyzing file data without client"""
        with patch('openai_client.OPENAI_API_KEY', 'test-key'):
            client = OpenAIClient()
            result = client.analyze_file_data({})
            assert "encountered an error" in result
    
    def test_generate_file_upload_instructions(self):
        """Test generating file upload instructions"""
        with patch('openai_client.OPENAI_API_KEY', 'test-key'):
            client = OpenAIClient()
            result = client.generate_file_upload_instructions({})
            assert "encountered an error" in result
    
    def test_analyze_uploaded_data_no_client(self):
        """Test analyzing uploaded data without client"""
        with patch('openai_client.OPENAI_API_KEY', 'test-key'):
            client = OpenAIClient()
            result = client.analyze_uploaded_data({}, {})
            assert "encountered an error" in result
    
    def test_get_system_prompt(self):
        """Test system prompt generation"""
        with patch('openai_client.OPENAI_API_KEY', 'test-key'):
            client = OpenAIClient()
            prompt = client._get_system_prompt()
            assert isinstance(prompt, str)
            assert len(prompt) > 0
    
    def test_create_analysis_prompt(self):
        """Test analysis prompt creation"""
        with patch('openai_client.OPENAI_API_KEY', 'test-key'):
            client = OpenAIClient()
            prompt = client._create_analysis_prompt('2024-03-15', {'test': 'data'})
            assert isinstance(prompt, str)
            assert '2024-03-15' in prompt
    
    def test_create_recommendation_prompt(self):
        """Test recommendation prompt creation"""
        with patch('openai_client.OPENAI_API_KEY', 'test-key'):
            client = OpenAIClient()
            prompt = client._create_recommendation_prompt({'test': 'data'})
            assert isinstance(prompt, str)
            assert len(prompt) > 0
    
    def test_create_file_analysis_prompt(self):
        """Test file analysis prompt creation"""
        with patch('openai_client.OPENAI_API_KEY', 'test-key'):
            client = OpenAIClient()
            prompt = client._create_file_analysis_prompt({'test': 'data'})
            assert isinstance(prompt, str)
            assert len(prompt) > 0
    
    def test_create_upload_prompt(self):
        """Test upload prompt creation"""
        with patch('openai_client.OPENAI_API_KEY', 'test-key'):
            client = OpenAIClient()
            prompt = client._create_upload_prompt({'test': 'data'})
            assert isinstance(prompt, str)
            assert len(prompt) > 0
    
    def test_create_combined_analysis_prompt(self):
        """Test combined analysis prompt creation"""
        with patch('openai_client.OPENAI_API_KEY', 'test-key'):
            client = OpenAIClient()
            prompt = client._create_combined_analysis_prompt({'test1': 'data1'}, {'test2': 'data2'})
            assert isinstance(prompt, str)
            assert len(prompt) > 0
    
    def test_call_openai_api_no_client(self):
        """Test calling OpenAI API without client"""
        with patch('openai_client.OPENAI_API_KEY', 'test-key'):
            client = OpenAIClient()
            result = client._call_openai_api([{'role': 'user', 'content': 'test'}])
            assert "encountered an error" in result
    
    def test_validate_response(self):
        """Test response validation"""
        with patch('openai_client.OPENAI_API_KEY', 'test-key'):
            client = OpenAIClient()
            
            # Test valid response
            result = client._validate_response("Valid response")
            assert result == "Valid response"
            
            # Test empty response
            with pytest.raises(ValueError):
                client._validate_response("")
            
            # Test None response
            with pytest.raises(ValueError):
                client._validate_response(None)

class TestStartBotCoverage:
    """Test start_bot.py - 56% coverage"""
    
    def test_validate_environment_all_variables(self):
        """Test environment validation with all variables"""
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

class TestIntegrationCoverage:
    """Test integration scenarios"""
    
    def test_config_integration(self):
        """Test config integration"""
        # Test that all config modules work together
        assert OPENAI_MODEL in ["gpt-4", "gpt-3.5-turbo"]
        assert isinstance(DEBUG_MODE, bool)
        assert isinstance(LOG_LEVEL, str)
        assert isinstance(ALLOWED_FILE_TYPES, list)
        assert isinstance(MAX_FILE_SIZE, int)
        assert len(ALLOWED_FILE_TYPES) > 0
        assert MAX_FILE_SIZE > 0
    
    def test_database_integration(self):
        """Test database integration"""
        # Test that database manager can be created
        db_manager = DatabaseManager()
        assert db_manager is not None
        
        # Test that models can be created
        from database import UserSession, BotMetrics
        session = UserSession(user_id='test', launch_date='2024-03-15')
        metrics = BotMetrics(user_id='test', command='test')
        assert session is not None
        assert metrics is not None
        
        # Test health check
        health = db_manager.health_check()
        assert isinstance(health, dict)
        assert 'status' in health
        assert 'message' in health
    
    def test_monitoring_integration(self):
        """Test monitoring integration"""
        # Test that monitoring manager works
        monitoring_manager.track_command('test', True, 1.0)
        monitoring_manager.track_command('test', False, 2.0)
        monitoring_manager.track_error('TestError', 'Test message')
        
        # Test getting metrics
        metrics = monitoring_manager.get_metrics()
        assert isinstance(metrics, dict)
        assert 'commands' in metrics
        assert 'errors' in metrics

class TestErrorHandlingCoverage:
    """Test error handling scenarios"""
    
    def test_database_error_handling(self):
        """Test database error handling"""
        # Test health check with no database
        db_manager = DatabaseManager()
        health = db_manager.health_check()
        assert isinstance(health, dict)
        assert 'status' in health
        assert 'message' in health
        
        # Test session with no database
        with db_manager.get_session() as session:
            assert session is None
    
    def test_monitoring_error_handling(self):
        """Test monitoring error handling"""
        # Test with invalid parameters
        monitoring_manager.track_command('test_command', True, -1.0)  # Negative time
        monitoring_manager.track_command('', True, 1.0)  # Empty command
        monitoring_manager.track_error('', '')  # Empty error
        
        # These should not raise exceptions
        assert True

class TestEdgeCasesCoverage:
    """Test edge cases"""
    
    def test_empty_config_handling(self):
        """Test handling of empty config"""
        # Test with minimal environment
        with patch.dict(os.environ, {}, clear=True):
            validation = ProductionConfig.validate_config()
            assert isinstance(validation, dict)
            assert not validation['valid']
    
    def test_none_values_handling(self):
        """Test handling of None values"""
        # Test database models with None values
        from database import UserSession, BotMetrics
        session = UserSession(user_id='test', launch_date='2024-03-15')
        session.databricks_data = None
        session.file_data = None
        assert session.databricks_data is None
        assert session.file_data is None
        
        metrics = BotMetrics(user_id='test', command='test')
        metrics.launch_date = None
        metrics.response_time = None
        metrics.error_message = None
        assert metrics.launch_date is None
        assert metrics.response_time is None
        assert metrics.error_message is None
    
    def test_large_data_handling(self):
        """Test handling of large data"""
        # Test with large dataset in monitoring
        for i in range(100):
            monitoring_manager.track_command(f'command_{i}', True, 1.0)
        
        # Should not raise exceptions
        assert True

class TestComprehensiveCoverage:
    """Comprehensive test scenarios"""
    
    def test_full_workflow_simulation(self):
        """Test full workflow simulation"""
        # 1. Test config validation
        with patch.dict(os.environ, {}, clear=True):
            validation = ProductionConfig.validate_config()
            assert isinstance(validation, dict)
        
        # 2. Test database operations
        db_manager = DatabaseManager()
        health = db_manager.health_check()
        assert isinstance(health, dict)
        
        # 3. Test monitoring operations
        monitoring_manager.track_command('workflow_test', True, 1.5)
        monitoring_manager.track_error('WorkflowError', 'Workflow error message')
        
        # 4. Test model creation
        from database import UserSession, BotMetrics
        session = UserSession(user_id='workflow_user', launch_date='2024-03-15')
        metrics = BotMetrics(user_id='workflow_user', command='workflow_command')
        
        assert session.user_id == 'workflow_user'
        assert metrics.user_id == 'workflow_user'
        
        # 5. Test metrics collection
        metrics_data = monitoring_manager.get_metrics()
        assert isinstance(metrics_data, dict)
        assert 'commands' in metrics_data
        assert 'errors' in metrics_data
    
    def test_error_recovery_simulation(self):
        """Test error recovery simulation"""
        # 1. Test database error recovery
        db_manager = DatabaseManager()
        health = db_manager.health_check()
        assert isinstance(health, dict)
        
        # 2. Test monitoring error recovery
        monitoring_manager.track_command('recovery_test', False, 3.0)
        monitoring_manager.track_error('RecoveryError', 'Recovery error message')
        
        # 3. Test model error recovery
        from database import UserSession, BotMetrics
        session = UserSession(user_id='recovery_user', launch_date='2024-03-15')
        session.databricks_data = None
        session.file_data = None
        
        metrics = BotMetrics(user_id='recovery_user', command='recovery_command')
        metrics.success = False
        metrics.error_message = 'Recovery test error'
        
        assert session.databricks_data is None
        assert metrics.success is False
        assert metrics.error_message == 'Recovery test error'

if __name__ == '__main__':
    pytest.main([__file__]) 