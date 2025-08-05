import pytest
import unittest
from unittest.mock import Mock, patch, MagicMock, call
import sys
import os
import json
import time
from datetime import datetime, timedelta
from contextlib import contextmanager

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from monitoring import MonitoringManager, monitor_command, monitor_error

class TestMonitoringManagerComprehensive:
    """Comprehensive tests for MonitoringManager"""
    
    def setup_method(self):
        """Set up test fixtures"""
        with patch('monitoring.logging') as mock_logging:
            self.monitoring_manager = MonitoringManager()
    
    def test_initialization_success(self):
        """Test successful monitoring manager initialization"""
        assert self.monitoring_manager is not None
        assert hasattr(self.monitoring_manager, 'start_time')
        assert hasattr(self.monitoring_manager, 'commands')
        assert hasattr(self.monitoring_manager, 'errors')
        assert hasattr(self.monitoring_manager, 'connection_count')
    
    def test_track_command_success(self):
        """Test successful command tracking"""
        command_name = 'vehicle_query'
        success = True
        response_time = 1500
        
        self.monitoring_manager.track_command(command_name, success, response_time)
        
        # Verify command was tracked
        assert command_name in self.monitoring_manager.commands
        command_data = self.monitoring_manager.commands[command_name]
        assert command_data['count'] == 1
        assert command_data['success_count'] == 1
        assert command_data['total_response_time'] == response_time
        assert command_data['avg_response_time'] == response_time
    
    def test_track_command_failure(self):
        """Test command tracking with failure"""
        command_name = 'vehicle_query'
        success = False
        response_time = 3000
        
        self.monitoring_manager.track_command(command_name, success, response_time)
        
        # Verify command was tracked
        assert command_name in self.monitoring_manager.commands
        command_data = self.monitoring_manager.commands[command_name]
        assert command_data['count'] == 1
        assert command_data['success_count'] == 0
        assert command_data['failure_count'] == 1
        assert command_data['total_response_time'] == response_time
    
    def test_track_command_multiple_calls(self):
        """Test multiple command tracking calls"""
        command_name = 'vehicle_query'
        
        # First call - success
        self.monitoring_manager.track_command(command_name, True, 1000)
        
        # Second call - failure
        self.monitoring_manager.track_command(command_name, False, 2000)
        
        # Third call - success
        self.monitoring_manager.track_command(command_name, True, 1500)
        
        # Verify aggregated data
        command_data = self.monitoring_manager.commands[command_name]
        assert command_data['count'] == 3
        assert command_data['success_count'] == 2
        assert command_data['failure_count'] == 1
        assert command_data['total_response_time'] == 4500
        assert command_data['avg_response_time'] == 1500
    
    def test_track_error_success(self):
        """Test successful error tracking"""
        error_type = 'databricks_error'
        error_message = 'Connection timeout'
        
        self.monitoring_manager.track_error(error_type, error_message)
        
        # Verify error was tracked
        assert error_type in self.monitoring_manager.errors
        error_data = self.monitoring_manager.errors[error_type]
        assert error_data['count'] == 1
        assert error_data['last_message'] == error_message
        assert 'last_occurrence' in error_data
    
    def test_track_error_multiple_calls(self):
        """Test multiple error tracking calls"""
        error_type = 'databricks_error'
        
        # First error
        self.monitoring_manager.track_error(error_type, 'Connection timeout')
        
        # Second error
        self.monitoring_manager.track_error(error_type, 'Authentication failed')
        
        # Verify aggregated data
        error_data = self.monitoring_manager.errors[error_type]
        assert error_data['count'] == 2
        assert error_data['last_message'] == 'Authentication failed'
    
    def test_update_connection_count(self):
        """Test connection count update"""
        initial_count = self.monitoring_manager.connection_count
        
        self.monitoring_manager.update_connection_count()
        
        assert self.monitoring_manager.connection_count == initial_count + 1
    
    def test_get_metrics_success(self):
        """Test successful metrics retrieval"""
        # Add some test data
        self.monitoring_manager.track_command('vehicle_query', True, 1000)
        self.monitoring_manager.track_command('file_upload', False, 2000)
        self.monitoring_manager.track_error('databricks_error', 'Connection timeout')
        self.monitoring_manager.update_connection_count()
        
        metrics = self.monitoring_manager.get_metrics()
        
        # Verify metrics structure
        assert 'uptime' in metrics
        assert 'commands' in metrics
        assert 'errors' in metrics
        assert 'connection_count' in metrics
        assert 'metrics_server_status' in metrics
        
        # Verify command metrics
        assert 'vehicle_query' in metrics['commands']
        assert 'file_upload' in metrics['commands']
        
        # Verify error metrics
        assert 'databricks_error' in metrics['errors']
        
        # Verify connection count
        assert metrics['connection_count'] == 1
    
    def test_get_uptime_success(self):
        """Test uptime calculation"""
        # Mock start time to be 1 hour ago
        with patch.object(self.monitoring_manager, 'start_time') as mock_start_time:
            mock_start_time.replace = Mock(return_value=datetime.now() - timedelta(hours=1))
            
            uptime = self.monitoring_manager.get_uptime()
            
            assert uptime > 0
            assert 'hours' in uptime or 'minutes' in uptime
    
    def test_get_stats_success(self):
        """Test statistics retrieval"""
        # Add test data
        self.monitoring_manager.track_command('vehicle_query', True, 1000)
        self.monitoring_manager.track_command('file_upload', True, 2000)
        self.monitoring_manager.track_command('dashboard', False, 3000)
        
        stats = self.monitoring_manager.get_stats()
        
        # Verify stats structure
        assert 'total_commands' in stats
        assert 'successful_commands' in stats
        assert 'failed_commands' in stats
        assert 'average_response_time' in stats
        assert 'command_breakdown' in stats
        
        # Verify calculated values
        assert stats['total_commands'] == 3
        assert stats['successful_commands'] == 2
        assert stats['failed_commands'] == 1
        assert stats['average_response_time'] == 2000  # (1000 + 2000 + 3000) / 3
    
    def test_reset_metrics_success(self):
        """Test metrics reset"""
        # Add some test data
        self.monitoring_manager.track_command('vehicle_query', True, 1000)
        self.monitoring_manager.track_error('databricks_error', 'Connection timeout')
        self.monitoring_manager.update_connection_count()
        
        # Reset metrics
        self.monitoring_manager.reset_metrics()
        
        # Verify reset
        assert len(self.monitoring_manager.commands) == 0
        assert len(self.monitoring_manager.errors) == 0
        assert self.monitoring_manager.connection_count == 0
    
    def test_start_metrics_server_success(self):
        """Test metrics server start"""
        with patch('monitoring.Flask') as mock_flask, \
             patch('monitoring.threading') as mock_threading:
            
            mock_app = Mock()
            mock_flask.return_value = mock_app
            
            mock_thread = Mock()
            mock_threading.Thread.return_value = mock_thread
            
            self.monitoring_manager.start_metrics_server()
            
            # Verify Flask app was created
            mock_flask.assert_called_once()
            
            # Verify route was added
            mock_app.route.assert_called()
            
            # Verify thread was started
            mock_threading.Thread.assert_called_once()
            mock_thread.start.assert_called_once()
    
    def test_start_metrics_server_error(self):
        """Test metrics server start with error"""
        with patch('monitoring.Flask') as mock_flask:
            mock_flask.side_effect = Exception("Flask error")
            
            # Should handle error gracefully
            self.monitoring_manager.start_metrics_server()
            
            # Verify no exception was raised
    
    def test_comprehensive_tracking(self):
        """Test comprehensive tracking workflow"""
        # Track various commands
        commands = [
            ('vehicle_query', True, 1000),
            ('file_upload', True, 2000),
            ('dashboard', False, 3000),
            ('help', True, 500),
            ('vehicle_query', True, 1500)
        ]
        
        for command, success, response_time in commands:
            self.monitoring_manager.track_command(command, success, response_time)
        
        # Track various errors
        errors = [
            ('databricks_error', 'Connection timeout'),
            ('openai_error', 'API rate limit exceeded'),
            ('file_parser_error', 'Invalid file format'),
            ('databricks_error', 'Authentication failed')
        ]
        
        for error_type, error_message in errors:
            self.monitoring_manager.track_error(error_type, error_message)
        
        # Update connection count
        for _ in range(5):
            self.monitoring_manager.update_connection_count()
        
        # Get comprehensive metrics
        metrics = self.monitoring_manager.get_metrics()
        stats = self.monitoring_manager.get_stats()
        
        # Verify metrics
        assert len(metrics['commands']) == 4  # 4 unique commands
        assert len(metrics['errors']) == 3     # 3 unique error types
        assert metrics['connection_count'] == 5
        
        # Verify stats
        assert stats['total_commands'] == 5
        assert stats['successful_commands'] == 4
        assert stats['failed_commands'] == 1
        assert stats['average_response_time'] == 1600  # (1000 + 2000 + 3000 + 500 + 1500) / 5
    
    def test_error_handling_comprehensive(self):
        """Test comprehensive error handling"""
        # Test various error scenarios
        error_scenarios = [
            (Exception("General error"), "general"),
            (ConnectionError("Network error"), "network"),
            (ValueError("Invalid data"), "data"),
            (TimeoutError("Timeout"), "timeout")
        ]
        
        for exception, error_type in error_scenarios:
            # Test command tracking with exception
            try:
                raise exception
            except Exception as e:
                self.monitoring_manager.track_error(str(type(e).__name__), str(e))
            
            # Test error tracking with exception
            try:
                raise exception
            except Exception as e:
                self.monitoring_manager.track_error(str(type(e).__name__), str(e))
        
        # Verify all errors were tracked
        metrics = self.monitoring_manager.get_metrics()
        assert len(metrics['errors']) >= 4
    
    def test_performance_metrics(self):
        """Test performance of monitoring operations"""
        import time
        
        # Test command tracking performance
        start_time = time.time()
        
        for i in range(1000):
            self.monitoring_manager.track_command(f'command_{i}', True, i)
        
        end_time = time.time()
        
        # Verify operation completed in reasonable time
        duration = end_time - start_time
        assert duration < 1.0  # Should complete within 1 second
        
        # Verify all commands were tracked
        metrics = self.monitoring_manager.get_metrics()
        assert len(metrics['commands']) == 1000
    
    def test_concurrent_access(self):
        """Test concurrent access to monitoring manager"""
        import threading
        import time
        
        results = []
        errors = []
        
        def track_commands():
            try:
                for i in range(100):
                    self.monitoring_manager.track_command(f'thread_command_{i}', True, i)
                results.append(True)
            except Exception as e:
                errors.append(str(e))
        
        # Start multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=track_commands)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all threads completed successfully
        assert len(results) == 5
        assert len(errors) == 0
        
        # Verify all commands were tracked
        metrics = self.monitoring_manager.get_metrics()
        assert len(metrics['commands']) == 500  # 5 threads * 100 commands each

class TestMonitoringDecorators:
    """Tests for monitoring decorators"""
    
    def setup_method(self):
        """Set up test fixtures"""
        with patch('monitoring.logging') as mock_logging:
            self.monitoring_manager = MonitoringManager()
    
    def test_monitor_command_decorator_success(self):
        """Test monitor_command decorator with success"""
        @monitor_command
        def test_function():
            return "success"
        
        result = test_function()
        
        assert result == "success"
        
        # Verify command was tracked
        metrics = self.monitoring_manager.get_metrics()
        assert 'test_function' in metrics['commands']
    
    def test_monitor_command_decorator_failure(self):
        """Test monitor_command decorator with failure"""
        @monitor_command
        def test_function():
            raise Exception("Test error")
        
        with pytest.raises(Exception):
            test_function()
        
        # Verify command was tracked as failure
        metrics = self.monitoring_manager.get_metrics()
        assert 'test_function' in metrics['commands']
        command_data = metrics['commands']['test_function']
        assert command_data['failure_count'] == 1
    
    def test_monitor_command_decorator_with_args(self):
        """Test monitor_command decorator with arguments"""
        @monitor_command
        def test_function(arg1, arg2, kwarg1=None):
            return f"{arg1}_{arg2}_{kwarg1}"
        
        result = test_function("a", "b", kwarg1="c")
        
        assert result == "a_b_c"
        
        # Verify command was tracked
        metrics = self.monitoring_manager.get_metrics()
        assert 'test_function' in metrics['commands']
    
    def test_monitor_error_decorator_success(self):
        """Test monitor_error decorator with success"""
        @monitor_error
        def test_function():
            return "success"
        
        result = test_function()
        
        assert result == "success"
        
        # Verify no error was tracked
        metrics = self.monitoring_manager.get_metrics()
        assert len(metrics['errors']) == 0
    
    def test_monitor_error_decorator_failure(self):
        """Test monitor_error decorator with failure"""
        @monitor_error
        def test_function():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError):
            test_function()
        
        # Verify error was tracked
        metrics = self.monitoring_manager.get_metrics()
        assert 'ValueError' in metrics['errors']
        error_data = metrics['errors']['ValueError']
        assert error_data['count'] == 1
        assert error_data['last_message'] == "Test error"
    
    def test_monitor_error_decorator_custom_error_type(self):
        """Test monitor_error decorator with custom error type"""
        @monitor_error
        def test_function():
            raise ConnectionError("Connection failed")
        
        with pytest.raises(ConnectionError):
            test_function()
        
        # Verify error was tracked
        metrics = self.monitoring_manager.get_metrics()
        assert 'ConnectionError' in metrics['errors']
        error_data = metrics['errors']['ConnectionError']
        assert error_data['count'] == 1
        assert error_data['last_message'] == "Connection failed"

class TestMonitoringIntegration:
    """Integration tests for monitoring system"""
    
    def setup_method(self):
        """Set up test fixtures"""
        with patch('monitoring.logging') as mock_logging:
            self.monitoring_manager = MonitoringManager()
    
    def test_full_monitoring_workflow(self):
        """Test complete monitoring workflow"""
        # Simulate a typical application workflow
        commands = [
            ('vehicle_query', True, 1200),
            ('file_upload', True, 2500),
            ('dashboard', False, 3500),
            ('help', True, 300),
            ('vehicle_query', True, 1100)
        ]
        
        errors = [
            ('databricks_error', 'Connection timeout'),
            ('openai_error', 'Rate limit exceeded'),
            ('file_parser_error', 'Invalid format')
        ]
        
        # Track all commands and errors
        for command, success, response_time in commands:
            self.monitoring_manager.track_command(command, success, response_time)
        
        for error_type, error_message in errors:
            self.monitoring_manager.track_error(error_type, error_message)
        
        # Update connection count
        for _ in range(10):
            self.monitoring_manager.update_connection_count()
        
        # Get comprehensive metrics
        metrics = self.monitoring_manager.get_metrics()
        stats = self.monitoring_manager.get_stats()
        uptime = self.monitoring_manager.get_uptime()
        
        # Verify all data was captured correctly
        assert len(metrics['commands']) == 4  # 4 unique commands
        assert len(metrics['errors']) == 3     # 3 unique errors
        assert metrics['connection_count'] == 10
        
        assert stats['total_commands'] == 5
        assert stats['successful_commands'] == 4
        assert stats['failed_commands'] == 1
        
        assert uptime is not None
        assert len(uptime) > 0
    
    def test_monitoring_persistence(self):
        """Test monitoring data persistence across instances"""
        # Create first instance and add data
        with patch('monitoring.logging') as mock_logging:
            manager1 = MonitoringManager()
            manager1.track_command('test_command', True, 1000)
            manager1.track_error('test_error', 'Test message')
            manager1.update_connection_count()
        
        # Create second instance and verify data is separate
        with patch('monitoring.logging') as mock_logging:
            manager2 = MonitoringManager()
            metrics2 = manager2.get_metrics()
            
            # Verify new instance has no data
            assert len(metrics2['commands']) == 0
            assert len(metrics2['errors']) == 0
            assert metrics2['connection_count'] == 0
    
    def test_monitoring_reset_functionality(self):
        """Test monitoring reset functionality"""
        # Add data to monitoring manager
        self.monitoring_manager.track_command('test_command', True, 1000)
        self.monitoring_manager.track_error('test_error', 'Test message')
        self.monitoring_manager.update_connection_count()
        
        # Verify data exists
        metrics_before = self.monitoring_manager.get_metrics()
        assert len(metrics_before['commands']) == 1
        assert len(metrics_before['errors']) == 1
        assert metrics_before['connection_count'] == 1
        
        # Reset monitoring
        self.monitoring_manager.reset_metrics()
        
        # Verify data was cleared
        metrics_after = self.monitoring_manager.get_metrics()
        assert len(metrics_after['commands']) == 0
        assert len(metrics_after['errors']) == 0
        assert metrics_after['connection_count'] == 0

if __name__ == '__main__':
    pytest.main([__file__]) 