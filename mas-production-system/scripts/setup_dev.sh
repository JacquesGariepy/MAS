#!/bin/bash

# MAS Development Environment Setup Script
# This script prepares everything needed for development

set -e  # Exit on error

# Colors for display
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Global variables
RUN_MODE=""
USE_OLLAMA=false
COMPOSE_FILE=""

# Utility functions
print_header() {
    echo -e "\n${BLUE}===================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}===================================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Choose development mode
choose_dev_mode() {
    print_header "Development Environment Setup Mode"
    
    echo "How would you like to run the MAS application?"
    echo "1) Full Docker mode (Recommended - everything runs in containers)"
    echo "2) Hybrid mode (Database/Redis in Docker, Python app locally)"
    echo "3) Local mode (Everything runs locally - advanced users)"
    
    read -p "Your choice (1-3) [1]: " mode_choice
    mode_choice=${mode_choice:-1}
    
    case $mode_choice in
        1)
            RUN_MODE="docker"
            print_success "Selected: Full Docker mode"
            ;;
        2)
            RUN_MODE="hybrid"
            print_success "Selected: Hybrid mode"
            ;;
        3)
            RUN_MODE="local"
            print_success "Selected: Local mode"
            print_warning "Make sure PostgreSQL and Redis are installed locally"
            ;;
        *)
            RUN_MODE="docker"
            print_warning "Invalid choice, using Docker mode"
            ;;
    esac
}

# Check prerequisites based on mode
check_prerequisites() {
    print_header "Checking Prerequisites"
    
    if [ "$RUN_MODE" = "docker" ] || [ "$RUN_MODE" = "hybrid" ]; then
        # Check Docker (native or through Docker Desktop)
        if command -v docker &> /dev/null; then
            print_success "Docker is installed (native)"
            DOCKER_CMD="docker"
        elif command -v docker.exe &> /dev/null; then
            print_success "Docker Desktop is available"
            DOCKER_CMD="docker.exe"
        else
            print_error "Docker is not installed or not accessible from WSL"
            print_info "Run: ./scripts/fix-docker-wsl.sh for setup instructions"
            exit 1
        fi
        
        # Check Docker Compose
        if command -v docker-compose &> /dev/null; then
            print_success "Docker Compose is installed (native)"
            COMPOSE_CMD="docker-compose"
        elif command -v docker-compose.exe &> /dev/null; then
            print_success "Docker Compose is available through Docker Desktop"
            COMPOSE_CMD="docker-compose.exe"
        elif $DOCKER_CMD compose version &> /dev/null 2>&1; then
            print_success "Docker Compose is available as Docker plugin"
            COMPOSE_CMD="$DOCKER_CMD compose"
        else
            print_error "Docker Compose is not installed"
            print_info "Run: ./scripts/fix-docker-wsl.sh for setup instructions"
            exit 1
        fi
        
        # Export commands for use in other functions
        export DOCKER_CMD
        export COMPOSE_CMD
    fi
    
    if [ "$RUN_MODE" = "hybrid" ] || [ "$RUN_MODE" = "local" ]; then
        # Check Python
        if ! command -v python3 &> /dev/null; then
            print_error "Python 3 is not installed."
            exit 1
        else
            print_success "Python 3 is installed"
        fi
        
        # Check pip
        if ! command -v pip3 &> /dev/null && ! command -v pip &> /dev/null; then
            print_error "pip is not installed."
            exit 1
        else
            print_success "pip is installed"
        fi
    fi
    
    if [ "$RUN_MODE" = "local" ]; then
        # Check PostgreSQL
        if ! command -v psql &> /dev/null; then
            print_warning "PostgreSQL client not found. Make sure PostgreSQL is installed."
        else
            print_success "PostgreSQL client found"
        fi
        
        # Check Redis
        if ! command -v redis-cli &> /dev/null; then
            print_warning "Redis client not found. Make sure Redis is installed."
        else
            print_success "Redis client found"
        fi
    fi
}

# Configure LLM provider
configure_llm_provider() {
    print_header "LLM Provider Configuration"
    
    if [ -f .env ]; then
        print_info "An .env file already exists. Do you want to reconfigure it?"
        read -p "Reconfigure LLM provider? (y/N): " reconfigure
        if [[ ! "$reconfigure" =~ ^[Yy]$ ]]; then
            # Read existing provider
            if grep -q "LLM_PROVIDER=ollama" .env; then
                USE_OLLAMA=true
            fi
            return
        fi
    fi
    
    echo -e "\nChoose your LLM provider:"
    echo "1) OpenAI (Cloud-based, requires API key)"
    echo "2) Ollama (Local, free) - Recommended"
    echo "3) LM Studio (Local, free)"
    echo "4) Keep existing configuration"
    
    read -p "Your choice (1-4) [2]: " provider_choice
    provider_choice=${provider_choice:-2}
    
    case $provider_choice in
        1)
            print_info "Configuring OpenAI"
            read -p "Enter your OpenAI API key: " api_key
            read -p "Model to use (e.g., gpt-4o-mini) [gpt-4o-mini]: " model
            model=${model:-gpt-4o-mini}
            
            cat > .env << EOF
# Docker Compose Configuration
# LLM Provider
LLM_PROVIDER=openai
LLM_API_KEY=$api_key
LLM_MODEL=$model

# Optional configurations
# SENTRY_DSN=https://xxx@sentry.io/xxx
# SLACK_WEBHOOK=https://hooks.slack.com/xxx
EOF
            print_success "OpenAI configuration saved"
            ;;
            
        2)
            print_info "Configuring Ollama (local)"
            echo -e "\nAvailable Ollama models:"
            echo "1) llama2 (7B, lightweight)"
            echo "2) mistral (7B, performant)"
            echo "3) codellama (7B, code-specialized)"
            echo "4) mixtral (8x7B, very performant but heavy)"
            echo "5) Other model"
            
            read -p "Your choice (1-5) [2]: " model_choice
            model_choice=${model_choice:-2}
            
            case $model_choice in
                1) model="llama2";;
                2) model="mistral";;
                3) model="codellama";;
                4) model="mixtral";;
                5) 
                    read -p "Ollama model name: " model
                    ;;
                *) model="mistral";;
            esac
            
            cat > .env << EOF
# Docker Compose Configuration
# LLM Provider
LLM_PROVIDER=ollama
OLLAMA_MODEL=$model

# Optional configurations
# SENTRY_DSN=https://xxx@sentry.io/xxx
# SLACK_WEBHOOK=https://hooks.slack.com/xxx
EOF
            print_success "Ollama configuration saved with model: $model"
            USE_OLLAMA=true
            ;;
            
        3)
            print_info "Configuring LM Studio"
            print_warning "Make sure LM Studio is running on your machine"
            read -p "LM Studio port [1234]: " port
            port=${port:-1234}
            read -p "Model name in LM Studio: " model
            
            cat > .env << EOF
# Docker Compose Configuration
# LLM Provider
LLM_PROVIDER=lmstudio
LLM_BASE_URL=http://host.docker.internal:$port/v1
LLM_MODEL=$model

# Optional configurations
# SENTRY_DSN=https://xxx@sentry.io/xxx
# SLACK_WEBHOOK=https://hooks.slack.com/xxx
EOF
            print_success "LM Studio configuration saved"
            ;;
            
        4)
            print_info "Keeping existing configuration"
            return
            ;;
            
        *)
            print_warning "Invalid choice, using Ollama as default"
            USE_OLLAMA=true
            ;;
    esac
}

# Setup Python environment for hybrid/local modes
setup_python_env() {
    if [ "$RUN_MODE" = "docker" ]; then
        return  # Skip Python setup for full Docker mode
    fi
    
    print_header "Python Environment Setup"
    
    # Check if python3-venv is installed
    if ! python3 -m venv --help &> /dev/null; then
        print_warning "python3-venv is not installed"
        print_info "Please install: sudo apt update && sudo apt install python3-venv python3-full"
        read -p "Continue without virtual environment? (y/N): " continue_without
        if [[ ! "$continue_without" =~ ^[Yy]$ ]]; then
            exit 1
        fi
        return
    fi
    
    # Create virtual environment if needed
    if [ ! -d "venv" ]; then
        print_info "Creating virtual environment..."
        python3 -m venv venv
        print_success "Virtual environment created"
    else
        print_info "Virtual environment already exists"
    fi
    
    # Activate and update environment
    source venv/bin/activate
    print_info "Updating pip..."
    pip install --upgrade pip setuptools wheel &> /dev/null
    
    # Install development dependencies
    if [ -f "services/core/requirements-dev.txt" ]; then
        print_info "Installing development dependencies..."
        pip install -r services/core/requirements-dev.txt
        print_success "Dependencies installed"
    elif [ -f "services/core/requirements.txt" ]; then
        print_info "Installing production dependencies..."
        pip install -r services/core/requirements.txt
        print_success "Dependencies installed"
    fi
}

# Setup local database for local mode
setup_local_database() {
    if [ "$RUN_MODE" != "local" ]; then
        return
    fi
    
    print_header "Local Database Setup"
    
    print_info "Setting up PostgreSQL database..."
    echo "Please ensure PostgreSQL is running and you have superuser access."
    
    read -p "PostgreSQL host [localhost]: " pg_host
    pg_host=${pg_host:-localhost}
    
    read -p "PostgreSQL port [5432]: " pg_port
    pg_port=${pg_port:-5432}
    
    read -p "PostgreSQL username [postgres]: " pg_user
    pg_user=${pg_user:-postgres}
    
    # Create database
    print_info "Creating database 'mas' if it doesn't exist..."
    createdb -h $pg_host -p $pg_port -U $pg_user mas 2>/dev/null || true
    
    # Update .env with local database URL
    echo "DATABASE_URL=postgresql://$pg_user:pass@$pg_host:$pg_port/mas" >> .env
    
    print_success "Local database configured"
}

# Prepare Docker volumes
prepare_docker_volumes() {
    if [ "$RUN_MODE" = "local" ]; then
        return
    fi
    
    print_header "Preparing Docker Volumes"
    
    # Create necessary directories
    mkdir -p logs
    mkdir -p services/core/logs
    
    # Set appropriate permissions
    chmod -R 755 logs
    chmod -R 755 services/core/logs
    
    print_success "Docker volumes prepared"
}

# Start services based on mode
start_services() {
    print_header "Starting Services"
    
    case $RUN_MODE in
        "docker")
            # Determine docker-compose file
            if [ "$USE_OLLAMA" = true ]; then
                COMPOSE_FILE="docker-compose.ollama.yml"
                print_info "Using Ollama integrated configuration"
            else
                COMPOSE_FILE="docker-compose.dev.yml"
                print_info "Using standard development configuration"
            fi
            
            # Stop existing containers
            print_info "Stopping existing containers..."
            $COMPOSE_CMD -f $COMPOSE_FILE down &> /dev/null || true
            
            # Build images
            print_info "Building Docker images..."
            $COMPOSE_CMD -f $COMPOSE_FILE build
            
            # Start services
            print_info "Starting Docker services..."
            $COMPOSE_CMD -f $COMPOSE_FILE up -d
            
            # Wait for services
            print_info "Waiting for services to be ready..."
            sleep 10
            
            # Check service status
            print_info "Checking service status..."
            $COMPOSE_CMD -f $COMPOSE_FILE ps
            
            print_success "Docker services started"
            ;;
            
        "hybrid")
            # Start only database and Redis in Docker
            COMPOSE_FILE="docker-compose.dev.yml"
            
            print_info "Starting database and Redis services..."
            $COMPOSE_CMD -f $COMPOSE_FILE up -d db redis
            
            if [ "$USE_OLLAMA" = true ]; then
                print_info "Starting Ollama service..."
                $COMPOSE_CMD -f docker-compose.ollama.yml up -d ollama ollama-setup
            fi
            
            print_success "Support services started"
            
            # Run migrations
            print_info "Running database migrations..."
            cd services/core
            alembic upgrade head
            cd ../..
            
            print_info "To start the application locally, run:"
            echo "  source venv/bin/activate"
            echo "  cd services/core"
            echo "  uvicorn src.main:app --reload --port 8000"
            ;;
            
        "local")
            print_info "Local mode selected"
            
            # Run migrations
            print_info "Running database migrations..."
            cd services/core
            alembic upgrade head
            cd ../..
            
            print_info "To start the application locally, run:"
            echo "  source venv/bin/activate"
            echo "  cd services/core"
            echo "  uvicorn src.main:app --reload --port 8000"
            ;;
    esac
}

# Display connection information
display_connection_info() {
    print_header "Connection Information"
    
    echo -e "${GREEN}Available services:${NC}"
    echo -e "  • MAS API: ${BLUE}http://localhost:8000${NC}"
    echo -e "  • API Documentation: ${BLUE}http://localhost:8000/docs${NC}"
    
    if [ "$RUN_MODE" != "local" ]; then
        echo -e "  • PostgreSQL: ${BLUE}localhost:5432${NC} (user: user, password: pass)"
        echo -e "  • Redis: ${BLUE}localhost:6379${NC}"
    fi
    
    if [ "$USE_OLLAMA" = true ] && [ "$RUN_MODE" != "local" ]; then
        echo -e "  • Ollama API: ${BLUE}http://localhost:11434${NC}"
    fi
    
    if [ "$RUN_MODE" != "local" ]; then
        echo -e "\n${GREEN}Development tools available:${NC}"
        echo -e "  • PgAdmin: ${BLUE}http://localhost:5050${NC} (admin@mas.local / admin)"
        echo -e "    To activate: ${YELLOW}$COMPOSE_CMD -f $COMPOSE_FILE --profile tools up -d${NC}"
        echo -e "  • RedisInsight: ${BLUE}http://localhost:8001${NC}"
        echo -e "    To activate: ${YELLOW}$COMPOSE_CMD -f $COMPOSE_FILE --profile tools up -d${NC}"
        
        echo -e "\n${GREEN}Useful commands:${NC}"
        echo -e "  • View logs: ${YELLOW}$COMPOSE_CMD -f $COMPOSE_FILE logs -f core${NC}"
        echo -e "  • Stop services: ${YELLOW}$COMPOSE_CMD -f $COMPOSE_FILE down${NC}"
        echo -e "  • Restart services: ${YELLOW}$COMPOSE_CMD -f $COMPOSE_FILE restart${NC}"
    fi
    
    echo -e "  • Quick launch: ${YELLOW}./launch_dev.sh${NC}"
}

# Create quick launch script
create_launch_script() {
    print_header "Creating Quick Launch Script"
    
    cat > launch_dev.sh << 'EOF'
#!/bin/bash

# MAS Quick Launch Script for Development Environment

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🚀 MAS Development Environment Quick Launch...${NC}"

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  .env file not found. Please run ./setup_dev.sh first${NC}"
    exit 1
fi

# Read configuration from .env
source .env

# Detect run mode from .env or command history
RUN_MODE=${RUN_MODE:-docker}
if [ -f ".run_mode" ]; then
    RUN_MODE=$(cat .run_mode)
fi

# Determine docker-compose file if using Docker
if [ "$RUN_MODE" != "local" ]; then
    if [ "$LLM_PROVIDER" = "ollama" ]; then
        COMPOSE_FILE="docker-compose.ollama.yml"
    else
        COMPOSE_FILE="docker-compose.dev.yml"
    fi
fi

# Launch options
echo -e "\nLaunch options:"
echo "1) Start all services"
echo "2) Start with debug tools (PgAdmin, RedisInsight)"
echo "3) View real-time logs"
echo "4) Restart services"
echo "5) Stop all services"
echo "6) Clean and restart (full reset)"
echo "7) Change run mode (current: $RUN_MODE)"

read -p "Your choice (1-7) [1]: " choice
choice=${choice:-1}

case $choice in
    1)
        case $RUN_MODE in
            "docker")
                echo -e "${BLUE}Starting Docker services...${NC}"
                docker-compose -f $COMPOSE_FILE up -d
                echo -e "${GREEN}✅ Services started${NC}"
                echo -e "\n${BLUE}API available at: http://localhost:8000${NC}"
                echo -e "${BLUE}Documentation: http://localhost:8000/docs${NC}"
                ;;
            "hybrid")
                echo -e "${BLUE}Starting support services...${NC}"
                docker-compose -f $COMPOSE_FILE up -d db redis
                if [ "$LLM_PROVIDER" = "ollama" ]; then
                    docker-compose -f docker-compose.ollama.yml up -d ollama
                fi
                echo -e "${GREEN}✅ Support services started${NC}"
                echo -e "\n${YELLOW}Start the application with:${NC}"
                echo "  source venv/bin/activate"
                echo "  cd services/core && uvicorn src.main:app --reload"
                ;;
            "local")
                echo -e "${YELLOW}Local mode - ensure PostgreSQL and Redis are running${NC}"
                echo -e "\n${YELLOW}Start the application with:${NC}"
                echo "  source venv/bin/activate"
                echo "  cd services/core && uvicorn src.main:app --reload"
                ;;
        esac
        ;;
    2)
        if [ "$RUN_MODE" = "docker" ]; then
            echo -e "${BLUE}Starting with debug tools...${NC}"
            docker-compose -f $COMPOSE_FILE --profile tools up -d
            echo -e "${GREEN}✅ Services and tools started${NC}"
            echo -e "\n${BLUE}Available services:${NC}"
            echo -e "  • API: http://localhost:8000"
            echo -e "  • PgAdmin: http://localhost:5050"
            echo -e "  • RedisInsight: http://localhost:8001"
        else
            echo -e "${YELLOW}Debug tools only available in Docker mode${NC}"
        fi
        ;;
    3)
        if [ "$RUN_MODE" != "local" ]; then
            echo -e "${BLUE}Showing logs...${NC}"
            docker-compose -f $COMPOSE_FILE logs -f
        else
            echo -e "${YELLOW}Use application logs in local mode${NC}"
        fi
        ;;
    4)
        if [ "$RUN_MODE" != "local" ]; then
            echo -e "${BLUE}Restarting services...${NC}"
            docker-compose -f $COMPOSE_FILE restart
            echo -e "${GREEN}✅ Services restarted${NC}"
        else
            echo -e "${YELLOW}Restart the application manually in local mode${NC}"
        fi
        ;;
    5)
        if [ "$RUN_MODE" != "local" ]; then
            echo -e "${BLUE}Stopping services...${NC}"
            docker-compose -f $COMPOSE_FILE down
            echo -e "${GREEN}✅ Services stopped${NC}"
        else
            echo -e "${YELLOW}Stop the application manually in local mode${NC}"
        fi
        ;;
    6)
        if [ "$RUN_MODE" != "local" ]; then
            echo -e "${YELLOW}⚠️  This will delete all data!${NC}"
            read -p "Are you sure? (y/N): " confirm
            if [[ "$confirm" =~ ^[Yy]$ ]]; then
                echo -e "${BLUE}Full cleanup...${NC}"
                docker-compose -f $COMPOSE_FILE down -v
                docker-compose -f $COMPOSE_FILE build --no-cache
                docker-compose -f $COMPOSE_FILE up -d
                echo -e "${GREEN}✅ Environment reset${NC}"
            fi
        else
            echo -e "${YELLOW}Clean database manually in local mode${NC}"
        fi
        ;;
    7)
        echo -e "${BLUE}Changing run mode...${NC}"
        echo "1) Docker mode (everything in containers)"
        echo "2) Hybrid mode (DB/Redis in Docker, app local)"
        echo "3) Local mode (everything local)"
        read -p "New mode (1-3): " new_mode
        case $new_mode in
            1) echo "docker" > .run_mode ;;
            2) echo "hybrid" > .run_mode ;;
            3) echo "local" > .run_mode ;;
        esac
        echo -e "${GREEN}✅ Run mode changed. Run this script again.${NC}"
        ;;
    *)
        echo -e "${YELLOW}Invalid choice${NC}"
        exit 1
        ;;
esac

# Show container status if using Docker
if [ "$RUN_MODE" != "local" ] && [ "$choice" -lt 5 ]; then
    echo -e "\n${BLUE}Service status:${NC}"
    docker-compose -f $COMPOSE_FILE ps
fi

# Offer to view logs
if [ "$RUN_MODE" != "local" ]; then
    echo -e "\n${BLUE}Press Enter to exit, or 'l' to view logs${NC}"
    read -n 1 -r key
    if [[ "$key" = "l" ]]; then
        docker-compose -f $COMPOSE_FILE logs -f core
    fi
fi
EOF
    
    chmod +x launch_dev.sh
    print_success "launch_dev.sh script created"
}

# Save run mode for future use
save_run_mode() {
    echo "$RUN_MODE" > .run_mode
}

# Main program
main() {
    print_header "🚀 MAS Development Environment Setup"
    
    # Change to project root directory
    cd "$(dirname "$0")/.."
    
    # Choose development mode
    choose_dev_mode
    
    # Save run mode
    save_run_mode
    
    # Check prerequisites
    check_prerequisites
    
    # Configure LLM provider
    configure_llm_provider
    
    # Setup based on mode
    setup_python_env
    setup_local_database
    prepare_docker_volumes
    
    # Start services
    start_services
    
    # Create launch script
    create_launch_script
    
    # Display info
    display_connection_info
    
    print_header "✅ Setup completed successfully!"
    echo -e "${GREEN}To quickly launch the environment in the future:${NC}"
    echo -e "  ${YELLOW}./launch_dev.sh${NC}"
    
    if [ "$RUN_MODE" != "local" ] && [ -n "$COMPOSE_FILE" ]; then
        echo -e "\n${GREEN}To view real-time logs:${NC}"
        echo -e "  ${YELLOW}$COMPOSE_CMD -f $COMPOSE_FILE logs -f core${NC}"
    fi
}

# Run main program
main