#!/usr/bin/env python3
"""
Script to fix errors in swarm_mas_unified.py
"""

import re
from pathlib import Path

def fix_swarm_file():
    """Apply fixes to the swarm_mas_unified.py file"""
    
    file_path = Path("/app/src/swarm_mas_unified.py")
    
    # Read the file
    with open(file_path, 'r') as f:
        content = f.read()
    
    print("Applying fixes...")
    
    # Fix 1: Add comparison methods to VisibilityLevel
    visibility_fix = '''class VisibilityLevel(Enum):
    NONE = 0
    PARTIAL = 1
    FULL = 2
    
    def __ge__(self, other):
        if isinstance(other, VisibilityLevel):
            return self.value >= other.value
        return NotImplemented
    
    def __le__(self, other):
        if isinstance(other, VisibilityLevel):
            return self.value <= other.value
        return NotImplemented
    
    def __gt__(self, other):
        if isinstance(other, VisibilityLevel):
            return self.value > other.value
        return NotImplemented
    
    def __lt__(self, other):
        if isinstance(other, VisibilityLevel):
            return self.value < other.value
        return NotImplemented'''
    
    content = re.sub(
        r'class VisibilityLevel\(Enum\):\s*\n\s*NONE = 0\s*\n\s*PARTIAL = 1\s*\n\s*FULL = 2',
        visibility_fix,
        content
    )
    
    # Fix 2: Add JSON encoder for datetime
    encoder_fix = '''
# Custom JSON encoder for datetime objects
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, timedelta):
            return str(obj)
        if isinstance(obj, uuid4):
            return str(obj)
        if hasattr(obj, '__dict__'):
            return obj.__dict__
        return super().default(obj)

def safe_json_dumps(obj, **kwargs):
    """Safely dump object to JSON with datetime handling"""
    return json.dumps(obj, cls=DateTimeEncoder, **kwargs)
'''
    
    # Insert after imports
    import_end = content.find('# Configure unified logging')
    if import_end > 0:
        content = content[:import_end] + encoder_fix + '\n' + content[import_end:]
    
    # Fix 3: Replace json.dumps with safe_json_dumps
    content = content.replace('json.dumps(', 'safe_json_dumps(')
    
    # Fix 4: Add _load_checkpoint method
    load_checkpoint_method = '''
    async def _load_checkpoint(self):
        """Load checkpoint data if available"""
        checkpoint_file = Path(f"/app/logs/checkpoint_{self.name}.json")
        if checkpoint_file.exists():
            try:
                with open(checkpoint_file, 'r') as f:
                    self.checkpoint_data = json.load(f)
                logger.info(f"✓ Loaded checkpoint from {checkpoint_file}")
            except Exception as e:
                logger.warning(f"Could not load checkpoint: {e}")
                self.checkpoint_data = {}
        else:
            logger.info("No checkpoint found, starting fresh")
            self.checkpoint_data = {}
    
    async def _save_checkpoint(self):
        """Save current state to checkpoint"""
        checkpoint_file = Path(f"/app/logs/checkpoint_{self.name}.json")
        try:
            checkpoint_data = {
                "timestamp": datetime.now().isoformat(),
                "state": self.state.value,
                "agents": len(self.agents),
                "tasks": len(self.task_registry)
            }
            with open(checkpoint_file, 'w') as f:
                json.dump(checkpoint_data, f, indent=2)
            logger.info(f"✓ Saved checkpoint to {checkpoint_file}")
        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}")
'''
    
    # Find where to insert the methods
    init_end = content.find('        logger.info(f"Initialized {self.name} - Unified Swarm Coordinator")')
    if init_end > 0:
        # Find the end of __init__ method
        next_method = content.find('\n    async def', init_end)
        if next_method > 0:
            content = content[:next_method] + load_checkpoint_method + content[next_method:]
    
    # Fix 5: Reduce memory requirements
    content = content.replace('"memory_mb": 32768', '"memory_mb": 8192')  # 32GB -> 8GB
    content = content.replace('"memory_mb": 2048', '"memory_mb": 256')   # 2GB -> 256MB per agent
    
    # Write the fixed file
    fixed_path = Path("/app/src/swarm_mas_unified_patched.py")
    with open(fixed_path, 'w') as f:
        f.write(content)
    
    print(f"✓ Fixed file saved to: {fixed_path}")
    print("\nApplied fixes:")
    print("1. Added comparison methods to VisibilityLevel enum")
    print("2. Added DateTimeEncoder for JSON serialization")  
    print("3. Added _load_checkpoint and _save_checkpoint methods")
    print("4. Reduced memory requirements (32GB -> 8GB total, 2GB -> 256MB per agent)")
    print("5. Replaced json.dumps with safe_json_dumps")

if __name__ == "__main__":
    fix_swarm_file()