# Troubleshooting Guide for MAS Development Setup

## Common Issues and Solutions

### 1. Docker not found in WSL
**Error:** `The command 'docker-compose' could not be found in this WSL 2 distro`

**Solution:**
```bash
# Run the Docker WSL fix script
./scripts/fix-docker-wsl.sh

# Then reload your shell
source ~/.bashrc

# Or enable WSL integration in Docker Desktop:
# 1. Open Docker Desktop on Windows
# 2. Go to Settings → Resources → WSL Integration
# 3. Enable integration with your WSL distro
# 4. Apply & Restart
```

### 2. Dependency conflicts during Docker build
**Error:** `ERROR: Cannot install -r requirements.txt ... because these package versions have conflicting dependencies`

**Solution:**
The requirements.txt has been updated to fix packaging conflicts. If you still see errors:
1. Pull the latest changes
2. Remove old Docker images: `docker system prune -a`
3. Rebuild: `docker-compose build --no-cache`

### 3. Script looking for docker-compose.yml in wrong directory
**Error:** `stat /path/to/scripts/docker-compose.dev.yml: no such file or directory`

**Solution:**
Always run scripts from the project root:
```bash
cd /path/to/mas-production-system
./scripts/setup_dev.sh
```

Or use the wrapper script:
```bash
./scripts/run-setup.sh
```

### 4. Permission denied when running scripts
**Error:** `Permission denied`

**Solution:**
```bash
chmod +x scripts/*.sh
```

### 5. Ports already in use
**Error:** `bind: address already in use`

**Solution:**
Check what's using the ports:
```bash
# Check port 8000 (API)
sudo lsof -i :8000

# Check port 5432 (PostgreSQL)
sudo lsof -i :5432

# Check port 6379 (Redis)
sudo lsof -i :6379

# Kill the process if needed
kill -9 <PID>
```

### 6. Database connection errors
**Error:** `could not connect to database`

**Solution:**
1. Ensure services are running:
   ```bash
   docker-compose ps
   ```

2. Check logs:
   ```bash
   docker-compose logs db
   ```

3. Wait for services to be ready:
   ```bash
   sleep 10  # Give services time to start
   ```

### 7. LM Studio connection issues
**Error:** `Connection refused to LM Studio`

**Solution:**
1. Ensure LM Studio is running on Windows
2. Check the port (default: 1234)
3. Use `host.docker.internal` in Docker to access Windows localhost
4. Verify in .env file:
   ```
   LLM_BASE_URL=http://host.docker.internal:1234/v1
   ```

### 8. launch_dev.sh not found
**Error:** `launch_dev.sh: No such file or directory`

**Solution:**
The launch_dev.sh script is created by setup_dev.sh in the project root. Run:
```bash
cd /path/to/mas-production-system
./scripts/setup_dev.sh
```

After successful setup, launch_dev.sh will be available in the project root:
```bash
./launch_dev.sh
```

## Quick Fixes

### Reset everything and start fresh:
```bash
# Stop all containers
docker-compose down -v

# Remove all Docker data
docker system prune -a

# Re-run setup
./scripts/setup_dev.sh
```

### Check Docker Desktop WSL integration:
```bash
# Test Docker access
docker.exe version

# Test Docker Compose access
docker-compose.exe version

# If working, create aliases
alias docker='docker.exe'
alias docker-compose='docker-compose.exe'
```

### View all logs:
```bash
# Development logs
docker-compose -f docker-compose.dev.yml logs -f

# Specific service logs
docker-compose -f docker-compose.dev.yml logs -f core
docker-compose -f docker-compose.dev.yml logs -f db
docker-compose -f docker-compose.dev.yml logs -f redis
```

## Still having issues?

1. Check the scripts/README.md for detailed documentation
2. Ensure you're using the latest version of the code
3. Try the Discord/Slack community (if available)
4. Create an issue on GitHub with:
   - Your OS and WSL version
   - Docker Desktop version
   - Full error message
   - Steps to reproduce