import os
import logging.config
from datetime import datetime
from typing import Dict, Any, List

# Environment Configuration
ENVIRONMENT = os.getenv('ENVIRONMENT', 'production')
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# Rate Limiting
RATE_LIMIT_REQUESTS = int(os.getenv('RATE_LIMIT_REQUESTS', '100'))
RATE_LIMIT_WINDOW = int(os.getenv('RATE_LIMIT_WINDOW', '3600'))

# Logging Configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE = os.getenv('LOG_FILE', 'logs/vehicle_bot.log')
LOG_MAX_SIZE = int(os.getenv('LOG_MAX_SIZE', '10485760'))  # 10MB
LOG_BACKUP_COUNT = int(os.getenv('LOG_BACKUP_COUNT', '5'))

# Database Configuration
DATABASE_URL = os.getenv('DATABASE_URL')
DATABASE_POOL_SIZE = int(os.getenv('DATABASE_POOL_SIZE', '10'))
DATABASE_MAX_OVERFLOW = int(os.getenv('DATABASE_MAX_OVERFLOW', '20'))
DATABASE_POOL_TIMEOUT = int(os.getenv('DATABASE_POOL_TIMEOUT', '30'))

# Cache Configuration
REDIS_URL = os.getenv('REDIS_URL')
REDIS_MAX_CONNECTIONS = int(os.getenv('REDIS_MAX_CONNECTIONS', '10'))
REDIS_SOCKET_TIMEOUT = int(os.getenv('REDIS_SOCKET_TIMEOUT', '5'))

# Monitoring Configuration
METRICS_PORT = int(os.getenv('METRICS_PORT', '9090'))
HEALTH_CHECK_INTERVAL = int(os.getenv('HEALTH_CHECK_INTERVAL', '30'))
SENTRY_DSN = os.getenv('SENTRY_DSN')

# Performance Configuration
MAX_CONCURRENT_REQUESTS = int(os.getenv('MAX_CONCURRENT_REQUESTS', '50'))
REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', '30'))
WORKER_THREADS = int(os.getenv('WORKER_THREADS', '4'))

# Security Configuration
API_KEY_ROTATION_DAYS = int(os.getenv('API_KEY_ROTATION_DAYS', '90'))
SESSION_TIMEOUT_MINUTES = int(os.getenv('SESSION_TIMEOUT_MINUTES', '60'))
MAX_FILE_SIZE_MB = int(os.getenv('MAX_FILE_SIZE_MB', '50'))

# Data Retention
DATA_RETENTION_DAYS = int(os.getenv('DATA_RETENTION_DAYS', '365'))
BACKUP_RETENTION_DAYS = int(os.getenv('BACKUP_RETENTION_DAYS', '90'))

# Slack Configuration
SLACK_BOT_TOKEN = os.getenv('SLACK_BOT_TOKEN')
SLACK_SIGNING_SECRET = os.getenv('SLACK_SIGNING_SECRET')
SLACK_APP_TOKEN = os.getenv('SLACK_APP_TOKEN')

# OpenAI Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')

# Databricks Configuration
DATABRICKS_HOST = os.getenv('DATABRICKS_HOST')
DATABRICKS_TOKEN = os.getenv('DATABRICKS_TOKEN')
DATABRICKS_CATALOG = os.getenv('DATABRICKS_CATALOG')
DATABRICKS_SCHEMA = os.getenv('DATABRICKS_SCHEMA')

# Google Sheets Configuration
GOOGLE_SHEETS_CREDENTIALS_FILE = os.getenv('GOOGLE_SHEETS_CREDENTIALS_FILE')
GOOGLE_SHEETS_TOKEN_FILE = os.getenv('GOOGLE_SHEETS_TOKEN_FILE')

# Smartsheet Configuration
SMARTSHEET_API_TOKEN = os.getenv('SMARTSHEET_API_TOKEN')

class ProductionConfig:
    """Production configuration class"""
    
    @classmethod
    def validate_config(cls) -> Dict[str, Any]:
        """Validate configuration and return status"""
        errors = []
        warnings = []
        
        # Required configurations
        required_configs = {
            'SLACK_BOT_TOKEN': SLACK_BOT_TOKEN,
            'SLACK_SIGNING_SECRET': SLACK_SIGNING_SECRET,
            'SLACK_APP_TOKEN': SLACK_APP_TOKEN,
            'OPENAI_API_KEY': OPENAI_API_KEY,
            'DATABRICKS_HOST': DATABRICKS_HOST,
            'DATABRICKS_TOKEN': DATABRICKS_TOKEN,
        }
        
        for config_name, config_value in required_configs.items():
            if not config_value:
                errors.append(f"Missing required configuration: {config_name}")
        
        # Database configuration
        if not DATABASE_URL:
            warnings.append("DATABASE_URL not configured - database features will be disabled")
        
        # Redis configuration
        if not REDIS_URL:
            warnings.append("REDIS_URL not configured - caching will be disabled")
        
        # Monitoring configuration
        if not SENTRY_DSN:
            warnings.append("SENTRY_DSN not configured - error tracking will be limited")
        
        # Performance warnings
        if RATE_LIMIT_REQUESTS < 10:
            warnings.append("RATE_LIMIT_REQUESTS is very low - may impact performance")
        
        if MAX_FILE_SIZE_MB > 100:
            warnings.append("MAX_FILE_SIZE_MB is very high - may impact memory usage")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'environment': ENVIRONMENT,
            'debug': DEBUG
        }
    
    @classmethod
    def get_logging_config(cls) -> Dict[str, Any]:
        """Get logging configuration"""
        return {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'standard': {
                    'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
                },
                'detailed': {
                    'format': '%(asctime)s [%(levelname)s] %(name)s:%(lineno)d: %(message)s'
                }
            },
            'handlers': {
                'console': {
                    'class': 'logging.StreamHandler',
                    'level': 'INFO',
                    'formatter': 'standard',
                    'stream': 'ext://sys.stdout'
                },
                'file': {
                    'class': 'logging.handlers.RotatingFileHandler',
                    'level': 'DEBUG',
                    'formatter': 'detailed',
                    'filename': LOG_FILE,
                    'maxBytes': LOG_MAX_SIZE,
                    'backupCount': LOG_BACKUP_COUNT
                }
            },
            'loggers': {
                '': {
                    'handlers': ['console', 'file'],
                    'level': LOG_LEVEL,
                    'propagate': False
                },
                'slack_bolt': {
                    'handlers': ['console', 'file'],
                    'level': 'INFO',
                    'propagate': False
                },
                'openai': {
                    'handlers': ['console', 'file'],
                    'level': 'INFO',
                    'propagate': False
                }
            }
        } 