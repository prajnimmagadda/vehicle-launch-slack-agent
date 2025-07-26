import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy import create_engine, Column, String, DateTime, Text, Integer, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager

from production_config import ProductionConfig

logger = logging.getLogger(__name__)
Base = declarative_base()

class UserSession(Base):
    """User session data for production"""
    __tablename__ = 'user_sessions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(50), nullable=False, index=True)
    launch_date = Column(String(20), nullable=False)
    databricks_data = Column(Text, nullable=True)  # JSON string
    file_data = Column(Text, nullable=True)  # JSON string
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)

class BotMetrics(Base):
    """Bot usage metrics for monitoring"""
    __tablename__ = 'bot_metrics'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(50), nullable=False, index=True)
    command = Column(String(50), nullable=False)
    launch_date = Column(String(20), nullable=True)
    response_time = Column(Integer, nullable=True)  # milliseconds
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class DatabaseManager:
    """Database manager for production data storage"""
    
    def __init__(self):
        """Initialize database connection"""
        self.engine = None
        self.SessionLocal = None
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize database connection and create tables"""
        try:
            if ProductionConfig.DATABASE_URL:
                self.engine = create_engine(
                    ProductionConfig.DATABASE_URL,
                    poolclass=QueuePool,
                    pool_size=ProductionConfig.DATABASE_POOL_SIZE,
                    max_overflow=ProductionConfig.DATABASE_MAX_OVERFLOW,
                    pool_pre_ping=True,
                    pool_recycle=3600
                )
                
                self.SessionLocal = sessionmaker(
                    autocommit=False,
                    autoflush=False,
                    bind=self.engine
                )
                
                # Create tables
                Base.metadata.create_all(bind=self.engine)
                logger.info("Database initialized successfully")
            else:
                logger.warning("No DATABASE_URL provided, using in-memory storage")
                self.engine = None
                self.SessionLocal = None
                
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            self.engine = None
            self.SessionLocal = None
    
    @contextmanager
    def get_session(self):
        """Get database session with proper error handling"""
        if not self.SessionLocal:
            logger.warning("Database not available, using fallback storage")
            yield None
            return
        
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    def store_user_session(self, user_id: str, launch_date: str, databricks_data: Dict, file_data: Optional[Dict] = None):
        """Store user session data"""
        try:
            with self.get_session() as session:
                if session is None:
                    return
                
                # Deactivate existing sessions for this user
                session.query(UserSession).filter(
                    UserSession.user_id == user_id,
                    UserSession.is_active == True
                ).update({'is_active': False})
                
                # Create new session
                new_session = UserSession(
                    user_id=user_id,
                    launch_date=launch_date,
                    databricks_data=json.dumps(databricks_data) if databricks_data else None,
                    file_data=json.dumps(file_data) if file_data else None,
                    is_active=True
                )
                
                session.add(new_session)
                logger.info(f"Stored session for user {user_id}")
                
        except Exception as e:
            logger.error(f"Error storing user session: {e}")
    
    def get_user_session(self, user_id: str) -> Optional[Dict]:
        """Retrieve user session data"""
        try:
            with self.get_session() as session:
                if session is None:
                    return None
                
                user_session = session.query(UserSession).filter(
                    UserSession.user_id == user_id,
                    UserSession.is_active == True
                ).first()
                
                if user_session:
                    return {
                        'launch_date': user_session.launch_date,
                        'databricks_data': json.loads(user_session.databricks_data) if user_session.databricks_data else {},
                        'file_data': json.loads(user_session.file_data) if user_session.file_data else None,
                        'created_at': user_session.created_at,
                        'updated_at': user_session.updated_at
                    }
                
                return None
                
        except Exception as e:
            logger.error(f"Error retrieving user session: {e}")
            return None
    
    def update_user_session(self, user_id: str, **kwargs):
        """Update user session data"""
        try:
            with self.get_session() as session:
                if session is None:
                    return
                
                user_session = session.query(UserSession).filter(
                    UserSession.user_id == user_id,
                    UserSession.is_active == True
                ).first()
                
                if user_session:
                    for key, value in kwargs.items():
                        if hasattr(user_session, key):
                            if isinstance(value, dict):
                                setattr(user_session, key, json.dumps(value))
                            else:
                                setattr(user_session, key, value)
                    
                    user_session.updated_at = datetime.utcnow()
                    logger.info(f"Updated session for user {user_id}")
                
        except Exception as e:
            logger.error(f"Error updating user session: {e}")
    
    def store_metrics(self, user_id: str, command: str, launch_date: Optional[str] = None, 
                     response_time: Optional[int] = None, success: bool = True, 
                     error_message: Optional[str] = None):
        """Store bot usage metrics"""
        try:
            with self.get_session() as session:
                if session is None:
                    return
                
                metric = BotMetrics(
                    user_id=user_id,
                    command=command,
                    launch_date=launch_date,
                    response_time=response_time,
                    success=success,
                    error_message=error_message
                )
                
                session.add(metric)
                logger.debug(f"Stored metric for user {user_id}, command {command}")
                
        except Exception as e:
            logger.error(f"Error storing metrics: {e}")
    
    def get_metrics_summary(self, days: int = 30) -> Dict[str, Any]:
        """Get metrics summary for monitoring"""
        try:
            with self.get_session() as session:
                if session is None:
                    return {}
                
                cutoff_date = datetime.utcnow() - timedelta(days=days)
                
                # Total commands
                total_commands = session.query(BotMetrics).filter(
                    BotMetrics.created_at >= cutoff_date
                ).count()
                
                # Successful commands
                successful_commands = session.query(BotMetrics).filter(
                    BotMetrics.created_at >= cutoff_date,
                    BotMetrics.success == True
                ).count()
                
                # Command breakdown
                command_breakdown = session.query(
                    BotMetrics.command,
                    session.query(BotMetrics).filter(
                        BotMetrics.command == BotMetrics.command,
                        BotMetrics.created_at >= cutoff_date
                    ).count().label('count')
                ).filter(
                    BotMetrics.created_at >= cutoff_date
                ).group_by(BotMetrics.command).all()
                
                # Average response time
                avg_response_time = session.query(
                    session.query(BotMetrics.response_time).filter(
                        BotMetrics.created_at >= cutoff_date,
                        BotMetrics.response_time.isnot(None)
                    ).scalar()
                ).scalar()
                
                return {
                    'total_commands': total_commands,
                    'successful_commands': successful_commands,
                    'success_rate': (successful_commands / total_commands * 100) if total_commands > 0 else 0,
                    'command_breakdown': {cmd: count for cmd, count in command_breakdown},
                    'avg_response_time': avg_response_time or 0,
                    'period_days': days
                }
                
        except Exception as e:
            logger.error(f"Error getting metrics summary: {e}")
            return {}
    
    def cleanup_old_data(self):
        """Clean up old data based on retention policy"""
        try:
            with self.get_session() as session:
                if session is None:
                    return
                
                # Clean up old sessions
                retention_date = datetime.utcnow() - timedelta(days=ProductionConfig.DATA_RETENTION_DAYS)
                deleted_sessions = session.query(UserSession).filter(
                    UserSession.created_at < retention_date
                ).delete()
                
                # Clean up old metrics
                retention_date = datetime.utcnow() - timedelta(days=ProductionConfig.DATA_RETENTION_DAYS)
                deleted_metrics = session.query(BotMetrics).filter(
                    BotMetrics.created_at < retention_date
                ).delete()
                
                logger.info(f"Cleaned up {deleted_sessions} old sessions and {deleted_metrics} old metrics")
                
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
    
    def health_check(self) -> Dict[str, Any]:
        """Database health check"""
        try:
            if not self.engine:
                return {'status': 'unavailable', 'message': 'Database not configured'}
            
            with self.get_session() as session:
                if session is None:
                    return {'status': 'unavailable', 'message': 'Database session failed'}
                
                # Test query
                session.execute("SELECT 1")
                return {'status': 'healthy', 'message': 'Database connection successful'}
                
        except Exception as e:
            return {'status': 'unhealthy', 'message': f'Database error: {str(e)}'}

# Global database manager instance
db_manager = DatabaseManager() 