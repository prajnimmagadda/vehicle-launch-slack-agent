import logging
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import requests
from typing import Dict, List, Optional
import io
from config import GOOGLE_SHEETS_CREDENTIALS_FILE, GOOGLE_SHEETS_SCOPES, SMARTSHEET_API_TOKEN, ALLOWED_FILE_TYPES

logger = logging.getLogger(__name__)

class FileParser:
    def __init__(self):
        """Initialize file parser with necessary credentials"""
        # TODO: Add your Google Sheets service account credentials file path
        self.google_creds = None
        if GOOGLE_SHEETS_CREDENTIALS_FILE:
            try:
                self.google_creds = Credentials.from_service_account_file(
                    GOOGLE_SHEETS_CREDENTIALS_FILE, 
                    scopes=GOOGLE_SHEETS_SCOPES
                )
            except Exception as e:
                logger.error(f"Error loading Google credentials: {e}")
    
    def parse_excel_file(self, file_content: bytes, filename: str) -> Dict:
        """
        Parse Excel file content
        
        Args:
            file_content: Raw file content
            filename: Name of the uploaded file
            
        Returns:
            Parsed data dictionary
        """
        try:
            # Read Excel file
            excel_data = pd.read_excel(io.BytesIO(file_content), sheet_name=None)
            
            parsed_data = {
                'file_type': 'excel',
                'filename': filename,
                'sheets': {},
                'summary': {}
            }
            
            for sheet_name, df in excel_data.items():
                # TODO: Update column mapping based on your Excel template structure
                sheet_data = self._parse_excel_sheet(df, sheet_name)
                parsed_data['sheets'][sheet_name] = sheet_data
            
            # Generate summary
            parsed_data['summary'] = self._generate_summary(parsed_data['sheets'])
            
            return parsed_data
            
        except Exception as e:
            logger.error(f"Error parsing Excel file: {e}")
            raise
    
    def parse_google_sheets(self, spreadsheet_id: str) -> Dict:
        """
        Parse Google Sheets data
        
        Args:
            spreadsheet_id: Google Sheets spreadsheet ID
            
        Returns:
            Parsed data dictionary
        """
        try:
            if not self.google_creds:
                raise Exception("Google credentials not configured")
            
            gc = gspread.authorize(self.google_creds)
            spreadsheet = gc.open_by_key(spreadsheet_id)
            
            parsed_data = {
                'file_type': 'google_sheets',
                'spreadsheet_id': spreadsheet_id,
                'sheets': {},
                'summary': {}
            }
            
            for worksheet in spreadsheet.worksheets():
                # Get all values from worksheet
                data = worksheet.get_all_records()
                df = pd.DataFrame(data)
                
                # TODO: Update column mapping based on your Google Sheets template structure
                sheet_data = self._parse_google_sheet(df, worksheet.title)
                parsed_data['sheets'][worksheet.title] = sheet_data
            
            # Generate summary
            parsed_data['summary'] = self._generate_summary(parsed_data['sheets'])
            
            return parsed_data
            
        except Exception as e:
            logger.error(f"Error parsing Google Sheets: {e}")
            raise
    
    def parse_smartsheet(self, sheet_id: str) -> Dict:
        """
        Parse Smartsheet data
        
        Args:
            sheet_id: Smartsheet sheet ID
            
        Returns:
            Parsed data dictionary
        """
        try:
            # TODO: Add your Smartsheet API token
            headers = {
                'Authorization': f'Bearer {SMARTSHEET_API_TOKEN}',
                'Content-Type': 'application/json'
            }
            
            # Get sheet details
            sheet_url = f"https://api.smartsheet.com/2.0/sheets/{sheet_id}"
            response = requests.get(sheet_url, headers=headers)
            response.raise_for_status()
            
            sheet_data = response.json()
            
            parsed_data = {
                'file_type': 'smartsheet',
                'sheet_id': sheet_id,
                'data': {},
                'summary': {}
            }
            
            # TODO: Update parsing logic based on your Smartsheet structure
            parsed_data['data'] = self._parse_smartsheet_data(sheet_data)
            parsed_data['summary'] = self._generate_summary({'main': parsed_data['data']})
            
            return parsed_data
            
        except Exception as e:
            logger.error(f"Error parsing Smartsheet: {e}")
            raise
    
    def _parse_excel_sheet(self, df: pd.DataFrame, sheet_name: str) -> Dict:
        """Parse individual Excel sheet"""
        # TODO: Update this mapping based on your Excel template structure
        # This is a placeholder - customize based on your actual Excel format
        
        sheet_data = {
            'sheet_name': sheet_name,
            'total_rows': len(df),
            'columns': list(df.columns),
            'data': df.to_dict('records'),
            'department_mapping': {}
        }
        
        # Map columns to departments based on your template
        # Example mapping - update based on your actual structure
        if 'BOM' in sheet_name.upper():
            sheet_data['department_mapping'] = {
                'part_number': 'part_number',
                'part_name': 'part_name',
                'status': 'status',
                'completion': 'completion_percentage'
            }
        elif 'MPL' in sheet_name.upper():
            sheet_data['department_mapping'] = {
                'part_id': 'part_id',
                'description': 'part_description',
                'status': 'status',
                'supplier': 'supplier_info'
            }
        # Add more department mappings as needed
        
        return sheet_data
    
    def _parse_google_sheet(self, df: pd.DataFrame, sheet_name: str) -> Dict:
        """Parse individual Google Sheets worksheet"""
        # Similar to Excel parsing but for Google Sheets format
        # TODO: Update based on your Google Sheets template structure
        
        sheet_data = {
            'sheet_name': sheet_name,
            'total_rows': len(df),
            'columns': list(df.columns),
            'data': df.to_dict('records'),
            'department_mapping': {}
        }
        
        # Map columns to departments - same logic as Excel
        if 'BOM' in sheet_name.upper():
            sheet_data['department_mapping'] = {
                'part_number': 'part_number',
                'part_name': 'part_name',
                'status': 'status',
                'completion': 'completion_percentage'
            }
        elif 'MPL' in sheet_name.upper():
            sheet_data['department_mapping'] = {
                'part_id': 'part_id',
                'description': 'part_description',
                'status': 'status',
                'supplier': 'supplier_info'
            }
        
        return sheet_data
    
    def _parse_smartsheet_data(self, sheet_data: Dict) -> Dict:
        """Parse Smartsheet data structure"""
        # TODO: Update based on your Smartsheet structure
        # This is a placeholder - customize based on your actual Smartsheet format
        
        parsed = {
            'sheet_name': sheet_data.get('name', 'Unknown'),
            'total_rows': len(sheet_data.get('rows', [])),
            'columns': [col.get('title', '') for col in sheet_data.get('columns', [])],
            'data': [],
            'department_mapping': {}
        }
        
        # Parse rows
        for row in sheet_data.get('rows', []):
            row_data = {}
            for cell in row.get('cells', []):
                column_id = cell.get('columnId')
                value = cell.get('value', '')
                row_data[f'col_{column_id}'] = value
            parsed['data'].append(row_data)
        
        return parsed
    
    def _generate_summary(self, sheets_data: Dict) -> Dict:
        """Generate summary statistics from parsed data"""
        summary = {
            'total_sheets': len(sheets_data),
            'total_records': 0,
            'departments_found': [],
            'status_counts': {},
            'completion_percentages': []
        }
        
        for sheet_name, sheet_data in sheets_data.items():
            summary['total_records'] += sheet_data.get('total_rows', 0)
            
            # Extract department info from sheet name
            if 'BOM' in sheet_name.upper():
                summary['departments_found'].append('BOM')
            elif 'MPL' in sheet_name.upper():
                summary['departments_found'].append('MPL')
            elif 'MFE' in sheet_name.upper():
                summary['departments_found'].append('MFE')
            elif '4P' in sheet_name.upper():
                summary['departments_found'].append('4P')
            elif 'PPAP' in sheet_name.upper():
                summary['departments_found'].append('PPAP')
        
        return summary
    
    def validate_file_type(self, filename: str) -> bool:
        """Validate if file type is supported"""
        return any(filename.lower().endswith(ext) for ext in ALLOWED_FILE_TYPES) 