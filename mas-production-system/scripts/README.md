# MAS Production System Scripts

This directory contains all scripts for development, deployment, and maintenance of the MAS Production System.

## Scripts Overview

### 🚀 setup_dev.sh
Main development environment setup script. Features:
- Three modes: Docker (recommended), Hybrid, or Local
- Interactive LLM provider selection (OpenAI, Ollama, LM Studio)
- Automatic Docker/WSL detection and configuration
- Creates `launch_dev.sh` for quick subsequent launches

**Usage:**
```bash
./scripts/setup_dev.sh
```

### 🔄 launch_dev.sh
Quick launch script created by setup_dev.sh. Features:
- Start/stop services
- View logs
- Switch between development modes
- Launch with debug tools (PgAdmin, RedisInsight)

**Note:** This script is automatically generated in the project root after running setup_dev.sh

### 🔧 fix-docker-wsl.sh
Helps fix Docker Desktop WSL 2 integration issues. Use when:
- Docker commands not found in WSL
- Need to set up Docker Desktop integration
- Want to create aliases for docker.exe commands

**Usage:**
```bash
./scripts/fix-docker-wsl.sh
```

### 📦 deploy.sh
Production deployment script. Features:
- Multiple environment support (local, staging, production)
- Automated testing before deployment
- Database backup functionality
- Support for Kubernetes, Docker Swarm, or Docker Compose
- Post-deployment health checks

**Usage:**
```bash
./scripts/deploy.sh [environment] [options]

# Examples:
./scripts/deploy.sh local
./scripts/deploy.sh staging --skip-tests
./scripts/deploy.sh production --force
```

### 🏥 health-checks.sh
Service health verification script. Checks:
- API endpoints availability
- Database connectivity
- Redis connectivity
- Service response times

**Usage:**
```bash
./scripts/health-checks.sh [environment]
```

## Environment Files (.env.example)

Yes, having two .env.example files is normal and intentional:

### 1. Root .env.example
- Used by Docker Compose
- Contains minimal configuration for container orchestration
- Focuses on LLM provider settings
- Simple format for quick setup

### 2. services/core/.env.example
- Comprehensive application configuration
- Used by the Python application directly
- Contains all possible configuration options
- Serves as documentation for all available settings

**Why two files?**
- **Separation of concerns**: Docker needs minimal config, app needs full config
- **Flexibility**: Can run app outside Docker with full config
- **Documentation**: Core .env.example shows all possible options
- **Simplicity**: Root .env keeps Docker setup simple

## Best Practices

1. **Always use scripts from the scripts directory**
   ```bash
   cd /path/to/mas-production-system
   ./scripts/setup_dev.sh
   ```

2. **For WSL users**
   - Ensure Docker Desktop is installed on Windows (not WSL)
   - Enable WSL integration in Docker Desktop settings
   - Run `fix-docker-wsl.sh` if encountering issues

3. **Environment configuration**
   - Copy `.env.example` to `.env` in project root
   - Only configure what you need (defaults work for most cases)
   - Don't commit `.env` files to git

4. **Development workflow**
   ```bash
   # First time setup
   ./scripts/setup_dev.sh
   
   # Daily usage
   ./launch_dev.sh  # Created in project root
   ```

## Troubleshooting

### Docker not found in WSL
```bash
./scripts/fix-docker-wsl.sh
```

### Permission denied
```bash
chmod +x scripts/*.sh
```

### Services not starting
1. Check Docker Desktop is running
2. Ensure ports 8000, 5432, 6379 are free
3. View logs: `docker-compose logs -f`

### Database connection issues
- In Docker mode: Use service names (db, redis)
- In Hybrid mode: Use localhost with exposed ports
- In Local mode: Ensure PostgreSQL/Redis are installed and running