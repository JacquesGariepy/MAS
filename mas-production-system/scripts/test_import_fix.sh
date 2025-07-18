#!/bin/bash
echo "Testing Agent Creation Fix"
echo "=========================="

# Generate unique ID
UNIQUE_ID=$(date +%s)

# Create a unique user
echo -e "\n1. Creating user test_$UNIQUE_ID..."
curl -s -X POST http://localhost:8088/auth/register \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"test_$UNIQUE_ID\",\"email\":\"test_$UNIQUE_ID@test.com\",\"password\":\"test123\"}" | jq .

# Login to get token
echo -e "\n2. Logging in..."
TOKEN=$(curl -s -X POST http://localhost:8088/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test_$UNIQUE_ID&password=test123" | jq -r .access_token)

echo "Token obtained: ${TOKEN:0:20}..."

# Create each type of agent
echo -e "\n3. Creating agents..."

echo -e "\n   a) Creating reactive agent..."
curl -s -X POST http://localhost:8088/api/v1/agents \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"ReactiveAgent_$UNIQUE_ID\",\"role\":\"Test reactive agent\",\"agent_type\":\"reactive\",\"capabilities\":[\"test\"]}" | jq .

echo -e "\n   b) Creating reflexive agent..."
curl -s -X POST http://localhost:8088/api/v1/agents \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"ReflexiveAgent_$UNIQUE_ID\",\"role\":\"Test reflexive agent\",\"agent_type\":\"reflexive\",\"capabilities\":[\"test\"],\"reactive_rules\":{}}" | jq .

echo -e "\n   c) Creating hybrid agent..."
curl -s -X POST http://localhost:8088/api/v1/agents \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"HybridAgent_$UNIQUE_ID\",\"role\":\"Test hybrid agent\",\"agent_type\":\"hybrid\",\"capabilities\":[\"test\"],\"reactive_rules\":{}}" | jq .

echo -e "\n✅ Test completed!"