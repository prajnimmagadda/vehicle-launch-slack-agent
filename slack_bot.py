import logging
import re
from datetime import datetime
from typing import Dict, Optional
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_bolt.context.say import Say
from slack_bolt.context.ack import Ack

from config import SLACK_BOT_TOKEN, SLACK_SIGNING_SECRET, SLACK_APP_TOKEN, DEBUG_MODE, LOG_LEVEL
from databricks_client import DatabricksClient
from openai_client import OpenAIClient
from file_parser import FileParser
from google_sheets_dashboard import GoogleSheetsDashboard

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class VehicleProgramSlackBot:
    def __init__(self):
        """Initialize the Slack bot with all necessary clients"""
        # Initialize Slack app
        self.app = App(
            token=SLACK_BOT_TOKEN,
            signing_secret=SLACK_SIGNING_SECRET
        )
        
        # Initialize clients
        self.databricks_client = DatabricksClient()
        self.openai_client = OpenAIClient()
        self.file_parser = FileParser()
        self.dashboard_creator = GoogleSheetsDashboard()
        
        # User session storage (in production, use a proper database)
        self.user_sessions = {}
        
        # Register event handlers
        self._register_handlers()
    
    def _register_handlers(self):
        """Register all Slack event handlers"""
        
        @self.app.message(re.compile(r"^/vehicle.*", re.IGNORECASE))
        def handle_vehicle_command(message, say: Say, ack: Ack):
            """Handle vehicle program queries"""
            ack()
            self._handle_vehicle_program_query(message, say)
        
        @self.app.message(re.compile(r"^/upload.*", re.IGNORECASE))
        def handle_upload_command(message, say: Say, ack: Ack):
            """Handle file upload requests"""
            ack()
            self._handle_upload_request(message, say)
        
        @self.app.message(re.compile(r"^/help.*", re.IGNORECASE))
        def handle_help_command(message, say: Say, ack: Ack):
            """Handle help requests"""
            ack()
            self._handle_help_request(message, say)
        
        @self.app.event("file_shared")
        def handle_file_upload(event, say: Say):
            """Handle file uploads"""
            self._handle_file_upload(event, say)
        
        @self.app.message(re.compile(r"^/dashboard.*", re.IGNORECASE))
        def handle_dashboard_command(message, say: Say, ack: Ack):
            """Handle dashboard creation requests"""
            ack()
            self._handle_dashboard_request(message, say)
    
    def _handle_vehicle_program_query(self, message, say: Say):
        """Handle vehicle program launch date queries"""
        try:
            user_id = message['user']
            text = message['text']
            
            # Extract launch date from message
            launch_date = self._extract_launch_date(text)
            
            if not launch_date:
                say(
                    text="Please provide a launch date in YYYY-MM-DD format.\n"
                         "Example: `/vehicle 2024-03-15`"
                )
                return
            
            # Send initial response
            say(text=f"🔍 Querying vehicle program status for launch date: {launch_date}\nPlease wait while I gather data from all departments...")
            
            # Query Databricks for all department statuses
            databricks_data = self.databricks_client.query_vehicle_program_status(launch_date)
            
            # Process with OpenAI
            analysis = self.openai_client.process_vehicle_program_query(launch_date, databricks_data)
            
            # Create visualization in Databricks
            visualization_url = self.databricks_client.create_visualization(databricks_data, launch_date)
            
            # Send comprehensive response
            response = f"""
🚗 *Vehicle Program Analysis for {launch_date}*

{analysis}

📊 *Databricks Visualization:* {visualization_url}

💡 *Next Steps:*
• Review the analysis above
• Check the Databricks visualization for detailed charts
• Use `/upload` to add additional data files if needed
• Use `/dashboard` to create a Google Sheets dashboard
            """
            
            say(text=response)
            
            # Store session data
            self.user_sessions[user_id] = {
                'launch_date': launch_date,
                'databricks_data': databricks_data,
                'last_query': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Error handling vehicle program query: {e}")
            say(text=f"❌ Error processing your request: {str(e)}")
    
    def _handle_upload_request(self, message, say: Say):
        """Handle file upload requests"""
        try:
            text = message['text']
            
            # Check if specific file type is mentioned
            if 'excel' in text.lower() or 'xlsx' in text.lower():
                instructions = self.openai_client.generate_file_upload_instructions('excel')
            elif 'google' in text.lower() or 'sheets' in text.lower():
                instructions = self.openai_client.generate_file_upload_instructions('google_sheets')
            elif 'smartsheet' in text.lower():
                instructions = self.openai_client.generate_file_upload_instructions('smartsheet')
            else:
                instructions = """
📁 *File Upload Instructions*

You can upload the following file types:
• **Excel files** (.xlsx, .xls)
• **Google Sheets** (share the spreadsheet ID)
• **Smartsheet** (provide the sheet ID)

*For Excel files:* Simply upload the file in this channel
*For Google Sheets:* Use `/upload google [spreadsheet-id]`
*For Smartsheet:* Use `/upload smartsheet [sheet-id]`

The file should contain vehicle program data with columns for:
• Part numbers/IDs
• Status information
• Completion percentages
• Department assignments
                """
            
            say(text=instructions)
            
        except Exception as e:
            logger.error(f"Error handling upload request: {e}")
            say(text=f"❌ Error generating upload instructions: {str(e)}")
    
    def _handle_file_upload(self, event, say: Say):
        """Handle actual file uploads"""
        try:
            file_info = event['file']
            user_id = event['user_id']
            
            # Check if user has an active session
            if user_id not in self.user_sessions:
                say(text="❌ Please first query a vehicle program using `/vehicle [launch-date]` before uploading files.")
                return
            
            session = self.user_sessions[user_id]
            
            # Validate file type
            filename = file_info['name']
            if not self.file_parser.validate_file_type(filename):
                say(text="❌ Unsupported file type. Please upload Excel files (.xlsx, .xls) only.")
                return
            
            say(text=f"📁 Processing uploaded file: {filename}\nPlease wait...")
            
            # Download and parse file
            # TODO: Implement actual file download from Slack
            # For now, this is a placeholder
            file_content = b""  # Placeholder - implement actual file download
            
            parsed_data = self.file_parser.parse_excel_file(file_content, filename)
            
            # Combine with existing Databricks data
            combined_analysis = self.openai_client.analyze_uploaded_data(
                parsed_data, 
                session['databricks_data']
            )
            
            # Update session
            session['file_data'] = parsed_data
            
            response = f"""
📊 *File Analysis Complete*

{combined_analysis}

💡 *Next Steps:*
• Use `/dashboard` to create a comprehensive Google Sheets dashboard
• The uploaded data has been combined with Databricks data for analysis
            """
            
            say(text=response)
            
        except Exception as e:
            logger.error(f"Error handling file upload: {e}")
            say(text=f"❌ Error processing uploaded file: {str(e)}")
    
    def _handle_dashboard_request(self, message, say: Say):
        """Handle dashboard creation requests"""
        try:
            user_id = message['user']
            
            # Check if user has an active session
            if user_id not in self.user_sessions:
                say(text="❌ Please first query a vehicle program using `/vehicle [launch-date]` before creating a dashboard.")
                return
            
            session = self.user_sessions[user_id]
            
            say(text="📊 Creating comprehensive dashboard...\nThis may take a few moments.")
            
            # Create dashboard
            dashboard_url = self.dashboard_creator.create_dashboard(
                databricks_data=session['databricks_data'],
                file_data=session.get('file_data'),
                launch_date=session['launch_date']
            )
            
            response = f"""
📊 *Dashboard Created Successfully!*

🔗 *Dashboard URL:* {dashboard_url}

The dashboard includes:
• Summary overview of all departments
• Individual department status sheets
• Uploaded file data (if any)
• Charts and visualizations
• Action items and recommendations

Share this dashboard with your team for collaborative review.
            """
            
            say(text=response)
            
        except Exception as e:
            logger.error(f"Error creating dashboard: {e}")
            say(text=f"❌ Error creating dashboard: {str(e)}")
    
    def _handle_help_request(self, message, say: Say):
        """Handle help requests"""
        help_text = """
🤖 *Vehicle Program Slack Bot - Help*

*Available Commands:*

🚗 `/vehicle [launch-date]` - Query vehicle program status
   Example: `/vehicle 2024-03-15`

📁 `/upload` - Get instructions for uploading data files
   Supports: Excel, Google Sheets, Smartsheet

📊 `/dashboard` - Create Google Sheets dashboard
   Combines Databricks data with uploaded files

❓ `/help` - Show this help message

*Workflow:*
1. Start with `/vehicle [launch-date]` to query Databricks
2. Optionally upload additional data files
3. Use `/dashboard` to create comprehensive reporting

*Data Sources:*
• Bill of Material (BOM)
• Master Parts List (MPL)
• Material Flow Engineering (MFE)
• 4P (People, Process, Place, Product)
• PPAP (Production Part Approval Process)
        """
        
        say(text=help_text)
    
    def _extract_launch_date(self, text: str) -> Optional[str]:
        """Extract launch date from message text"""
        # Look for date pattern YYYY-MM-DD
        date_pattern = r'\b(\d{4}-\d{2}-\d{2})\b'
        match = re.search(date_pattern, text)
        
        if match:
            return match.group(1)
        
        return None
    
    def start(self):
        """Start the Slack bot"""
        try:
            logger.info("Starting Vehicle Program Slack Bot...")
            
            # Start the app using Socket Mode
            handler = SocketModeHandler(self.app, SLACK_APP_TOKEN)
            handler.start()
            
        except Exception as e:
            logger.error(f"Error starting Slack bot: {e}")
            raise

def main():
    """Main function to start the bot"""
    try:
        bot = VehicleProgramSlackBot()
        bot.start()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Error in main: {e}")

if __name__ == "__main__":
    main() 