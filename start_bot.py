#!/usr/bin/env python3
"""
Startup script for the Vehicle Program Slack Bot
"""

import os
import sys
import logging
from dotenv import load_dotenv

def validate_environment():
    """Validate that all required environment variables are set"""
    required_vars = [
        'SLACK_BOT_TOKEN',
        'SLACK_SIGNING_SECRET', 
        'SLACK_APP_TOKEN',
        'OPENAI_API_KEY',
        'DATABRICKS_HOST',
        'DATABRICKS_TOKEN'
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if not value or value.strip() == '':
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease check your .env file and ensure all required variables are set.")
        return False
    
    print("✅ All required environment variables are set")
    return True

def main():
    """Main startup function"""
    print("🚗 Starting Vehicle Program Slack Bot...")
    
    # Load environment variables
    load_dotenv()
    
    # Validate environment
    if not validate_environment():
        sys.exit(1)
    
    try:
        # Import and start the bot
        from slack_bot import VehicleProgramSlackBot
        
        print("🤖 Initializing Slack Bot...")
        bot = VehicleProgramSlackBot()
        
        print("🔌 Starting bot (press Ctrl+C to stop)...")
        bot.start()
        
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
    except Exception as e:
        print(f"❌ Error starting bot: {e}")
        logging.error(f"Startup error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 