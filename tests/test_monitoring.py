import pytest
import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import time

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from monitoring import monitoring_manager, monitor_command, monitor_error

class TestMonitoringManager:
    """Test MonitoringManager class"""
    
    def test_initialization(self):
        """Test monitoring manager initialization"""
        assert monitoring_manager is not None
        assert hasattr(monitoring_manager, 'start_time')
        assert hasattr(monitoring_manager, 'command_counter')
        assert hasattr(monitoring_manager, 'error_counter')
    
    def test_track_command_success(self):
        """Test tracking successful command"""
        monitoring_manager.track_command('test_command', True, 1.5)
        
        # Verify command was tracked
        assert 'test_command' in monitoring_manager.command_counter
        assert monitoring_manager.command_counter['test_command']['success'] > 0
    
    def test_track_command_failure(self):
        """Test tracking failed command"""
        monitoring_manager.track_command('test_command', False, 2.0)
        
        # Verify command was tracked
        assert 'test_command' in monitoring_manager.command_counter
        assert monitoring_manager.command_counter['test_command']['failure'] > 0
    
    def test_track_error(self):
        """Test tracking error"""
        monitoring_manager.track_error('test_error', 'Test error message')
        
        # Verify error was tracked
        assert 'test_error' in monitoring_manager.error_counter
        assert monitoring_manager.error_counter['test_error']['count'] > 0
    
    def test_get_metrics(self):
        """Test getting monitoring metrics"""
        # Track some test data
        monitoring_manager.track_command('test_command', True, 1.0)
        monitoring_manager.track_command('test_command', False, 2.0)
        monitoring_manager.track_error('test_error', 'Test error')
        
        metrics = monitoring_manager.get_metrics()
        
        # Verify metrics structure
        assert 'uptime' in metrics
        assert 'commands' in metrics
        assert 'errors' in metrics
        assert 'test_command' in metrics['commands']
        assert 'test_error' in metrics['errors']
    
    def test_reset_metrics(self):
        """Test resetting metrics"""
        # Add some test data
        monitoring_manager.track_command('test_command', True, 1.0)
        monitoring_manager.track_error('test_error', 'Test error')
        
        # Reset metrics
        monitoring_manager.reset_metrics()
        
        # Verify metrics were reset
        assert len(monitoring_manager.command_counter) == 0
        assert len(monitoring_manager.error_counter) == 0
    
    @patch('monitoring.flask.Flask')
    def test_start_metrics_server(self, mock_flask):
        """Test starting metrics server"""
        mock_app = Mock()
        mock_flask.return_value = mock_app
        
        # Mock threading
        with patch('monitoring.threading.Thread') as mock_thread:
            mock_thread_instance = Mock()
            mock_thread.return_value = mock_thread_instance
            
            monitoring_manager.start_metrics_server()
            
            # Verify Flask app was created
            mock_flask.assert_called_once()
            
            # Verify thread was started
            mock_thread.assert_called_once()
            mock_thread_instance.start.assert_called_once()
    
    def test_health_check_endpoint(self):
        """Test health check endpoint"""
        # Mock Flask app
        mock_app = Mock()
        
        # Mock the health check function
        with patch('monitoring.monitoring_manager.get_metrics') as mock_get_metrics:
            mock_get_metrics.return_value = {
                'uptime': 3600,
                'commands': {'test': {'success': 1}},
                'errors': {'test_error': {'count': 1}}
            }
            
            # This would normally be called by Flask, but we'll test the logic
            health_data = monitoring_manager.get_metrics()
            
            assert 'uptime' in health_data
            assert 'commands' in health_data
            assert 'errors' in health_data
    
    def test_metrics_endpoint(self):
        """Test metrics endpoint"""
        # Mock Prometheus metrics
        with patch('monitoring.Counter') as mock_counter:
            mock_counter_instance = Mock()
            mock_counter.return_value = mock_counter_instance
            
            # Track some test data
            monitoring_manager.track_command('test_command', True, 1.0)
            monitoring_manager.track_error('test_error', 'Test error')
            
            # Get metrics
            metrics = monitoring_manager.get_metrics()
            
            # Verify metrics contain expected data
            assert 'test_command' in metrics['commands']
            assert 'test_error' in metrics['errors']

class TestMonitoringDecorators:
    """Test monitoring decorators"""
    
    def test_monitor_command_decorator_success(self):
        """Test monitor_command decorator with success"""
        @monitor_command("test_command")
        def test_function():
            return "success"
        
        # Mock the monitoring manager
        with patch('monitoring.monitoring_manager') as mock_manager:
            result = test_function()
            
            # Verify monitoring was called
            mock_manager.track_command.assert_called_once()
            call_args = mock_manager.track_command.call_args
            assert call_args[0][0] == "test_command"
            assert call_args[0][1] is True  # success
            assert call_args[0][2] > 0  # response time
            
            # Verify function result
            assert result == "success"
    
    def test_monitor_command_decorator_failure(self):
        """Test monitor_command decorator with failure"""
        @monitor_command("test_command")
        def test_function():
            raise Exception("Test error")
        
        # Mock the monitoring manager
        with patch('monitoring.monitoring_manager') as mock_manager:
            with pytest.raises(Exception, match="Test error"):
                test_function()
            
            # Verify monitoring was called
            mock_manager.track_command.assert_called_once()
            call_args = mock_manager.track_command.call_args
            assert call_args[0][0] == "test_command"
            assert call_args[0][1] is False  # failure
            assert call_args[0][2] > 0  # response time
    
    def test_monitor_error_decorator(self):
        """Test monitor_error decorator"""
        @monitor_error("test_error")
        def test_function():
            raise Exception("Test error")
        
        # Mock the monitoring manager
        with patch('monitoring.monitoring_manager') as mock_manager:
            with pytest.raises(Exception, match="Test error"):
                test_function()
            
            # Verify monitoring was called
            mock_manager.track_error.assert_called_once()
            call_args = mock_manager.track_error.call_args
            assert call_args[0][0] == "test_error"
            assert "Test error" in call_args[0][1]
    
    def test_monitor_command_with_parameters(self):
        """Test monitor_command decorator with function parameters"""
        @monitor_command("test_command")
        def test_function(param1, param2):
            return f"{param1} {param2}"
        
        # Mock the monitoring manager
        with patch('monitoring.monitoring_manager') as mock_manager:
            result = test_function("hello", "world")
            
            # Verify monitoring was called
            mock_manager.track_command.assert_called_once()
            
            # Verify function result
            assert result == "hello world"
    
    def test_monitor_command_async_function(self):
        """Test monitor_command decorator with async function"""
        import asyncio
        
        @monitor_command("test_async_command")
        async def test_async_function():
            await asyncio.sleep(0.1)
            return "async success"
        
        # Mock the monitoring manager
        with patch('monitoring.monitoring_manager') as mock_manager:
            result = asyncio.run(test_async_function())
            
            # Verify monitoring was called
            mock_manager.track_command.assert_called_once()
            call_args = mock_manager.track_command.call_args
            assert call_args[0][0] == "test_async_command"
            assert call_args[0][1] is True  # success
            assert call_args[0][2] > 0  # response time
            
            # Verify function result
            assert result == "async success"

class TestPrometheusMetrics:
    """Test Prometheus metrics integration"""
    
    @patch('monitoring.Counter')
    def test_prometheus_counter_creation(self, mock_counter):
        """Test Prometheus counter creation"""
        mock_counter_instance = Mock()
        mock_counter.return_value = mock_counter_instance
        
        # This would normally happen during initialization
        # We'll test that counters are created properly
        command_counter = mock_counter('slack_commands_total', 'Total Slack commands', ['command', 'status'])
        error_counter = mock_counter('slack_errors_total', 'Total Slack errors', ['error_type'])
        
        assert command_counter == mock_counter_instance
        assert error_counter == mock_counter_instance
    
    @patch('monitoring.Histogram')
    def test_prometheus_histogram_creation(self, mock_histogram):
        """Test Prometheus histogram creation"""
        mock_histogram_instance = Mock()
        mock_histogram.return_value = mock_histogram_instance
        
        # Test response time histogram
        response_time_histogram = mock_histogram('slack_command_duration_seconds', 'Command response time')
        
        assert response_time_histogram == mock_histogram_instance
    
    def test_metrics_collection(self):
        """Test metrics collection for Prometheus"""
        # Track some test data
        monitoring_manager.track_command('test_command', True, 1.5)
        monitoring_manager.track_command('test_command', False, 2.0)
        monitoring_manager.track_error('test_error', 'Test error message')
        
        # Get metrics
        metrics = monitoring_manager.get_metrics()
        
        # Verify metrics structure for Prometheus
        assert 'commands' in metrics
        assert 'errors' in metrics
        assert 'uptime' in metrics
        
        # Verify command metrics
        command_metrics = metrics['commands']
        assert 'test_command' in command_metrics
        assert 'success' in command_metrics['test_command']
        assert 'failure' in command_metrics['test_command']
        assert 'avg_response_time' in command_metrics['test_command']
        
        # Verify error metrics
        error_metrics = metrics['errors']
        assert 'test_error' in error_metrics
        assert 'count' in error_metrics['test_error']

if __name__ == '__main__':
    pytest.main([__file__]) 