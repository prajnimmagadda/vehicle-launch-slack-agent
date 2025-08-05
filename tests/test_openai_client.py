import pytest
import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from openai_client import OpenAIClient

class TestOpenAIClient:
    """Test OpenAIClient class"""
    
    @patch('openai_client.openai.OpenAI')
    @patch('openai_client.OPENAI_API_KEY', 'test_api_key')
    def test_initialization(self, mock_openai):
        """Test OpenAI client initialization"""
        mock_client = Mock()
        mock_openai.return_value = mock_client
        
        client = OpenAIClient()
        
        assert client.client == mock_client
        mock_openai.assert_called_once_with(api_key='test_api_key')
    
    @patch('openai_client.openai.OpenAI')
    @patch('openai_client.OPENAI_API_KEY', 'test_api_key')
    def test_analyze_program_status_success(self, mock_openai):
        """Test successful program status analysis"""
        mock_client = Mock()
        mock_openai.return_value = mock_client
        
        # Mock the chat completion response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Analysis: Program is on track with 75% completion"
        mock_client.chat.completions.create.return_value = mock_response
        
        client = OpenAIClient()
        
        # Mock program data
        program_data = {
            'bill_of_material': {'status': 'complete', 'count': 10},
            'master_parts_list': {'status': 'in_progress', 'count': 5},
            'material_flow_engineering': {'status': 'pending', 'count': 3}
        }
        
        result = client.analyze_program_status(program_data, '2024-03-15')
        
        # Verify OpenAI was called
        mock_client.chat.completions.create.assert_called_once()
        
        # Verify the response
        assert "Analysis:" in result
        assert "Program is on track" in result
    
    @patch('openai_client.openai.OpenAI')
    @patch('openai_client.OPENAI_API_KEY', 'test_api_key')
    def test_analyze_program_status_exception(self, mock_openai):
        """Test program status analysis with exception"""
        mock_client = Mock()
        mock_openai.return_value = mock_client
        
        # Mock an exception
        mock_client.chat.completions.create.side_effect = Exception("API error")
        
        client = OpenAIClient()
        
        program_data = {'test': {'status': 'complete'}}
        
        with pytest.raises(Exception, match="API error"):
            client.analyze_program_status(program_data, '2024-03-15')
    
    @patch('openai_client.openai.OpenAI')
    @patch('openai_client.OPENAI_API_KEY', 'test_api_key')
    def test_generate_recommendations_success(self, mock_openai):
        """Test successful recommendation generation"""
        mock_client = Mock()
        mock_openai.return_value = mock_client
        
        # Mock the chat completion response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Recommendations:\n1. Accelerate MPL completion\n2. Review MFE bottlenecks"
        mock_client.chat.completions.create.return_value = mock_response
        
        client = OpenAIClient()
        
        # Mock analysis data
        analysis_data = {
            'status': 'in_progress',
            'completion_percentage': 65,
            'bottlenecks': ['MPL', 'MFE']
        }
        
        result = client.generate_recommendations(analysis_data)
        
        # Verify OpenAI was called
        mock_client.chat.completions.create.assert_called_once()
        
        # Verify the response
        assert "Recommendations:" in result
        assert "Accelerate" in result
    
    @patch('openai_client.openai.OpenAI')
    @patch('openai_client.OPENAI_API_KEY', 'test_api_key')
    def test_analyze_file_data_success(self, mock_openai):
        """Test successful file data analysis"""
        mock_client = Mock()
        mock_openai.return_value = mock_client
        
        # Mock the chat completion response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "File Analysis:\n- 3 sheets processed\n- 15 total records\n- Data quality: Good"
        mock_client.chat.completions.create.return_value = mock_response
        
        client = OpenAIClient()
        
        # Mock file data
        file_data = {
            'file_type': 'excel',
            'filename': 'test_data.xlsx',
            'sheets': {
                'BOM': {'data': 'mock_data', 'summary': {'count': 10}},
                'MPL': {'data': 'mock_data', 'summary': {'count': 5}}
            }
        }
        
        result = client.analyze_file_data(file_data)
        
        # Verify OpenAI was called
        mock_client.chat.completions.create.assert_called_once()
        
        # Verify the response
        assert "File Analysis:" in result
        assert "sheets processed" in result
    
    @patch('openai_client.openai.OpenAI')
    @patch('openai_client.OPENAI_API_KEY', 'test_api_key')
    def test_get_system_prompt(self, mock_openai):
        """Test system prompt generation"""
        mock_client = Mock()
        mock_openai.return_value = mock_client
        
        client = OpenAIClient()
        
        prompt = client._get_system_prompt()
        
        # Verify prompt contains expected content
        assert "vehicle program" in prompt.lower()
        assert "analysis" in prompt.lower()
        assert "recommendations" in prompt.lower()
    
    @patch('openai_client.openai.OpenAI')
    @patch('openai_client.OPENAI_API_KEY', 'test_api_key')
    def test_create_analysis_prompt(self, mock_openai):
        """Test analysis prompt creation"""
        mock_client = Mock()
        mock_openai.return_value = mock_client
        
        client = OpenAIClient()
        
        program_data = {
            'bill_of_material': {'status': 'complete', 'count': 10},
            'master_parts_list': {'status': 'in_progress', 'count': 5}
        }
        
        prompt = client._create_analysis_prompt(program_data, '2024-03-15')
        
        # Verify prompt structure
        assert "2024-03-15" in prompt
        assert "bill_of_material" in prompt
        assert "master_parts_list" in prompt
        assert "complete" in prompt
        assert "in_progress" in prompt
    
    @patch('openai_client.openai.OpenAI')
    @patch('openai_client.OPENAI_API_KEY', 'test_api_key')
    def test_create_recommendation_prompt(self, mock_openai):
        """Test recommendation prompt creation"""
        mock_client = Mock()
        mock_openai.return_value = mock_client
        
        client = OpenAIClient()
        
        analysis_data = {
            'status': 'at_risk',
            'completion_percentage': 45,
            'bottlenecks': ['MPL', 'MFE'],
            'critical_path': ['BOM', 'MPL', 'PPAP']
        }
        
        prompt = client._create_recommendation_prompt(analysis_data)
        
        # Verify prompt structure
        assert "at_risk" in prompt
        assert "45" in prompt
        assert "MPL" in prompt
        assert "MFE" in prompt
        assert "critical_path" in prompt
    
    @patch('openai_client.openai.OpenAI')
    @patch('openai_client.OPENAI_API_KEY', 'test_api_key')
    def test_create_file_analysis_prompt(self, mock_openai):
        """Test file analysis prompt creation"""
        mock_client = Mock()
        mock_openai.return_value = mock_client
        
        client = OpenAIClient()
        
        file_data = {
            'file_type': 'excel',
            'filename': 'vehicle_data.xlsx',
            'sheets': {
                'BOM': {'summary': {'count': 10, 'status_distribution': {'complete': 8, 'pending': 2}}},
                'MPL': {'summary': {'count': 5, 'status_distribution': {'in_progress': 3, 'pending': 2}}}
            }
        }
        
        prompt = client._create_file_analysis_prompt(file_data)
        
        # Verify prompt structure
        assert "vehicle_data.xlsx" in prompt
        assert "excel" in prompt
        assert "BOM" in prompt
        assert "MPL" in prompt
        assert "10" in prompt
        assert "5" in prompt
    
    @patch('openai_client.openai.OpenAI')
    @patch('openai_client.OPENAI_API_KEY', 'test_api_key')
    def test_call_openai_api_success(self, mock_openai):
        """Test successful OpenAI API call"""
        mock_client = Mock()
        mock_openai.return_value = mock_client
        
        # Mock the chat completion response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Test response"
        mock_client.chat.completions.create.return_value = mock_response
        
        client = OpenAIClient()
        
        messages = [
            {"role": "system", "content": "You are a helpful assistant"},
            {"role": "user", "content": "Analyze this data"}
        ]
        
        result = client._call_openai_api(messages)
        
        # Verify API call
        mock_client.chat.completions.create.assert_called_once()
        call_args = mock_client.chat.completions.create.call_args
        
        # Verify parameters
        assert call_args[1]['model'] == 'gpt-3.5-turbo'
        assert call_args[1]['messages'] == messages
        assert call_args[1]['max_tokens'] == 1000
        assert call_args[1]['temperature'] == 0.7
        
        # Verify response
        assert result == "Test response"
    
    @patch('openai_client.openai.OpenAI')
    @patch('openai_client.OPENAI_API_KEY', 'test_api_key')
    def test_call_openai_api_exception(self, mock_openai):
        """Test OpenAI API call with exception"""
        mock_client = Mock()
        mock_openai.return_value = mock_client
        
        # Mock an exception
        mock_client.chat.completions.create.side_effect = Exception("API error")
        
        client = OpenAIClient()
        
        messages = [{"role": "user", "content": "Test"}]
        
        with pytest.raises(Exception, match="API error"):
            client._call_openai_api(messages)
    
    @patch('openai_client.openai.OpenAI')
    @patch('openai_client.OPENAI_API_KEY', 'test_api_key')
    def test_validate_response(self, mock_openai):
        """Test response validation"""
        mock_client = Mock()
        mock_openai.return_value = mock_client
        
        client = OpenAIClient()
        
        # Test valid response
        valid_response = "This is a valid analysis response"
        result = client._validate_response(valid_response)
        assert result == valid_response
        
        # Test empty response
        empty_response = ""
        with pytest.raises(ValueError, match="Empty response from OpenAI"):
            client._validate_response(empty_response)
        
        # Test None response
        with pytest.raises(ValueError, match="Empty response from OpenAI"):
            client._validate_response(None)

if __name__ == '__main__':
    pytest.main([__file__]) 