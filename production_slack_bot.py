import logging
import logging.config
import re
import time
import threading
from datetime import datetime
from typing import Dict, Optional
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_bolt.context.say import Say
from slack_bolt.context.ack import Ack

from production_config import ProductionConfig
from databricks_client import DatabricksClient
from openai_client import OpenAIClient
from file_parser import FileParser
from google_sheets_dashboard import GoogleSheetsDashboard
from database import db_manager
from monitoring import monitoring_manager, monitor_command, monitor_error

# Configure logging
logging.config.dictConfig(ProductionConfig.get_logging_config())
logger = logging.getLogger(__name__)

class ProductionSlackBot:
    """Production-ready Slack bot with monitoring and error handling"""
    
    def __init__(self):
        """Initialize the production Slack bot"""
        # Validate configuration
        config_validation = ProductionConfig.validate_config()
        if not config_validation['valid']:
            logger.error(f"Configuration validation failed: {config_validation['errors']}")
            raise ValueError("Invalid configuration")
        
        if config_validation['warnings']:
            logger.warning(f"Configuration warnings: {config_validation['warnings']}")
        
        # Initialize Slack app
        self.app = App(
            token=ProductionConfig.SLACK_BOT_TOKEN,
            signing_secret=ProductionConfig.SLACK_SIGNING_SECRET
        )
        
        # Initialize clients with production settings
        self.databricks_client = DatabricksClient()
        self.openai_client = OpenAIClient()
        self.file_parser = FileParser()
        self.dashboard_creator = GoogleSheetsDashboard()
        
        # Initialize monitoring
        monitoring_manager.start_metrics_server()
        
        # Register event handlers
        self._register_handlers()
        
        logger.info("Production Slack bot initialized successfully")
    
    def _register_handlers(self):
        """Register all Slack event handlers with monitoring"""
        
        @self.app.message(re.compile(r"^/vehicle.*", re.IGNORECASE))
        @monitor_command("vehicle_query")
        def handle_vehicle_command(message, say: Say, ack: Ack):
            """Handle vehicle program queries with monitoring"""
            ack()
            self._handle_vehicle_program_query(message, say)
        
        @self.app.message(re.compile(r"^/upload.*", re.IGNORECASE))
        @monitor_command("upload_request")
        def handle_upload_command(message, say: Say, ack: Ack):
            """Handle file upload requests with monitoring"""
            ack()
            self._handle_upload_request(message, say)
        
        @self.app.message(re.compile(r"^/help.*", re.IGNORECASE))
        @monitor_command("help_request")
        def handle_help_command(message, say: Say, ack: Ack):
            """Handle help requests with monitoring"""
            ack()
            self._handle_help_request(message, say)
        
        @self.app.event("file_shared")
        @monitor_command("file_upload")
        def handle_file_upload(event, say: Say):
            """Handle file uploads with monitoring"""
            self._handle_file_upload(event, say)
        
        @self.app.message(re.compile(r"^/dashboard.*", re.IGNORECASE))
        @monitor_command("dashboard_request")
        def handle_dashboard_command(message, say: Say, ack: Ack):
            """Handle dashboard creation requests with monitoring"""
            ack()
            self._handle_dashboard_request(message, say)
        
        @self.app.message(re.compile(r"^/status.*", re.IGNORECASE))
        @monitor_command("status_request")
        def handle_status_command(message, say: Say, ack: Ack):
            """Handle status requests with monitoring"""
            ack()
            self._handle_status_request(message, say)
    
    @monitor_error("vehicle_program_query")
    def _handle_vehicle_program_query(self, message, say: Say):
        """Handle vehicle program launch date queries with enhanced error handling"""
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
            
            # Store session data
            db_manager.store_user_session(user_id, launch_date, databricks_data)
            
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
            
        except Exception as e:
            logger.error(f"Error handling vehicle program query: {e}")
            monitoring_manager.track_error('vehicle_program_query', str(e), user_id=message.get('user'))
            say(text=f"❌ Error processing your request. Please try again or contact support if the issue persists.")
    
    @monitor_error("upload_request")
    def _handle_upload_request(self, message, say: Say):
        """Handle file upload requests with enhanced error handling"""
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
            monitoring_manager.track_error('upload_request', str(e), user_id=message.get('user'))
            say(text=f"❌ Error generating upload instructions. Please try again.")
    
    @monitor_error("file_upload")
    def _handle_file_upload(self, event, say: Say):
        """Handle actual file uploads with enhanced error handling"""
        try:
            file_info = event['file']
            user_id = event['user_id']
            
            # Check if user has an active session
            session_data = db_manager.get_user_session(user_id)
            if not session_data:
                say(text="❌ Please first query a vehicle program using `/vehicle [launch-date]` before uploading files.")
                return
            
            # Validate file type
            filename = file_info['name']
            if not self.file_parser.validate_file_type(filename):
                say(text="❌ Unsupported file type. Please upload Excel files (.xlsx, .xls) only.")
                return
            
            # Validate file size
            if file_info.get('size', 0) > ProductionConfig.MAX_FILE_SIZE:
                say(text=f"❌ File too large. Maximum size is {ProductionConfig.MAX_FILE_SIZE / 1024 / 1024:.1f}MB.")
                return
            
            say(text=f"📁 Processing uploaded file: {filename}\nPlease wait...")
            
            # Download and parse file
            # TODO: Implement actual file download from Slack
            file_content = b""  # Placeholder - implement actual file download
            
            parsed_data = self.file_parser.parse_excel_file(file_content, filename)
            
            # Combine with existing Databricks data
            combined_analysis = self.openai_client.analyze_uploaded_data(
                parsed_data, 
                session_data['databricks_data']
            )
            
            # Update session with file data
            db_manager.update_user_session(user_id, file_data=parsed_data)
            
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
            monitoring_manager.track_error('file_upload', str(e), user_id=event.get('user_id'))
            say(text=f"❌ Error processing uploaded file. Please try again or contact support.")
    
    @monitor_error("dashboard_request")
    def _handle_dashboard_request(self, message, say: Say):
        """Handle dashboard creation requests with enhanced error handling"""
        try:
            user_id = message['user']
            
            # Check if user has an active session
            session_data = db_manager.get_user_session(user_id)
            if not session_data:
                say(text="❌ Please first query a vehicle program using `/vehicle [launch-date]` before creating a dashboard.")
                return
            
            say(text="📊 Creating comprehensive dashboard...\nThis may take a few moments.")
            
            # Create dashboard
            dashboard_url = self.dashboard_creator.create_dashboard(
                databricks_data=session_data['databricks_data'],
                file_data=session_data.get('file_data'),
                launch_date=session_data['launch_date']
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
            monitoring_manager.track_error('dashboard_request', str(e), user_id=message.get('user'))
            say(text=f"❌ Error creating dashboard. Please try again or contact support.")
    
    @monitor_error("status_request")
    def _handle_status_request(self, message, say: Say):
        """Handle status requests with system information"""
        try:
            status = monitoring_manager.get_status()
            
            response = f"""
📊 *System Status*

🕒 **Uptime:** {status.get('uptime', 'Unknown')}
🌍 **Environment:** {status.get('environment', 'Unknown')}

📈 **Recent Activity (7 days):**
• Total Commands: {status.get('metrics', {}).get('total_commands', 0)}
• Success Rate: {status.get('metrics', {}).get('success_rate', 0):.1f}%
• Avg Response Time: {status.get('metrics', {}).get('avg_response_time', 0):.0f}ms

⚙️ **Configuration:**
• Database: {'✅' if status.get('configuration', {}).get('database_configured') else '❌'}
• Redis: {'✅' if status.get('configuration', {}).get('redis_configured') else '❌'}
• Sentry: {'✅' if status.get('configuration', {}).get('sentry_configured') else '❌'}
• Metrics: {'✅' if status.get('configuration', {}).get('metrics_enabled') else '❌'}
            """
            
            say(text=response)
            
        except Exception as e:
            logger.error(f"Error handling status request: {e}")
            say(text="❌ Error retrieving system status.")
    
    @monitor_error("help_request")
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

📈 `/status` - Check system status and metrics

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

*Support:*
For issues or questions, contact your system administrator.
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
        """Start the production Slack bot"""
        try:
            logger.info("Starting Production Vehicle Program Slack Bot...")
            
            # Start the app using Socket Mode
            handler = SocketModeHandler(self.app, ProductionConfig.SLACK_APP_TOKEN)
            handler.start()
            
        except Exception as e:
            logger.error(f"Error starting Slack bot: {e}")
            monitoring_manager.track_error('bot_startup', str(e))
            raise
    
    def stop(self):
        """Stop the production Slack bot"""
        try:
            logger.info("Stopping Production Slack Bot...")
            monitoring_manager.stop_metrics_server()
            logger.info("Production Slack Bot stopped successfully")
        except Exception as e:
            logger.error(f"Error stopping Slack bot: {e}")

def main():
    """Main function to start the production bot"""
    try:
        bot = ProductionSlackBot()
        bot.start()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Error in main: {e}")
        monitoring_manager.track_error('main_error', str(e))

if __name__ == "__main__":
    main() 