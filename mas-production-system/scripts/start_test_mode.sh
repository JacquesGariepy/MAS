#!/bin/bash
# Start MAS in test mode with mock LLM

echo "🚀 Starting MAS in Test Mode (Mock LLM)"
echo "========================================="

# Export test environment variables
export ENV_FILE=config/test.env

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose not found. Please install Docker Compose."
    exit 1
fi

# Stop any running containers
echo "🛑 Stopping existing containers..."
docker-compose -f docker-compose.dev.yml down

# Start services with test configuration
echo "🚀 Starting services with mock LLM configuration..."
docker-compose -f docker-compose.dev.yml --env-file config/test.env up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Check service health
echo "🔍 Checking service health..."
docker-compose -f docker-compose.dev.yml ps

# Show logs for core service
echo ""
echo "📋 Core service logs:"
docker-compose -f docker-compose.dev.yml logs --tail=20 core

echo ""
echo "✅ MAS started in test mode!"
echo "   - API: http://localhost:8088"
echo "   - LLM: Mock mode (no external API required)"
echo ""
echo "🧪 Run tests with: python examples/test_all_agent_types_fixed.py"
echo "📊 View logs with: docker-compose -f docker-compose.dev.yml logs -f"