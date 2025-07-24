#!/usr/bin/env python3
"""
Test autonomous agent with new software environment integration
"""

import asyncio
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'services', 'core'))

from examples.autonomous_fixed import AutonomousAgent
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/app/logs/autonomous_test.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

async def test_with_predefined_request():
    """Test autonomous agent with a predefined request"""
    
    print("\n" + "="*80)
    print("🤖 TESTING AUTONOMOUS AGENT WITH SOFTWARE ENVIRONMENT")
    print("="*80)
    
    # Create autonomous agent
    agent = AutonomousAgent()
    
    # Predefined test request
    test_request = "Create a simple Python function that calculates factorial and write unit tests for it"
    
    print(f"\n📝 Test Request: {test_request}")
    print("-" * 80)
    
    try:
        # Process the request
        result = await agent.process_request(test_request)
        
        print("\n✅ Request completed successfully!")
        print("\n📊 Summary:")
        print(f"- Total tasks: {result.get('total_tasks', 0)}")
        print(f"- Completed: {result.get('completed', 0)}")
        print(f"- Success rate: {result.get('success_rate', 0):.1f}%")
        
        if result.get('artifacts'):
            print("\n📁 Created artifacts:")
            for artifact in result['artifacts']:
                print(f"  - {artifact}")
                
    except Exception as e:
        logger.error(f"Error processing request: {e}", exc_info=True)
        print(f"\n❌ Error: {str(e)}")
        
    finally:
        # Cleanup
        await agent.cleanup()
        print("\n✅ Agent cleanup complete")

async def test_environment_integration():
    """Test if the new environment is properly integrated"""
    
    print("\n" + "="*80)
    print("🔧 TESTING ENVIRONMENT INTEGRATION")
    print("="*80)
    
    try:
        # Try to import the environment module
        from src.core.environment import SoftwareEnvironment, EnvironmentAdapter
        print("✓ Environment modules imported successfully")
        
        # Create a simple environment
        env = SoftwareEnvironment()
        print("✓ Software environment created")
        
        # Create adapter
        adapter = EnvironmentAdapter(env)
        print("✓ Environment adapter created")
        
        print("\n✅ Environment integration test passed!")
        
    except ImportError as e:
        print(f"\n⚠️ Environment not fully integrated: {e}")
        print("The autonomous agent will work with minimal environment")
    except Exception as e:
        print(f"\n❌ Environment integration error: {e}")

async def main():
    """Main test function"""
    
    # First test environment integration
    await test_environment_integration()
    
    # Then test autonomous agent
    await test_with_predefined_request()

if __name__ == "__main__":
    print("🚀 Starting Autonomous Agent Test...")
    asyncio.run(main())