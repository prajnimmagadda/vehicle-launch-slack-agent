import openai
import logging
from typing import Dict, Optional
from config import OPENAI_API_KEY, OPENAI_MODEL

logger = logging.getLogger(__name__)


class OpenAIClient:
    """OpenAI client for processing vehicle program queries"""

    def __init__(self):
        """Initialize OpenAI client"""
        self.api_key = OPENAI_API_KEY or "test-key"
        self.model = OPENAI_MODEL
        # Only create client if API key is available
        if self.api_key and self.api_key != "test-key":
            self.client = openai.OpenAI(api_key=self.api_key)
        else:
            self.client = None

    def process_vehicle_program_query(self, launch_date: str, databricks_data: Dict) -> str:
        """
        Process vehicle program query using OpenAI
        Args:
            launch_date: Vehicle launch date
            databricks_data: Data from Databricks
        Returns:
            Analysis response from OpenAI
        """
        try:
            if not self.client:
                return "OpenAI client not configured. Please check your API key."
            
            prompt = self._create_analysis_prompt(launch_date, databricks_data)
            response = self.client.chat.completions.create(
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

    def analyze_program_status(self, program_data: Dict, launch_date: str) -> str:
        """
        Analyze program status using OpenAI
        Args:
            program_data: Program data from all departments
            launch_date: Vehicle launch date
        Returns:
            Analysis response from OpenAI
        """
        try:
            prompt = self._create_analysis_prompt(launch_date, program_data)
            response = self._call_openai_api([
                {"role": "system", "content": self._get_system_prompt()},
                {"role": "user", "content": prompt}
            ])
            return self._validate_response(response)
        except Exception as e:
            logger.error(f"Error analyzing program status: {e}")
            return f"Sorry, I encountered an error while analyzing the program status: {str(e)}"

    def generate_recommendations(self, analysis_data: Dict) -> str:
        """
        Generate recommendations based on analysis data
        Args:
            analysis_data: Analysis data with status and issues
        Returns:
            Recommendations from OpenAI
        """
        try:
            prompt = self._create_recommendation_prompt(analysis_data)
            response = self._call_openai_api([
                {"role": "system", "content": self._get_system_prompt()},
                {"role": "user", "content": prompt}
            ])
            return self._validate_response(response)
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return f"Sorry, I encountered an error while generating recommendations: {str(e)}"

    def analyze_file_data(self, file_data: Dict) -> str:
        """
        Analyze uploaded file data
        Args:
            file_data: Data from uploaded files
        Returns:
            Analysis of file data
        """
        try:
            prompt = self._create_file_analysis_prompt(file_data)
            response = self._call_openai_api([
                {"role": "system", "content": self._get_system_prompt()},
                {"role": "user", "content": prompt}
            ])
            return self._validate_response(response)
        except Exception as e:
            logger.error(f"Error analyzing file data: {e}")
            return f"Sorry, I encountered an error while analyzing the file data: {str(e)}"

    def generate_file_upload_instructions(self, missing_data: Dict) -> str:
        """
        Generate instructions for file upload based on missing data
        Args:
            missing_data: Dictionary of missing data categories
        Returns:
            Instructions for file upload
        """
        try:
            prompt = self._create_upload_prompt(missing_data)
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error generating upload instructions: {e}")
            return f"Sorry, I encountered an error while generating upload instructions: {str(e)}"

    def analyze_uploaded_data(self, databricks_data: Dict, file_data: Dict) -> str:
        """
        Analyze combined data from Databricks and uploaded files
        Args:
            databricks_data: Data from Databricks
            file_data: Data from uploaded files
        Returns:
            Analysis of combined data
        """
        try:
            prompt = self._create_combined_analysis_prompt(databricks_data, file_data)
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1200,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error analyzing combined data: {e}")
            return f"Sorry, I encountered an error while analyzing the combined data: {str(e)}"

    def _get_system_prompt(self) -> str:
        """Get system prompt for OpenAI"""
        return """You are an AI assistant specialized in vehicle program launch analysis. 
        You help analyze data from various departments including Bill of Materials, Master Parts List, 
        Material Flow Engineering, 4P, and PPAP. Provide clear, actionable insights and recommendations."""

    def _create_analysis_prompt(self, launch_date: str, databricks_data: Dict) -> str:
        """Create analysis prompt for vehicle program data"""
        return f"""Analyze the vehicle program launch data for {launch_date}.
        
        Databricks Data:
        {databricks_data}
        
        Please provide:
        1. Overall status summary
        2. Key issues and risks
        3. Recommendations for improvement
        4. Next steps for launch readiness"""

    def _create_recommendation_prompt(self, analysis_data: Dict) -> str:
        """Create prompt for generating recommendations"""
        return f"""Based on the analysis data, provide specific recommendations:
        
        Analysis Data: {analysis_data}
        
        Please provide:
        1. Priority actions to take
        2. Resource allocation recommendations
        3. Timeline adjustments if needed
        4. Risk mitigation strategies
        5. Success metrics to track"""

    def _create_file_analysis_prompt(self, file_data: Dict) -> str:
        """Create prompt for file data analysis"""
        return f"""Analyze the uploaded file data:
        
        File Data: {file_data}
        
        Please provide:
        1. Data quality assessment
        2. Completeness analysis
        3. Key insights from the data
        4. Data validation results
        5. Integration recommendations"""

    def _create_upload_prompt(self, missing_data: Dict) -> str:
        """Create prompt for file upload instructions"""
        return f"""Based on the missing data categories, provide clear instructions for file upload:
        
        Missing Data: {missing_data}
        
        Please provide:
        1. What file formats are accepted
        2. Required data structure
        3. How to upload files
        4. What information will be extracted"""

    def _create_combined_analysis_prompt(self, databricks_data: Dict, file_data: Dict) -> str:
        """Create prompt for combined data analysis"""
        return f"""Analyze the combined data from Databricks and uploaded files:
        
        Databricks Data: {databricks_data}
        File Data: {file_data}
        
        Please provide:
        1. Comprehensive status overview
        2. Data completeness assessment
        3. Identified gaps and issues
        4. Actionable recommendations
        5. Launch readiness score"""

    def _call_openai_api(self, messages: list) -> str:
        """Call OpenAI API with given messages"""
        if not self.client:
            return "OpenAI client not configured. Please check your API key."
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=1000,
            temperature=0.7
        )
        return response.choices[0].message.content

    def _validate_response(self, response: str) -> str:
        """Validate OpenAI response"""
        if not response or response.strip() == "":
            raise ValueError("Empty response from OpenAI")
        return response 