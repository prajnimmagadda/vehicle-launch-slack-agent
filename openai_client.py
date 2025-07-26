import logging
import openai
from typing import Dict, List, Optional
from config import OPENAI_API_KEY, OPENAI_MODEL

logger = logging.getLogger(__name__)

class OpenAIClient:
    def __init__(self):
        """Initialize OpenAI client"""
        # TODO: Add your OpenAI API key
        openai.api_key = OPENAI_API_KEY
        self.model = OPENAI_MODEL
    
    def process_vehicle_program_query(self, launch_date: str, databricks_data: Dict) -> str:
        """
        Process vehicle program query using OpenAI
        
        Args:
            launch_date: Vehicle program launch date
            databricks_data: Data from Databricks queries
            
        Returns:
            Formatted response for Slack
        """
        try:
            # Create prompt for OpenAI
            prompt = self._create_analysis_prompt(launch_date, databricks_data)
            
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error processing OpenAI query: {e}")
            return f"Sorry, I encountered an error while analyzing the data: {str(e)}"
    
    def generate_file_upload_instructions(self, file_type: str) -> str:
        """
        Generate instructions for file upload based on file type
        
        Args:
            file_type: Type of file (excel, google_sheets, smartsheet)
            
        Returns:
            Instructions for file upload
        """
        try:
            prompt = f"Generate clear, step-by-step instructions for uploading a {file_type} file for vehicle program data analysis. Include format requirements and what data should be included."
            
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that provides clear instructions for file uploads."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.5
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error generating upload instructions: {e}")
            return f"Error generating instructions: {str(e)}"
    
    def analyze_uploaded_data(self, file_data: Dict, databricks_data: Dict) -> str:
        """
        Analyze uploaded file data combined with Databricks data
        
        Args:
            file_data: Data from uploaded file
            databricks_data: Data from Databricks
            
        Returns:
            Analysis results
        """
        try:
            prompt = self._create_combined_analysis_prompt(file_data, databricks_data)
            
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error analyzing uploaded data: {e}")
            return f"Error analyzing data: {str(e)}"
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for OpenAI"""
        return """
        You are an expert vehicle program launch analyst. Your role is to:
        1. Analyze vehicle program launch data from multiple departments
        2. Provide clear, actionable insights
        3. Identify risks and opportunities
        4. Suggest next steps for program success
        5. Communicate findings in a professional but accessible manner
        
        Focus on:
        - Bill of Material (BOM) status and completeness
        - Master Parts List (MPL) readiness
        - Material Flow Engineering (MFE) optimization
        - 4P (People, Process, Place, Product) alignment
        - PPAP (Production Part Approval Process) compliance
        
        Always provide specific recommendations and highlight critical issues that need immediate attention.
        """
    
    def _create_analysis_prompt(self, launch_date: str, databricks_data: Dict) -> str:
        """Create analysis prompt for OpenAI"""
        return f"""
        Analyze the vehicle program launch data for launch date: {launch_date}
        
        Department Status Summary:
        {self._format_department_data(databricks_data)}
        
        Please provide:
        1. Overall program health assessment
        2. Department-specific insights and recommendations
        3. Critical risks and mitigation strategies
        4. Next steps for program success
        5. Timeline recommendations for any delayed items
        
        Format your response in a clear, structured manner suitable for Slack communication.
        """
    
    def _create_combined_analysis_prompt(self, file_data: Dict, databricks_data: Dict) -> str:
        """Create combined analysis prompt for uploaded and Databricks data"""
        return f"""
        Analyze the combined vehicle program data from both uploaded files and Databricks:
        
        Uploaded File Data:
        {self._format_file_data(file_data)}
        
        Databricks Data:
        {self._format_department_data(databricks_data)}
        
        Please provide:
        1. Comprehensive analysis of all data sources
        2. Data consistency assessment
        3. Gap analysis between uploaded and Databricks data
        4. Recommendations for data reconciliation
        5. Overall program status and next steps
        """
    
    def _format_department_data(self, data: Dict) -> str:
        """Format department data for prompt"""
        formatted = ""
        for dept, dept_data in data.items():
            if dept_data.get('status') == 'success':
                summary = dept_data.get('summary', {})
                formatted += f"\n{dept.upper()}:\n"
                formatted += f"  - Total Items: {summary.get('total_items', 0)}\n"
                formatted += f"  - Completed: {summary.get('completed', 0)}\n"
                formatted += f"  - Pending: {summary.get('pending', 0)}\n"
                formatted += f"  - Overdue: {summary.get('overdue', 0)}\n"
            else:
                formatted += f"\n{dept.upper()}: Error - {dept_data.get('error', 'Unknown error')}\n"
        return formatted
    
    def _format_file_data(self, file_data: Dict) -> str:
        """Format uploaded file data for prompt"""
        # TODO: Implement based on your file parsing structure
        return str(file_data) 