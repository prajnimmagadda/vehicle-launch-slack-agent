import os
import logging
from datetime import datetime
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

class ProductionConfig:
    """Production configuration with enhanced security and monitoring"""
    
    # =============================================================================
    # ENVIRONMENT
    # =============================================================================
    ENVIRONMENT = os.getenv('ENVIRONMENT', 'production')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # =============================================================================
    # SECURITY CONFIGURATION
    # =============================================================================
    # Rate limiting
    RATE_LIMIT_REQUESTS = int(os.getenv('RATE_LIMIT_REQUESTS', '100'))
    RATE_LIMIT_WINDOW = int(os.getenv('RATE_LIMIT_WINDOW', '3600'))  # 1 hour
    
    # API key rotation
    API_KEY_ROTATION_DAYS = int(os.getenv('API_KEY_ROTATION_DAYS', '90'))
    
    # Data retention
    DATA_RETENTION_DAYS = int(os.getenv('DATA_RETENTION_DAYS', '365'))
    
    # =============================================================================
    # LOGGING CONFIGURATION
    # =============================================================================
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_FILE = os.getenv('LOG_FILE', 'logs/vehicle_bot.log')
    LOG_MAX_SIZE = int(os.getenv('LOG_MAX_SIZE', '10485760'))  # 10MB
    LOG_BACKUP_COUNT = int(os.getenv('LOG_BACKUP_COUNT', '5'))
    
    # =============================================================================
    # MONITORING CONFIGURATION
    # =============================================================================
    ENABLE_METRICS = os.getenv('ENABLE_METRICS', 'True').lower() == 'true'
    METRICS_PORT = int(os.getenv('METRICS_PORT', '9090'))
    
    # Health check
    HEALTH_CHECK_ENDPOINT = os.getenv('HEALTH_CHECK_ENDPOINT', '/health')
    
    # =============================================================================
    # DATABASE CONFIGURATION (for production data storage)
    # =============================================================================
    DATABASE_URL = os.getenv('DATABASE_URL')
    DATABASE_POOL_SIZE = int(os.getenv('DATABASE_POOL_SIZE', '10'))
    DATABASE_MAX_OVERFLOW = int(os.getenv('DATABASE_MAX_OVERFLOW', '20'))
    
    # =============================================================================
    # CACHE CONFIGURATION
    # =============================================================================
    REDIS_URL = os.getenv('REDIS_URL')
    CACHE_TTL = int(os.getenv('CACHE_TTL', '3600'))  # 1 hour
    
    # =============================================================================
    # SLACK CONFIGURATION (Enhanced)
    # =============================================================================
    SLACK_BOT_TOKEN = os.getenv('SLACK_BOT_TOKEN')
    SLACK_SIGNING_SECRET = os.getenv('SLACK_SIGNING_SECRET')
    SLACK_APP_TOKEN = os.getenv('SLACK_APP_TOKEN')
    
    # Slack app settings
    SLACK_APP_ID = os.getenv('SLACK_APP_ID')
    SLACK_TEAM_ID = os.getenv('SLACK_TEAM_ID')
    
    # =============================================================================
    # OPENAI CONFIGURATION (Enhanced)
    # =============================================================================
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4')
    OPENAI_MAX_TOKENS = int(os.getenv('OPENAI_MAX_TOKENS', '2000'))
    OPENAI_TEMPERATURE = float(os.getenv('OPENAI_TEMPERATURE', '0.7'))
    OPENAI_TIMEOUT = int(os.getenv('OPENAI_TIMEOUT', '30'))
    
    # =============================================================================
    # DATABRICKS CONFIGURATION (Enhanced)
    # =============================================================================
    DATABRICKS_HOST = os.getenv('DATABRICKS_HOST')
    DATABRICKS_TOKEN = os.getenv('DATABRICKS_TOKEN')
    DATABRICKS_CATALOG = os.getenv('DATABRICKS_CATALOG')
    DATABRICKS_SCHEMA = os.getenv('DATABRICKS_SCHEMA')
    DATABRICKS_TIMEOUT = int(os.getenv('DATABRICKS_TIMEOUT', '60'))
    DATABRICKS_RETRY_ATTEMPTS = int(os.getenv('DATABRICKS_RETRY_ATTEMPTS', '3'))
    
    # Databricks table names
    DATABRICKS_TABLES = {
        'bill_of_material': os.getenv('DATABRICKS_TABLES_BILL_OF_MATERIAL'),
        'master_parts_list': os.getenv('DATABRICKS_TABLES_MASTER_PARTS_LIST'),
        'material_flow_engineering': os.getenv('DATABRICKS_TABLES_MATERIAL_FLOW_ENGINEERING'),
        '4p': os.getenv('DATABRICKS_TABLES_4P'),
        'ppap': os.getenv('DATABRICKS_TABLES_PPAP'),
    }
    
    # =============================================================================
    # GOOGLE SHEETS CONFIGURATION (Enhanced)
    # =============================================================================
    GOOGLE_SHEETS_CREDENTIALS_FILE = os.getenv('GOOGLE_SHEETS_CREDENTIALS_FILE')
    GOOGLE_SHEETS_SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    DASHBOARD_TEMPLATE_ID = os.getenv('DASHBOARD_TEMPLATE_ID')
    
    # =============================================================================
    # SMARTSHEET CONFIGURATION (Enhanced)
    # =============================================================================
    SMARTSHEET_API_TOKEN = os.getenv('SMARTSHEET_API_TOKEN')
    SMARTSHEET_TIMEOUT = int(os.getenv('SMARTSHEET_TIMEOUT', '30'))
    
    # =============================================================================
    # FILE UPLOAD CONFIGURATION (Enhanced)
    # =============================================================================
    ALLOWED_FILE_TYPES = ['.xlsx', '.xls', '.csv']
    MAX_FILE_SIZE = int(os.getenv('MAX_FILE_SIZE', '10485760'))  # 10MB
    UPLOAD_TIMEOUT = int(os.getenv('UPLOAD_TIMEOUT', '300'))  # 5 minutes
    
    # =============================================================================
    # ERROR HANDLING CONFIGURATION
    # =============================================================================
    SENTRY_DSN = os.getenv('SENTRY_DSN')
    ERROR_NOTIFICATION_WEBHOOK = os.getenv('ERROR_NOTIFICATION_WEBHOOK')
    
    # =============================================================================
    # PERFORMANCE CONFIGURATION
    # =============================================================================
    WORKER_THREADS = int(os.getenv('WORKER_THREADS', '4'))
    REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', '30'))
    MAX_CONCURRENT_REQUESTS = int(os.getenv('MAX_CONCURRENT_REQUESTS', '10'))
    
    @classmethod
    def validate_config(cls) -> Dict[str, Any]:
        """Validate all required configuration values"""
        errors = []
        warnings = []
        
        # Required configurations
        required_configs = [
            'SLACK_BOT_TOKEN', 'SLACK_SIGNING_SECRET', 'SLACK_APP_TOKEN',
            'OPENAI_API_KEY', 'DATABRICKS_HOST', 'DATABRICKS_TOKEN'
        ]
        
        for config in required_configs:
            if not getattr(cls, config):
                errors.append(f"Missing required configuration: {config}")
        
        # Optional but recommended configurations
        recommended_configs = [
            'DATABASE_URL', 'REDIS_URL', 'SENTRY_DSN'
        ]
        
        for config in recommended_configs:
            if not getattr(cls, config):
                warnings.append(f"Missing recommended configuration: {config}")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    @classmethod
    def get_logging_config(cls) -> Dict[str, Any]:
        """Get logging configuration for production"""
        return {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'detailed': {
                    'format': cls.LOG_FORMAT,
                    'datefmt': '%Y-%m-%d %H:%M:%S'
                },
                'simple': {
                    'format': '%(levelname)s - %(message)s'
                }
            },
            'handlers': {
                'console': {
                    'class': 'logging.StreamHandler',
                    'level': cls.LOG_LEVEL,
                    'formatter': 'simple',
                    'stream': 'ext://sys.stdout'
                },
                'file': {
                    'class': 'logging.handlers.RotatingFileHandler',
                    'level': cls.LOG_LEVEL,
                    'formatter': 'detailed',
                    'filename': cls.LOG_FILE,
                    'maxBytes': cls.LOG_MAX_SIZE,
                    'backupCount': cls.LOG_BACKUP_COUNT
                }
            },
            'loggers': {
                '': {
                    'handlers': ['console', 'file'],
                    'level': cls.LOG_LEVEL,
                    'propagate': False
                }
            }
        } 