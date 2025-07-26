import logging
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from typing import Dict, List, Optional
import pandas as pd
from config import GOOGLE_SHEETS_CREDENTIALS_FILE, GOOGLE_SHEETS_SCOPES, DASHBOARD_TEMPLATE_ID

logger = logging.getLogger(__name__)

class GoogleSheetsDashboard:
    def __init__(self):
        """Initialize Google Sheets dashboard creator"""
        # TODO: Add your Google Sheets service account credentials file path
        self.creds = None
        self.service = None
        
        if GOOGLE_SHEETS_CREDENTIALS_FILE:
            try:
                self.creds = Credentials.from_service_account_file(
                    GOOGLE_SHEETS_CREDENTIALS_FILE, 
                    scopes=GOOGLE_SHEETS_SCOPES
                )
                self.service = build('sheets', 'v4', credentials=self.creds)
            except Exception as e:
                logger.error(f"Error loading Google credentials: {e}")
    
    def create_dashboard(self, databricks_data: Dict, file_data: Optional[Dict] = None, launch_date: str = None) -> str:
        """
        Create a comprehensive dashboard in Google Sheets
        
        Args:
            databricks_data: Data from Databricks queries
            file_data: Optional data from uploaded files
            launch_date: Vehicle program launch date
            
        Returns:
            URL of the created dashboard
        """
        try:
            if not self.creds:
                raise Exception("Google credentials not configured")
            
            # Create new spreadsheet
            gc = gspread.authorize(self.creds)
            
            # TODO: Add your dashboard template ID if you have one
            if DASHBOARD_TEMPLATE_ID:
                # Copy from template
                template = gc.open_by_key(DASHBOARD_TEMPLATE_ID)
                dashboard = template.copy(title=f"Vehicle Program Dashboard - {launch_date}")
            else:
                # Create new spreadsheet
                dashboard = gc.create(f"Vehicle Program Dashboard - {launch_date}")
            
            # Create dashboard sheets
            self._create_summary_sheet(dashboard, databricks_data, file_data, launch_date)
            self._create_department_sheets(dashboard, databricks_data)
            self._create_file_data_sheets(dashboard, file_data)
            self._create_charts_and_visualizations(dashboard, databricks_data, file_data)
            
            # Make the spreadsheet accessible
            dashboard.share('', perm_type='anyone', role='reader')
            
            return dashboard.url
            
        except Exception as e:
            logger.error(f"Error creating dashboard: {e}")
            raise
    
    def _create_summary_sheet(self, dashboard, databricks_data: Dict, file_data: Optional[Dict], launch_date: str):
        """Create summary sheet with overview"""
        try:
            summary_sheet = dashboard.worksheet('Summary') if 'Summary' in [ws.title for ws in dashboard.worksheets()] else dashboard.add_worksheet(title='Summary', rows=50, cols=20)
            
            # Create summary data
            summary_data = [
                ['Vehicle Program Launch Dashboard'],
                [''],
                ['Launch Date:', launch_date],
                ['Generated:', pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')],
                [''],
                ['Department Status Summary'],
                ['Department', 'Total Items', 'Completed', 'Pending', 'Overdue', 'Completion %']
            ]
            
            # Add Databricks data
            for dept, dept_data in databricks_data.items():
                if dept_data.get('status') == 'success':
                    summary = dept_data.get('summary', {})
                    total = summary.get('total_items', 0)
                    completed = summary.get('completed', 0)
                    pending = summary.get('pending', 0)
                    overdue = summary.get('overdue', 0)
                    completion_pct = (completed / total * 100) if total > 0 else 0
                    
                    summary_data.append([
                        dept.upper(),
                        total,
                        completed,
                        pending,
                        overdue,
                        f"{completion_pct:.1f}%"
                    ])
            
            # Add file data summary if available
            if file_data:
                summary_data.extend([
                    [''],
                    ['File Upload Summary'],
                    ['File Type', 'Total Records', 'Departments Found']
                ])
                
                summary_data.append([
                    file_data.get('file_type', 'Unknown'),
                    file_data.get('summary', {}).get('total_records', 0),
                    ', '.join(file_data.get('summary', {}).get('departments_found', []))
                ])
            
            # Update the sheet
            summary_sheet.clear()
            summary_sheet.update('A1', summary_data)
            
            # Format the sheet
            self._format_summary_sheet(summary_sheet)
            
        except Exception as e:
            logger.error(f"Error creating summary sheet: {e}")
            raise
    
    def _create_department_sheets(self, dashboard, databricks_data: Dict):
        """Create individual sheets for each department"""
        try:
            for dept, dept_data in databricks_data.items():
                if dept_data.get('status') == 'success':
                    # Create or get department sheet
                    sheet_name = f"{dept.upper()}_Status"
                    dept_sheet = dashboard.worksheet(sheet_name) if sheet_name in [ws.title for ws in dashboard.worksheets()] else dashboard.add_worksheet(title=sheet_name, rows=100, cols=20)
                    
                    # TODO: Update this based on your actual data structure
                    # This is a placeholder - customize based on your department data format
                    dept_data_rows = dept_data.get('data', [])
                    
                    if dept_data_rows:
                        # Convert to DataFrame for easier handling
                        df = pd.DataFrame(dept_data_rows)
                        
                        # Create headers
                        headers = list(df.columns) if not df.empty else ['No Data Available']
                        sheet_data = [headers]
                        
                        # Add data rows
                        for _, row in df.iterrows():
                            sheet_data.append(row.tolist())
                        
                        # Update sheet
                        dept_sheet.clear()
                        dept_sheet.update('A1', sheet_data)
                        
                        # Format department sheet
                        self._format_department_sheet(dept_sheet, dept)
                    
        except Exception as e:
            logger.error(f"Error creating department sheets: {e}")
            raise
    
    def _create_file_data_sheets(self, dashboard, file_data: Optional[Dict]):
        """Create sheets for uploaded file data"""
        if not file_data:
            return
        
        try:
            if file_data.get('file_type') == 'excel':
                for sheet_name, sheet_data in file_data.get('sheets', {}).items():
                    # Create sheet for each Excel worksheet
                    upload_sheet = dashboard.add_worksheet(title=f"Upload_{sheet_name}", rows=100, cols=20)
                    
                    # Add data
                    if sheet_data.get('data'):
                        df = pd.DataFrame(sheet_data['data'])
                        headers = list(df.columns)
                        sheet_data_rows = [headers]
                        
                        for _, row in df.iterrows():
                            sheet_data_rows.append(row.tolist())
                        
                        upload_sheet.update('A1', sheet_data_rows)
            
            elif file_data.get('file_type') == 'google_sheets':
                for sheet_name, sheet_data in file_data.get('sheets', {}).items():
                    # Create sheet for each Google Sheets worksheet
                    upload_sheet = dashboard.add_worksheet(title=f"Upload_{sheet_name}", rows=100, cols=20)
                    
                    # Add data
                    if sheet_data.get('data'):
                        df = pd.DataFrame(sheet_data['data'])
                        headers = list(df.columns)
                        sheet_data_rows = [headers]
                        
                        for _, row in df.iterrows():
                            sheet_data_rows.append(row.tolist())
                        
                        upload_sheet.update('A1', sheet_data_rows)
            
            elif file_data.get('file_type') == 'smartsheet':
                # Create sheet for Smartsheet data
                upload_sheet = dashboard.add_worksheet(title="Upload_Smartsheet", rows=100, cols=20)
                
                smartsheet_data = file_data.get('data', {})
                if smartsheet_data.get('data'):
                    df = pd.DataFrame(smartsheet_data['data'])
                    headers = list(df.columns)
                    sheet_data_rows = [headers]
                    
                    for _, row in df.iterrows():
                        sheet_data_rows.append(row.tolist())
                    
                    upload_sheet.update('A1', sheet_data_rows)
                    
        except Exception as e:
            logger.error(f"Error creating file data sheets: {e}")
            raise
    
    def _create_charts_and_visualizations(self, dashboard, databricks_data: Dict, file_data: Optional[Dict]):
        """Create charts and visualizations in the dashboard"""
        try:
            # TODO: Implement chart creation using Google Sheets API
            # This would involve creating charts based on the data
            # For now, this is a placeholder
            
            logger.info("Chart creation functionality to be implemented")
            
            # Example chart creation (placeholder)
            # chart_request = {
            #     'addChart': {
            #         'chart': {
            #             'spec': {
            #                 'title': 'Department Completion Status',
            #                 'basicChart': {
            #                     'chartType': 'COLUMN',
            #                     'domains': [{'dataRange': {'sourceRange': {'sources': [{'sheetId': sheet_id, 'startRowIndex': 0, 'endRowIndex': 10, 'startColumnIndex': 0, 'endColumnIndex': 2}]}}}],
            #                     'series': [{'dataRange': {'sourceRange': {'sources': [{'sheetId': sheet_id, 'startRowIndex': 0, 'endRowIndex': 10, 'startColumnIndex': 2, 'endColumnIndex': 3}]}}}]
            #                 }
            #             }
            #         }
            #     }
            # }
            
        except Exception as e:
            logger.error(f"Error creating charts: {e}")
            raise
    
    def _format_summary_sheet(self, sheet):
        """Format the summary sheet with styling"""
        try:
            # TODO: Implement Google Sheets formatting
            # This would involve setting colors, fonts, borders, etc.
            logger.info("Summary sheet formatting to be implemented")
            
        except Exception as e:
            logger.error(f"Error formatting summary sheet: {e}")
            raise
    
    def _format_department_sheet(self, sheet, department: str):
        """Format department sheet with styling"""
        try:
            # TODO: Implement Google Sheets formatting for department sheets
            logger.info(f"Department sheet formatting for {department} to be implemented")
            
        except Exception as e:
            logger.error(f"Error formatting department sheet: {e}")
            raise
    
    def update_dashboard(self, dashboard_url: str, new_data: Dict):
        """Update existing dashboard with new data"""
        try:
            # TODO: Implement dashboard update functionality
            # This would involve updating existing sheets with new data
            logger.info("Dashboard update functionality to be implemented")
            
        except Exception as e:
            logger.error(f"Error updating dashboard: {e}")
            raise 