.PHONY: help install test lint format build deploy clean

PYTHON := python3.11
PIP := $(PYTHON) -m pip
DOCKER_COMPOSE := docker-compose
KUBECTL := kubectl

# Colors
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[0;33m
NC := \033[0m

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  ${GREEN}%-15s${NC} %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install all dependencies
	@echo "${YELLOW}Installing Python dependencies...${NC}"
	$(PIP) install -r services/core/requirements.txt
	$(PIP) install -r services/core/requirements-dev.txt
	
	@echo "${YELLOW}Installing Node dependencies...${NC}"
	cd services/api && npm install
	
	@echo "${GREEN}Dependencies installed!${NC}"

test: ## Run all tests
	@echo "${YELLOW}Running Python tests...${NC}"
	cd services/core && pytest tests/ -v --cov=src --cov-report=term-missing
	
	@echo "${YELLOW}Running TypeScript tests...${NC}"
	cd services/api && npm test
	
	@echo "${GREEN}All tests passed!${NC}"

lint: ## Run linters
	@echo "${YELLOW}Linting Python code...${NC}"
	black --check services/
	flake8 services/
	mypy services/ --ignore-missing-imports
	
	@echo "${YELLOW}Linting TypeScript code...${NC}"
	cd services/api && npm run lint
	
	@echo "${GREEN}Linting complete!${NC}"

format: ## Format code
	@echo "${YELLOW}Formatting Python code...${NC}"
	black services/
	isort services/
	
	@echo "${YELLOW}Formatting TypeScript code...${NC}"
	cd services/api && npm run format
	
	@echo "${GREEN}Formatting complete!${NC}"

build: ## Build Docker images
	@echo "${YELLOW}Building Docker images...${NC}"
	$(DOCKER_COMPOSE) build
	
	@echo "${GREEN}Build complete!${NC}"

dev: ## Start development environment
	@echo "${YELLOW}Starting development environment...${NC}"
	$(DOCKER_COMPOSE) up -d
	
	@echo "${GREEN}Development environment started!${NC}"
	@echo "API: http://localhost:8000"
	@echo "Docs: http://localhost:8000/docs"

stop: ## Stop development environment
	@echo "${YELLOW}Stopping development environment...${NC}"
	$(DOCKER_COMPOSE) down
	
	@echo "${GREEN}Development environment stopped!${NC}"

migrate: ## Run database migrations
	@echo "${YELLOW}Running database migrations...${NC}"
	cd services/core && alembic upgrade head
	
	@echo "${GREEN}Migrations complete!${NC}"

deploy-staging: ## Deploy to staging
	@echo "${YELLOW}Deploying to staging...${NC}"
	./scripts/deploy.sh staging
	
	@echo "${GREEN}Staging deployment complete!${NC}"

deploy-prod: ## Deploy to production
	@echo "${RED}Deploying to production...${NC}"
	@read -p "Are you sure you want to deploy to production? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		./scripts/deploy.sh production; \
		echo "${GREEN}Production deployment complete!${NC}"; \
	else \
		echo "${YELLOW}Deployment cancelled.${NC}"; \
	fi

logs: ## View logs
	$(DOCKER_COMPOSE) logs -f

clean: ## Clean up
	@echo "${YELLOW}Cleaning up...${NC}"
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name "node_modules" -exec rm -rf {} +
	find . -type d -name "dist" -exec rm -rf {} +
	find . -type f -name ".coverage" -delete
	
	@echo "${GREEN}Cleanup complete!${NC}"

monitor: ## Open monitoring dashboards
	@echo "${YELLOW}Opening monitoring dashboards...${NC}"
	@echo "Grafana: http://localhost:3000"
	@echo "Prometheus: http://localhost:9090"
	@echo "Jaeger: http://localhost:16686"

security-scan: ## Run security scans
	@echo "${YELLOW}Running security scans...${NC}"
	bandit -r services/ -ll
	safety check
	
	@echo "${GREEN}Security scan complete!${NC}"

performance-test: ## Run performance tests
	@echo "${YELLOW}Running performance tests...${NC}"
	cd tests/performance && locust -f locustfile.py --headless -u 100 -r 10 -t 60s
	
	@echo "${GREEN}Performance test complete!${NC}"

backup: ## Backup database
	@echo "${YELLOW}Backing up database...${NC}"
	./scripts/backup.sh
	
	@echo "${GREEN}Backup complete!${NC}"

restore: ## Restore database
	@echo "${YELLOW}Restoring database...${NC}"
	./scripts/restore.sh
	
	@echo "${GREEN}Restore complete!${NC}"