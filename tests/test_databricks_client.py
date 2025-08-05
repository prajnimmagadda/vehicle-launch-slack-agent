import pytest
import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import pandas as pd

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from databricks_client import DatabricksClient

class TestDatabricksClient:
    """Test DatabricksClient class"""
    
    @patch('databricks_client.WorkspaceClient')
    @patch('databricks_client.DATABRICKS_HOST', 'https://test.databricks.com')
    @patch('databricks_client.DATABRICKS_TOKEN', 'test_token')
    def test_initialization(self, mock_workspace_client):
        """Test Databricks client initialization"""
        mock_client = Mock()
        mock_workspace_client.return_value = mock_client
        
        client = DatabricksClient()
        
        assert client.client == mock_client
        mock_workspace_client.assert_called_once_with(
            host='https://test.databricks.com',
            token='test_token'
        )
    
    @patch('databricks_client.WorkspaceClient')
    @patch('databricks_client.DATABRICKS_HOST', 'https://test.databricks.com')
    @patch('databricks_client.DATABRICKS_TOKEN', 'test_token')
    def test_query_vehicle_program_status_success(self, mock_workspace_client):
        """Test successful vehicle program status query"""
        mock_client = Mock()
        mock_workspace_client.return_value = mock_client
        
        client = DatabricksClient()
        
        # Mock the individual query methods
        with patch.object(client, '_query_bom_status') as mock_bom:
            with patch.object(client, '_query_mpl_status') as mock_mpl:
                with patch.object(client, '_query_mfe_status') as mock_mfe:
                    with patch.object(client, '_query_4p_status') as mock_4p:
                        with patch.object(client, '_query_ppap_status') as mock_ppap:
                            
                            mock_bom.return_value = {'status': 'complete', 'count': 10}
                            mock_mpl.return_value = {'status': 'in_progress', 'count': 5}
                            mock_mfe.return_value = {'status': 'pending', 'count': 3}
                            mock_4p.return_value = {'status': 'complete', 'count': 8}
                            mock_ppap.return_value = {'status': 'not_started', 'count': 0}
                            
                            result = client.query_vehicle_program_status('2024-03-15')
                            
                            # Verify all queries were called
                            mock_bom.assert_called_once_with('2024-03-15')
                            mock_mpl.assert_called_once_with('2024-03-15')
                            mock_mfe.assert_called_once_with('2024-03-15')
                            mock_4p.assert_called_once_with('2024-03-15')
                            mock_ppap.assert_called_once_with('2024-03-15')
                            
                            # Verify result structure
                            assert 'bill_of_material' in result
                            assert 'master_parts_list' in result
                            assert 'material_flow_engineering' in result
                            assert '4p' in result
                            assert 'ppap' in result
    
    @patch('databricks_client.WorkspaceClient')
    @patch('databricks_client.DATABRICKS_HOST', 'https://test.databricks.com')
    @patch('databricks_client.DATABRICKS_TOKEN', 'test_token')
    def test_query_vehicle_program_status_exception(self, mock_workspace_client):
        """Test vehicle program status query with exception"""
        mock_client = Mock()
        mock_workspace_client.return_value = mock_client
        
        client = DatabricksClient()
        
        # Mock an exception in one of the query methods
        with patch.object(client, '_query_bom_status', side_effect=Exception("Database error")):
            with pytest.raises(Exception, match="Database error"):
                client.query_vehicle_program_status('2024-03-15')
    
    @patch('databricks_client.WorkspaceClient')
    @patch('databricks_client.DATABRICKS_HOST', 'https://test.databricks.com')
    @patch('databricks_client.DATABRICKS_TOKEN', 'test_token')
    @patch('databricks_client.DATABRICKS_CATALOG', 'test_catalog')
    @patch('databricks_client.DATABRICKS_SCHEMA', 'test_schema')
    @patch('databricks_client.DATABRICKS_TABLES', {'bill_of_material': 'bom_table'})
    def test_query_bom_status(self, mock_workspace_client):
        """Test BOM status query"""
        mock_client = Mock()
        mock_workspace_client.return_value = mock_client
        
        client = DatabricksClient()
        
        # Mock the execute query method
        with patch.object(client, '_execute_query') as mock_execute:
            mock_execute.return_value = {'status': 'complete', 'count': 10}
            
            result = client._query_bom_status('2024-03-15')
            
            # Verify the query was executed
            mock_execute.assert_called_once()
            call_args = mock_execute.call_args
            assert 'bom_table' in call_args[0][0]  # Check SQL contains table name
            assert '2024-03-15' in call_args[0][0]  # Check SQL contains date
            assert call_args[0][1] == 'BOM'  # Check department parameter
    
    @patch('databricks_client.WorkspaceClient')
    @patch('databricks_client.DATABRICKS_HOST', 'https://test.databricks.com')
    @patch('databricks_client.DATABRICKS_TOKEN', 'test_token')
    @patch('databricks_client.DATABRICKS_CATALOG', 'test_catalog')
    @patch('databricks_client.DATABRICKS_SCHEMA', 'test_schema')
    @patch('databricks_client.DATABRICKS_TABLES', {'master_parts_list': 'mpl_table'})
    def test_query_mpl_status(self, mock_workspace_client):
        """Test Master Parts List status query"""
        mock_client = Mock()
        mock_workspace_client.return_value = mock_client
        
        client = DatabricksClient()
        
        with patch.object(client, '_execute_query') as mock_execute:
            mock_execute.return_value = {'status': 'in_progress', 'count': 5}
            
            result = client._query_mpl_status('2024-03-15')
            
            mock_execute.assert_called_once()
            call_args = mock_execute.call_args
            assert 'mpl_table' in call_args[0][0]
            assert call_args[0][1] == 'MPL'
    
    @patch('databricks_client.WorkspaceClient')
    @patch('databricks_client.DATABRICKS_HOST', 'https://test.databricks.com')
    @patch('databricks_client.DATABRICKS_TOKEN', 'test_token')
    def test_execute_query_success(self, mock_workspace_client):
        """Test successful query execution"""
        mock_client = Mock()
        mock_workspace_client.return_value = mock_client
        
        # Mock the SQL execution
        mock_sql_execution = Mock()
        mock_sql_execution.status = Mock()
        mock_sql_execution.status.__eq__ = lambda self, other: other == 'FINISHED'
        mock_sql_execution.result = Mock()
        mock_sql_execution.result.data_array = [
            ['part1', 'Part A', 'complete', 100, '2024-01-01'],
            ['part2', 'Part B', 'in_progress', 75, '2024-01-02']
        ]
        mock_sql_execution.result.schema = Mock()
        mock_sql_execution.result.schema.columns = [
            Mock(name='part_number'),
            Mock(name='part_name'),
            Mock(name='status'),
            Mock(name='completion_percentage'),
            Mock(name='last_updated')
        ]
        
        mock_client.sql.execute_statement.return_value = mock_sql_execution
        
        client = DatabricksClient()
        
        result = client._execute_query("SELECT * FROM test_table", "TEST")
        
        # Verify the query was executed
        mock_client.sql.execute_statement.assert_called_once()
        
        # Verify result structure
        assert 'status' in result
        assert 'data' in result
        assert 'count' in result
        assert result['count'] == 2
    
    @patch('databricks_client.WorkspaceClient')
    @patch('databricks_client.DATABRICKS_HOST', 'https://test.databricks.com')
    @patch('databricks_client.DATABRICKS_TOKEN', 'test_token')
    def test_execute_query_failure(self, mock_workspace_client):
        """Test query execution with failure"""
        mock_client = Mock()
        mock_workspace_client.return_value = mock_client
        
        # Mock a failed query
        mock_client.sql.execute_statement.side_effect = Exception("Query failed")
        
        client = DatabricksClient()
        
        with pytest.raises(Exception, match="Query failed"):
            client._execute_query("SELECT * FROM test_table", "TEST")
    
    @patch('databricks_client.WorkspaceClient')
    @patch('databricks_client.DATABRICKS_HOST', 'https://test.databricks.com')
    @patch('databricks_client.DATABRICKS_TOKEN', 'test_token')
    def test_create_visualization(self, mock_workspace_client):
        """Test visualization creation"""
        mock_client = Mock()
        mock_workspace_client.return_value = mock_client
        
        client = DatabricksClient()
        
        # Mock data for visualization
        test_data = {
            'bill_of_material': {'status': 'complete', 'count': 10},
            'master_parts_list': {'status': 'in_progress', 'count': 5},
            'material_flow_engineering': {'status': 'pending', 'count': 3}
        }
        
        # Mock the visualization creation
        with patch('databricks_client.plotly.graph_objects') as mock_plotly:
            mock_fig = Mock()
            mock_plotly.Figure.return_value = mock_fig
            
            result = client.create_visualization(test_data, '2024-03-15')
            
            # Verify visualization was created
            assert 'visualization_url' in result
            assert '2024-03-15' in result['visualization_url']

if __name__ == '__main__':
    pytest.main([__file__]) 