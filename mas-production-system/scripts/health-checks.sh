#!/bin/bash
set -euo pipefail

ENVIRONMENT=${1:-staging}
MAX_RETRIES=30
RETRY_INTERVAL=10

# Load environment configuration
source "config/${ENVIRONMENT}.env"

echo "Running health checks for ${ENVIRONMENT}..."

# Function to check endpoint
check_endpoint() {
    local url=$1
    local expected_status=${2:-200}
    
    echo -n "Checking ${url}... "
    
    for i in $(seq 1 ${MAX_RETRIES}); do
        status=$(curl -s -o /dev/null -w "%{http_code}" "${url}" || echo "000")
        
        if [[ "${status}" == "${expected_status}" ]]; then
            echo "OK (${status})"
            return 0
        fi
        
        if [[ $i -lt ${MAX_RETRIES} ]]; then
            echo -n "."
            sleep ${RETRY_INTERVAL}
        fi
    done
    
    echo "FAILED (${status})"
    return 1
}

# Check API health
check_endpoint "${API_URL}/health" 200

# Check metrics endpoint
check_endpoint "${API_URL}/metrics" 200

# Check specific services
for service in agents organizations messages; do
    check_endpoint "${API_URL}/api/v1/${service}" 200
done

# Database connectivity check
echo -n "Checking database connectivity... "
kubectl exec -n mas-system deployment/mas-core -- python -c "
import asyncio
from src.database import engine

async def check():
    async with engine.connect() as conn:
        result = await conn.execute('SELECT 1')
        print('OK')

asyncio.run(check())
" || echo "FAILED"

# Redis connectivity check
echo -n "Checking Redis connectivity... "
kubectl exec -n mas-system deployment/mas-core -- python -c "
import asyncio
from src.cache import cache

async def check():
    await cache.set('health_check', 'ok')
    result = await cache.get('health_check')
    if result == 'ok':
        print('OK')
    else:
        print('FAILED')

asyncio.run(check())
" || echo "FAILED"

echo "Health checks complete!"