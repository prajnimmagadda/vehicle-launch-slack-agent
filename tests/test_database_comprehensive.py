import pytest
import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
from datetime import datetime, timedelta

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database import DatabaseManager, UserSession, BotMetrics

class TestDatabaseManagerComprehensive:
    """Comprehensive tests for DatabaseManager"""
    
    def setup_method(self):
        """Setup test method"""
        self.mock_engine = Mock()
        self.mock_session = Mock()
        self.mock_session_factory = Mock()
        
    @patch('database.create_engine')
    @patch('database.sessionmaker')
    def test_initialization_with_database_url(self, mock_sessionmaker, mock_create_engine):
        """Test database initialization with valid URL"""
        mock_create_engine.return_value = self.mock_engine
        mock_sessionmaker.return_value = self.mock_session_factory
        self.mock_session_factory.return_value = self.mock_session
        
        with patch.dict(os.environ, {'DATABASE_URL': 'postgresql://test:test@localhost/test'}):
            db_manager = DatabaseManager()
            
            assert db_manager.engine is not None
            assert db_manager.SessionLocal is not None
            mock_create_engine.assert_called_once()
            mock_sessionmaker.assert_called_once()
    
    @patch('database.create_engine')
    def test_initialization_no_database_url(self, mock_create_engine):
        """Test database initialization without URL"""
        with patch.dict(os.environ, {}, clear=True):
            db_manager = DatabaseManager()
            
            assert db_manager.engine is None
            assert db_manager.SessionLocal is None
            mock_create_engine.assert_not_called()
    
    @patch('database.create_engine')
    @patch('database.sessionmaker')
    def test_health_check_healthy(self, mock_sessionmaker, mock_create_engine):
        """Test database health check when healthy"""
        mock_create_engine.return_value = self.mock_engine
        mock_sessionmaker.return_value = self.mock_session_factory
        self.mock_session_factory.return_value = self.mock_session
        
        # Mock successful connection
        self.mock_session.execute.return_value = Mock()
        
        with patch.dict(os.environ, {'DATABASE_URL': 'postgresql://test:test@localhost/test'}):
            db_manager = DatabaseManager()
            health = db_manager.health_check()
            
            assert health['status'] == 'healthy'
            assert 'message' in health
    
    @patch('database.create_engine')
    @patch('database.sessionmaker')
    def test_health_check_unhealthy(self, mock_sessionmaker, mock_create_engine):
        """Test database health check when unhealthy"""
        mock_create_engine.return_value = self.mock_engine
        mock_sessionmaker.return_value = self.mock_session_factory
        self.mock_session_factory.return_value = self.mock_session
        
        # Mock connection failure
        self.mock_session.execute.side_effect = Exception("Connection failed")
        
        with patch.dict(os.environ, {'DATABASE_URL': 'postgresql://test:test@localhost/test'}):
            db_manager = DatabaseManager()
            health = db_manager.health_check()
            
            assert health['status'] == 'unhealthy'
            assert 'error' in health['message']
    
    def test_health_check_no_database(self):
        """Test database health check without database"""
        db_manager = DatabaseManager()
        health = db_manager.health_check()
        
        assert health['status'] == 'unhealthy'
        assert 'No database configured' in health['message']
    
    @patch('database.create_engine')
    @patch('database.sessionmaker')
    def test_get_session_success(self, mock_sessionmaker, mock_create_engine):
        """Test getting database session successfully"""
        mock_create_engine.return_value = self.mock_engine
        mock_sessionmaker.return_value = self.mock_session_factory
        self.mock_session_factory.return_value = self.mock_session
        
        with patch.dict(os.environ, {'DATABASE_URL': 'postgresql://test:test@localhost/test'}):
            db_manager = DatabaseManager()
            session = db_manager.get_session()
            
            assert session is not None
            self.mock_session_factory.assert_called_once()
    
    @patch('database.create_engine')
    @patch('database.sessionmaker')
    def test_get_session_exception(self, mock_sessionmaker, mock_create_engine):
        """Test getting database session with exception"""
        mock_create_engine.return_value = self.mock_engine
        mock_sessionmaker.return_value = self.mock_session_factory
        self.mock_session_factory.side_effect = Exception("Session creation failed")
        
        with patch.dict(os.environ, {'DATABASE_URL': 'postgresql://test:test@localhost/test'}):
            db_manager = DatabaseManager()
            
            with pytest.raises(Exception):
                db_manager.get_session()
    
    @patch('database.create_engine')
    @patch('database.sessionmaker')
    def test_save_command_log(self, mock_sessionmaker, mock_create_engine):
        """Test saving command log"""
        mock_create_engine.return_value = self.mock_engine
        mock_sessionmaker.return_value = self.mock_session_factory
        self.mock_session_factory.return_value = self.mock_session
        
        with patch.dict(os.environ, {'DATABASE_URL': 'postgresql://test:test@localhost/test'}):
            db_manager = DatabaseManager()
            
            # Mock the session context manager
            with patch.object(db_manager, 'get_session') as mock_get_session:
                mock_get_session.return_value.__enter__.return_value = self.mock_session
                mock_get_session.return_value.__exit__.return_value = None
                
                result = db_manager.store_metrics(
                    user_id='U123',
                    command='test_command',
                    launch_date='2024-03-15',
                    response_time=1500,
                    success=True,
                    error_message=None
                )
                
                assert result is True
                self.mock_session.add.assert_called_once()
                self.mock_session.commit.assert_called_once()
    
    @patch('database.create_engine')
    @patch('database.sessionmaker')
    def test_save_error_log(self, mock_sessionmaker, mock_create_engine):
        """Test saving error log"""
        mock_create_engine.return_value = self.mock_engine
        mock_sessionmaker.return_value = self.mock_session_factory
        self.mock_session_factory.return_value = self.mock_session
        
        with patch.dict(os.environ, {'DATABASE_URL': 'postgresql://test:test@localhost/test'}):
            db_manager = DatabaseManager()
            
            # Mock the session context manager
            with patch.object(db_manager, 'get_session') as mock_get_session:
                mock_get_session.return_value.__enter__.return_value = self.mock_session
                mock_get_session.return_value.__exit__.return_value = None
                
                result = db_manager.store_metrics(
                    user_id='U123',
                    command='test_command',
                    launch_date='2024-03-15',
                    response_time=2000,
                    success=False,
                    error_message='Test error message'
                )
                
                assert result is True
                self.mock_session.add.assert_called_once()
                self.mock_session.commit.assert_called_once()
    
    @patch('database.create_engine')
    @patch('database.sessionmaker')
    def test_get_command_stats(self, mock_sessionmaker, mock_create_engine):
        """Test getting command statistics"""
        mock_create_engine.return_value = self.mock_engine
        mock_sessionmaker.return_value = self.mock_session_factory
        self.mock_session_factory.return_value = self.mock_session
        
        # Mock query results
        mock_result = Mock()
        mock_result.scalar.return_value = 10
        self.mock_session.execute.return_value = mock_result
        
        with patch.dict(os.environ, {'DATABASE_URL': 'postgresql://test:test@localhost/test'}):
            db_manager = DatabaseManager()
            
            # Mock the session context manager
            with patch.object(db_manager, 'get_session') as mock_get_session:
                mock_get_session.return_value.__enter__.return_value = self.mock_session
                mock_get_session.return_value.__exit__.return_value = None
                
                stats = db_manager.get_metrics_summary(days=7)
                
                assert 'total_commands' in stats
                assert 'successful_commands' in stats
                assert 'failed_commands' in stats
                assert 'avg_response_time' in stats
                self.mock_session.execute.assert_called()
    
    @patch('database.create_engine')
    @patch('database.sessionmaker')
    def test_get_error_stats(self, mock_sessionmaker, mock_create_engine):
        """Test getting error statistics"""
        mock_create_engine.return_value = self.mock_engine
        mock_sessionmaker.return_value = self.mock_session_factory
        self.mock_session_factory.return_value = self.mock_session
        
        # Mock query results
        mock_result = Mock()
        mock_result.scalar.return_value = 5
        self.mock_session.execute.return_value = mock_result
        
        with patch.dict(os.environ, {'DATABASE_URL': 'postgresql://test:test@localhost/test'}):
            db_manager = DatabaseManager()
            
            # Mock the session context manager
            with patch.object(db_manager, 'get_session') as mock_get_session:
                mock_get_session.return_value.__enter__.return_value = self.mock_session
                mock_get_session.return_value.__exit__.return_value = None
                
                stats = db_manager.get_metrics_summary(days=7)
                
                assert 'total_commands' in stats
                assert 'error_summary' in stats
                self.mock_session.execute.assert_called()
    
    @patch('database.create_engine')
    @patch('database.sessionmaker')
    def test_cleanup_old_logs(self, mock_sessionmaker, mock_create_engine):
        """Test cleaning up old logs"""
        mock_create_engine.return_value = self.mock_engine
        mock_sessionmaker.return_value = self.mock_session_factory
        self.mock_session_factory.return_value = self.mock_session
        
        # Mock delete results
        mock_result = Mock()
        mock_result.rowcount = 50
        self.mock_session.execute.return_value = mock_result
        
        with patch.dict(os.environ, {'DATABASE_URL': 'postgresql://test:test@localhost/test'}):
            db_manager = DatabaseManager()
            
            # Mock the session context manager
            with patch.object(db_manager, 'get_session') as mock_get_session:
                mock_get_session.return_value.__enter__.return_value = self.mock_session
                mock_get_session.return_value.__exit__.return_value = None
                
                result = db_manager.cleanup_old_data()
                
                assert result == 50
                self.mock_session.execute.assert_called()
                self.mock_session.commit.assert_called_once()
    
    @patch('database.create_engine')
    @patch('database.sessionmaker')
    def test_create_tables(self, mock_sessionmaker, mock_create_engine):
        """Test creating database tables"""
        mock_create_engine.return_value = self.mock_engine
        mock_sessionmaker.return_value = self.mock_session_factory
        self.mock_session_factory.return_value = self.mock_session
        
        with patch.dict(os.environ, {'DATABASE_URL': 'postgresql://test:test@localhost/test'}):
            db_manager = DatabaseManager()
            
            # Mock Base.metadata.create_all
            with patch('database.Base.metadata.create_all') as mock_create_all:
                result = db_manager.create_tables()
                
                assert result is True
                mock_create_all.assert_called_once_with(self.mock_engine)
    
    @patch('database.create_engine')
    @patch('database.sessionmaker')
    def test_close(self, mock_sessionmaker, mock_create_engine):
        """Test closing database connection"""
        mock_create_engine.return_value = self.mock_engine
        mock_sessionmaker.return_value = self.mock_session_factory
        self.mock_session_factory.return_value = self.mock_session
        
        with patch.dict(os.environ, {'DATABASE_URL': 'postgresql://test:test@localhost/test'}):
            db_manager = DatabaseManager()
            db_manager.close()
            
            self.mock_engine.dispose.assert_called_once()

class TestUserSession:
    """Test UserSession model"""
    
    def test_user_session_creation(self):
        """Test UserSession model creation"""
        session = UserSession(
            user_id='U123',
            launch_date='2024-03-15',
            databricks_data='{"test": "data"}',
            file_data='{"file": "data"}'
        )
        
        assert session.user_id == 'U123'
        assert session.launch_date == '2024-03-15'
        assert session.databricks_data == '{"test": "data"}'
        assert session.file_data == '{"file": "data"}'
        assert session.is_active is True
    
    def test_user_session_repr(self):
        """Test UserSession string representation"""
        session = UserSession(
            user_id='U123',
            launch_date='2024-03-15'
        )
        
        repr_str = repr(session)
        assert 'UserSession' in repr_str
        assert 'U123' in repr_str

class TestBotMetrics:
    """Test BotMetrics model"""
    
    def test_bot_metrics_creation(self):
        """Test BotMetrics model creation"""
        metrics = BotMetrics(
            user_id='U123',
            command='test_command',
            launch_date='2024-03-15',
            response_time=1500,
            success=True,
            error_message=None
        )
        
        assert metrics.user_id == 'U123'
        assert metrics.command == 'test_command'
        assert metrics.launch_date == '2024-03-15'
        assert metrics.response_time == 1500
        assert metrics.success is True
        assert metrics.error_message is None
    
    def test_bot_metrics_repr(self):
        """Test BotMetrics string representation"""
        metrics = BotMetrics(
            user_id='U123',
            command='test_command'
        )
        
        repr_str = repr(metrics)
        assert 'BotMetrics' in repr_str
        assert 'test_command' in repr_str

if __name__ == '__main__':
    pytest.main([__file__]) 