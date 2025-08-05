# 🚀 Slack AI Integration Setup Guide

This guide will walk you through all the tokens, keys, and credentials needed to make your Slack AI integration fully functional.

## 📋 Prerequisites

Before starting, ensure you have:
- A Slack workspace with admin permissions
- An OpenAI account with API access
- A Databricks workspace (if using Databricks features)
- A Google Cloud account (if using Google Sheets features)
- A Smartsheet account (if using Smartsheet features)

---

## 🔑 Required Credentials

### 1. **Slack Configuration** (Required)

#### A. Create a Slack App
1. Go to [https://api.slack.com/apps](https://api.slack.com/apps)
2. Click "Create New App" → "From scratch"
3. Name your app (e.g., "Vehicle Launch AI Assistant")
4. Select your workspace

#### B. Configure Slack App Permissions
1. In your Slack app settings, go to "OAuth & Permissions"
2. Add the following Bot Token Scopes:
   - `chat:write` - Send messages
   - `channels:read` - View channels
   - `channels:history` - View messages in channels
   - `users:read` - View users
   - `files:read` - Read uploaded files
   - `files:write` - Upload files
   - `reactions:write` - Add reactions
   - `commands` - Add slash commands

3. Add the following User Token Scopes:
   - `chat:write` - Send messages as user

#### C. Get Your Slack Tokens
1. **Bot User OAuth Token** (`SLACK_BOT_TOKEN`):
   - Go to "OAuth & Permissions"
   - Copy the "Bot User OAuth Token" (starts with `xoxb-`)

2. **Signing Secret** (`SLACK_SIGNING_SECRET`):
   - Go to "Basic Information"
   - Copy the "Signing Secret"

3. **App-Level Token** (`SLACK_APP_TOKEN`):
   - Go to "Basic Information"
   - Click "Generate Token and Scopes"
   - Add scope: `connections:write`
   - Copy the generated token (starts with `xapp-`)

#### D. Install App to Workspace
1. Go to "Install App" in your Slack app settings
2. Click "Install to Workspace"
3. Authorize the app

---

### 2. **OpenAI Configuration** (Required)

#### A. Get OpenAI API Key
1. Go to [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2. Click "Create new secret key"
3. Name your key (e.g., "Slack AI Integration")
4. Copy the API key (starts with `sk-`)

**Environment Variable:** `OPENAI_API_KEY=sk-your-api-key-here`

---

### 3. **Databricks Configuration** (Required)

#### A. Get Databricks Host
1. Log into your Databricks workspace
2. Copy your workspace URL (e.g., `https://your-workspace.cloud.databricks.com`)

#### B. Generate Databricks Token
1. In Databricks, click your profile picture → "User Settings"
2. Go to "Access Tokens" tab
3. Click "Generate New Token"
4. Add a comment (e.g., "Slack AI Integration")
5. Copy the token (starts with `dapi`)

#### C. Configure Catalog and Schema
1. Note your catalog name (default is usually `hive_metastore`)
2. Note your schema name (or create one for this project)

**Environment Variables:**
```
DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
DATABRICKS_TOKEN=dapi-your-token-here
DATABRICKS_CATALOG=your_catalog_name
DATABRICKS_SCHEMA=your_schema_name
```

---

### 4. **Database Configuration** (Optional but Recommended)

#### A. PostgreSQL (Recommended for Production)
1. Set up a PostgreSQL database
2. Create a database for the application
3. Get connection string: `postgresql://username:password@host:port/database`

#### B. SQLite (Development/Testing)
- No setup required, will use local file

**Environment Variable:** `DATABASE_URL=postgresql://username:password@host:port/database`

---

### 5. **Google Sheets Configuration** (Optional)

#### A. Create Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Google Sheets API

#### B. Create Service Account
1. Go to "IAM & Admin" → "Service Accounts"
2. Click "Create Service Account"
3. Name it (e.g., "Slack AI Sheets Service")
4. Grant "Editor" role
5. Create and download the JSON key file

#### C. Share Google Sheets
1. Create or open the Google Sheets you want to use
2. Share with the service account email (from JSON file)
3. Give "Editor" permissions

**Environment Variables:**
```
GOOGLE_SHEETS_CREDENTIALS_FILE=path/to/your/service-account-key.json
DASHBOARD_TEMPLATE_ID=your-google-sheets-template-id-here
```

---

### 6. **Smartsheet Configuration** (Optional)

#### A. Get Smartsheet API Token
1. Log into [Smartsheet](https://www.smartsheet.com/)
2. Go to Personal Settings → API Access
3. Generate a new API token
4. Copy the token

**Environment Variable:** `SMARTSHEET_API_TOKEN=your-smartsheet-token-here`

---

### 7. **Redis Configuration** (Optional - for Caching)

#### A. Local Redis (Development)
```bash
# Install Redis
brew install redis  # macOS
sudo apt-get install redis-server  # Ubuntu

# Start Redis
redis-server
```

#### B. Cloud Redis (Production)
- Use Redis Cloud, AWS ElastiCache, or similar service
- Get connection string: `redis://username:password@host:port`

**Environment Variable:** `REDIS_URL=redis://localhost:6379`

---

### 8. **Monitoring Configuration** (Optional)

#### A. Sentry (Error Tracking)
1. Go to [Sentry.io](https://sentry.io/)
2. Create a new project
3. Copy the DSN (Data Source Name)

**Environment Variable:** `SENTRY_DSN=https://your-sentry-dsn-here`

---

## 🔧 Environment Setup

### Step 1: Create Environment File
Create a `.env` file in your project root:

```bash
cp env_template.txt .env
```

### Step 2: Fill in Your Credentials
Edit the `.env` file with your actual credentials:

```env
# =============================================================================
# SLACK CONFIGURATION
# =============================================================================
SLACK_BOT_TOKEN=xoxb-your-actual-bot-token
SLACK_SIGNING_SECRET=your-actual-signing-secret
SLACK_APP_TOKEN=xapp-your-actual-app-token

# =============================================================================
# OPENAI CONFIGURATION
# =============================================================================
OPENAI_API_KEY=sk-your-actual-openai-key

# =============================================================================
# DATABRICKS CONFIGURATION
# =============================================================================
DATABRICKS_HOST=https://your-actual-workspace.cloud.databricks.com
DATABRICKS_TOKEN=dapi-your-actual-databricks-token
DATABRICKS_CATALOG=your_actual_catalog
DATABRICKS_SCHEMA=your_actual_schema

# =============================================================================
# DATABASE CONFIGURATION
# =============================================================================
DATABASE_URL=postgresql://username:password@host:port/database

# =============================================================================
# GOOGLE SHEETS CONFIGURATION (Optional)
# =============================================================================
GOOGLE_SHEETS_CREDENTIALS_FILE=path/to/your/actual-credentials.json

# =============================================================================
# SMARTSHEET CONFIGURATION (Optional)
# =============================================================================
SMARTSHEET_API_TOKEN=your-actual-smartsheet-token

# =============================================================================
# REDIS CONFIGURATION (Optional)
# =============================================================================
REDIS_URL=redis://localhost:6379

# =============================================================================
# MONITORING CONFIGURATION (Optional)
# =============================================================================
SENTRY_DSN=https://your-actual-sentry-dsn

# =============================================================================
# APPLICATION SETTINGS
# =============================================================================
DEBUG_MODE=False
LOG_LEVEL=INFO
```

### Step 3: Load Environment Variables
```bash
# Load environment variables
source .env

# Or use python-dotenv
pip install python-dotenv
```

---

## 🚀 Testing Your Setup

### Step 1: Validate Configuration
```bash
python -c "
from production_config import ProductionConfig
result = ProductionConfig.validate_config()
print('Configuration Status:', '✅ Valid' if result['valid'] else '❌ Invalid')
if result['errors']:
    print('Errors:', result['errors'])
if result['warnings']:
    print('Warnings:', result['warnings'])
"
```

### Step 2: Test Individual Components
```bash
# Test Slack connection
python -c "
import os
from slack_bolt import App
app = App(token=os.getenv('SLACK_BOT_TOKEN'))
print('✅ Slack connection successful')
"

# Test OpenAI connection
python -c "
import openai
openai.api_key = os.getenv('OPENAI_API_KEY')
print('✅ OpenAI connection successful')
"

# Test Databricks connection
python -c "
from databricks_client import DatabricksClient
client = DatabricksClient()
print('✅ Databricks connection successful')
"
```

### Step 3: Run Tests
```bash
# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=. --cov-report=html
```

---

## 🔒 Security Best Practices

### 1. **Never Commit Credentials**
- Add `.env` to your `.gitignore`
- Use environment variables, not hardcoded values
- Rotate tokens regularly

### 2. **Use Different Tokens for Different Environments**
- Development: Use test workspaces and sandbox APIs
- Production: Use production workspaces and APIs
- Staging: Use staging environments

### 3. **Limit Permissions**
- Only grant necessary permissions to each service
- Use service accounts with minimal required access
- Regularly audit and rotate tokens

### 4. **Monitor Usage**
- Set up alerts for unusual API usage
- Monitor costs and usage limits
- Log all API calls for debugging

---

## 🆘 Troubleshooting

### Common Issues:

#### 1. **Slack App Not Responding**
- Check if app is installed to workspace
- Verify bot token permissions
- Check app-level token has `connections:write` scope

#### 2. **OpenAI API Errors**
- Verify API key is correct
- Check account has sufficient credits
- Ensure model name is correct

#### 3. **Databricks Connection Issues**
- Verify workspace URL is correct
- Check token has proper permissions
- Ensure catalog/schema exist

#### 4. **Database Connection Errors**
- Check connection string format
- Verify database exists and is accessible
- Check firewall/network settings

#### 5. **Google Sheets Permission Errors**
- Verify service account has access to sheets
- Check JSON credentials file path
- Ensure API is enabled in Google Cloud

---

## 📞 Support

If you encounter issues:

1. **Check the logs**: Look for error messages in `logs/vehicle_bot.log`
2. **Validate configuration**: Run the validation script above
3. **Test individual components**: Use the test scripts provided
4. **Check documentation**: Refer to each service's official documentation

---

## 🎯 Next Steps

Once your credentials are configured:

1. **Start the bot**: `python start_bot.py`
2. **Test in Slack**: Send a message to your bot
3. **Monitor logs**: Check for any errors or issues
4. **Deploy**: Follow deployment instructions for your platform

**Happy coding! 🚀** 