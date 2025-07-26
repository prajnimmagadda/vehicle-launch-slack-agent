import logging
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Callable
from functools import wraps
import requests
import json
from flask import Flask, jsonify
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

from production_config import ProductionConfig
from database import db_manager

logger = logging.getLogger(__name__)

# Prometheus metrics
COMMAND_COUNTER = Counter('slack_bot_commands_total', 'Total number of commands', ['command', 'status'])
RESPONSE_TIME = Histogram('slack_bot_response_time_seconds', 'Response time in seconds', ['command'])
ACTIVE_USERS = Gauge('slack_bot_active_users', 'Number of active users')
ERROR_COUNTER = Counter('slack_bot_errors_total', 'Total number of errors', ['error_type'])

class MonitoringManager:
    """Production monitoring and health checks"""
    
    def __init__(self):
        """Initialize monitoring"""
        self.start_time = datetime.utcnow()
        self.health_checks = {}
        self.metrics_thread = None
        self.metrics_running = False
        
        # Initialize Sentry if configured
        if ProductionConfig.SENTRY_DSN:
            try:
                import sentry_sdk
                from sentry_sdk.integrations.logging import LoggingIntegration
                
                sentry_logging = LoggingIntegration(
                    level=logging.INFO,
                    event_level=logging.ERROR
                )
                
                sentry_sdk.init(
                    dsn=ProductionConfig.SENTRY_DSN,
                    integrations=[sentry_logging],
                    environment=ProductionConfig.ENVIRONMENT,
                    traces_sample_rate=0.1
                )
                logger.info("Sentry initialized successfully")
            except ImportError:
                logger.warning("Sentry SDK not installed, error tracking disabled")
            except Exception as e:
                logger.error(f"Failed to initialize Sentry: {e}")
    
    def start_metrics_server(self):
        """Start Prometheus metrics server"""
        if not ProductionConfig.ENABLE_METRICS:
            return
        
        try:
            app = Flask(__name__)
            
            @app.route('/metrics')
            def metrics():
                return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}
            
            @app.route('/health')
            def health():
                return jsonify(self.get_health_status())
            
            @app.route('/status')
            def status():
                return jsonify(self.get_status())
            
            def run_server():
                app.run(host='0.0.0.0', port=ProductionConfig.METRICS_PORT)
            
            self.metrics_thread = threading.Thread(target=run_server, daemon=True)
            self.metrics_thread.start()
            self.metrics_running = True
            logger.info(f"Metrics server started on port {ProductionConfig.METRICS_PORT}")
            
        except Exception as e:
            logger.error(f"Failed to start metrics server: {e}")
    
    def stop_metrics_server(self):
        """Stop metrics server"""
        self.metrics_running = False
        if self.metrics_thread:
            self.metrics_thread.join(timeout=5)
        logger.info("Metrics server stopped")
    
    def track_command(self, command: str, success: bool = True, response_time: Optional[float] = None):
        """Track command execution metrics"""
        try:
            # Update Prometheus metrics
            COMMAND_COUNTER.labels(command=command, status='success' if success else 'error').inc()
            
            if response_time:
                RESPONSE_TIME.labels(command=command).observe(response_time)
            
            # Update database metrics
            db_manager.store_metrics(
                user_id='system',
                command=command,
                response_time=int(response_time * 1000) if response_time else None,
                success=success
            )
            
        except Exception as e:
            logger.error(f"Error tracking command metrics: {e}")
    
    def track_error(self, error_type: str, error_message: str, user_id: Optional[str] = None):
        """Track error occurrences"""
        try:
            # Update Prometheus metrics
            ERROR_COUNTER.labels(error_type=error_type).inc()
            
            # Log to Sentry if configured
            if ProductionConfig.SENTRY_DSN:
                import sentry_sdk
                with sentry_sdk.push_scope() as scope:
                    if user_id:
                        scope.set_user({"id": user_id})
                    scope.set_tag("error_type", error_type)
                    sentry_sdk.capture_message(error_message, level="error")
            
            # Send notification if configured
            if ProductionConfig.ERROR_NOTIFICATION_WEBHOOK:
                self._send_error_notification(error_type, error_message, user_id)
            
            logger.error(f"Error tracked: {error_type} - {error_message}")
            
        except Exception as e:
            logger.error(f"Error tracking error metrics: {e}")
    
    def _send_error_notification(self, error_type: str, error_message: str, user_id: Optional[str]):
        """Send error notification to webhook"""
        try:
            payload = {
                'error_type': error_type,
                'error_message': error_message,
                'user_id': user_id,
                'timestamp': datetime.utcnow().isoformat(),
                'environment': ProductionConfig.ENVIRONMENT
            }
            
            response = requests.post(
                ProductionConfig.ERROR_NOTIFICATION_WEBHOOK,
                json=payload,
                timeout=10
            )
            
            if response.status_code != 200:
                logger.warning(f"Error notification failed: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Failed to send error notification: {e}")
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status"""
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'uptime': str(datetime.utcnow() - self.start_time),
            'environment': ProductionConfig.ENVIRONMENT,
            'version': '1.0.0',
            'checks': {}
        }
        
        # Database health check
        db_health = db_manager.health_check()
        health_status['checks']['database'] = db_health
        
        # Configuration validation
        config_validation = ProductionConfig.validate_config()
        health_status['checks']['configuration'] = {
            'status': 'valid' if config_validation['valid'] else 'invalid',
            'errors': config_validation['errors'],
            'warnings': config_validation['warnings']
        }
        
        # Overall status
        if not config_validation['valid'] or db_health['status'] != 'healthy':
            health_status['status'] = 'unhealthy'
        
        return health_status
    
    def get_status(self) -> Dict[str, Any]:
        """Get detailed system status"""
        try:
            metrics_summary = db_manager.get_metrics_summary(days=7)
            
            return {
                'uptime': str(datetime.utcnow() - self.start_time),
                'environment': ProductionConfig.ENVIRONMENT,
                'metrics': metrics_summary,
                'configuration': {
                    'database_configured': bool(ProductionConfig.DATABASE_URL),
                    'redis_configured': bool(ProductionConfig.REDIS_URL),
                    'sentry_configured': bool(ProductionConfig.SENTRY_DSN),
                    'metrics_enabled': ProductionConfig.ENABLE_METRICS
                }
            }
        except Exception as e:
            logger.error(f"Error getting status: {e}")
            return {'error': str(e)}
    
    def update_active_users(self, count: int):
        """Update active users metric"""
        try:
            ACTIVE_USERS.set(count)
        except Exception as e:
            logger.error(f"Error updating active users metric: {e}")
    
    def cleanup_old_data(self):
        """Clean up old monitoring data"""
        try:
            db_manager.cleanup_old_data()
            logger.info("Old monitoring data cleaned up")
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")

# Global monitoring manager
monitoring_manager = MonitoringManager()

def monitor_command(command_name: str):
    """Decorator to monitor command execution"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            success = True
            error_message = None
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                error_message = str(e)
                monitoring_manager.track_error('command_execution', str(e))
                raise
            finally:
                response_time = time.time() - start_time
                monitoring_manager.track_command(command_name, success, response_time)
                
                if not success:
                    logger.error(f"Command {command_name} failed: {error_message}")
        
        return wrapper
    return decorator

def monitor_error(error_type: str):
    """Decorator to monitor specific error types"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                monitoring_manager.track_error(error_type, str(e))
                raise
        return wrapper
    return decorator 