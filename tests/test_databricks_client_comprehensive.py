import pytest
import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from databricks_client import DatabricksClient

class TestDatabricksClientComprehensive:
    """Comprehensive tests for DatabricksClient"""
    
    def setup_method(self):
        """Setup test method"""
        self.mock_workspace = Mock()
        self.mock_statement = Mock()
        self.mock_result = Mock()
        
    @patch('databricks_client.DatabricksConnect')
    def test_initialization_success(self, mock_databricks_connect):
        """Test successful client initialization"""
        mock_databricks_connect.return_value = self.mock_workspace
        
        client = DatabricksClient()
        
        assert client.workspace is not None
        mock_databricks_connect.assert_called_once()
    
    @patch('databricks_client.DatabricksConnect')
    def test_initialization_failure(self, mock_databricks_connect):
        """Test client initialization failure"""
        mock_databricks_connect.side_effect = Exception("Connection failed")
        
        with pytest.raises(Exception):
            DatabricksClient()
    
    @patch('databricks_client.DatabricksConnect')
    def test_execute_query_success(self, mock_databricks_connect):
        """Test successful query execution"""
        mock_databricks_connect.return_value = self.mock_workspace
        
        # Mock statement execution
        self.mock_workspace.statement.execute.return_value = self.mock_statement
        self.mock_statement.result.return_value = self.mock_result
        self.mock_result.data = [{'column1': 'value1', 'column2': 'value2'}]
        
        client = DatabricksClient()
        result = client.execute_query("SELECT * FROM test_table")
        
        assert result['status'] == 'success'
        assert 'data' in result
        assert len(result['data']) > 0
        self.mock_workspace.statement.execute.assert_called_once()
    
    @patch('databricks_client.DatabricksConnect')
    def test_execute_query_failure(self, mock_databricks_connect):
        """Test query execution failure"""
        mock_databricks_connect.return_value = self.mock_workspace
        
        # Mock statement execution failure
        self.mock_workspace.statement.execute.side_effect = Exception("Query failed")
        
        client = DatabricksClient()
        
        with pytest.raises(Exception):
            client.execute_query("SELECT * FROM test_table")
    
    @patch('databricks_client.DatabricksConnect')
    def test_execute_query_empty_result(self, mock_databricks_connect):
        """Test query execution with empty result"""
        mock_databricks_connect.return_value = self.mock_workspace
        
        # Mock empty result
        self.mock_workspace.statement.execute.return_value = self.mock_statement
        self.mock_statement.result.return_value = self.mock_result
        self.mock_result.data = []
        
        client = DatabricksClient()
        result = client.execute_query("SELECT * FROM empty_table")
        
        assert result['status'] == 'success'
        assert 'data' in result
        assert len(result['data']) == 0
    
    @patch('databricks_client.DatabricksConnect')
    def test_get_bill_of_materials(self, mock_databricks_connect):
        """Test getting bill of materials"""
        mock_databricks_connect.return_value = self.mock_workspace
        
        # Mock query execution
        self.mock_workspace.statement.execute.return_value = self.mock_statement
        self.mock_statement.result.return_value = self.mock_result
        self.mock_result.data = [
            {'part_number': 'P001', 'description': 'Part 1', 'status': 'complete'},
            {'part_number': 'P002', 'description': 'Part 2', 'status': 'pending'}
        ]
        
        client = DatabricksClient()
        result = client.get_bill_of_materials()
        
        assert result['status'] == 'success'
        assert 'data' in result
        assert len(result['data']) == 2
        assert result['data'][0]['part_number'] == 'P001'
    
    @patch('databricks_client.DatabricksConnect')
    def test_get_master_parts_list(self, mock_databricks_connect):
        """Test getting master parts list"""
        mock_databricks_connect.return_value = self.mock_workspace
        
        # Mock query execution
        self.mock_workspace.statement.execute.return_value = self.mock_statement
        self.mock_statement.result.return_value = self.mock_result
        self.mock_result.data = [
            {'part_id': 'MP001', 'description': 'Master Part 1'},
            {'part_id': 'MP002', 'description': 'Master Part 2'}
        ]
        
        client = DatabricksClient()
        result = client.get_master_parts_list()
        
        assert result['status'] == 'success'
        assert 'data' in result
        assert len(result['data']) == 2
        assert result['data'][0]['part_id'] == 'MP001'
    
    @patch('databricks_client.DatabricksConnect')
    def test_get_material_flow_engineering(self, mock_databricks_connect):
        """Test getting material flow engineering data"""
        mock_databricks_connect.return_value = self.mock_workspace
        
        # Mock query execution
        self.mock_workspace.statement.execute.return_value = self.mock_statement
        self.mock_statement.result.return_value = self.mock_result
        self.mock_result.data = [
            {'flow_id': 'MF001', 'status': 'active'},
            {'flow_id': 'MF002', 'status': 'inactive'}
        ]
        
        client = DatabricksClient()
        result = client.get_material_flow_engineering()
        
        assert result['status'] == 'success'
        assert 'data' in result
        assert len(result['data']) == 2
        assert result['data'][0]['flow_id'] == 'MF001'
    
    @patch('databricks_client.DatabricksConnect')
    def test_get_4p_data(self, mock_databricks_connect):
        """Test getting 4P data"""
        mock_databricks_connect.return_value = self.mock_workspace
        
        # Mock query execution
        self.mock_workspace.statement.execute.return_value = self.mock_statement
        self.mock_statement.result.return_value = self.mock_result
        self.mock_result.data = [
            {'4p_id': '4P001', 'category': 'Production'},
            {'4p_id': '4P002', 'category': 'Planning'}
        ]
        
        client = DatabricksClient()
        result = client.get_4p_data()
        
        assert result['status'] == 'success'
        assert 'data' in result
        assert len(result['data']) == 2
        assert result['data'][0]['4p_id'] == '4P001'
    
    @patch('databricks_client.DatabricksConnect')
    def test_get_ppap_data(self, mock_databricks_connect):
        """Test getting PPAP data"""
        mock_databricks_connect.return_value = self.mock_workspace
        
        # Mock query execution
        self.mock_workspace.statement.execute.return_value = self.mock_statement
        self.mock_statement.result.return_value = self.mock_result
        self.mock_result.data = [
            {'ppap_id': 'PPAP001', 'status': 'approved'},
            {'ppap_id': 'PPAP002', 'status': 'pending'}
        ]
        
        client = DatabricksClient()
        result = client.get_ppap_data()
        
        assert result['status'] == 'success'
        assert 'data' in result
        assert len(result['data']) == 2
        assert result['data'][0]['ppap_id'] == 'PPAP001'
    
    @patch('databricks_client.DatabricksConnect')
    def test_get_all_department_data(self, mock_databricks_connect):
        """Test getting all department data"""
        mock_databricks_connect.return_value = self.mock_workspace
        
        # Mock query execution for all departments
        self.mock_workspace.statement.execute.return_value = self.mock_statement
        self.mock_statement.result.return_value = self.mock_result
        self.mock_result.data = [{'test': 'data'}]
        
        client = DatabricksClient()
        result = client.get_all_department_data()
        
        assert result['status'] == 'success'
        assert 'bill_of_material' in result
        assert 'master_parts_list' in result
        assert 'material_flow_engineering' in result
        assert '4p' in result
        assert 'ppap' in result
        
        # Verify all departments were queried
        assert self.mock_workspace.statement.execute.call_count == 5
    
    @patch('databricks_client.DatabricksConnect')
    def test_get_all_department_data_partial_failure(self, mock_databricks_connect):
        """Test getting all department data with partial failures"""
        mock_databricks_connect.return_value = self.mock_workspace
        
        # Mock some successful and some failed queries
        def mock_execute(query):
            if 'bill_of_material' in query:
                self.mock_result.data = [{'bom': 'data'}]
                return self.mock_statement
            else:
                raise Exception("Query failed")
        
        self.mock_workspace.statement.execute.side_effect = mock_execute
        self.mock_statement.result.return_value = self.mock_result
        
        client = DatabricksClient()
        result = client.get_all_department_data()
        
        assert result['status'] == 'partial_success'
        assert 'bill_of_material' in result
        assert result['bill_of_material']['status'] == 'success'
    
    @patch('databricks_client.DatabricksConnect')
    def test_create_visualization_success(self, mock_databricks_connect):
        """Test successful visualization creation"""
        mock_databricks_connect.return_value = self.mock_workspace
        
        # Mock plotly
        with patch('databricks_client.plotly') as mock_plotly:
            mock_fig = Mock()
            mock_plotly.graph_objects.Figure.return_value = mock_fig
            
            client = DatabricksClient()
            data = [{'x': 1, 'y': 2}, {'x': 2, 'y': 4}]
            result = client.create_visualization(data, 'test_chart')
            
            assert result['status'] == 'success'
            assert 'chart_html' in result
            mock_fig.add_trace.assert_called()
    
    @patch('databricks_client.DatabricksConnect')
    def test_create_visualization_failure(self, mock_databricks_connect):
        """Test visualization creation failure"""
        mock_databricks_connect.return_value = self.mock_workspace
        
        # Mock plotly to raise exception
        with patch('databricks_client.plotly') as mock_plotly:
            mock_plotly.graph_objects.Figure.side_effect = Exception("Plotly error")
            
            client = DatabricksClient()
            data = [{'x': 1, 'y': 2}]
            
            with pytest.raises(Exception):
                client.create_visualization(data, 'test_chart')
    
    @patch('databricks_client.DatabricksConnect')
    def test_health_check_success(self, mock_databricks_connect):
        """Test successful health check"""
        mock_databricks_connect.return_value = self.mock_workspace
        
        # Mock successful connection
        self.mock_workspace.statement.execute.return_value = self.mock_statement
        self.mock_statement.result.return_value = self.mock_result
        self.mock_result.data = [{'test': 'data'}]
        
        client = DatabricksClient()
        health = client.health_check()
        
        assert health['status'] == 'healthy'
        assert 'message' in health
    
    @patch('databricks_client.DatabricksConnect')
    def test_health_check_failure(self, mock_databricks_connect):
        """Test health check failure"""
        mock_databricks_connect.return_value = self.mock_workspace
        
        # Mock connection failure
        self.mock_workspace.statement.execute.side_effect = Exception("Connection failed")
        
        client = DatabricksClient()
        health = client.health_check()
        
        assert health['status'] == 'unhealthy'
        assert 'error' in health['message']
    
    @patch('databricks_client.DatabricksConnect')
    def test_close_connection(self, mock_databricks_connect):
        """Test closing connection"""
        mock_databricks_connect.return_value = self.mock_workspace
        
        client = DatabricksClient()
        client.close()
        
        # Verify connection was closed
        self.mock_workspace.close.assert_called_once()
    
    @patch('databricks_client.DatabricksConnect')
    def test_comprehensive_workflow(self, mock_databricks_connect):
        """Test comprehensive workflow"""
        mock_databricks_connect.return_value = self.mock_workspace
        
        # Mock all operations
        self.mock_workspace.statement.execute.return_value = self.mock_statement
        self.mock_statement.result.return_value = self.mock_result
        self.mock_result.data = [{'test': 'data'}]
        
        client = DatabricksClient()
        
        # Test health check
        health = client.health_check()
        assert health['status'] == 'healthy'
        
        # Test getting all department data
        all_data = client.get_all_department_data()
        assert all_data['status'] == 'success'
        
        # Test creating visualization
        with patch('databricks_client.plotly') as mock_plotly:
            mock_fig = Mock()
            mock_plotly.graph_objects.Figure.return_value = mock_fig
            
            viz_result = client.create_visualization([{'x': 1, 'y': 2}], 'test')
            assert viz_result['status'] == 'success'
        
        # Test closing connection
        client.close()
        self.mock_workspace.close.assert_called_once()
    
    @patch('databricks_client.DatabricksConnect')
    def test_error_handling_comprehensive(self, mock_databricks_connect):
        """Test comprehensive error handling"""
        mock_databricks_connect.return_value = self.mock_workspace
        
        # Test various error scenarios
        client = DatabricksClient()
        
        # Test query with invalid SQL
        self.mock_workspace.statement.execute.side_effect = Exception("Invalid SQL")
        
        with pytest.raises(Exception):
            client.execute_query("INVALID SQL")
        
        # Test connection timeout
        self.mock_workspace.statement.execute.side_effect = Exception("Connection timeout")
        
        with pytest.raises(Exception):
            client.execute_query("SELECT * FROM test")
        
        # Test authentication failure
        self.mock_workspace.statement.execute.side_effect = Exception("Authentication failed")
        
        with pytest.raises(Exception):
            client.execute_query("SELECT * FROM test")
    
    @patch('databricks_client.DatabricksConnect')
    def test_data_validation(self, mock_databricks_connect):
        """Test data validation"""
        mock_databricks_connect.return_value = self.mock_workspace
        
        # Mock query execution
        self.mock_workspace.statement.execute.return_value = self.mock_statement
        self.mock_statement.result.return_value = self.mock_result
        
        client = DatabricksClient()
        
        # Test with null data
        self.mock_result.data = None
        result = client.execute_query("SELECT * FROM test")
        assert result['status'] == 'success'
        assert result['data'] == []
        
        # Test with empty data
        self.mock_result.data = []
        result = client.execute_query("SELECT * FROM test")
        assert result['status'] == 'success'
        assert result['data'] == []
        
        # Test with large dataset
        self.mock_result.data = [{'id': i} for i in range(1000)]
        result = client.execute_query("SELECT * FROM test")
        assert result['status'] == 'success'
        assert len(result['data']) == 1000

if __name__ == '__main__':
    pytest.main([__file__]) 