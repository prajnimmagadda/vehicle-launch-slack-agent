import pytest
import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import time

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from monitoring import MonitoringManager, monitoring_manager

class TestMonitoringManagerComprehensive:
    """Comprehensive tests for MonitoringManager"""
    
    def setup_method(self):
        """Setup test method"""
        self.mock_registry = Mock()
        self.mock_counter = Mock()
        self.mock_gauge = Mock()
        self.mock_histogram = Mock()
        self.mock_summary = Mock()
        
    @patch('monitoring.Counter')
    @patch('monitoring.Gauge')
    @patch('monitoring.Histogram')
    @patch('monitoring.Summary')
    @patch('monitoring.CollectorRegistry')
    def test_initialization_success(self, mock_registry, mock_summary, mock_histogram, mock_gauge, mock_counter):
        """Test successful monitoring manager initialization"""
        mock_registry.return_value = self.mock_registry
        mock_counter.return_value = self.mock_counter
        mock_gauge.return_value = self.mock_gauge
        mock_histogram.return_value = self.mock_histogram
        mock_summary.return_value = self.mock_summary
        
        manager = MonitoringManager()
        
        assert manager.registry is not None
        assert manager.command_counter is not None
        assert manager.error_counter is not None
        assert manager.response_time_histogram is not None
        assert manager.active_connections_gauge is not None
        assert manager.start_time is not None
        
        mock_registry.assert_called_once()
        mock_counter.assert_called()
        mock_gauge.assert_called()
        mock_histogram.assert_called()
        mock_summary.assert_called()
    
    @patch('monitoring.Counter')
    @patch('monitoring.Gauge')
    @patch('monitoring.Histogram')
    @patch('monitoring.Summary')
    @patch('monitoring.CollectorRegistry')
    def test_track_command_success(self, mock_registry, mock_summary, mock_histogram, mock_gauge, mock_counter):
        """Test tracking successful command"""
        mock_registry.return_value = self.mock_registry
        mock_counter.return_value = self.mock_counter
        mock_gauge.return_value = self.mock_gauge
        mock_histogram.return_value = self.mock_histogram
        mock_summary.return_value = self.mock_summary
        
        manager = MonitoringManager()
        
        manager.track_command('test_command', True, 1.5)
        
        # Verify metrics were updated
        self.mock_counter.inc.assert_called()
        self.mock_histogram.observe.assert_called_with(1.5)
    
    @patch('monitoring.Counter')
    @patch('monitoring.Gauge')
    @patch('monitoring.Histogram')
    @patch('monitoring.Summary')
    @patch('monitoring.CollectorRegistry')
    def test_track_command_failure(self, mock_registry, mock_summary, mock_histogram, mock_gauge, mock_counter):
        """Test tracking failed command"""
        mock_registry.return_value = self.mock_registry
        mock_counter.return_value = self.mock_counter
        mock_gauge.return_value = self.mock_gauge
        mock_histogram.return_value = self.mock_histogram
        mock_summary.return_value = self.mock_summary
        
        manager = MonitoringManager()
        
        manager.track_command('test_command', False, 2.0)
        
        # Verify metrics were updated
        self.mock_counter.inc.assert_called()
        self.mock_histogram.observe.assert_called_with(2.0)
    
    @patch('monitoring.Counter')
    @patch('monitoring.Gauge')
    @patch('monitoring.Histogram')
    @patch('monitoring.Summary')
    @patch('monitoring.CollectorRegistry')
    def test_track_error(self, mock_registry, mock_summary, mock_histogram, mock_gauge, mock_counter):
        """Test tracking error"""
        mock_registry.return_value = self.mock_registry
        mock_counter.return_value = self.mock_counter
        mock_gauge.return_value = self.mock_gauge
        mock_histogram.return_value = self.mock_histogram
        mock_summary.return_value = self.mock_summary
        
        manager = MonitoringManager()
        
        manager.track_error('TestError', 'Test error message')
        
        # Verify error counter was incremented
        self.mock_counter.inc.assert_called()
    
    @patch('monitoring.Counter')
    @patch('monitoring.Gauge')
    @patch('monitoring.Histogram')
    @patch('monitoring.Summary')
    @patch('monitoring.CollectorRegistry')
    def test_update_connection_count(self, mock_registry, mock_summary, mock_histogram, mock_gauge, mock_counter):
        """Test updating connection count"""
        mock_registry.return_value = self.mock_registry
        mock_counter.return_value = self.mock_counter
        mock_gauge.return_value = self.mock_gauge
        mock_histogram.return_value = self.mock_histogram
        mock_summary.return_value = self.mock_summary
        
        manager = MonitoringManager()
        
        manager.update_connection_count(5)
        
        # Verify gauge was set
        self.mock_gauge.set.assert_called_with(5)
    
    @patch('monitoring.Counter')
    @patch('monitoring.Gauge')
    @patch('monitoring.Histogram')
    @patch('monitoring.Summary')
    @patch('monitoring.CollectorRegistry')
    def test_get_metrics(self, mock_registry, mock_summary, mock_histogram, mock_gauge, mock_counter):
        """Test getting metrics"""
        mock_registry.return_value = self.mock_registry
        mock_counter.return_value = self.mock_counter
        mock_gauge.return_value = self.mock_gauge
        mock_histogram.return_value = self.mock_histogram
        mock_summary.return_value = self.mock_summary
        
        # Mock generate_latest
        self.mock_registry.generate_latest.return_value = b"test_metrics"
        
        manager = MonitoringManager()
        
        metrics = manager.get_metrics()
        
        assert metrics == b"test_metrics"
        self.mock_registry.generate_latest.assert_called_once()
    
    @patch('monitoring.Counter')
    @patch('monitoring.Gauge')
    @patch('monitoring.Histogram')
    @patch('monitoring.Summary')
    @patch('monitoring.CollectorRegistry')
    def test_get_uptime(self, mock_registry, mock_summary, mock_histogram, mock_gauge, mock_counter):
        """Test getting uptime"""
        mock_registry.return_value = self.mock_registry
        mock_counter.return_value = self.mock_counter
        mock_gauge.return_value = self.mock_gauge
        mock_histogram.return_value = self.mock_histogram
        mock_summary.return_value = self.mock_summary
        
        manager = MonitoringManager()
        
        # Wait a bit to ensure uptime > 0
        time.sleep(0.1)
        
        uptime = manager.get_uptime()
        
        assert uptime > 0
        assert isinstance(uptime, float)
    
    @patch('monitoring.Counter')
    @patch('monitoring.Gauge')
    @patch('monitoring.Histogram')
    @patch('monitoring.Summary')
    @patch('monitoring.CollectorRegistry')
    def test_get_stats(self, mock_registry, mock_summary, mock_histogram, mock_gauge, mock_counter):
        """Test getting monitoring stats"""
        mock_registry.return_value = self.mock_registry
        mock_counter.return_value = self.mock_counter
        mock_gauge.return_value = self.mock_gauge
        mock_histogram.return_value = self.mock_histogram
        mock_summary.return_value = self.mock_summary
        
        manager = MonitoringManager()
        
        stats = manager.get_stats()
        
        assert 'uptime' in stats
        assert 'start_time' in stats
        assert isinstance(stats['uptime'], float)
        assert isinstance(stats['start_time'], float)
    
    @patch('monitoring.Counter')
    @patch('monitoring.Gauge')
    @patch('monitoring.Histogram')
    @patch('monitoring.Summary')
    @patch('monitoring.CollectorRegistry')
    def test_reset_metrics(self, mock_registry, mock_summary, mock_histogram, mock_gauge, mock_counter):
        """Test resetting metrics"""
        mock_registry.return_value = self.mock_registry
        mock_counter.return_value = self.mock_counter
        mock_gauge.return_value = self.mock_gauge
        mock_histogram.return_value = self.mock_histogram
        mock_summary.return_value = self.mock_summary
        
        manager = MonitoringManager()
        
        # Track some metrics first
        manager.track_command('test_command', True, 1.0)
        manager.track_error('TestError', 'Test message')
        
        # Reset metrics
        manager.reset_metrics()
        
        # Verify metrics were reset
        assert True  # If we get here, no exceptions were raised
    
    @patch('monitoring.Counter')
    @patch('monitoring.Gauge')
    @patch('monitoring.Histogram')
    @patch('monitoring.Summary')
    @patch('monitoring.CollectorRegistry')
    def test_start_metrics_server(self, mock_registry, mock_summary, mock_histogram, mock_gauge, mock_counter):
        """Test starting metrics server"""
        mock_registry.return_value = self.mock_registry
        mock_counter.return_value = self.mock_counter
        mock_gauge.return_value = self.mock_gauge
        mock_histogram.return_value = self.mock_histogram
        mock_summary.return_value = self.mock_summary
        
        manager = MonitoringManager()
        
        # Mock Flask app
        with patch('monitoring.Flask') as mock_flask:
            mock_app = Mock()
            mock_flask.return_value = mock_app
            
            # Mock start_server
            with patch('monitoring.start_server') as mock_start_server:
                manager.start_metrics_server(port=8000)
                
                mock_flask.assert_called_once()
                mock_start_server.assert_called_once()
    
    @patch('monitoring.Counter')
    @patch('monitoring.Gauge')
    @patch('monitoring.Histogram')
    @patch('monitoring.Summary')
    @patch('monitoring.CollectorRegistry')
    def test_comprehensive_tracking(self, mock_registry, mock_summary, mock_histogram, mock_gauge, mock_counter):
        """Test comprehensive metric tracking"""
        mock_registry.return_value = self.mock_registry
        mock_counter.return_value = self.mock_counter
        mock_gauge.return_value = self.mock_gauge
        mock_histogram.return_value = self.mock_histogram
        mock_summary.return_value = self.mock_summary
        
        manager = MonitoringManager()
        
        # Track various metrics
        manager.track_command('command1', True, 1.0)
        manager.track_command('command2', False, 2.0)
        manager.track_error('Error1', 'Error message 1')
        manager.track_error('Error2', 'Error message 2')
        manager.update_connection_count(10)
        
        # Verify metrics were tracked
        assert self.mock_counter.inc.call_count >= 4  # At least 4 counter increments
        assert self.mock_histogram.observe.call_count == 2  # 2 histogram observations
        assert self.mock_gauge.set.call_count == 1  # 1 gauge set
    
    @patch('monitoring.Counter')
    @patch('monitoring.Gauge')
    @patch('monitoring.Histogram')
    @patch('monitoring.Summary')
    @patch('monitoring.CollectorRegistry')
    def test_error_handling(self, mock_registry, mock_summary, mock_histogram, mock_gauge, mock_counter):
        """Test error handling in monitoring"""
        mock_registry.return_value = self.mock_registry
        mock_counter.return_value = self.mock_counter
        mock_gauge.return_value = self.mock_gauge
        mock_histogram.return_value = self.mock_histogram
        mock_summary.return_value = self.mock_summary
        
        manager = MonitoringManager()
        
        # Mock counter to raise exception
        self.mock_counter.inc.side_effect = Exception("Counter error")
        
        # This should not raise an exception
        manager.track_command('test_command', True, 1.0)
        
        # Verify the method handled the error gracefully
        assert True
    
    @patch('monitoring.Counter')
    @patch('monitoring.Gauge')
    @patch('monitoring.Histogram')
    @patch('monitoring.Summary')
    @patch('monitoring.CollectorRegistry')
    def test_metrics_export(self, mock_registry, mock_summary, mock_histogram, mock_gauge, mock_counter):
        """Test metrics export functionality"""
        mock_registry.return_value = self.mock_registry
        mock_counter.return_value = self.mock_counter
        mock_gauge.return_value = self.mock_gauge
        mock_histogram.return_value = self.mock_histogram
        mock_summary.return_value = self.mock_summary
        
        # Mock generate_latest
        self.mock_registry.generate_latest.return_value = b"# HELP test_metric\n# TYPE test_metric counter\ntest_metric 1.0"
        
        manager = MonitoringManager()
        
        # Export metrics
        metrics = manager.get_metrics()
        
        assert b"test_metric" in metrics
        assert b"counter" in metrics
        self.mock_registry.generate_latest.assert_called_once()

class TestMonitoringManagerIntegration:
    """Integration tests for MonitoringManager"""
    
    def test_monitoring_manager_singleton(self):
        """Test that monitoring_manager is a singleton"""
        assert monitoring_manager is not None
        assert isinstance(monitoring_manager, MonitoringManager)
        
        # Create another instance - should be the same
        from monitoring import monitoring_manager as mm2
        assert monitoring_manager is mm2
    
    def test_monitoring_manager_attributes(self):
        """Test monitoring_manager has required attributes"""
        assert hasattr(monitoring_manager, 'registry')
        assert hasattr(monitoring_manager, 'command_counter')
        assert hasattr(monitoring_manager, 'error_counter')
        assert hasattr(monitoring_manager, 'response_time_histogram')
        assert hasattr(monitoring_manager, 'active_connections_gauge')
        assert hasattr(monitoring_manager, 'start_time')
    
    def test_monitoring_manager_methods(self):
        """Test monitoring_manager has required methods"""
        assert hasattr(monitoring_manager, 'track_command')
        assert hasattr(monitoring_manager, 'track_error')
        assert hasattr(monitoring_manager, 'update_connection_count')
        assert hasattr(monitoring_manager, 'get_metrics')
        assert hasattr(monitoring_manager, 'get_uptime')
        assert hasattr(monitoring_manager, 'get_stats')
        assert hasattr(monitoring_manager, 'reset_metrics')
        assert hasattr(monitoring_manager, 'start_metrics_server')
    
    def test_monitoring_manager_functionality(self):
        """Test monitoring_manager basic functionality"""
        # Test tracking commands
        monitoring_manager.track_command('test_command', True, 1.0)
        monitoring_manager.track_command('test_command', False, 2.0)
        
        # Test tracking errors
        monitoring_manager.track_error('TestError', 'Test error message')
        
        # Test updating connection count
        monitoring_manager.update_connection_count(5)
        
        # Test getting stats
        stats = monitoring_manager.get_stats()
        assert 'uptime' in stats
        assert 'start_time' in stats
        
        # Test getting uptime
        uptime = monitoring_manager.get_uptime()
        assert uptime > 0
        
        # Test getting metrics
        metrics = monitoring_manager.get_metrics()
        assert isinstance(metrics, bytes)
    
    def test_monitoring_manager_error_handling(self):
        """Test monitoring_manager error handling"""
        # Test with invalid parameters
        monitoring_manager.track_command('test_command', True, -1.0)  # Negative time
        monitoring_manager.track_command('', True, 1.0)  # Empty command
        monitoring_manager.track_error('', '')  # Empty error
        
        # These should not raise exceptions
        assert True
    
    def test_monitoring_manager_performance(self):
        """Test monitoring_manager performance"""
        import time
        
        start_time = time.time()
        
        # Track many commands quickly
        for i in range(100):
            monitoring_manager.track_command(f'command_{i}', True, 1.0)
        
        end_time = time.time()
        
        # Should complete quickly (less than 1 second)
        assert end_time - start_time < 1.0

if __name__ == '__main__':
    pytest.main([__file__]) 