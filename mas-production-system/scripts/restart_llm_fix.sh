#!/bin/bash
# Script to restart services and apply LLM JSON fix

echo "🔧 Applying LLM JSON Fix..."
echo "================================"

# Check if Docker services are running
if docker-compose -f docker-compose.dev.yml ps | grep -q "core"; then
    echo "✅ Docker services detected"
    
    # Restart the core service to ensure changes are loaded
    echo "🔄 Restarting core service..."
    docker-compose -f docker-compose.dev.yml restart core
    
    # Wait for service to be ready
    echo "⏳ Waiting for service to be ready..."
    sleep 10
    
    # Check service logs
    echo "📋 Recent logs:"
    docker-compose -f docker-compose.dev.yml logs --tail=20 core
else
    echo "❌ Docker services not running. Starting them..."
    docker-compose -f docker-compose.dev.yml up -d
    
    echo "⏳ Waiting for services to start..."
    sleep 15
fi

echo ""
echo "✅ Services restarted with LLM JSON fix applied!"
echo ""
echo "📝 Test the fix with:"
echo "   python examples/test_llm_json_fix.py"
echo ""
echo "🚀 Or run the autonomous example:"
echo "   python examples/autonomous.py"