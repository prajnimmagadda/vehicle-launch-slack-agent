import os
from dotenv import load_dotenv

load_dotenv()

# =============================================================================
# SLACK CONFIGURATION
# =============================================================================
SLACK_BOT_TOKEN = os.getenv('SLACK_BOT_TOKEN')  # TODO: Add your Slack Bot Token
SLACK_SIGNING_SECRET = os.getenv('SLACK_SIGNING_SECRET')  # TODO: Add your Slack Signing Secret
SLACK_APP_TOKEN = os.getenv('SLACK_APP_TOKEN')  # TODO: Add your Slack App Token

# =============================================================================
# OPENAI CONFIGURATION
# =============================================================================
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')  # TODO: Add your OpenAI API Key
OPENAI_MODEL = "gpt-4"  # or "gpt-3.5-turbo" based on your needs

# =============================================================================
# DATABRICKS CONFIGURATION
# =============================================================================
DATABRICKS_HOST = os.getenv('DATABRICKS_HOST')  # TODO: Add your Databricks workspace URL
DATABRICKS_TOKEN = os.getenv('DATABRICKS_TOKEN')  # TODO: Add your Databricks access token
DATABRICKS_CATALOG = os.getenv('DATABRICKS_CATALOG', 'your_catalog_name')  # TODO: Specify your catalog name
DATABRICKS_SCHEMA = os.getenv('DATABRICKS_SCHEMA', 'your_schema_name')  # TODO: Specify your schema name

# Databricks table names - TODO: Update with your actual table names
DATABRICKS_TABLES = {
    'bill_of_material': os.getenv('DATABRICKS_TABLES_BILL_OF_MATERIAL', 'your_bom_table_name'),
    'master_parts_list': os.getenv('DATABRICKS_TABLES_MASTER_PARTS_LIST', 'your_mpl_table_name'),
    'material_flow_engineering': os.getenv('DATABRICKS_TABLES_MATERIAL_FLOW_ENGINEERING', 'your_mfe_table_name'),
    '4p': os.getenv('DATABRICKS_TABLES_4P', 'your_4p_table_name'),
    'ppap': os.getenv('DATABRICKS_TABLES_PPAP', 'your_ppap_table_name'),
}

# =============================================================================
# GOOGLE SHEETS CONFIGURATION
# =============================================================================
GOOGLE_SHEETS_CREDENTIALS_FILE = os.getenv('GOOGLE_SHEETS_CREDENTIALS_FILE', 'credentials.json')  # TODO: Add path to your Google service account JSON
GOOGLE_SHEETS_SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']

# =============================================================================
# SMARTSHEET CONFIGURATION
# =============================================================================
SMARTSHEET_API_TOKEN = os.getenv('SMARTSHEET_API_TOKEN')  # TODO: Add your Smartsheet API token

# =============================================================================
# APPLICATION SETTINGS
# =============================================================================
DEBUG_MODE = os.getenv('DEBUG_MODE', 'True').lower() == 'true'
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# File upload settings
ALLOWED_FILE_TYPES = ['.xlsx', '.xls', '.csv']
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# Dashboard template settings
DASHBOARD_TEMPLATE_ID = os.getenv('DASHBOARD_TEMPLATE_ID')  # TODO: Add Google Sheets template ID if you have one 