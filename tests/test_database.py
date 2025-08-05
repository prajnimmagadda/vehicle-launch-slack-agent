import pytest
import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database import DatabaseManager

class TestDatabaseManager:
    """Test DatabaseManager class"""
    
    @patch('database.DATABASE_URL', None)
    def test_initialization_no_database_url(self):
        """Test DatabaseManager initialization without DATABASE_URL"""
        db_manager = DatabaseManager()
        assert db_manager.engine is None
        assert db_manager.session_factory is None
    
    @patch('database.DATABASE_URL', 'postgresql://user:pass@localhost/testdb')
    @patch('database.create_engine')
    def test_initialization_with_database_url(self, mock_create_engine):
        """Test DatabaseManager initialization with DATABASE_URL"""
        mock_engine = Mock()
        mock_create_engine.return_value = mock_engine
        
        db_manager = DatabaseManager()
        
        assert db_manager.engine == mock_engine
        mock_create_engine.assert_called_once()
    
    @patch('database.DATABASE_URL', 'postgresql://user:pass@localhost/testdb')
    @patch('database.create_engine')
    def test_health_check_healthy(self, mock_create_engine):
        """Test database health check when healthy"""
        mock_engine = Mock()
        mock_create_engine.return_value = mock_engine
        
        # Mock successful connection
        mock_connection = Mock()
        mock_engine.connect.return_value.__enter__.return_value = mock_connection
        mock_connection.execute.return_value.scalar.return_value = 1
        
        db_manager = DatabaseManager()
        health = db_manager.health_check()
        
        assert health['status'] == 'healthy'
        assert 'message' in health
        assert 'uptime' in health
    
    @patch('database.DATABASE_URL', 'postgresql://user:pass@localhost/testdb')
    @patch('database.create_engine')
    def test_health_check_unhealthy(self, mock_create_engine):
        """Test database health check when unhealthy"""
        mock_engine = Mock()
        mock_create_engine.return_value = mock_engine
        
        # Mock failed connection
        mock_engine.connect.side_effect = Exception("Connection failed")
        
        db_manager = DatabaseManager()
        health = db_manager.health_check()
        
        assert health['status'] == 'unhealthy'
        assert 'error' in health
        assert 'Connection failed' in health['error']
    
    @patch('database.DATABASE_URL', None)
    def test_health_check_no_database(self):
        """Test database health check when no database configured"""
        db_manager = DatabaseManager()
        health = db_manager.health_check()
        
        assert health['status'] == 'disabled'
        assert 'message' in health
        assert 'not configured' in health['message']
    
    @patch('database.DATABASE_URL', 'postgresql://user:pass@localhost/testdb')
    @patch('database.create_engine')
    def test_get_session_success(self, mock_create_engine):
        """Test successful session creation"""
        mock_engine = Mock()
        mock_create_engine.return_value = mock_engine
        
        db_manager = DatabaseManager()
        
        with db_manager.get_session() as session:
            assert session is not None
    
    @patch('database.DATABASE_URL', 'postgresql://user:pass@localhost/testdb')
    @patch('database.create_engine')
    def test_get_session_exception(self, mock_create_engine):
        """Test session creation with exception"""
        mock_engine = Mock()
        mock_create_engine.return_value = mock_engine
        
        # Mock session factory that raises exception
        mock_session_factory = Mock()
        mock_session_factory.side_effect = Exception("Session creation failed")
        db_manager = DatabaseManager()
        db_manager.session_factory = mock_session_factory
        
        with pytest.raises(Exception, match="Session creation failed"):
            with db_manager.get_session():
                pass
    
    @patch('database.DATABASE_URL', 'postgresql://user:pass@localhost/testdb')
    @patch('database.create_engine')
    def test_save_command_log(self, mock_create_engine):
        """Test saving command log"""
        mock_engine = Mock()
        mock_create_engine.return_value = mock_engine
        
        db_manager = DatabaseManager()
        
        # Mock session
        mock_session = Mock()
        db_manager.session_factory = Mock()
        db_manager.session_factory.return_value = mock_session
        
        # Test saving command log
        db_manager.save_command_log(
            command="test_command",
            user_id="test_user",
            channel_id="test_channel",
            success=True,
            response_time=1.5,
            error_message=None
        )
        
        # Verify session was used
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
    
    @patch('database.DATABASE_URL', 'postgresql://user:pass@localhost/testdb')
    @patch('database.create_engine')
    def test_save_error_log(self, mock_create_engine):
        """Test saving error log"""
        mock_engine = Mock()
        mock_create_engine.return_value = mock_engine
        
        db_manager = DatabaseManager()
        
        # Mock session
        mock_session = Mock()
        db_manager.session_factory = Mock()
        db_manager.session_factory.return_value = mock_session
        
        # Test saving error log
        db_manager.save_error_log(
            error_type="test_error",
            error_message="Test error message",
            stack_trace="Test stack trace",
            user_id="test_user",
            channel_id="test_channel"
        )
        
        # Verify session was used
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
    
    @patch('database.DATABASE_URL', 'postgresql://user:pass@localhost/testdb')
    @patch('database.create_engine')
    def test_get_command_stats(self, mock_create_engine):
        """Test getting command statistics"""
        mock_engine = Mock()
        mock_create_engine.return_value = mock_engine
        
        db_manager = DatabaseManager()
        
        # Mock session and query result
        mock_session = Mock()
        mock_result = Mock()
        mock_result.fetchall.return_value = [
            ('test_command', 10, 8, 2, 1.5)
        ]
        mock_session.execute.return_value = mock_result
        
        db_manager.session_factory = Mock()
        db_manager.session_factory.return_value = mock_session
        
        stats = db_manager.get_command_stats()
        
        # Verify query was executed
        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()
        
        # Verify result structure
        assert len(stats) == 1
        assert stats[0]['command'] == 'test_command'
        assert stats[0]['total_calls'] == 10
        assert stats[0]['successful_calls'] == 8
        assert stats[0]['failed_calls'] == 2
        assert stats[0]['avg_response_time'] == 1.5
    
    @patch('database.DATABASE_URL', 'postgresql://user:pass@localhost/testdb')
    @patch('database.create_engine')
    def test_get_error_stats(self, mock_create_engine):
        """Test getting error statistics"""
        mock_engine = Mock()
        mock_create_engine.return_value = mock_engine
        
        db_manager = DatabaseManager()
        
        # Mock session and query result
        mock_session = Mock()
        mock_result = Mock()
        mock_result.fetchall.return_value = [
            ('test_error', 5, '2024-01-01')
        ]
        mock_session.execute.return_value = mock_result
        
        db_manager.session_factory = Mock()
        db_manager.session_factory.return_value = mock_session
        
        stats = db_manager.get_error_stats()
        
        # Verify query was executed
        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()
        
        # Verify result structure
        assert len(stats) == 1
        assert stats[0]['error_type'] == 'test_error'
        assert stats[0]['count'] == 5
        assert stats[0]['last_occurrence'] == '2024-01-01'
    
    @patch('database.DATABASE_URL', 'postgresql://user:pass@localhost/testdb')
    @patch('database.create_engine')
    def test_cleanup_old_logs(self, mock_create_engine):
        """Test cleanup of old logs"""
        mock_engine = Mock()
        mock_create_engine.return_value = mock_engine
        
        db_manager = DatabaseManager()
        
        # Mock session
        mock_session = Mock()
        db_manager.session_factory = Mock()
        db_manager.session_factory.return_value = mock_session
        
        # Test cleanup
        db_manager.cleanup_old_logs(days=30)
        
        # Verify cleanup queries were executed
        assert mock_session.execute.call_count == 2  # One for commands, one for errors
        mock_session.commit.assert_called_once()
    
    @patch('database.DATABASE_URL', 'postgresql://user:pass@localhost/testdb')
    @patch('database.create_engine')
    def test_create_tables(self, mock_create_engine):
        """Test table creation"""
        mock_engine = Mock()
        mock_create_engine.return_value = mock_engine
        
        db_manager = DatabaseManager()
        
        # Mock metadata
        mock_metadata = Mock()
        with patch('database.MetaData') as mock_metadata_class:
            mock_metadata_class.return_value = mock_metadata
            
            db_manager.create_tables()
            
            # Verify tables were created
            mock_metadata.create_all.assert_called_once_with(mock_engine)
    
    @patch('database.DATABASE_URL', 'postgresql://user:pass@localhost/testdb')
    @patch('database.create_engine')
    def test_close(self, mock_create_engine):
        """Test database connection closure"""
        mock_engine = Mock()
        mock_create_engine.return_value = mock_engine
        
        db_manager = DatabaseManager()
        db_manager.close()
        
        # Verify engine was disposed
        mock_engine.dispose.assert_called_once()

if __name__ == '__main__':
    pytest.main([__file__]) 