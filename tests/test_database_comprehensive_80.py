import pytest
import unittest
from unittest.mock import Mock, patch, MagicMock, call
import sys
import os
import json
from datetime import datetime, timedelta
from contextlib import contextmanager

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database import DatabaseManager, UserSession, BotMetrics

class TestDatabaseManagerComprehensive:
    """Comprehensive tests for DatabaseManager"""
    
    def setup_method(self):
        """Set up test fixtures"""
        with patch('database.ProductionConfig') as mock_config:
            mock_config.DATABASE_URL = 'sqlite:///:memory:'
            mock_config.DATABASE_POOL_SIZE = 5
            mock_config.DATABASE_MAX_OVERFLOW = 10
            
            with patch('database.create_engine') as mock_create_engine, \
                 patch('database.sessionmaker') as mock_sessionmaker, \
                 patch('database.Base.metadata.create_all') as mock_create_all:
                
                # Configure mocks
                mock_engine = Mock()
                mock_create_engine.return_value = mock_engine
                
                mock_session_class = Mock()
                mock_sessionmaker.return_value = mock_session_class
                
                self.db_manager = DatabaseManager()
    
    def test_initialization_success(self):
        """Test successful database initialization"""
        assert self.db_manager.engine is not None
        assert self.db_manager.SessionLocal is not None
    
    def test_initialization_no_database_url(self):
        """Test initialization without database URL"""
        with patch('database.ProductionConfig') as mock_config:
            mock_config.DATABASE_URL = None
            
            with patch('database.create_engine') as mock_create_engine, \
                 patch('database.sessionmaker') as mock_sessionmaker:
                
                db_manager = DatabaseManager()
                
                # Should not create engine
                mock_create_engine.assert_not_called()
                assert db_manager.engine is None
                assert db_manager.SessionLocal is None
    
    def test_initialization_with_error(self):
        """Test initialization with database error"""
        with patch('database.ProductionConfig') as mock_config:
            mock_config.DATABASE_URL = 'invalid://url'
            
            with patch('database.create_engine') as mock_create_engine:
                mock_create_engine.side_effect = Exception("Database error")
                
                db_manager = DatabaseManager()
                
                # Should handle error gracefully
                assert db_manager.engine is None
                assert db_manager.SessionLocal is None
    
    def test_get_session_success(self):
        """Test successful session creation"""
        mock_session = Mock()
        self.db_manager.SessionLocal.return_value = mock_session
        
        with self.db_manager.get_session() as session:
            assert session == mock_session
        
        # Verify session was committed and closed
        mock_session.commit.assert_called_once()
        mock_session.close.assert_called_once()
    
    def test_get_session_no_database(self):
        """Test session creation when database is not available"""
        self.db_manager.SessionLocal = None
        
        with self.db_manager.get_session() as session:
            assert session is None
    
    def test_get_session_with_error(self):
        """Test session creation with error"""
        mock_session = Mock()
        mock_session.commit.side_effect = Exception("Commit error")
        self.db_manager.SessionLocal.return_value = mock_session
        
        with pytest.raises(Exception):
            with self.db_manager.get_session() as session:
                pass
        
        # Verify session was rolled back and closed
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()
    
    def test_store_user_session_success(self):
        """Test successful user session storage"""
        mock_session = Mock()
        self.db_manager.SessionLocal.return_value = mock_session
        
        user_id = 'U123456'
        launch_date = '2024-03-15'
        databricks_data = {'BOM': {'status': 'success'}}
        file_data = {'file': 'data'}
        
        self.db_manager.store_user_session(user_id, launch_date, databricks_data, file_data)
        
        # Verify session was added
        mock_session.add.assert_called_once()
        added_session = mock_session.add.call_args[0][0]
        assert isinstance(added_session, UserSession)
        assert added_session.user_id == user_id
        assert added_session.launch_date == launch_date
        assert json.loads(added_session.databricks_data) == databricks_data
        assert json.loads(added_session.file_data) == file_data
    
    def test_store_user_session_no_database(self):
        """Test user session storage when database is not available"""
        self.db_manager.SessionLocal = None
        
        # Should not raise exception
        self.db_manager.store_user_session('U123456', '2024-03-15', {})
    
    def test_store_user_session_with_error(self):
        """Test user session storage with error"""
        mock_session = Mock()
        mock_session.add.side_effect = Exception("Add error")
        self.db_manager.SessionLocal.return_value = mock_session
        
        with pytest.raises(Exception):
            self.db_manager.store_user_session('U123456', '2024-03-15', {})
    
    def test_get_user_session_success(self):
        """Test successful user session retrieval"""
        mock_session = Mock()
        self.db_manager.SessionLocal.return_value = mock_session
        
        # Mock existing session
        existing_session = UserSession(
            user_id='U123456',
            launch_date='2024-03-15',
            databricks_data=json.dumps({'BOM': {'status': 'success'}}),
            file_data=json.dumps({'file': 'data'})
        )
        mock_session.query.return_value.filter.return_value.first.return_value = existing_session
        
        result = self.db_manager.get_user_session('U123456')
        
        assert result is not None
        assert result['user_id'] == 'U123456'
        assert result['launch_date'] == '2024-03-15'
        assert result['databricks_data'] == {'BOM': {'status': 'success'}}
        assert result['file_data'] == {'file': 'data'}
    
    def test_get_user_session_not_found(self):
        """Test user session retrieval when not found"""
        mock_session = Mock()
        self.db_manager.SessionLocal.return_value = mock_session
        
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        result = self.db_manager.get_user_session('U123456')
        
        assert result is None
    
    def test_get_user_session_no_database(self):
        """Test user session retrieval when database is not available"""
        self.db_manager.SessionLocal = None
        
        result = self.db_manager.get_user_session('U123456')
        
        assert result is None
    
    def test_update_user_session_success(self):
        """Test successful user session update"""
        mock_session = Mock()
        self.db_manager.SessionLocal.return_value = mock_session
        
        # Mock existing session
        existing_session = UserSession(
            user_id='U123456',
            launch_date='2024-03-15',
            databricks_data=json.dumps({'BOM': {'status': 'success'}})
        )
        mock_session.query.return_value.filter.return_value.first.return_value = existing_session
        
        self.db_manager.update_user_session('U123456', launch_date='2024-04-15')
        
        # Verify session was updated
        assert existing_session.launch_date == '2024-04-15'
    
    def test_update_user_session_not_found(self):
        """Test user session update when not found"""
        mock_session = Mock()
        self.db_manager.SessionLocal.return_value = mock_session
        
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        # Should not raise exception
        self.db_manager.update_user_session('U123456', launch_date='2024-04-15')
    
    def test_store_metrics_success(self):
        """Test successful metrics storage"""
        mock_session = Mock()
        self.db_manager.SessionLocal.return_value = mock_session
        
        user_id = 'U123456'
        command = 'vehicle_query'
        launch_date = '2024-03-15'
        response_time = 1500
        success = True
        error_message = None
        
        self.db_manager.store_metrics(user_id, command, launch_date, response_time, success, error_message)
        
        # Verify metrics were added
        mock_session.add.assert_called_once()
        added_metrics = mock_session.add.call_args[0][0]
        assert isinstance(added_metrics, BotMetrics)
        assert added_metrics.user_id == user_id
        assert added_metrics.command == command
        assert added_metrics.launch_date == launch_date
        assert added_metrics.response_time == response_time
        assert added_metrics.success == success
        assert added_metrics.error_message == error_message
    
    def test_store_metrics_with_error(self):
        """Test metrics storage with error"""
        mock_session = Mock()
        mock_session.add.side_effect = Exception("Add error")
        self.db_manager.SessionLocal.return_value = mock_session
        
        with pytest.raises(Exception):
            self.db_manager.store_metrics('U123456', 'test_command')
    
    def test_get_metrics_summary_success(self):
        """Test successful metrics summary retrieval"""
        mock_session = Mock()
        self.db_manager.SessionLocal.return_value = mock_session
        
        # Mock metrics data
        mock_metrics = [
            BotMetrics(user_id='U123456', command='vehicle_query', success=True, response_time=1000),
            BotMetrics(user_id='U123456', command='file_upload', success=True, response_time=2000),
            BotMetrics(user_id='U123456', command='dashboard', success=False, response_time=3000, error_message='Error')
        ]
        mock_session.query.return_value.filter.return_value.all.return_value = mock_metrics
        
        result = self.db_manager.get_metrics_summary(days=30)
        
        assert 'total_commands' in result
        assert 'successful_commands' in result
        assert 'failed_commands' in result
        assert 'average_response_time' in result
        assert 'command_breakdown' in result
    
    def test_get_metrics_summary_no_data(self):
        """Test metrics summary retrieval with no data"""
        mock_session = Mock()
        self.db_manager.SessionLocal.return_value = mock_session
        
        mock_session.query.return_value.filter.return_value.all.return_value = []
        
        result = self.db_manager.get_metrics_summary(days=30)
        
        assert result['total_commands'] == 0
        assert result['successful_commands'] == 0
        assert result['failed_commands'] == 0
        assert result['average_response_time'] == 0
    
    def test_cleanup_old_data_success(self):
        """Test successful cleanup of old data"""
        mock_session = Mock()
        self.db_manager.SessionLocal.return_value = mock_session
        
        # Mock old sessions and metrics
        old_sessions = [UserSession(id=1), UserSession(id=2)]
        old_metrics = [BotMetrics(id=1), BotMetrics(id=2)]
        
        mock_session.query.return_value.filter.return_value.all.side_effect = [old_sessions, old_metrics]
        
        result = self.db_manager.cleanup_old_data()
        
        # Verify cleanup was performed
        assert mock_session.delete.call_count == 4  # 2 sessions + 2 metrics
        assert result == 4
    
    def test_cleanup_old_data_no_data(self):
        """Test cleanup with no old data"""
        mock_session = Mock()
        self.db_manager.SessionLocal.return_value = mock_session
        
        mock_session.query.return_value.filter.return_value.all.return_value = []
        
        result = self.db_manager.cleanup_old_data()
        
        assert result == 0
    
    def test_health_check_healthy(self):
        """Test health check when database is healthy"""
        mock_session = Mock()
        self.db_manager.SessionLocal.return_value = mock_session
        
        # Mock successful connection test
        mock_session.execute.return_value = Mock()
        
        result = self.db_manager.health_check()
        
        assert result['status'] == 'healthy'
        assert 'message' in result
        assert 'uptime' in result
    
    def test_health_check_unhealthy(self):
        """Test health check when database is unhealthy"""
        mock_session = Mock()
        self.db_manager.SessionLocal.return_value = mock_session
        
        # Mock connection error
        mock_session.execute.side_effect = Exception("Connection error")
        
        result = self.db_manager.health_check()
        
        assert result['status'] == 'unhealthy'
        assert 'error' in result['message'].lower()
    
    def test_health_check_no_database(self):
        """Test health check when database is not available"""
        self.db_manager.SessionLocal = None
        
        result = self.db_manager.health_check()
        
        assert result['status'] == 'unavailable'
        assert 'not configured' in result['message'].lower()

class TestUserSession:
    """Tests for UserSession model"""
    
    def test_user_session_creation(self):
        """Test UserSession creation"""
        session = UserSession(
            user_id='U123456',
            launch_date='2024-03-15',
            databricks_data=json.dumps({'test': 'data'}),
            file_data=json.dumps({'file': 'data'})
        )
        
        assert session.user_id == 'U123456'
        assert session.launch_date == '2024-03-15'
        assert session.databricks_data == json.dumps({'test': 'data'})
        assert session.file_data == json.dumps({'file': 'data'})
        assert session.is_active is True
    
    def test_user_session_repr(self):
        """Test UserSession string representation"""
        session = UserSession(user_id='U123456', launch_date='2024-03-15')
        
        repr_str = repr(session)
        assert 'UserSession' in repr_str
        assert 'U123456' in repr_str

class TestBotMetrics:
    """Tests for BotMetrics model"""
    
    def test_bot_metrics_creation(self):
        """Test BotMetrics creation"""
        metrics = BotMetrics(
            user_id='U123456',
            command='vehicle_query',
            launch_date='2024-03-15',
            response_time=1500,
            success=True,
            error_message=None
        )
        
        assert metrics.user_id == 'U123456'
        assert metrics.command == 'vehicle_query'
        assert metrics.launch_date == '2024-03-15'
        assert metrics.response_time == 1500
        assert metrics.success is True
        assert metrics.error_message is None
    
    def test_bot_metrics_with_error(self):
        """Test BotMetrics creation with error"""
        metrics = BotMetrics(
            user_id='U123456',
            command='vehicle_query',
            launch_date='2024-03-15',
            response_time=3000,
            success=False,
            error_message='Connection timeout'
        )
        
        assert metrics.success is False
        assert metrics.error_message == 'Connection timeout'
    
    def test_bot_metrics_repr(self):
        """Test BotMetrics string representation"""
        metrics = BotMetrics(user_id='U123456', command='vehicle_query')
        
        repr_str = repr(metrics)
        assert 'BotMetrics' in repr_str
        assert 'vehicle_query' in repr_str

class TestDatabaseIntegration:
    """Integration tests for database operations"""
    
    def test_full_workflow(self):
        """Test complete database workflow"""
        with patch('database.ProductionConfig') as mock_config:
            mock_config.DATABASE_URL = 'sqlite:///:memory:'
            mock_config.DATABASE_POOL_SIZE = 5
            mock_config.DATABASE_MAX_OVERFLOW = 10
            
            with patch('database.create_engine') as mock_create_engine, \
                 patch('database.sessionmaker') as mock_sessionmaker, \
                 patch('database.Base.metadata.create_all') as mock_create_all:
                
                mock_engine = Mock()
                mock_create_engine.return_value = mock_engine
                
                mock_session_class = Mock()
                mock_sessionmaker.return_value = mock_session_class
                
                db_manager = DatabaseManager()
                
                # Test session storage
                mock_session = Mock()
                mock_session_class.return_value = mock_session
                
                db_manager.store_user_session('U123456', '2024-03-15', {'test': 'data'})
                
                # Test session retrieval
                mock_session.query.return_value.filter.return_value.first.return_value = UserSession(
                    user_id='U123456',
                    launch_date='2024-03-15',
                    databricks_data=json.dumps({'test': 'data'})
                )
                
                result = db_manager.get_user_session('U123456')
                
                assert result is not None
                assert result['user_id'] == 'U123456'
    
    def test_error_handling_comprehensive(self):
        """Test comprehensive error handling"""
        with patch('database.ProductionConfig') as mock_config:
            mock_config.DATABASE_URL = 'sqlite:///:memory:'
            
            with patch('database.create_engine') as mock_create_engine, \
                 patch('database.sessionmaker') as mock_sessionmaker:
                
                mock_engine = Mock()
                mock_create_engine.return_value = mock_engine
                
                mock_session_class = Mock()
                mock_sessionmaker.return_value = mock_session_class
                
                db_manager = DatabaseManager()
                
                # Test various error scenarios
                error_scenarios = [
                    (Exception("General error"), "general"),
                    (ConnectionError("Network error"), "network"),
                    (ValueError("Invalid data"), "data"),
                    (TimeoutError("Timeout"), "timeout")
                ]
                
                for exception, error_type in error_scenarios:
                    mock_session = Mock()
                    mock_session.commit.side_effect = exception
                    mock_session_class.return_value = mock_session
                    
                    with pytest.raises(Exception):
                        with db_manager.get_session():
                            pass
                    
                    # Verify session was rolled back and closed
                    mock_session.rollback.assert_called_once()
                    mock_session.close.assert_called_once()
    
    def test_performance_metrics(self):
        """Test performance of database operations"""
        import time
        
        with patch('database.ProductionConfig') as mock_config:
            mock_config.DATABASE_URL = 'sqlite:///:memory:'
            
            with patch('database.create_engine') as mock_create_engine, \
                 patch('database.sessionmaker') as mock_sessionmaker:
                
                mock_engine = Mock()
                mock_create_engine.return_value = mock_engine
                
                mock_session_class = Mock()
                mock_sessionmaker.return_value = mock_session_class
                
                db_manager = DatabaseManager()
                
                # Test session creation performance
                mock_session = Mock()
                mock_session_class.return_value = mock_session
                
                start_time = time.time()
                
                with db_manager.get_session() as session:
                    pass
                
                end_time = time.time()
                
                # Verify operation completed in reasonable time
                duration = end_time - start_time
                assert duration < 1.0  # Should complete within 1 second

if __name__ == '__main__':
    pytest.main([__file__]) 