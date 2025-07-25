#!/usr/bin/env python3
"""
Production Swarm Demo with Request Processing
Demonstrates all capabilities from autonomous_fixed.py in the swarm
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the enhanced swarm
from src.swarm_mas_production_enhanced import EnhancedSwarmCoordinator, SwarmConfig

async def main():
    """Main demonstration"""
    print("\n" + "="*80)
    print("🚀 PRODUCTION SWARM WITH AUTONOMOUS CAPABILITIES")
    print("All features from autonomous_fixed.py integrated")
    print("="*80 + "\n")
    
    # Create configuration
    config = SwarmConfig(
        name="ProductionDemo",
        num_analysts=2,
        num_developers=3,
        num_validators=2,
        num_architects=1,
        num_testers=2,
        max_agents=12,
        enable_decomposition=True,
        enable_validation=True,
        max_decomposition_depth=2,
        default_project_structure=True
    )
    
    # Create and initialize swarm
    print("🔧 Initializing production swarm...")
    swarm = EnhancedSwarmCoordinator(config)
    await swarm.initialize()
    
    # Get initial status
    status = await swarm.get_status()
    print(f"✅ Swarm initialized with {status['agents']['total']} agents")
    print(f"   - Analysts: {config.num_analysts}")
    print(f"   - Developers: {config.num_developers}")
    print(f"   - Validators: {config.num_validators}")
    print(f"   - Architects: {config.num_architects}")
    print(f"   - Testers: {config.num_testers}")
    
    # Example requests
    requests = [
        {
            'name': "REST API Development",
            'request': "Create a REST API with user authentication, PostgreSQL database integration, JWT tokens, and comprehensive test coverage. Include user CRUD operations, password reset functionality, and role-based access control."
        },
        {
            'name': "Data Processing Pipeline",
            'request': "Build a data processing pipeline that ingests CSV files, validates data, transforms it according to business rules, and stores results in a database. Include error handling, logging, and performance monitoring."
        },
        {
            'name': "Web Application",
            'request': "Create a web application with React frontend and Python backend. Include user registration, login, dashboard with charts, and real-time notifications using WebSockets."
        }
    ]
    
    print(f"\n📋 Processing {len(requests)} complex requests...")
    
    # Process each request
    results = []
    for i, req in enumerate(requests):
        print(f"\n{'='*60}")
        print(f"📌 Request {i+1}: {req['name']}")
        print(f"{'='*60}")
        
        try:
            # Process the request through the full pipeline
            result = await swarm.process_request(req['request'])
            results.append(result)
            
            # Show results
            print(f"\n✅ Processing complete!")
            print(f"  - Success: {result['success']}")
            print(f"  - Project Path: {result.get('project_path', 'N/A')}")
            print(f"  - Tasks Created: {result['metrics']['tasks_created']}")
            print(f"  - Tasks Completed: {result['metrics']['tasks_completed']}")
            print(f"  - Validation Score: {result['metrics']['validation_score']:.1f}%")
            print(f"  - Duration: {result['metrics']['duration']:.1f}s")
            
            # Show some files created
            if result.get('project_path'):
                project_path = Path(result['project_path'])
                if project_path.exists():
                    files = list(project_path.rglob("*"))[:10]  # First 10 files
                    if files:
                        print(f"\n📁 Files created:")
                        for file in files:
                            if file.is_file():
                                print(f"    - {file.relative_to(project_path)}")
                                
        except Exception as e:
            print(f"\n❌ Error processing request: {e}")
            import traceback
            traceback.print_exc()
            
    # Final summary
    print(f"\n{'='*80}")
    print("📊 FINAL SUMMARY")
    print(f"{'='*80}")
    
    final_status = await swarm.get_status()
    
    print(f"\n🔧 Swarm Performance:")
    print(f"  - Total Tasks: {final_status['tasks']['total']}")
    print(f"  - Completed: {final_status['tasks']['completed']}")
    print(f"  - Failed: {final_status['tasks']['failed']}")
    print(f"  - Decomposed: {final_status['tasks']['decomposed']}")
    print(f"  - Average Validation: {final_status['validation']['average_score']:.1f}%")
    
    print(f"\n👥 Agent Activity:")
    print(f"  - Active Agents: {final_status['agents']['active']}")
    print(f"  - Busy Agents: {final_status['agents']['busy']}")
    print(f"  - Idle Agents: {final_status['agents']['idle']}")
    
    print(f"\n⚡ System Metrics:")
    print(f"  - Uptime: {final_status['uptime']:.1f}s")
    print(f"  - Coordination Cycles: {final_status['performance']['coordination_cycles']}")
    print(f"  - Messages Sent: {final_status['performance']['messages_sent']}")
    print(f"  - CPU Usage: {final_status['system']['cpu_percent']:.1f}%")
    print(f"  - Memory Usage: {final_status['system']['memory_percent']:.1f}%")
    
    # Calculate success rate
    successful = sum(1 for r in results if r.get('success', False))
    success_rate = (successful / len(results)) * 100 if results else 0
    
    print(f"\n🎯 Overall Success Rate: {success_rate:.1f}% ({successful}/{len(results)})")
    
    # Shutdown
    print(f"\n👋 Shutting down swarm...")
    await swarm.shutdown()
    print("✅ Demo complete!")
    

if __name__ == "__main__":
    # Run the demo
    asyncio.run(main())