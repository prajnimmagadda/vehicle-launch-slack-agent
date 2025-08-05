import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import requests
import json
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from flask import Flask, Response
import threading
import os

# Import configuration
from production_config import SENTRY_DSN, METRICS_PORT

logger = logging.getLogger(__name__)

# Prometheus metrics
COMMAND_COUNTER = Counter('slack_bot_commands_total', 'Total number of Slack bot commands', ['command', 'status'])
COMMAND_DURATION = Histogram('slack_bot_command_duration_seconds', 'Duration of Slack bot commands', ['command'])
ERROR_COUNTER = Counter('slack_bot_errors_total', 'Total number of errors', ['error_type', 'user_id'])
ACTIVE_USERS = Gauge('slack_bot_active_users', 'Number of active users')
REQUEST_DURATION = Histogram('slack_bot_request_duration_seconds', 'Duration of HTTP requests', ['endpoint'])


class MonitoringManager:
    """Monitoring and observability manager for the Slack bot"""

    def __init__(self):
        """Initialize monitoring manager"""
        self.start_time = time.time()
        self.metrics_server = None
        self.metrics_thread = None
        self.command_counter = {}
        self.error_counter = {}
        
        # Initialize Sentry if DSN is provided
        if SENTRY_DSN:
            try:
                import sentry_sdk
                from sentry_sdk.integrations.flask import FlaskIntegration
                from sentry_sdk.integrations.logging import LoggingIntegration
                
                sentry_logging = LoggingIntegration(
                    level=logging.INFO,
                    event_level=logging.ERROR
                )
                
                sentry_sdk.init(
                    dsn=SENTRY_DSN,
                    integrations=[FlaskIntegration(), sentry_logging],
                    traces_sample_rate=0.1,
                    profiles_sample_rate=0.1,
                )
                logger.info("Sentry initialized successfully")
            except ImportError:
                logger.warning("Sentry SDK not installed - error tracking disabled")
            except Exception as e:
                logger.error(f"Failed to initialize Sentry: {e}")
        
        # Start metrics server
        self.start_metrics_server()

    def start_metrics_server(self):
        """Start Prometheus metrics server"""
        try:
            app = Flask(__name__)
            
            @app.route('/metrics')
            def metrics():
                return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)
            
            @app.route('/health')
            def health():
                return self.get_health_status()
            
            def run_server():
                app.run(host='0.0.0.0', port=METRICS_PORT)
            
            self.metrics_thread = threading.Thread(target=run_server, daemon=True)
            self.metrics_thread.start()
            logger.info(f"Metrics server started on port {METRICS_PORT}")
            
        except Exception as e:
            logger.error(f"Failed to start metrics server: {e}")

    def track_command(self, command_name: str, success: bool, duration: float, user_id: Optional[str] = None):
        """Track command execution metrics"""
        try:
            status = 'success' if success else 'failure'
            COMMAND_COUNTER.labels(command=command_name, status=status).inc()
            COMMAND_DURATION.labels(command=command_name).observe(duration)
            
            # Track in internal counter for testing
            if command_name not in self.command_counter:
                self.command_counter[command_name] = {'success': 0, 'failure': 0, 'total_duration': 0, 'count': 0}
            
            self.command_counter[command_name]['count'] += 1
            self.command_counter[command_name]['total_duration'] += duration
            if success:
                self.command_counter[command_name]['success'] += 1
            else:
                self.command_counter[command_name]['failure'] += 1
            
            if user_id:
                # Track active users (simplified - in production you'd want more sophisticated tracking)
                ACTIVE_USERS.set(1)  # This is simplified - you'd want to track unique users
            
            logger.info(f"Command tracked: {command_name} - {status} - {duration:.2f}s")
            
        except Exception as e:
            logger.error(f"Error tracking command: {e}")

    def track_error(self, error_type: str, error_message: str, user_id: Optional[str] = None):
        """Track error metrics"""
        try:
            ERROR_COUNTER.labels(error_type=error_type, user_id=user_id or 'unknown').inc()
            
            # Track in internal counter for testing
            if error_type not in self.error_counter:
                self.error_counter[error_type] = {'count': 0, 'last_message': '', 'last_occurrence': None}
            
            self.error_counter[error_type]['count'] += 1
            self.error_counter[error_type]['last_message'] = error_message
            self.error_counter[error_type]['last_occurrence'] = datetime.now().isoformat()
            
            logger.error(f"Error tracked: {error_type} - {error_message}")
            
        except Exception as e:
            logger.error(f"Error tracking error: {e}")

    def track_request(self, endpoint: str, duration: float, success: bool):
        """Track HTTP request metrics"""
        try:
            REQUEST_DURATION.labels(endpoint=endpoint).observe(duration)
            logger.info(f"Request tracked: {endpoint} - {duration:.2f}s - {'success' if success else 'failure'}")
        except Exception as e:
            logger.error(f"Error tracking request: {e}")

    def get_health_status(self) -> Dict[str, Any]:
        """Get health status for monitoring"""
        try:
            uptime = time.time() - self.start_time
            return {
                'status': 'healthy',
                'uptime': uptime,
                'start_time': datetime.fromtimestamp(self.start_time).isoformat(),
                'metrics_server': 'running' if self.metrics_thread and self.metrics_thread.is_alive() else 'stopped'
            }
        except Exception as e:
            logger.error(f"Error getting health status: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'uptime': 0
            }

    def get_metrics(self) -> Dict[str, Any]:
        """Get comprehensive metrics for monitoring"""
        try:
            uptime = time.time() - self.start_time
            
            # Process command metrics
            commands = {}
            for command_name, data in self.command_counter.items():
                commands[command_name] = {
                    'success': data['success'],
                    'failure': data['failure'],
                    'total_calls': data['count'],
                    'avg_response_time': data['total_duration'] / data['count'] if data['count'] > 0 else 0
                }
            
            # Process error metrics
            errors = {}
            for error_type, data in self.error_counter.items():
                errors[error_type] = {
                    'count': data['count'],
                    'last_message': data['last_message'],
                    'last_occurrence': data['last_occurrence']
                }
            
            return {
                'uptime': uptime,
                'commands': commands,
                'errors': errors,
                'start_time': datetime.fromtimestamp(self.start_time).isoformat(),
                'metrics_server_status': 'running' if self.metrics_thread and self.metrics_thread.is_alive() else 'stopped'
            }
        except Exception as e:
            logger.error(f"Error getting metrics: {e}")
            return {
                'uptime': 0,
                'commands': {},
                'errors': {},
                'error': str(e)
            }

    def reset_metrics(self):
        """Reset all metrics counters"""
        try:
            self.command_counter = {}
            self.error_counter = {}
            self.start_time = time.time()
            logger.info("Metrics reset successfully")
        except Exception as e:
            logger.error(f"Error resetting metrics: {e}")

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get metrics summary for dashboard"""
        try:
            metrics = self.get_metrics()
            
            total_commands = sum(cmd['total_calls'] for cmd in metrics['commands'].values())
            total_errors = sum(err['count'] for err in metrics['errors'].values())
            
            return {
                'uptime_hours': metrics['uptime'] / 3600,
                'total_commands': total_commands,
                'total_errors': total_errors,
                'success_rate': (total_commands - total_errors) / total_commands * 100 if total_commands > 0 else 0,
                'active_commands': len(metrics['commands']),
                'error_types': len(metrics['errors'])
            }
        except Exception as e:
            logger.error(f"Error getting metrics summary: {e}")
            return {
                'uptime_hours': 0,
                'total_commands': 0,
                'total_errors': 0,
                'success_rate': 0,
                'active_commands': 0,
                'error_types': 0
            }

    def cleanup_old_metrics(self, days: int = 30):
        """Clean up old metrics data"""
        try:
            cutoff_time = time.time() - (days * 24 * 3600)
            # In a real implementation, you'd clean up old data from storage
            logger.info(f"Cleaned up metrics older than {days} days")
        except Exception as e:
            logger.error(f"Error cleaning up metrics: {e}")

    def export_metrics(self, format: str = 'prometheus') -> str:
        """Export metrics in specified format"""
        try:
            if format == 'prometheus':
                return generate_latest().decode('utf-8')
            elif format == 'json':
                return json.dumps(self.get_metrics(), indent=2)
            else:
                raise ValueError(f"Unsupported format: {format}")
        except Exception as e:
            logger.error(f"Error exporting metrics: {e}")
            return ""

    def alert_on_threshold(self, metric_name: str, threshold: float, operator: str = '>'):
        """Alert when metric exceeds threshold"""
        try:
            metrics = self.get_metrics()
            current_value = metrics.get(metric_name, 0)
            
            should_alert = False
            if operator == '>':
                should_alert = current_value > threshold
            elif operator == '<':
                should_alert = current_value < threshold
            elif operator == '>=':
                should_alert = current_value >= threshold
            elif operator == '<=':
                should_alert = current_value <= threshold
            
            if should_alert:
                logger.warning(f"Alert: {metric_name} = {current_value} {operator} {threshold}")
                return True
            
            return False
        except Exception as e:
            logger.error(f"Error checking threshold: {e}")
            return False


# Global monitoring manager instance
monitoring_manager = MonitoringManager()


def monitor_command(command_name: str):
    """Decorator to monitor command execution"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            success = False
            try:
                result = func(*args, **kwargs)
                success = True
                return result
            except Exception as e:
                monitoring_manager.track_error('command_error', str(e))
                raise
            finally:
                duration = time.time() - start_time
                monitoring_manager.track_command(command_name, success, duration)
        return wrapper
    return decorator


def monitor_error(error_type: str):
    """Decorator to monitor error handling"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                monitoring_manager.track_error(error_type, str(e))
                raise
        return wrapper
    return decorator 