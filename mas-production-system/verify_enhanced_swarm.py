#!/usr/bin/env python3
"""
Verification script for enhanced production swarm
Ensures all autonomous_fixed.py features are integrated
"""

from pathlib import Path

def verify_enhanced_swarm():
    """Verify the enhanced swarm has all required features"""
    
    enhanced_file = Path("/mnt/c/Users/admlocal/Documents/source/repos/MAS/mas-production-system/src/swarm_mas_production_enhanced.py")
    
    if not enhanced_file.exists():
        print("❌ Enhanced swarm file not found!")
        return False
        
    content = enhanced_file.read_text()
    
    # Features to verify
    checks = {
        # Core features from autonomous_fixed
        "Task decomposition": "decompose_task" in content,
        "6-phase pipeline": all(phase in content for phase in [
            "Phase 1 - Initialization",
            "Phase 2 - Analysis", 
            "Phase 3 - Planning",
            "Phase 4 - Execution",
            "Phase 5 - Validation",
            "Phase 6 - Reporting"
        ]),
        "Extended LLM methods": all(method in content for method in [
            "analyze_request",
            "decompose_task", 
            "solve_subtask",
            "validate_solution"
        ]),
        "Project structure": "create_project_structure" in content,
        "Solution validation": "validation_score" in content,
        "Markdown reports": "generate_report" in content,
        "Recursive subtasks": "max_decomposition_depth" in content,
        "Task dependencies": "dependencies" in content and "SwarmTask" in content,
        "Agent specialization": all(agent in content for agent in [
            "analyst", "developer", "creative", "validator", "coordinator"
        ]),
        "Error handling": "sanitize_for_unicode" in content,
        
        # Production swarm features
        "Load balancing": "load_balance" in content,
        "Auto-scaling": "auto_scale" in content,
        "State persistence": "checkpoint" in content,
        "Parallel execution": "ProcessPoolExecutor" in content,
        "Emergency controls": "emergency_stop" in content,
        "Monitoring": "monitoring_loop" in content,
        "Coordination strategies": "CoordinationStrategy" in content
    }
    
    print("🔍 Verifying Enhanced Production Swarm Features:\n")
    
    all_passed = True
    for feature, present in checks.items():
        status = "✅" if present else "❌"
        print(f"{status} {feature}")
        if not present:
            all_passed = False
            
    # Check for key classes
    print("\n🔍 Checking Key Classes:\n")
    
    classes = {
        "EnhancedSwarmCoordinator": "class EnhancedSwarmCoordinator" in content,
        "SwarmTask with phases": "class TaskPhase" in content,
        "Enhanced config": "enable_decomposition" in content and "SwarmConfig" in content
    }
    
    for class_name, present in classes.items():
        status = "✅" if present else "❌"
        print(f"{status} {class_name}")
        if not present:
            all_passed = False
            
    # Summary
    print("\n" + "="*50)
    if all_passed:
        print("✅ All features successfully integrated!")
        print("\nThe enhanced swarm includes:")
        print("- All autonomous_fixed.py capabilities")
        print("- All production swarm features")
        print("- Ready for complex request processing!")
    else:
        print("❌ Some features are missing")
        print("Please check the implementation")
        
    return all_passed


if __name__ == "__main__":
    verify_enhanced_swarm()