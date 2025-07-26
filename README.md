# Vehicle Program Slack Agent

A comprehensive Slack bot that integrates with OpenAI, Databricks, and Google Sheets to provide vehicle program launch tracking and analysis.

## Features

- 🤖 **Interactive Slack Bot**: Query vehicle program status using natural language
- 📊 **Databricks Integration**: Query BOM, MPL, MFE, 4P, and PPAP data
- 🧠 **OpenAI Analysis**: AI-powered insights and recommendations
- 📁 **File Upload Support**: Excel, Google Sheets, and Smartsheet integration
- 📈 **Automated Dashboards**: Google Sheets dashboard creation
- 📊 **Databricks Visualizations**: Automated chart and dashboard generation

## Prerequisites

Before setting up the Slack agent, you'll need:

1. **Slack App** - Create a Slack app at https://api.slack.com/apps
2. **OpenAI API Key** - Get from https://platform.openai.com/api-keys
3. **Databricks Workspace** - Access to your Databricks environment
4. **Google Service Account** - For Google Sheets integration
5. **Smartsheet API Token** - For Smartsheet integration (optional)

## Setup Instructions

### 1. Clone and Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy the template file and add your credentials:

```bash
# Copy the template
cp env_template.txt .env

# Edit the .env file with your actual credentials
nano .env
```

Fill in your actual credentials in the `.env` file:

```env
# Slack Configuration
SLACK_BOT_TOKEN=xoxb-your-actual-bot-token
SLACK_SIGNING_SECRET=your-actual-signing-secret
SLACK_APP_TOKEN=xapp-your-actual-app-token

# OpenAI Configuration
OPENAI_API_KEY=sk-your-actual-openai-key

# Databricks Configuration
DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
DATABRICKS_TOKEN=dapi-your-actual-databricks-token
DATABRICKS_CATALOG=your_actual_catalog
DATABRICKS_SCHEMA=your_actual_schema

# Databricks Table Names
DATABRICKS_TABLES_BILL_OF_MATERIAL=your_actual_bom_table
DATABRICKS_TABLES_MASTER_PARTS_LIST=your_actual_mpl_table
DATABRICKS_TABLES_MATERIAL_FLOW_ENGINEERING=your_actual_mfe_table
DATABRICKS_TABLES_4P=your_actual_4p_table
DATABRICKS_TABLES_PPAP=your_actual_ppap_table

# Google Sheets Configuration
GOOGLE_SHEETS_CREDENTIALS_FILE=path/to/your/google-credentials.json

# Smartsheet Configuration
SMARTSHEET_API_TOKEN=your-actual-smartsheet-token
```

### 3. Slack App Configuration

1. **Create a Slack App**:
   - Go to https://api.slack.com/apps
   - Click "Create New App" → "From scratch"
   - Name your app (e.g., "Vehicle Program Bot")

2. **Configure Bot Token Scopes**:
   - Go to "OAuth & Permissions"
   - Add these Bot Token Scopes:
     - `chat:write`
     - `files:read`
     - `app_mentions:read`
     - `channels:history`
     - `groups:history`
     - `im:history`
     - `mpim:history`

3. **Enable Socket Mode**:
   - Go to "Socket Mode"
   - Enable Socket Mode
   - Generate an App-Level Token

4. **Install App to Workspace**:
   - Go to "Install App"
   - Click "Install to Workspace"

5. **Get Your Tokens**:
   - Copy the Bot User OAuth Token (starts with `xoxb-`)
   - Copy the Signing Secret
   - Copy the App-Level Token (starts with `xapp-`)

### 4. Databricks Configuration

1. **Get Databricks Host**:
   - Your workspace URL (e.g., `https://your-workspace.cloud.databricks.com`)

2. **Generate Access Token**:
   - Go to User Settings → Access Tokens
   - Generate a new token

3. **Update Table Names**:
   - Update the table names in your `.env` file to match your actual Databricks tables

### 5. Google Sheets Configuration

1. **Create Service Account**:
   - Go to Google Cloud Console
   - Create a new project or select existing
   - Enable Google Sheets API
   - Create a Service Account
   - Download the JSON credentials file

2. **Share Templates** (Optional):
   - If you have a dashboard template, share it with the service account email
   - Add the template ID to your `.env` file

### 6. Customize Data Queries

Update the SQL queries in `databricks_client.py` to match your actual table structure:

```python
# Example: Update BOM query
def _query_bom_status(self, launch_date: str) -> Dict:
    query = f"""
    SELECT 
        part_number,
        part_name,
        status,
        completion_percentage,
        last_updated
    FROM {DATABRICKS_CATALOG}.{DATABRICKS_SCHEMA}.{DATABRICKS_TABLES['bill_of_material']}
    WHERE launch_date = '{launch_date}'
    """
    return self._execute_query(query, "BOM")
```

### 7. Run the Bot

```bash
python slack_bot.py
```

## Usage

### Basic Commands

- `/vehicle 2024-03-15` - Query vehicle program status for a specific launch date
- `/upload` - Get instructions for uploading data files
- `/dashboard` - Create a Google Sheets dashboard
- `/help` - Show help information

### Workflow

1. **Query Program Status**:
   ```
   /vehicle 2024-03-15
   ```
   This will:
   - Query all departments in Databricks
   - Generate AI analysis
   - Create Databricks visualizations

2. **Upload Additional Data** (Optional):
   - Upload Excel files directly to Slack
   - Or provide Google Sheets/Smartsheet IDs
   - Data will be combined with Databricks data

3. **Create Dashboard**:
   ```
   /dashboard
   ```
   This creates a comprehensive Google Sheets dashboard with:
   - Summary overview
   - Department-specific sheets
   - Charts and visualizations
   - Action items

## File Structure

```
slack-ai-integration/
├── config.py                 # Configuration and environment variables
├── slack_bot.py             # Main Slack bot implementation
├── databricks_client.py     # Databricks integration
├── openai_client.py         # OpenAI integration
├── file_parser.py           # File upload and parsing
├── google_sheets_dashboard.py # Dashboard creation
├── requirements.txt         # Python dependencies
├── env_template.txt         # Environment variables template
└── README.md               # This file
```

## Customization Points

### 1. Databricks Queries

Update the SQL queries in `databricks_client.py` to match your schema:

```python
# Update table names in config.py
DATABRICKS_TABLES = {
    'bill_of_material': 'your_actual_bom_table',
    'master_parts_list': 'your_actual_mpl_table',
    # ... etc
}
```

### 2. File Parsing

Customize the file parsing logic in `file_parser.py`:

```python
def _parse_excel_sheet(self, df: pd.DataFrame, sheet_name: str) -> Dict:
    # Update column mappings based on your Excel template
    if 'BOM' in sheet_name.upper():
        sheet_data['department_mapping'] = {
            'part_number': 'your_actual_column_name',
            'status': 'your_actual_status_column',
            # ... etc
        }
```

### 3. Dashboard Templates

Create a Google Sheets template and update the template ID in your `.env` file.

### 4. OpenAI Prompts

Customize the analysis prompts in `openai_client.py`:

```python
def _get_system_prompt(self) -> str:
    return """
    You are an expert vehicle program launch analyst...
    # Add your specific requirements
    """
```

## Troubleshooting

### Common Issues

1. **Slack Bot Not Responding**:
   - Check that all tokens are correct
   - Verify Socket Mode is enabled
   - Ensure the bot is invited to the channel

2. **Databricks Connection Errors**:
   - Verify your Databricks host URL
   - Check that your access token is valid
   - Ensure table names match your schema

3. **File Upload Issues**:
   - Check file format (Excel files only)
   - Verify file size (max 10MB)
   - Ensure proper column structure

4. **Google Sheets Errors**:
   - Verify service account credentials
   - Check that Google Sheets API is enabled
   - Ensure proper sharing permissions

### Debug Mode

Enable debug mode in your `.env` file:

```env
DEBUG_MODE=True
LOG_LEVEL=DEBUG
```

## Security Notes

- Never commit your `.env` file to version control
- Use environment variables for all sensitive data
- Regularly rotate API tokens
- Implement proper access controls for your Databricks workspace

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the logs for error messages
3. Verify all credentials are correct
4. Test individual components separately

## License

This project is for internal use. Please ensure compliance with your organization's data handling policies. 