import pytest
import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import json
from datetime import datetime, timedelta

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from production_config import ProductionConfig
from database import DatabaseManager, UserSession, BotMetrics
from monitoring import monitoring_manager
from file_parser import FileParser
from openai_client import OpenAIClient
from databricks_client import DatabricksClient

class TestProductionConfigFinal:
    """Final tests for ProductionConfig to achieve 80% coverage"""
    
    def test_config_validation_success(self):
        """Test successful configuration validation"""
        with patch.dict(os.environ, {
            'SLACK_BOT_TOKEN': 'test_token',
            'SLACK_APP_TOKEN': 'test_app_token',
            'OPENAI_API_KEY': 'test_openai_key',
            'DATABRICKS_HOST': 'test_host',
            'DATABRICKS_TOKEN': 'test_token',
            'GOOGLE_CREDENTIALS': 'test_creds',
            'DATABASE_URL': 'test_db_url'
        }):
            config = ProductionConfig()
            assert config.validate_config() is True
    
    def test_config_validation_failure(self):
        """Test configuration validation failure"""
        with patch.dict(os.environ, {}, clear=True):
            config = ProductionConfig()
            assert config.validate_config() is False
    
    def test_logging_config(self):
        """Test logging configuration"""
        config = ProductionConfig()
        logging_config = config.get_logging_config()
        assert 'version' in logging_config
        assert 'handlers' in logging_config
        assert 'loggers' in logging_config

class TestDatabaseManagerFinal:
    """Final tests for DatabaseManager to achieve 80% coverage"""
    
    def test_initialization_with_database_url(self):
        """Test initialization with database URL"""
        with patch.dict(os.environ, {'DATABASE_URL': 'sqlite:///test.db'}):
            db_manager = DatabaseManager()
            assert db_manager is not None
    
    def test_initialization_without_database_url(self):
        """Test initialization without database URL"""
        with patch.dict(os.environ, {}, clear=True):
            db_manager = DatabaseManager()
            assert db_manager is not None
    
    def test_store_user_session_success(self):
        """Test storing user session successfully"""
        db_manager = DatabaseManager()
        session_data = {
            'user_id': 'U123',
            'channel_id': 'C123',
            'file_data': {'test': 'data'}
        }
        result = db_manager.store_user_session(**session_data)
        assert result is True
    
    def test_store_user_session_error(self):
        """Test storing user session with error"""
        db_manager = DatabaseManager()
        # Test with invalid data to trigger error
        result = db_manager.store_user_session('invalid', 'invalid', None)
        assert result is False
    
    def test_get_user_session_success(self):
        """Test getting user session successfully"""
        db_manager = DatabaseManager()
        # First store a session
        db_manager.store_user_session('U123', 'C123', {'test': 'data'})
        # Then retrieve it
        session = db_manager.get_user_session('U123')
        assert session is not None
    
    def test_get_user_session_not_found(self):
        """Test getting user session that doesn't exist"""
        db_manager = DatabaseManager()
        session = db_manager.get_user_session('nonexistent')
        assert session is None
    
    def test_store_metrics_success(self):
        """Test storing metrics successfully"""
        db_manager = DatabaseManager()
        metrics_data = {
            'command_name': 'test_command',
            'success': True,
            'response_time': 1.5
        }
        result = db_manager.store_metrics(**metrics_data)
        assert result is True
    
    def test_store_metrics_error(self):
        """Test storing metrics with error"""
        db_manager = DatabaseManager()
        # Test with invalid data to trigger error
        result = db_manager.store_metrics('invalid', 'invalid', 'invalid')
        assert result is False
    
    def test_get_metrics_summary_success(self):
        """Test getting metrics summary successfully"""
        db_manager = DatabaseManager()
        # Add some test data
        db_manager.store_metrics('test_cmd', True, 1.0)
        db_manager.store_metrics('test_cmd', True, 2.0)
        
        summary = db_manager.get_metrics_summary()
        assert 'total_commands' in summary
        assert 'success_rate' in summary
        assert 'avg_response_time' in summary
    
    def test_get_metrics_summary_no_data(self):
        """Test getting metrics summary with no data"""
        db_manager = DatabaseManager()
        summary = db_manager.get_metrics_summary()
        assert 'total_commands' in summary
        assert summary['total_commands'] == 0
    
    def test_cleanup_old_data_success(self):
        """Test cleaning up old data successfully"""
        db_manager = DatabaseManager()
        # Add some test data
        db_manager.store_user_session('U123', 'C123', {'test': 'data'})
        db_manager.store_metrics('test_cmd', True, 1.0)
        
        # Clean up old data
        result = db_manager.cleanup_old_data()
        assert result is not None
    
    def test_cleanup_old_data_no_data(self):
        """Test cleaning up old data when no data exists"""
        db_manager = DatabaseManager()
        result = db_manager.cleanup_old_data()
        assert result == 0
    
    def test_health_check_healthy(self):
        """Test health check when database is healthy"""
        db_manager = DatabaseManager()
        health = db_manager.health_check()
        assert 'status' in health
        assert 'message' in health
    
    def test_health_check_no_database(self):
        """Test health check when no database is configured"""
        with patch.dict(os.environ, {}, clear=True):
            db_manager = DatabaseManager()
            health = db_manager.health_check()
            assert 'status' in health
            assert 'message' in health

class TestMonitoringManagerFinal:
    """Final tests for MonitoringManager to achieve 80% coverage"""
    
    def test_track_command_success(self):
        """Test tracking command success"""
        monitoring_manager.track_command('test_cmd', True, 1.0)
        metrics = monitoring_manager.get_metrics_summary()
        assert 'total_commands' in metrics
    
    def test_track_command_failure(self):
        """Test tracking command failure"""
        monitoring_manager.track_command('test_cmd', False, 2.0)
        metrics = monitoring_manager.get_metrics_summary()
        assert 'total_commands' in metrics
    
    def test_track_error(self):
        """Test tracking error"""
        monitoring_manager.track_error('test_error', 'Error message')
        metrics = monitoring_manager.get_metrics_summary()
        assert 'total_commands' in metrics
    
    def test_get_metrics_summary(self):
        """Test getting metrics summary"""
        # Add some test data
        monitoring_manager.track_command('test_cmd', True, 1.0)
        monitoring_manager.track_error('test_error', 'Error message')
        
        summary = monitoring_manager.get_metrics_summary()
        assert 'total_commands' in summary
        assert 'success_rate' in summary
        assert 'uptime_hours' in summary
    
    def test_reset_metrics(self):
        """Test resetting metrics"""
        # Add some test data
        monitoring_manager.track_command('test_cmd', True, 1.0)
        
        # Reset metrics
        monitoring_manager.reset_metrics()
        
        # Check that metrics are reset
        summary = monitoring_manager.get_metrics_summary()
        assert summary['total_commands'] == 0

class TestFileParserFinal:
    """Final tests for FileParser to achieve 80% coverage"""
    
    def test_parse_excel_file_success(self):
        """Test parsing Excel file successfully"""
        parser = FileParser()
        
        # Create a mock Excel file
        mock_data = {
            'columns': ['part_number', 'status'],
            'data': [{'part_number': 'P001', 'status': 'Complete'}]
        }
        
        with patch('pandas.read_excel') as mock_read_excel:
            mock_read_excel.return_value = Mock()
            mock_read_excel.return_value.to_dict.return_value = mock_data
            
            result = parser.parse_excel_file('test.xlsx')
            assert 'columns' in result
            assert 'data' in result
    
    def test_parse_excel_file_error(self):
        """Test parsing Excel file with error"""
        parser = FileParser()
        
        with patch('pandas.read_excel', side_effect=Exception('File error')):
            result = parser.parse_excel_file('invalid.xlsx')
            assert 'error' in result
    
    def test_parse_google_sheet_success(self):
        """Test parsing Google Sheet successfully"""
        parser = FileParser()
        
        mock_data = {
            'columns': ['part_id', 'description'],
            'data': [{'part_id': 'P001', 'description': 'Test part'}]
        }
        
        with patch('gspread.authorize') as mock_authorize:
            mock_sheet = Mock()
            mock_sheet.get_all_records.return_value = mock_data['data']
            mock_authorize.return_value.open_by_key.return_value.sheet1 = mock_sheet
            
            result = parser.parse_google_sheet('test_sheet_id')
            assert 'columns' in result
            assert 'data' in result
    
    def test_parse_google_sheet_error(self):
        """Test parsing Google Sheet with error"""
        parser = FileParser()
        
        with patch('gspread.authorize', side_effect=Exception('Auth error')):
            result = parser.parse_google_sheet('invalid_sheet_id')
            assert 'error' in result
    
    def test_parse_smartsheet_success(self):
        """Test parsing Smartsheet successfully"""
        parser = FileParser()
        
        mock_data = {
            'columns': ['part_number', 'status'],
            'data': [{'part_number': 'P001', 'status': 'In Progress'}]
        }
        
        with patch('smartsheet.Smartsheet') as mock_smartsheet:
            mock_sheet = Mock()
            mock_sheet.to_dict.return_value = mock_data
            mock_smartsheet.return_value.Sheets.get_sheet.return_value = mock_sheet
            
            result = parser.parse_smartsheet('test_sheet_id')
            assert 'columns' in result
            assert 'data' in result
    
    def test_parse_smartsheet_error(self):
        """Test parsing Smartsheet with error"""
        parser = FileParser()
        
        with patch('smartsheet.Smartsheet', side_effect=Exception('API error')):
            result = parser.parse_smartsheet('invalid_sheet_id')
            assert 'error' in result

class TestOpenAIClientFinal:
    """Final tests for OpenAIClient to achieve 80% coverage"""
    
    def test_initialization_success(self):
        """Test successful initialization"""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'}):
            client = OpenAIClient()
            assert client is not None
    
    def test_initialization_no_api_key(self):
        """Test initialization without API key"""
        with patch.dict(os.environ, {}, clear=True):
            client = OpenAIClient()
            assert client is not None
    
    def test_process_vehicle_program_query_success(self):
        """Test processing vehicle program query successfully"""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'}):
            client = OpenAIClient()
            
            with patch('openai.OpenAI') as mock_openai:
                mock_response = Mock()
                mock_response.choices = [Mock()]
                mock_response.choices[0].message.content = 'Test response'
                mock_openai.return_value.chat.completions.create.return_value = mock_response
                
                result = client.process_vehicle_program_query('Test query', '2024-01-01')
                assert 'Test response' in result
    
    def test_process_vehicle_program_query_error(self):
        """Test processing vehicle program query with error"""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'}):
            client = OpenAIClient()
            
            with patch('openai.OpenAI', side_effect=Exception('API error')):
                result = client.process_vehicle_program_query('Test query', '2024-01-01')
                assert 'error' in result.lower()
    
    def test_generate_recommendations_success(self):
        """Test generating recommendations successfully"""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'}):
            client = OpenAIClient()
            
            with patch('openai.OpenAI') as mock_openai:
                mock_response = Mock()
                mock_response.choices = [Mock()]
                mock_response.choices[0].message.content = 'Test recommendations'
                mock_openai.return_value.chat.completions.create.return_value = mock_response
                
                result = client.generate_recommendations('Test data')
                assert 'Test recommendations' in result
    
    def test_generate_recommendations_error(self):
        """Test generating recommendations with error"""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'}):
            client = OpenAIClient()
            
            with patch('openai.OpenAI', side_effect=Exception('API error')):
                result = client.generate_recommendations('Test data')
                assert 'error' in result.lower()
    
    def test_analyze_file_data_success(self):
        """Test analyzing file data successfully"""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'}):
            client = OpenAIClient()
            
            with patch('openai.OpenAI') as mock_openai:
                mock_response = Mock()
                mock_response.choices = [Mock()]
                mock_response.choices[0].message.content = 'Test analysis'
                mock_openai.return_value.chat.completions.create.return_value = mock_response
                
                result = client.analyze_file_data('Test file data')
                assert 'Test analysis' in result
    
    def test_analyze_file_data_error(self):
        """Test analyzing file data with error"""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'}):
            client = OpenAIClient()
            
            with patch('openai.OpenAI', side_effect=Exception('API error')):
                result = client.analyze_file_data('Test file data')
                assert 'error' in result.lower()

class TestDatabricksClientFinal:
    """Final tests for DatabricksClient to achieve 80% coverage"""
    
    def test_initialization_success(self):
        """Test successful initialization"""
        with patch.dict(os.environ, {
            'DATABRICKS_HOST': 'test_host',
            'DATABRICKS_TOKEN': 'test_token'
        }):
            client = DatabricksClient()
            assert client is not None
    
    def test_initialization_no_credentials(self):
        """Test initialization without credentials"""
        with patch.dict(os.environ, {}, clear=True):
            client = DatabricksClient()
            assert client is not None
    
    def test_execute_statement_success(self):
        """Test executing statement successfully"""
        with patch.dict(os.environ, {
            'DATABRICKS_HOST': 'test_host',
            'DATABRICKS_TOKEN': 'test_token'
        }):
            client = DatabricksClient()
            
            with patch('databricks.connect') as mock_connect:
                mock_connection = Mock()
                mock_cursor = Mock()
                mock_cursor.fetchall.return_value = [{'result': 'test'}]
                mock_connection.cursor.return_value = mock_cursor
                mock_connect.return_value = mock_connection
                
                result = client.execute_statement('SELECT * FROM test')
                assert result is not None
    
    def test_execute_statement_error(self):
        """Test executing statement with error"""
        with patch.dict(os.environ, {
            'DATABRICKS_HOST': 'test_host',
            'DATABRICKS_TOKEN': 'test_token'
        }):
            client = DatabricksClient()
            
            with patch('databricks.connect', side_effect=Exception('Connection error')):
                result = client.execute_statement('SELECT * FROM test')
                assert result is None
    
    def test_get_bill_of_materials_success(self):
        """Test getting bill of materials successfully"""
        with patch.dict(os.environ, {
            'DATABRICKS_HOST': 'test_host',
            'DATABRICKS_TOKEN': 'test_token'
        }):
            client = DatabricksClient()
            
            with patch.object(client, 'execute_statement') as mock_execute:
                mock_execute.return_value = [{'part_number': 'P001', 'quantity': 5}]
                
                result = client.get_bill_of_materials('2024-01-01')
                assert result is not None
    
    def test_get_bill_of_materials_error(self):
        """Test getting bill of materials with error"""
        with patch.dict(os.environ, {
            'DATABRICKS_HOST': 'test_host',
            'DATABRICKS_TOKEN': 'test_token'
        }):
            client = DatabricksClient()
            
            with patch.object(client, 'execute_statement', return_value=None):
                result = client.get_bill_of_materials('2024-01-01')
                assert result is None
    
    def test_get_master_parts_list_success(self):
        """Test getting master parts list successfully"""
        with patch.dict(os.environ, {
            'DATABRICKS_HOST': 'test_host',
            'DATABRICKS_TOKEN': 'test_token'
        }):
            client = DatabricksClient()
            
            with patch.object(client, 'execute_statement') as mock_execute:
                mock_execute.return_value = [{'part_id': 'P001', 'description': 'Test part'}]
                
                result = client.get_master_parts_list('2024-01-01')
                assert result is not None
    
    def test_get_master_parts_list_error(self):
        """Test getting master parts list with error"""
        with patch.dict(os.environ, {
            'DATABRICKS_HOST': 'test_host',
            'DATABRICKS_TOKEN': 'test_token'
        }):
            client = DatabricksClient()
            
            with patch.object(client, 'execute_statement', return_value=None):
                result = client.get_master_parts_list('2024-01-01')
                assert result is None

class TestIntegrationFinal:
    """Final integration tests to achieve 80% coverage"""
    
    def test_database_monitoring_integration(self):
        """Test database and monitoring integration"""
        # Test database operations
        db_manager = DatabaseManager()
        db_manager.store_user_session('U123', 'C123', {'test': 'data'})
        db_manager.store_metrics('test_cmd', True, 1.0)
        
        # Test monitoring operations
        monitoring_manager.track_command('test_cmd', True, 1.0)
        monitoring_manager.track_error('test_error', 'Error message')
        
        # Verify both systems work together
        db_summary = db_manager.get_metrics_summary()
        monitoring_summary = monitoring_manager.get_metrics_summary()
        
        assert 'total_commands' in db_summary
        assert 'total_commands' in monitoring_summary
    
    def test_file_parser_openai_integration(self):
        """Test file parser and OpenAI integration"""
        # Test file parsing
        parser = FileParser()
        
        with patch('pandas.read_excel') as mock_read_excel:
            mock_data = {
                'columns': ['part_number', 'status'],
                'data': [{'part_number': 'P001', 'status': 'Complete'}]
            }
            mock_read_excel.return_value = Mock()
            mock_read_excel.return_value.to_dict.return_value = mock_data
            
            parsed_data = parser.parse_excel_file('test.xlsx')
            assert 'columns' in parsed_data
        
        # Test OpenAI analysis
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'}):
            client = OpenAIClient()
            
            with patch('openai.OpenAI') as mock_openai:
                mock_response = Mock()
                mock_response.choices = [Mock()]
                mock_response.choices[0].message.content = 'Test analysis'
                mock_openai.return_value.chat.completions.create.return_value = mock_response
                
                analysis = client.analyze_file_data(str(parsed_data))
                assert 'Test analysis' in analysis
    
    def test_databricks_openai_integration(self):
        """Test Databricks and OpenAI integration"""
        # Test Databricks query
        with patch.dict(os.environ, {
            'DATABRICKS_HOST': 'test_host',
            'DATABRICKS_TOKEN': 'test_token'
        }):
            client = DatabricksClient()
            
            with patch('databricks.connect') as mock_connect:
                mock_connection = Mock()
                mock_cursor = Mock()
                mock_cursor.fetchall.return_value = [{'part_number': 'P001', 'quantity': 5}]
                mock_connection.cursor.return_value = mock_cursor
                mock_connect.return_value = mock_connection
                
                bom_data = client.get_bill_of_materials('2024-01-01')
                assert bom_data is not None
        
        # Test OpenAI analysis of Databricks data
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'}):
            client = OpenAIClient()
            
            with patch('openai.OpenAI') as mock_openai:
                mock_response = Mock()
                mock_response.choices = [Mock()]
                mock_response.choices[0].message.content = 'BOM analysis'
                mock_openai.return_value.chat.completions.create.return_value = mock_response
                
                analysis = client.process_vehicle_program_query('Analyze BOM', '2024-01-01')
                assert 'BOM analysis' in analysis

if __name__ == '__main__':
    pytest.main([__file__, '-v']) 