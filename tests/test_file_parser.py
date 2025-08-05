import pytest
import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import pandas as pd
import io

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from file_parser import FileParser

class TestFileParser:
    """Test FileParser class"""
    
    @patch('file_parser.GOOGLE_SHEETS_CREDENTIALS_FILE', None)
    def test_initialization_no_credentials(self):
        """Test FileParser initialization without Google credentials"""
        parser = FileParser()
        assert parser.google_creds is None
    
    @patch('file_parser.GOOGLE_SHEETS_CREDENTIALS_FILE', '/path/to/credentials.json')
    @patch('file_parser.GOOGLE_SHEETS_SCOPES', ['https://www.googleapis.com/auth/spreadsheets'])
    def test_initialization_with_credentials(self):
        """Test FileParser initialization with Google credentials"""
        with patch('file_parser.Credentials') as mock_credentials:
            mock_creds = Mock()
            mock_credentials.from_service_account_file.return_value = mock_creds
            
            parser = FileParser()
            
            assert parser.google_creds == mock_creds
            mock_credentials.from_service_account_file.assert_called_once()
    
    @patch('file_parser.GOOGLE_SHEETS_CREDENTIALS_FILE', '/path/to/credentials.json')
    def test_initialization_credentials_error(self):
        """Test FileParser initialization with credentials error"""
        with patch('file_parser.Credentials') as mock_credentials:
            mock_credentials.from_service_account_file.side_effect = Exception("File not found")
            
            # Should not raise exception, just log error
            parser = FileParser()
            assert parser.google_creds is None
    
    def test_validate_file_type_valid(self):
        """Test file type validation with valid files"""
        parser = FileParser()
        
        valid_files = [
            "data.xlsx",
            "report.xls", 
            "data.csv",
            "DATA.XLSX",
            "file.xls"
        ]
        
        for filename in valid_files:
            assert parser.validate_file_type(filename) is True
    
    def test_validate_file_type_invalid(self):
        """Test file type validation with invalid files"""
        parser = FileParser()
        
        invalid_files = [
            "data.txt",
            "report.pdf",
            "data.doc",
            "file.docx",
            "data.json"
        ]
        
        for filename in invalid_files:
            assert parser.validate_file_type(filename) is False
    
    @patch('file_parser.pd.read_excel')
    def test_parse_excel_file_success(self, mock_read_excel):
        """Test successful Excel file parsing"""
        parser = FileParser()
        
        # Mock Excel data
        mock_data = {
            'Sheet1': pd.DataFrame({
                'part_number': ['P001', 'P002'],
                'status': ['complete', 'pending'],
                'completion': [100, 75]
            }),
            'Sheet2': pd.DataFrame({
                'part_id': ['ID001', 'ID002'],
                'description': ['Part A', 'Part B']
            })
        }
        mock_read_excel.return_value = mock_data
        
        # Mock file content
        file_content = b"fake excel content"
        filename = "test_data.xlsx"
        
        # Mock the sheet parsing methods
        with patch.object(parser, '_parse_excel_sheet') as mock_parse_sheet:
            with patch.object(parser, '_generate_summary') as mock_summary:
                mock_parse_sheet.return_value = {'status': 'parsed'}
                mock_summary.return_value = {'total_sheets': 2}
                
                result = parser.parse_excel_file(file_content, filename)
                
                # Verify structure
                assert result['file_type'] == 'excel'
                assert result['filename'] == filename
                assert 'sheets' in result
                assert 'summary' in result
                
                # Verify Excel was read
                mock_read_excel.assert_called_once()
                
                # Verify parsing was called for each sheet
                assert mock_parse_sheet.call_count == 2
    
    @patch('file_parser.pd.read_excel')
    def test_parse_excel_file_error(self, mock_read_excel):
        """Test Excel file parsing with error"""
        parser = FileParser()
        
        mock_read_excel.side_effect = Exception("Invalid Excel file")
        
        file_content = b"invalid content"
        filename = "invalid.xlsx"
        
        with pytest.raises(Exception, match="Invalid Excel file"):
            parser.parse_excel_file(file_content, filename)
    
    @patch('file_parser.gspread.authorize')
    def test_parse_google_sheets_success(self, mock_authorize):
        """Test successful Google Sheets parsing"""
        parser = FileParser()
        parser.google_creds = Mock()
        
        # Mock gspread objects
        mock_gc = Mock()
        mock_authorize.return_value = mock_gc
        
        mock_spreadsheet = Mock()
        mock_gc.open_by_key.return_value = mock_spreadsheet
        
        mock_worksheet1 = Mock()
        mock_worksheet1.title = "Sheet1"
        mock_worksheet1.get_all_records.return_value = [
            {'part_number': 'P001', 'status': 'complete'},
            {'part_number': 'P002', 'status': 'pending'}
        ]
        
        mock_worksheet2 = Mock()
        mock_worksheet2.title = "Sheet2"
        mock_worksheet2.get_all_records.return_value = [
            {'part_id': 'ID001', 'description': 'Part A'}
        ]
        
        mock_spreadsheet.worksheets.return_value = [mock_worksheet1, mock_worksheet2]
        
        # Mock the sheet parsing methods
        with patch.object(parser, '_parse_google_sheet') as mock_parse_sheet:
            with patch.object(parser, '_generate_summary') as mock_summary:
                mock_parse_sheet.return_value = {'status': 'parsed'}
                mock_summary.return_value = {'total_sheets': 2}
                
                result = parser.parse_google_sheets("test_spreadsheet_id")
                
                # Verify structure
                assert result['file_type'] == 'google_sheets'
                assert result['spreadsheet_id'] == "test_spreadsheet_id"
                assert 'sheets' in result
                assert 'summary' in result
                
                # Verify gspread was called
                mock_authorize.assert_called_once_with(parser.google_creds)
                mock_gc.open_by_key.assert_called_once_with("test_spreadsheet_id")
                
                # Verify parsing was called for each worksheet
                assert mock_parse_sheet.call_count == 2
    
    def test_parse_google_sheets_no_credentials(self):
        """Test Google Sheets parsing without credentials"""
        parser = FileParser()
        parser.google_creds = None
        
        with pytest.raises(Exception, match="Google credentials not configured"):
            parser.parse_google_sheets("test_spreadsheet_id")
    
    @patch('file_parser.requests.get')
    def test_parse_smartsheet_success(self, mock_get):
        """Test successful Smartsheet parsing"""
        parser = FileParser()
        
        # Mock requests response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'sheets': [
                {
                    'id': 123,
                    'name': 'Sheet1',
                    'columns': [
                        {'id': 1, 'title': 'part_number'},
                        {'id': 2, 'title': 'status'}
                    ],
                    'rows': [
                        {'cells': [{'columnId': 1, 'value': 'P001'}, {'columnId': 2, 'value': 'complete'}]},
                        {'cells': [{'columnId': 1, 'value': 'P002'}, {'columnId': 2, 'value': 'pending'}]}
                    ]
                }
            ]
        }
        mock_get.return_value = mock_response
        
        # Mock the data parsing method
        with patch.object(parser, '_parse_smartsheet_data') as mock_parse_data:
            with patch.object(parser, '_generate_summary') as mock_summary:
                mock_parse_data.return_value = {'status': 'parsed'}
                mock_summary.return_value = {'total_sheets': 1}
                
                result = parser.parse_smartsheet("test_sheet_id")
                
                # Verify structure
                assert result['file_type'] == 'smartsheet'
                assert result['sheet_id'] == "test_sheet_id"
                assert 'sheets' in result
                assert 'summary' in result
                
                # Verify API call
                mock_get.assert_called_once()
                call_args = mock_get.call_args
                assert 'test_sheet_id' in call_args[0][0]
    
    @patch('file_parser.requests.get')
    def test_parse_smartsheet_error(self, mock_get):
        """Test Smartsheet parsing with error"""
        parser = FileParser()
        
        # Mock failed request
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        with pytest.raises(Exception, match="Failed to fetch Smartsheet data"):
            parser.parse_smartsheet("invalid_sheet_id")
    
    def test_parse_excel_sheet(self):
        """Test Excel sheet parsing"""
        parser = FileParser()
        
        # Create test DataFrame
        df = pd.DataFrame({
            'part_number': ['P001', 'P002', 'P003'],
            'part_name': ['Part A', 'Part B', 'Part C'],
            'status': ['complete', 'in_progress', 'pending'],
            'completion_percentage': [100, 75, 25]
        })
        
        result = parser._parse_excel_sheet(df, "BOM")
        
        # Verify structure
        assert 'data' in result
        assert 'summary' in result
        assert 'department_mapping' in result
        assert result['data'].shape[0] == 3
        assert 'part_number' in result['data'].columns
    
    def test_parse_google_sheet(self):
        """Test Google Sheet parsing"""
        parser = FileParser()
        
        # Create test DataFrame
        df = pd.DataFrame({
            'part_id': ['ID001', 'ID002'],
            'description': ['Part A', 'Part B'],
            'supplier': ['Supplier A', 'Supplier B']
        })
        
        result = parser._parse_google_sheet(df, "MPL")
        
        # Verify structure
        assert 'data' in result
        assert 'summary' in result
        assert 'department_mapping' in result
        assert result['data'].shape[0] == 2
        assert 'part_id' in result['data'].columns
    
    def test_parse_smartsheet_data(self):
        """Test Smartsheet data parsing"""
        parser = FileParser()
        
        # Mock Smartsheet data structure
        sheet_data = {
            'id': 123,
            'name': 'Test Sheet',
            'columns': [
                {'id': 1, 'title': 'part_number'},
                {'id': 2, 'title': 'status'}
            ],
            'rows': [
                {'cells': [{'columnId': 1, 'value': 'P001'}, {'columnId': 2, 'value': 'complete'}]},
                {'cells': [{'columnId': 1, 'value': 'P002'}, {'columnId': 2, 'value': 'pending'}]}
            ]
        }
        
        result = parser._parse_smartsheet_data(sheet_data)
        
        # Verify structure
        assert 'data' in result
        assert 'summary' in result
        assert 'department_mapping' in result
        assert len(result['data']) == 2
    
    def test_generate_summary(self):
        """Test summary generation"""
        parser = FileParser()
        
        # Mock sheets data
        sheets_data = {
            'BOM': {'data': pd.DataFrame({'status': ['complete', 'pending']}), 'summary': {'count': 2}},
            'MPL': {'data': pd.DataFrame({'status': ['in_progress']}), 'summary': {'count': 1}}
        }
        
        result = parser._generate_summary(sheets_data)
        
        # Verify summary structure
        assert 'total_sheets' in result
        assert 'total_records' in result
        assert 'departments' in result
        assert result['total_sheets'] == 2
        assert result['total_records'] == 3

if __name__ == '__main__':
    pytest.main([__file__]) 