#!/bin/bash
# ============================================================================
# CredBuzz Backend - Docker Deployment Script
# ============================================================================
# This script helps you deploy the CredBuzz Backend using Docker
# Run with: ./deploy.sh [command]
# Commands: build, start, stop, restart, logs, clean, backup, restore
# ============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Project directory
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

# Functions
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

check_env_file() {
    if [ ! -f ".env.docker" ]; then
        print_error ".env.docker file not found!"
        print_info "Creating from example file..."
        cp .env.docker.example .env.docker
        print_info "Please edit .env.docker with your production values"
        print_info "Run: nano .env.docker"
        exit 1
    fi
}

check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed!"
        print_info "Install Docker first: https://docs.docker.com/engine/install/"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed!"
        print_info "Install Docker Compose first: https://docs.docker.com/compose/install/"
        exit 1
    fi
    
    print_success "Docker and Docker Compose are installed"
}

build_images() {
    print_info "Building Docker images..."
    docker-compose build --no-cache
    print_success "Docker images built successfully"
}

start_services() {
    print_info "Starting services..."
    docker-compose up -d
    print_success "Services started"
    
    print_info "Waiting for services to be healthy..."
    sleep 10
    
    print_info "Running migrations..."
    docker-compose exec -T web python manage.py migrate
    
    print_info "Collecting static files..."
    docker-compose exec -T web python manage.py collectstatic --noinput
    
    print_success "Deployment complete!"
    print_info "Access your application at: http://localhost:8000"
}

stop_services() {
    print_info "Stopping services..."
    docker-compose stop
    print_success "Services stopped"
}

restart_services() {
    print_info "Restarting services..."
    docker-compose restart
    print_success "Services restarted"
}

view_logs() {
    print_info "Showing logs (Ctrl+C to exit)..."
    docker-compose logs -f
}

view_status() {
    print_info "Container Status:"
    docker-compose ps
    echo ""
    print_info "Service Health:"
    docker-compose exec web python manage.py check || true
}

clean_docker() {
    print_info "Cleaning up Docker resources..."
    read -p "This will remove all containers and volumes. Continue? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker-compose down -v
        docker system prune -f
        print_success "Cleanup complete"
    else
        print_info "Cleanup cancelled"
    fi
}

backup_database() {
    print_info "Backing up database..."
    BACKUP_FILE="backup_$(date +%Y%m%d_%H%M%S).sql"
    docker-compose exec -T db pg_dump -U credbuzz_user credbuzz_db > "$BACKUP_FILE"
    print_success "Database backed up to: $BACKUP_FILE"
}

restore_database() {
    if [ -z "$1" ]; then
        print_error "Please provide backup file: ./deploy.sh restore <backup_file.sql>"
        exit 1
    fi
    
    if [ ! -f "$1" ]; then
        print_error "Backup file not found: $1"
        exit 1
    fi
    
    print_info "Restoring database from: $1"
    read -p "This will overwrite the current database. Continue? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cat "$1" | docker-compose exec -T db psql -U credbuzz_user -d credbuzz_db
        print_success "Database restored"
    else
        print_info "Restore cancelled"
    fi
}

create_superuser() {
    print_info "Creating Django superuser..."
    docker-compose exec web python manage.py createsuperuser
}

run_migrations() {
    print_info "Running migrations..."
    docker-compose exec web python manage.py migrate
    print_success "Migrations complete"
}

collect_static() {
    print_info "Collecting static files..."
    docker-compose exec web python manage.py collectstatic --noinput
    print_success "Static files collected"
}

show_help() {
    echo "CredBuzz Backend - Docker Deployment Script"
    echo ""
    echo "Usage: ./deploy.sh [command]"
    echo ""
    echo "Commands:"
    echo "  build          - Build Docker images"
    echo "  start          - Start all services"
    echo "  stop           - Stop all services"
    echo "  restart        - Restart all services"
    echo "  logs           - View logs (follow mode)"
    echo "  status         - Show container status"
    echo "  clean          - Clean up Docker resources"
    echo "  backup         - Backup database"
    echo "  restore <file> - Restore database from backup"
    echo "  superuser      - Create Django superuser"
    echo "  migrate        - Run database migrations"
    echo "  collectstatic  - Collect static files"
    echo "  shell          - Access Django shell"
    echo "  bash           - Access container bash"
    echo "  help           - Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./deploy.sh build"
    echo "  ./deploy.sh start"
    echo "  ./deploy.sh logs"
    echo "  ./deploy.sh backup"
    echo "  ./deploy.sh restore backup_20240110_120000.sql"
}

# Main script
main() {
    check_docker
    
    case "$1" in
        build)
            check_env_file
            build_images
            ;;
        start)
            check_env_file
            start_services
            ;;
        stop)
            stop_services
            ;;
        restart)
            restart_services
            ;;
        logs)
            view_logs
            ;;
        status)
            view_status
            ;;
        clean)
            clean_docker
            ;;
        backup)
            backup_database
            ;;
        restore)
            restore_database "$2"
            ;;
        superuser)
            create_superuser
            ;;
        migrate)
            run_migrations
            ;;
        collectstatic)
            collect_static
            ;;
        shell)
            docker-compose exec web python manage.py shell
            ;;
        bash)
            docker-compose exec web bash
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            if [ -z "$1" ]; then
                print_error "No command specified"
            else
                print_error "Unknown command: $1"
            fi
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
