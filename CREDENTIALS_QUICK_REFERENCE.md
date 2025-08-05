# 🔑 Credentials Quick Reference

## Required Credentials

| Service | Environment Variable | Format | Where to Get |
|---------|---------------------|---------|--------------|
| **Slack Bot Token** | `SLACK_BOT_TOKEN` | `xoxb-...` | Slack App → OAuth & Permissions |
| **Slack Signing Secret** | `SLACK_SIGNING_SECRET` | `...` | Slack App → Basic Information |
| **Slack App Token** | `SLACK_APP_TOKEN` | `xapp-...` | Slack App → Basic Information → Generate Token |
| **OpenAI API Key** | `OPENAI_API_KEY` | `sk-...` | [OpenAI Platform](https://platform.openai.com/api-keys) |
| **Databricks Host** | `DATABRICKS_HOST` | `https://workspace.cloud.databricks.com` | Your Databricks workspace URL |
| **Databricks Token** | `DATABRICKS_TOKEN` | `dapi...` | Databricks → User Settings → Access Tokens |

## Optional Credentials

| Service | Environment Variable | Format | Where to Get |
|---------|---------------------|---------|--------------|
| **Database URL** | `DATABASE_URL` | `postgresql://user:pass@host:port/db` | Your database connection string |
| **Google Credentials** | `GOOGLE_SHEETS_CREDENTIALS_FILE` | `path/to/file.json` | Google Cloud → Service Accounts |
| **Smartsheet Token** | `SMARTSHEET_API_TOKEN` | `...` | Smartsheet → Personal Settings → API Access |
| **Redis URL** | `REDIS_URL` | `redis://localhost:6379` | Your Redis connection string |
| **Sentry DSN** | `SENTRY_DSN` | `https://...` | [Sentry.io](https://sentry.io/) |

## Quick Setup Commands

```bash
# 1. Copy environment template
cp env_template.txt .env

# 2. Edit with your credentials
nano .env

# 3. Validate configuration
python -c "from production_config import ProductionConfig; print(ProductionConfig.validate_config())"

# 4. Test connections
python -c "import os; print('Slack:', '✅' if os.getenv('SLACK_BOT_TOKEN') else '❌')"
python -c "import os; print('OpenAI:', '✅' if os.getenv('OPENAI_API_KEY') else '❌')"
python -c "import os; print('Databricks:', '✅' if os.getenv('DATABRICKS_TOKEN') else '❌')"
```

## Minimum Required Setup

For basic functionality, you need these 6 credentials:

```env
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_SIGNING_SECRET=your-signing-secret
SLACK_APP_TOKEN=xapp-your-app-token
OPENAI_API_KEY=sk-your-openai-key
DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
DATABRICKS_TOKEN=dapi-your-databricks-token
```

## Security Checklist

- [ ] `.env` file is in `.gitignore`
- [ ] No credentials in code files
- [ ] Tokens have minimal required permissions
- [ ] Different tokens for dev/prod environments
- [ ] Regular token rotation schedule
- [ ] Monitoring for unusual API usage

## Common Issues

| Issue | Solution |
|-------|----------|
| Slack app not responding | Check bot token and app installation |
| OpenAI API errors | Verify API key and account credits |
| Databricks connection failed | Check workspace URL and token permissions |
| Database connection errors | Verify connection string format |
| Google Sheets access denied | Share sheets with service account email | 