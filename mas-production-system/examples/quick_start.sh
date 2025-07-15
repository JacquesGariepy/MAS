#!/bin/bash

# Quick start script for testing MAS agents and swarms

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

API_URL="http://localhost:8080"  # Port changed to avoid conflicts

echo -e "${BLUE}MAS Quick Start - Agent & Swarm Testing${NC}"
echo "========================================"

# Check if API is running
check_api() {
    echo -e "\n${YELLOW}Checking if MAS API is running...${NC}"
    if curl -s -f "$API_URL/health" > /dev/null; then
        echo -e "${GREEN}✅ API is running${NC}"
        return 0
    else
        echo -e "${RED}❌ API is not running${NC}"
        echo -e "${YELLOW}Please start MAS first:${NC}"
        echo "  - Docker: ./scripts/setup_dev.sh"
        echo "  - Or: docker-compose -f docker-compose.dev.yml up"
        return 1
    fi
}

# Create a simple agent
test_simple_agent() {
    echo -e "\n${BLUE}1. Creating a simple agent...${NC}"
    
    RESPONSE=$(curl -s -X POST "$API_URL/api/v1/agents" \
        -H "Content-Type: application/json" \
        -d '{
            "name": "QuickTestAgent",
            "type": "cognitive",
            "config": {
                "llm_provider": "ollama",
                "model": "qwen3:4b",
                "temperature": 0.7
            }
        }')
    
    AGENT_ID=$(echo $RESPONSE | grep -o '"id":"[^"]*' | cut -d'"' -f4)
    
    if [ -z "$AGENT_ID" ]; then
        echo -e "${RED}Failed to create agent${NC}"
        echo "Response: $RESPONSE"
        return 1
    fi
    
    echo -e "${GREEN}✅ Agent created with ID: $AGENT_ID${NC}"
    
    # Test the agent
    echo -e "\n${BLUE}2. Testing agent with a simple task...${NC}"
    
    TASK_RESPONSE=$(curl -s -X POST "$API_URL/api/v1/agents/$AGENT_ID/execute" \
        -H "Content-Type: application/json" \
        -d '{
            "task": "Write a hello world function in Python",
            "max_tokens": 200
        }')
    
    echo -e "${GREEN}Agent response:${NC}"
    echo "$TASK_RESPONSE" | jq '.' 2>/dev/null || echo "$TASK_RESPONSE"
}

# Create and test a swarm
test_swarm() {
    echo -e "\n${BLUE}3. Creating a development swarm...${NC}"
    
    SWARM_RESPONSE=$(curl -s -X POST "$API_URL/api/v1/swarms" \
        -H "Content-Type: application/json" \
        -d '{
            "name": "QuickDevTeam",
            "agents": [
                {
                    "name": "Designer",
                    "type": "cognitive",
                    "role": "design"
                },
                {
                    "name": "Coder",
                    "type": "cognitive",
                    "role": "implementation"
                },
                {
                    "name": "Tester",
                    "type": "cognitive",
                    "role": "testing"
                }
            ],
            "topology": "mesh"
        }')
    
    SWARM_ID=$(echo $SWARM_RESPONSE | grep -o '"id":"[^"]*' | cut -d'"' -f4)
    
    if [ -z "$SWARM_ID" ]; then
        echo -e "${RED}Failed to create swarm${NC}"
        echo "Response: $SWARM_RESPONSE"
        return 1
    fi
    
    echo -e "${GREEN}✅ Swarm created with ID: $SWARM_ID${NC}"
    
    # Test the swarm
    echo -e "\n${BLUE}4. Testing swarm with a collaborative task...${NC}"
    
    SWARM_TASK_RESPONSE=$(curl -s -X POST "$API_URL/api/v1/swarms/$SWARM_ID/execute" \
        -H "Content-Type: application/json" \
        -d '{
            "task": "Design a simple TODO API with one endpoint",
            "strategy": "collaborative",
            "max_rounds": 3
        }')
    
    echo -e "${GREEN}Swarm response:${NC}"
    echo "$SWARM_TASK_RESPONSE" | jq '.' 2>/dev/null || echo "$SWARM_TASK_RESPONSE"
}

# Interactive mode
interactive_mode() {
    echo -e "\n${BLUE}Interactive Mode${NC}"
    echo "================"
    
    while true; do
        echo -e "\n${YELLOW}Choose an option:${NC}"
        echo "1) Create and test an agent"
        echo "2) Create and test a swarm"
        echo "3) Run Python examples"
        echo "4) View API documentation"
        echo "5) Check system health"
        echo "q) Quit"
        
        read -p "Your choice: " choice
        
        case $choice in
            1)
                test_simple_agent
                ;;
            2)
                test_swarm
                ;;
            3)
                echo -e "${BLUE}Running Python examples...${NC}"
                python3 examples/agent_examples.py
                ;;
            4)
                echo -e "${BLUE}Opening API documentation...${NC}"
                echo "Visit: $API_URL/docs"
                which xdg-open > /dev/null && xdg-open "$API_URL/docs" || echo "Please open $API_URL/docs in your browser"
                ;;
            5)
                echo -e "${BLUE}System Health:${NC}"
                curl -s "$API_URL/health" | jq '.' 2>/dev/null || curl "$API_URL/health"
                ;;
            q|Q)
                echo -e "${GREEN}Goodbye!${NC}"
                exit 0
                ;;
            *)
                echo -e "${RED}Invalid choice${NC}"
                ;;
        esac
    done
}

# Main execution
main() {
    # Check if API is running
    if ! check_api; then
        exit 1
    fi
    
    # Check if running in interactive mode
    if [ "$1" == "--interactive" ] || [ "$1" == "-i" ]; then
        interactive_mode
    else
        # Run all tests
        test_simple_agent
        test_swarm
        
        echo -e "\n${GREEN}Quick start completed!${NC}"
        echo -e "${YELLOW}To run in interactive mode: $0 --interactive${NC}"
        echo -e "${YELLOW}To view more examples: python3 examples/agent_examples.py${NC}"
    fi
}

# Run main
main "$@"