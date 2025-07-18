#!/usr/bin/env python3
"""
Run autonomous agent with the fixed LLM service
This script ensures the JSON parsing fix is applied before running
"""

import subprocess
import sys
import os
import time

def check_docker_services():
    """Check if Docker services are running"""
    try:
        result = subprocess.run(
            ["docker-compose", "-f", "docker-compose.dev.yml", "ps"],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(__file__))
        )
        return "core" in result.stdout and "Up" in result.stdout
    except:
        return False

def restart_core_service():
    """Restart the core service to ensure latest code is loaded"""
    print("🔄 Restarting core service to apply LLM fix...")
    try:
        subprocess.run(
            ["docker-compose", "-f", "docker-compose.dev.yml", "restart", "core"],
            cwd=os.path.dirname(os.path.dirname(__file__))
        )
        print("⏳ Waiting for service to be ready...")
        time.sleep(10)
        print("✅ Core service restarted")
        return True
    except Exception as e:
        print(f"❌ Failed to restart service: {e}")
        return False

def run_autonomous_agent():
    """Run the autonomous agent inside Docker"""
    print("\n🚀 Running autonomous agent with fixed LLM service...")
    print("=" * 60)
    
    cmd = [
        "docker-compose", "-f", "docker-compose.dev.yml", 
        "exec", "core", 
        "python", "/app/examples/autonomous.py"
    ]
    
    if len(sys.argv) > 1:
        # Pass any additional arguments
        cmd.extend(sys.argv[1:])
    
    try:
        subprocess.run(cmd, cwd=os.path.dirname(os.path.dirname(__file__)))
    except KeyboardInterrupt:
        print("\n\n👋 Agent stopped by user")
    except Exception as e:
        print(f"\n❌ Error running agent: {e}")

def main():
    print("🔧 Autonomous Agent Runner (with LLM Fix)")
    print("=" * 60)
    
    # Check if Docker services are running
    if not check_docker_services():
        print("❌ Docker services not running. Please start them first:")
        print("   cd mas-production-system")
        print("   docker-compose -f docker-compose.dev.yml up -d")
        return 1
    
    # Ask if user wants to restart service
    response = input("\n🔄 Restart core service to ensure fix is applied? (y/n): ")
    if response.lower() == 'y':
        if not restart_core_service():
            return 1
    
    # Run the autonomous agent
    run_autonomous_agent()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())