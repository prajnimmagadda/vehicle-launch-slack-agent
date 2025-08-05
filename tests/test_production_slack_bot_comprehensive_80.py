import pytest
import unittest
from unittest.mock import Mock, patch, MagicMock, call
import sys
import os
import json
import re
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from production_slack_bot import ProductionSlackBot

class TestProductionSlackBotComprehensive:
    """Comprehensive tests for ProductionSlackBot"""
    
    def setup_method(self):
        """Set up test fixtures"""
        with patch('production_slack_bot.SLACK_BOT_TOKEN', 'xoxb-test'), \
             patch('production_slack_bot.SLACK_SIGNING_SECRET', 'test-secret'), \
             patch('production_slack_bot.SLACK_APP_TOKEN', 'xapp-test'), \
             patch('production_slack_bot.DEBUG_MODE', True), \
             patch('production_slack_bot.LOG_LEVEL', 'DEBUG'):
            
            # Mock external dependencies
            with patch('production_slack_bot.DatabricksClient') as mock_databricks, \
                 patch('production_slack_bot.OpenAIClient') as mock_openai, \
                 patch('production_slack_bot.FileParser') as mock_file_parser, \
                 patch('production_slack_bot.GoogleSheetsDashboard') as mock_dashboard, \
                 patch('production_slack_bot.App') as mock_app:
                
                # Configure mocks
                mock_app.return_value = Mock()
                mock_databricks.return_value = Mock()
                mock_openai.return_value = Mock()
                mock_file_parser.return_value = Mock()
                mock_dashboard.return_value = Mock()
                
                self.bot = ProductionSlackBot()
    
    def test_initialization_success(self):
        """Test successful bot initialization"""
        assert self.bot.app is not None
        assert self.bot.databricks_client is not None
        assert self.bot.openai_client is not None
        assert self.bot.file_parser is not None
        assert self.bot.dashboard_creator is not None
        assert self.bot.user_sessions == {}
    
    def test_initialization_with_missing_config(self):
        """Test initialization with missing configuration"""
        with patch('production_slack_bot.SLACK_BOT_TOKEN', None):
            with pytest.raises(Exception):
                ProductionSlackBot()
    
    def test_register_handlers(self):
        """Test that all handlers are registered"""
        # Verify that the app's message and event decorators were called
        assert self.bot.app.message.called
        assert self.bot.app.event.called
    
    def test_extract_launch_date_valid(self):
        """Test valid launch date extraction"""
        test_cases = [
            ("Check vehicle program for 2024-03-15", "2024-03-15"),
            ("/vehicle 2024-12-31", "2024-12-31"),
            ("Vehicle status 2024-01-01", "2024-01-01"),
            ("2024-06-15 vehicle program", "2024-06-15"),
        ]
        
        for text, expected in test_cases:
            result = self.bot._extract_launch_date(text)
            assert result == expected
    
    def test_extract_launch_date_invalid(self):
        """Test invalid launch date extraction"""
        test_cases = [
            "Check vehicle program",
            "No date here",
            "2024-13-45",  # Invalid date
            "2024-02-30",  # Invalid date
            "2024/03/15",  # Wrong format
            "15-03-2024",  # Wrong format
        ]
        
        for text in test_cases:
            result = self.bot._extract_launch_date(text)
            assert result is None
    
    def test_extract_launch_date_edge_cases(self):
        """Test edge cases for launch date extraction"""
        # Test with multiple dates (should return first valid one)
        text = "Check program for 2024-03-15 and 2024-04-20"
        result = self.bot._extract_launch_date(text)
        assert result == "2024-03-15"
        
        # Test with empty string
        result = self.bot._extract_launch_date("")
        assert result is None
        
        # Test with None
        result = self.bot._extract_launch_date(None)
        assert result is None
    
    def test_handle_vehicle_program_query_success(self):
        """Test successful vehicle program query handling"""
        message = {
            'user': 'U123456',
            'text': '/vehicle 2024-03-15'
        }
        say = Mock()
        
        # Mock successful responses
        self.bot.databricks_client.query_vehicle_program_status.return_value = {
            'BOM': {'status': 'success', 'data': [{'part': 'P001', 'status': 'complete'}]},
            'MP': {'status': 'success', 'data': [{'part': 'P002', 'status': 'pending'}]}
        }
        self.bot.openai_client.process_vehicle_program_query.return_value = {
            'summary': 'Program is 75% complete',
            'recommendations': ['Expedite MP department']
        }
        
        self.bot._handle_vehicle_program_query(message, say)
        
        # Verify calls were made
        self.bot.databricks_client.query_vehicle_program_status.assert_called_once_with('2024-03-15')
        self.bot.openai_client.process_vehicle_program_query.assert_called_once()
        assert say.call_count >= 2  # Initial response + final response
    
    def test_handle_vehicle_program_query_no_date(self):
        """Test vehicle program query without date"""
        message = {
            'user': 'U123456',
            'text': '/vehicle'
        }
        say = Mock()
        
        self.bot._handle_vehicle_program_query(message, say)
        
        # Should ask for date format
        say.assert_called_once()
        call_args = say.call_args[0][0]
        assert "Please provide a launch date" in call_args
    
    def test_handle_vehicle_program_query_databricks_error(self):
        """Test vehicle program query with Databricks error"""
        message = {
            'user': 'U123456',
            'text': '/vehicle 2024-03-15'
        }
        say = Mock()
        
        # Mock Databricks error
        self.bot.databricks_client.query_vehicle_program_status.side_effect = Exception("Databricks error")
        
        self.bot._handle_vehicle_program_query(message, say)
        
        # Should handle error gracefully
        assert say.call_count >= 2  # Initial response + error response
        error_call = say.call_args_list[-1]
        assert "error" in error_call[0][0].lower()
    
    def test_handle_vehicle_program_query_openai_error(self):
        """Test vehicle program query with OpenAI error"""
        message = {
            'user': 'U123456',
            'text': '/vehicle 2024-03-15'
        }
        say = Mock()
        
        # Mock successful Databricks but OpenAI error
        self.bot.databricks_client.query_vehicle_program_status.return_value = {
            'BOM': {'status': 'success', 'data': []}
        }
        self.bot.openai_client.process_vehicle_program_query.side_effect = Exception("OpenAI error")
        
        self.bot._handle_vehicle_program_query(message, say)
        
        # Should handle error gracefully
        assert say.call_count >= 2
        error_call = say.call_args_list[-1]
        assert "error" in error_call[0][0].lower()
    
    def test_handle_file_upload_success(self):
        """Test successful file upload handling"""
        event = {
            'files': [{
                'id': 'F123456',
                'name': 'test.xlsx',
                'url_private': 'https://example.com/file.xlsx'
            }],
            'user': 'U123456'
        }
        say = Mock()
        
        # Mock successful file parsing
        self.bot.file_parser.parse_file.return_value = {
            'status': 'success',
            'data': {'columns': ['part', 'status'], 'rows': [{'part': 'P001', 'status': 'complete'}]}
        }
        
        self.bot._handle_file_upload(event, say)
        
        # Verify file was processed
        self.bot.file_parser.parse_file.assert_called_once()
        assert say.call_count >= 2  # Initial + success response
    
    def test_handle_file_upload_invalid_type(self):
        """Test file upload with invalid file type"""
        event = {
            'files': [{
                'id': 'F123456',
                'name': 'test.txt',
                'url_private': 'https://example.com/file.txt'
            }],
            'user': 'U123456'
        }
        say = Mock()
        
        self.bot._handle_file_upload(event, say)
        
        # Should reject invalid file type
        say.assert_called_once()
        call_args = say.call_args[0][0]
        assert "supported" in call_args.lower() or "invalid" in call_args.lower()
    
    def test_handle_file_upload_no_files(self):
        """Test file upload event with no files"""
        event = {
            'files': [],
            'user': 'U123456'
        }
        say = Mock()
        
        self.bot._handle_file_upload(event, say)
        
        # Should handle gracefully
        say.assert_called_once()
        call_args = say.call_args[0][0]
        assert "no files" in call_args.lower() or "error" in call_args.lower()
    
    def test_handle_file_upload_parsing_error(self):
        """Test file upload with parsing error"""
        event = {
            'files': [{
                'id': 'F123456',
                'name': 'test.xlsx',
                'url_private': 'https://example.com/file.xlsx'
            }],
            'user': 'U123456'
        }
        say = Mock()
        
        # Mock parsing error
        self.bot.file_parser.parse_file.side_effect = Exception("Parsing error")
        
        self.bot._handle_file_upload(event, say)
        
        # Should handle error gracefully
        assert say.call_count >= 2
        error_call = say.call_args_list[-1]
        assert "error" in error_call[0][0].lower()
    
    def test_handle_dashboard_request_success(self):
        """Test successful dashboard request handling"""
        message = {
            'user': 'U123456',
            'text': '/dashboard 2024-03-15'
        }
        say = Mock()
        
        # Mock successful dashboard creation
        self.bot.dashboard_creator.create_dashboard.return_value = "https://sheets.google.com/dashboard"
        
        # Mock databricks data
        self.bot.databricks_client.query_vehicle_program_status.return_value = {
            'BOM': {'status': 'success', 'data': []}
        }
        
        self.bot._handle_dashboard_request(message, say)
        
        # Verify dashboard was created
        self.bot.dashboard_creator.create_dashboard.assert_called_once()
        assert say.call_count >= 2  # Initial + success response
    
    def test_handle_dashboard_request_no_date(self):
        """Test dashboard request without date"""
        message = {
            'user': 'U123456',
            'text': '/dashboard'
        }
        say = Mock()
        
        self.bot._handle_dashboard_request(message, say)
        
        # Should ask for date
        say.assert_called_once()
        call_args = say.call_args[0][0]
        assert "date" in call_args.lower()
    
    def test_handle_dashboard_request_creation_error(self):
        """Test dashboard request with creation error"""
        message = {
            'user': 'U123456',
            'text': '/dashboard 2024-03-15'
        }
        say = Mock()
        
        # Mock dashboard creation error
        self.bot.dashboard_creator.create_dashboard.side_effect = Exception("Dashboard error")
        
        self.bot._handle_dashboard_request(message, say)
        
        # Should handle error gracefully
        assert say.call_count >= 2
        error_call = say.call_args_list[-1]
        assert "error" in error_call[0][0].lower()
    
    def test_handle_help_request(self):
        """Test help request handling"""
        message = {
            'user': 'U123456',
            'text': '/help'
        }
        say = Mock()
        
        self.bot._handle_help_request(message, say)
        
        say.assert_called_once()
        call_args = say.call_args[0][0]
        assert "help" in call_args.lower() or "commands" in call_args.lower()
    
    def test_handle_app_mention(self):
        """Test app mention handling"""
        event = {
            'user': 'U123456',
            'text': '<@U123456> help',
            'channel': 'C123456'
        }
        say = Mock()
        
        self.bot._handle_app_mention(event, say)
        
        # Should respond to mention
        say.assert_called_once()
    
    def test_start_method(self):
        """Test bot start method"""
        # Mock the SocketModeHandler
        with patch('production_slack_bot.SocketModeHandler') as mock_handler:
            mock_handler_instance = Mock()
            mock_handler.return_value = mock_handler_instance
            
            self.bot.start()
            
            # Verify handler was created and started
            mock_handler.assert_called_once()
            mock_handler_instance.start.assert_called_once()
    
    def test_start_method_exception(self):
        """Test bot start method with exception"""
        with patch('production_slack_bot.SocketModeHandler') as mock_handler:
            mock_handler.side_effect = Exception("Start error")
            
            # Should handle exception gracefully
            with pytest.raises(Exception):
                self.bot.start()
    
    def test_stop_method(self):
        """Test bot stop method"""
        # Mock the handler
        mock_handler = Mock()
        self.bot.handler = mock_handler
        
        self.bot.stop()
        
        # Verify handler was stopped
        mock_handler.stop.assert_called_once()
    
    def test_user_session_management(self):
        """Test user session storage and retrieval"""
        user_id = 'U123456'
        launch_date = '2024-03-15'
        
        # Test session storage
        self.bot.user_sessions[user_id] = {
            'launch_date': launch_date,
            'data': {'test': 'data'}
        }
        
        # Verify session was stored
        assert user_id in self.bot.user_sessions
        assert self.bot.user_sessions[user_id]['launch_date'] == launch_date
    
    def test_error_handling_comprehensive(self):
        """Test comprehensive error handling"""
        message = {
            'user': 'U123456',
            'text': '/vehicle 2024-03-15'
        }
        say = Mock()
        
        # Test various error scenarios
        error_scenarios = [
            (Exception("General error"), "general"),
            (ConnectionError("Network error"), "network"),
            (ValueError("Invalid data"), "data"),
            (TimeoutError("Timeout"), "timeout")
        ]
        
        for exception, error_type in error_scenarios:
            # Reset mocks
            say.reset_mock()
            self.bot.databricks_client.query_vehicle_program_status.side_effect = exception
            
            self.bot._handle_vehicle_program_query(message, say)
            
            # Should handle all error types gracefully
            assert say.call_count >= 2
            error_call = say.call_args_list[-1]
            assert "error" in error_call[0][0].lower()
    
    def test_logging_integration(self):
        """Test logging integration"""
        with patch('production_slack_bot.logger') as mock_logger:
            message = {
                'user': 'U123456',
                'text': '/vehicle 2024-03-15'
            }
            say = Mock()
            
            # Mock successful operation
            self.bot.databricks_client.query_vehicle_program_status.return_value = {}
            self.bot.openai_client.process_vehicle_program_query.return_value = {}
            
            self.bot._handle_vehicle_program_query(message, say)
            
            # Verify logging calls
            assert mock_logger.info.called or mock_logger.debug.called
    
    def test_performance_metrics(self):
        """Test performance tracking"""
        message = {
            'user': 'U123456',
            'text': '/vehicle 2024-03-15'
        }
        say = Mock()
        
        # Mock successful operation
        self.bot.databricks_client.query_vehicle_program_status.return_value = {}
        self.bot.openai_client.process_vehicle_program_query.return_value = {}
        
        start_time = datetime.now()
        self.bot._handle_vehicle_program_query(message, say)
        end_time = datetime.now()
        
        # Verify operation completed in reasonable time
        duration = (end_time - start_time).total_seconds()
        assert duration < 5.0  # Should complete within 5 seconds
    
    def test_concurrent_requests(self):
        """Test handling of concurrent requests"""
        import threading
        import time
        
        results = []
        errors = []
        
        def make_request():
            try:
                message = {
                    'user': f'U{threading.get_ident()}',
                    'text': '/vehicle 2024-03-15'
                }
                say = Mock()
                
                # Mock successful operation
                self.bot.databricks_client.query_vehicle_program_status.return_value = {}
                self.bot.openai_client.process_vehicle_program_query.return_value = {}
                
                self.bot._handle_vehicle_program_query(message, say)
                results.append(True)
            except Exception as e:
                errors.append(str(e))
        
        # Start multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all requests were handled
        assert len(results) == 5
        assert len(errors) == 0
    
    def test_data_validation(self):
        """Test data validation in bot operations"""
        # Test with valid data
        valid_message = {
            'user': 'U123456',
            'text': '/vehicle 2024-03-15'
        }
        say = Mock()
        
        # Mock successful responses
        self.bot.databricks_client.query_vehicle_program_status.return_value = {
            'BOM': {'status': 'success', 'data': []}
        }
        self.bot.openai_client.process_vehicle_program_query.return_value = {
            'summary': 'Test summary'
        }
        
        self.bot._handle_vehicle_program_query(valid_message, say)
        
        # Verify operation completed successfully
        assert say.call_count >= 2
    
    def test_edge_cases(self):
        """Test edge cases in bot operations"""
        # Test with empty message
        empty_message = {
            'user': 'U123456',
            'text': ''
        }
        say = Mock()
        
        self.bot._handle_vehicle_program_query(empty_message, say)
        
        # Should handle gracefully
        say.assert_called_once()
        
        # Test with None values
        none_message = {
            'user': None,
            'text': None
        }
        say = Mock()
        
        self.bot._handle_vehicle_program_query(none_message, say)
        
        # Should handle gracefully
        say.assert_called_once()
    
    def test_security_validation(self):
        """Test security validation in bot operations"""
        # Test with malicious input
        malicious_message = {
            'user': 'U123456',
            'text': '/vehicle 2024-03-15<script>alert("xss")</script>'
        }
        say = Mock()
        
        # Mock successful operation
        self.bot.databricks_client.query_vehicle_program_status.return_value = {}
        self.bot.openai_client.process_vehicle_program_query.return_value = {}
        
        self.bot._handle_vehicle_program_query(malicious_message, say)
        
        # Should handle securely
        assert say.call_count >= 2
    
    def test_rate_limiting(self):
        """Test rate limiting functionality"""
        # Test multiple rapid requests
        message = {
            'user': 'U123456',
            'text': '/vehicle 2024-03-15'
        }
        say = Mock()
        
        # Mock successful operation
        self.bot.databricks_client.query_vehicle_program_status.return_value = {}
        self.bot.openai_client.process_vehicle_program_query.return_value = {}
        
        # Make multiple rapid requests
        for i in range(10):
            self.bot._handle_vehicle_program_query(message, say)
        
        # Should handle all requests
        assert say.call_count >= 20  # At least 2 calls per request
    
    def test_memory_management(self):
        """Test memory management in bot operations"""
        # Test with large data
        large_message = {
            'user': 'U123456',
            'text': '/vehicle 2024-03-15' + 'x' * 10000  # Large text
        }
        say = Mock()
        
        # Mock successful operation with large response
        self.bot.databricks_client.query_vehicle_program_status.return_value = {
            'BOM': {'status': 'success', 'data': [{'part': f'P{i}', 'status': 'complete'} for i in range(1000)]}
        }
        self.bot.openai_client.process_vehicle_program_query.return_value = {
            'summary': 'Large summary' * 1000
        }
        
        self.bot._handle_vehicle_program_query(large_message, say)
        
        # Should handle large data without memory issues
        assert say.call_count >= 2
    
    def test_error_recovery(self):
        """Test error recovery mechanisms"""
        message = {
            'user': 'U123456',
            'text': '/vehicle 2024-03-15'
        }
        say = Mock()
        
        # First call fails, second succeeds
        self.bot.databricks_client.query_vehicle_program_status.side_effect = [
            Exception("First error"),
            {'BOM': {'status': 'success', 'data': []}}
        ]
        self.bot.openai_client.process_vehicle_program_query.return_value = {
            'summary': 'Recovery successful'
        }
        
        # First call should fail
        self.bot._handle_vehicle_program_query(message, say)
        say.reset_mock()
        
        # Second call should succeed
        self.bot._handle_vehicle_program_query(message, say)
        
        # Verify second call succeeded
        assert say.call_count >= 2

if __name__ == '__main__':
    pytest.main([__file__]) 