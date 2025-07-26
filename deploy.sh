#!/bin/bash

# Production Deployment Script for Vehicle Program Slack Bot
# Usage: ./deploy.sh [start|stop|restart|logs|status]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="vehicle-program-slack-bot"
COMPOSE_FILE="docker-compose.yml"

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
}

# Function to check if .env file exists
check_env_file() {
    if [ ! -f ".env" ]; then
        print_error ".env file not found. Please create it from env_template.txt"
        exit 1
    fi
}

# Function to validate environment variables
validate_env() {
    print_status "Validating environment variables..."
    
    # Check required variables
    required_vars=(
        "SLACK_BOT_TOKEN"
        "SLACK_SIGNING_SECRET"
        "SLACK_APP_TOKEN"
        "OPENAI_API_KEY"
        "DATABRICKS_HOST"
        "DATABRICKS_TOKEN"
    )
    
    missing_vars=()
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            missing_vars+=("$var")
        fi
    done
    
    if [ ${#missing_vars[@]} -ne 0 ]; then
        print_error "Missing required environment variables:"
        for var in "${missing_vars[@]}"; do
            echo "  - $var"
        done
        exit 1
    fi
    
    print_status "Environment validation passed"
}

# Function to start the application
start_app() {
    print_status "Starting Vehicle Program Slack Bot..."
    
    check_docker
    check_env_file
    validate_env
    
    # Create necessary directories
    mkdir -p logs
    mkdir -p grafana/dashboards
    mkdir -p grafana/datasources
    
    # Build and start services
    docker-compose -f $COMPOSE_FILE up -d --build
    
    print_status "Services started successfully"
    print_status "Monitoring dashboard: http://localhost:3000 (admin/admin)"
    print_status "Metrics endpoint: http://localhost:9090/metrics"
    print_status "Health check: http://localhost:9090/health"
}

# Function to stop the application
stop_app() {
    print_status "Stopping Vehicle Program Slack Bot..."
    docker-compose -f $COMPOSE_FILE down
    print_status "Services stopped successfully"
}

# Function to restart the application
restart_app() {
    print_status "Restarting Vehicle Program Slack Bot..."
    stop_app
    sleep 5
    start_app
}

# Function to show logs
show_logs() {
    print_status "Showing logs..."
    docker-compose -f $COMPOSE_FILE logs -f
}

# Function to show status
show_status() {
    print_status "Checking service status..."
    docker-compose -f $COMPOSE_FILE ps
    
    echo ""
    print_status "Service URLs:"
    echo "  - Slack Bot Health: http://localhost:9090/health"
    echo "  - Grafana Dashboard: http://localhost:3000"
    echo "  - Prometheus Metrics: http://localhost:9091"
}

# Function to backup data
backup_data() {
    print_status "Creating backup..."
    
    timestamp=$(date +%Y%m%d_%H%M%S)
    backup_dir="backup_$timestamp"
    
    mkdir -p "$backup_dir"
    
    # Backup database
    docker exec vehicle-bot-postgres pg_dump -U botuser vehicle_bot > "$backup_dir/database.sql"
    
    # Backup logs
    cp -r logs "$backup_dir/"
    
    # Create backup archive
    tar -czf "backup_$timestamp.tar.gz" "$backup_dir"
    rm -rf "$backup_dir"
    
    print_status "Backup created: backup_$timestamp.tar.gz"
}

# Function to restore data
restore_data() {
    if [ -z "$1" ]; then
        print_error "Please provide backup file path"
        echo "Usage: $0 restore <backup_file.tar.gz>"
        exit 1
    fi
    
    print_status "Restoring from backup: $1"
    
    # Extract backup
    tar -xzf "$1"
    backup_dir=$(basename "$1" .tar.gz)
    
    # Restore database
    docker exec -i vehicle-bot-postgres psql -U botuser vehicle_bot < "$backup_dir/database.sql"
    
    # Restore logs
    cp -r "$backup_dir/logs" ./
    
    # Cleanup
    rm -rf "$backup_dir"
    
    print_status "Restore completed successfully"
}

# Function to update the application
update_app() {
    print_status "Updating Vehicle Program Slack Bot..."
    
    # Pull latest changes
    git pull origin main
    
    # Rebuild and restart
    docker-compose -f $COMPOSE_FILE down
    docker-compose -f $COMPOSE_FILE up -d --build
    
    print_status "Update completed successfully"
}

# Function to show help
show_help() {
    echo "Vehicle Program Slack Bot - Deployment Script"
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  start     - Start the application"
    echo "  stop      - Stop the application"
    echo "  restart   - Restart the application"
    echo "  logs      - Show application logs"
    echo "  status    - Show service status"
    echo "  backup    - Create a backup of data"
    echo "  restore   - Restore from backup"
    echo "  update    - Update the application"
    echo "  help      - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 start"
    echo "  $0 backup"
    echo "  $0 restore backup_20240101_120000.tar.gz"
}

# Main script logic
case "${1:-help}" in
    start)
        start_app
        ;;
    stop)
        stop_app
        ;;
    restart)
        restart_app
        ;;
    logs)
        show_logs
        ;;
    status)
        show_status
        ;;
    backup)
        backup_data
        ;;
    restore)
        restore_data "$2"
        ;;
    update)
        update_app
        ;;
    help|*)
        show_help
        ;;
esac 