#!/usr/bin/env python3
"""
Comprehensive fix for base_agent.py
"""

import os

def fix_base_agent():
    """Completely fix the base_agent.py file"""
    
    file_path = '/app/src/core/agents/base_agent.py'
    
    print(f"🔧 Applying comprehensive fix to {file_path}")
    
    # Read the file
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Fix the BDI cycle method
    # The issue is around line 195-220 where the actions handling is messed up
    
    # First, let's fix the _bdi_cycle method
    fixed_bdi_cycle = '''    async def _bdi_cycle(self):
        """Execute one BDI cycle"""
        try:
            logger.debug(f"Agent {self.name} starting BDI cycle")
            
            # Perceive
            perceptions = await self.perceive(self.context.environment)
            await self.update_beliefs(perceptions)
            
            # Deliberate
            new_intentions = await self.deliberate()
            for intention in new_intentions:
                await self.commit_to_intention(intention)
            
            # Act
            if self.bdi.intentions:
                actions = await self.act()
                
                # Ensure actions is a list
                if isinstance(actions, str):
                    # Try to parse as JSON
                    try:
                        actions = json.loads(actions)
                        if not isinstance(actions, list):
                            actions = [actions]
                    except:
                        # Create action from string
                        actions = [{"type": "execute", "description": actions}]
                elif isinstance(actions, dict):
                    actions = [actions]
                elif not isinstance(actions, list):
                    logger.warning(f"Invalid actions type: {type(actions)}")
                    actions = []
                
                # Execute actions
                for action in actions:
                    await self._execute_action(action)
            
            logger.debug(f"Agent {self.name} completed BDI cycle")
                    
        except Exception as e:
            logger.error(f"Error in BDI cycle for agent {self.name}: {str(e)}")
            self.metrics["errors"] += 1'''
    
    # Replace the broken _bdi_cycle method
    import re
    pattern = r'async def _bdi_cycle\(self\):.*?(?=\n    async def|$)'
    content = re.sub(pattern, fixed_bdi_cycle, content, flags=re.DOTALL)
    
    # Fix the _execute_action method (remove duplicates)
    fixed_execute_action = '''    async def _execute_action(self, action: Dict[str, Any]):
        """Execute a single action"""
        # Ensure action is a dict
        if isinstance(action, str):
            # Try to parse string as action description
            action = {"type": "execute", "description": action}
            logger.warning(f"Received string instead of dict for action, wrapped in dict")
        elif not isinstance(action, dict):
            logger.error(f"Invalid action type: {type(action)}")
            return
        
        # Execute action based on type
        action_type = action.get("type")
        
        if action_type == "tool_call":
            await self._execute_tool_call(action)
        elif action_type == "send_message":
            await self._send_message(action)
        elif action_type == "update_belief":
            await self.update_beliefs(action.get("beliefs", {}))
        else:
            logger.warning(f"Unknown action type: {action_type}")
        
        self.metrics["actions_executed"] += 1'''
    
    # Replace the broken _execute_action method
    pattern = r'async def _execute_action\(self, action: Dict\[str, Any\]\):.*?(?=\n    async def|$)'
    content = re.sub(pattern, fixed_execute_action, content, flags=re.DOTALL)
    
    # Fix the update_beliefs method to handle strings
    if 'async def update_beliefs(self, new_beliefs: Dict[str, Any]):' in content:
        old_update_beliefs = '''async def update_beliefs(self, new_beliefs: Dict[str, Any]):
        """Update agent's beliefs"""
        self.bdi.beliefs.update(new_beliefs)
        logger.debug(f"Agent {self.name} updated beliefs: {new_beliefs}")'''
        
        new_update_beliefs = '''async def update_beliefs(self, new_beliefs: Dict[str, Any]):
        """Update agent's beliefs"""
        # Ensure new_beliefs is a dict
        if isinstance(new_beliefs, str):
            try:
                new_beliefs = json.loads(new_beliefs)
            except json.JSONDecodeError:
                new_beliefs = {"belief_update": new_beliefs}
                logger.warning(f"Received string for beliefs, wrapped in dict")
        elif not isinstance(new_beliefs, dict):
            logger.error(f"Invalid beliefs type: {type(new_beliefs)}")
            return
        
        self.bdi.beliefs.update(new_beliefs)
        logger.debug(f"Agent {self.name} updated beliefs: {new_beliefs}")'''
        
        content = content.replace(old_update_beliefs, new_update_beliefs)
    
    # Write the fixed content
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"✅ Applied comprehensive fix to base_agent.py")
    
    return file_path

if __name__ == "__main__":
    fix_base_agent()
    print("\n✅ Fix complete!")
    print("\nNow try running:")
    print("  docker exec mas-production-system-core-1 python /app/examples/autonomous_fixed.py")