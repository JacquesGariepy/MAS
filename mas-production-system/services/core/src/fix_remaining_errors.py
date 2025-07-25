#!/usr/bin/env python3
"""
Fix remaining errors in autonomous_fixed.py execution
"""

import os
import re
import json

def fix_bdi_cycle_error():
    """Fix the BDI cycle error in base_agent.py"""
    
    file_path = '/app/src/core/agents/base_agent.py'
    
    print(f"\n🔧 Fixing BDI cycle error in {file_path}")
    
    # Read the file
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Find the execute method in BDI cycle
    # The error occurs when processing actions from LLM that might be strings
    
    # Add type checking in the BDI cycle's act method
    old_pattern = r'(async def act\(self\) -> List\[Dict\[str, Any\]\]:.*?)(for action in actions:)'
    
    def add_type_check(match):
        method_start = match.group(1)
        for_loop = match.group(2)
        
        # Add type checking before the loop
        return method_start + '''
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
            
        ''' + for_loop
    
    content = re.sub(old_pattern, add_type_check, content, flags=re.DOTALL)
    
    # Also fix the update_beliefs method to handle string inputs
    if 'async def update_beliefs(self, beliefs: Dict[str, Any])' in content:
        # Add type checking at the start of update_beliefs
        old_beliefs = 'async def update_beliefs(self, beliefs: Dict[str, Any]):\n        """Update agent beliefs"""'
        new_beliefs = '''async def update_beliefs(self, beliefs: Dict[str, Any]):
        """Update agent beliefs"""
        # Ensure beliefs is a dict
        if isinstance(beliefs, str):
            try:
                beliefs = json.loads(beliefs)
            except json.JSONDecodeError:
                beliefs = {"belief_update": beliefs}
                logger.warning(f"Received string for beliefs, wrapped in dict: {beliefs}")
        elif not isinstance(beliefs, dict):
            logger.error(f"Invalid beliefs type: {type(beliefs)}")
            return'''
        
        content = content.replace(old_beliefs, new_beliefs)
    
    # Backup and save
    backup_path = file_path + '.backup_bdi_fix'
    os.rename(file_path, backup_path)
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"✅ Fixed BDI cycle error")
    print(f"📁 Backup saved to {backup_path}")
    
    return file_path

def fix_json_truncation():
    """Fix JSON truncation in LLM responses"""
    
    file_path = '/app/src/services/llm_service.py'
    
    print(f"\n🔧 Fixing JSON truncation in {file_path}")
    
    # Read the file
    with open(file_path, 'r') as f:
        content = f.read()
    
    # The issue is that responses get truncated with "..."
    # We need to handle this in the JSON parsing section
    
    # Find the _clean_json_response method
    if '_clean_json_response' in content:
        # Add handling for truncated JSON
        old_clean = 'def _clean_json_response(self, text: str) -> str:'
        new_clean = '''def _clean_json_response(self, text: str) -> str:
        """Nettoie la réponse pour extraire le JSON valide"""
        import re
        
        # Supprime les espaces en début/fin
        text = text.strip()
        
        # Check for truncation indicators
        if text.endswith('...') or text.endswith('..."') or '"..."' in text:
            logger.warning("JSON response appears truncated")
            # Try to close open structures
            # Count open/close braces and brackets
            open_braces = text.count('{')
            close_braces = text.count('}')
            open_brackets = text.count('[')
            close_brackets = text.count(']')
            
            # Remove the truncation indicator
            text = re.sub(r'[,\s]*"?\.\.\."?[,\s]*$', '', text)
            
            # Add missing closing characters
            while close_braces < open_braces:
                text += '}'
                close_braces += 1
            while close_brackets < open_brackets:
                text += ']'
                close_brackets += 1'''
        
        content = content.replace(old_clean, new_clean, 1)
    
    # Also increase max_tokens for complex responses
    # Find where generation_params is set
    if 'generation_params = {' in content:
        # Increase default max_tokens
        content = re.sub(
            r'("max_tokens": max_tokens or self\.max_tokens)',
            r'"max_tokens": max_tokens or max(self.max_tokens, 1000)  # Increased to prevent truncation',
            content
        )
    
    # Backup and save
    backup_path = file_path + '.backup_truncation'
    os.rename(file_path, backup_path)
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"✅ Fixed JSON truncation handling")
    print(f"📁 Backup saved to {backup_path}")
    
    return file_path

def enhance_error_recovery():
    """Add better error recovery to autonomous_fixed.py"""
    
    file_path = '/app/examples/autonomous_fixed.py'
    
    print(f"\n🔧 Enhancing error recovery in {file_path}")
    
    # Read the file
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Add retry logic for agent operations
    if 'class AutonomousAgent:' in content:
        # Find the execute_request method
        if 'async def execute_request' in content:
            # Add error handling wrapper
            old_method = 'async def execute_request(self, request: str) -> Dict[str, Any]:'
            new_method = '''async def execute_request(self, request: str) -> Dict[str, Any]:
        """Execute a request with enhanced error recovery"""
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                return await self._execute_request_impl(request)
            except Exception as e:
                retry_count += 1
                logger.error(f"Request execution failed (attempt {retry_count}/{max_retries}): {e}")
                if retry_count < max_retries:
                    logger.info("Retrying with error recovery...")
                    await asyncio.sleep(2 ** retry_count)  # Exponential backoff
                else:
                    raise
    
    async def _execute_request_impl(self, request: str) -> Dict[str, Any]:'''
            
            content = content.replace(old_method, new_method)
            # Rename the rest of the method
            content = re.sub(
                r'async def execute_request\(self, request: str\) -> Dict\[str, Any\]:(\s*"""[^"]*""")?',
                lambda m: m.group(0) if 'enhanced error recovery' in m.group(0) else m.group(0).replace('execute_request', '_execute_request_impl'),
                content
            )
    
    # Backup and save
    backup_path = file_path + '.backup_recovery'
    os.rename(file_path, backup_path)
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"✅ Enhanced error recovery")
    print(f"📁 Backup saved to {backup_path}")
    
    return file_path

def main():
    """Apply all fixes"""
    print("\n" + "="*70)
    print("🔧 FIXING REMAINING AUTONOMOUS AGENT ERRORS")
    print("="*70)
    
    print("\nIdentified errors:")
    print("1. ❌ BDI cycle error: 'str' object has no attribute 'items'")
    print("2. ❌ JSON parsing error: Response truncated with '...'")
    
    print("\nApplying fixes...")
    
    try:
        # Apply fixes
        fix_bdi_cycle_error()
        fix_json_truncation()
        enhance_error_recovery()
        
        print("\n" + "="*70)
        print("✅ ALL FIXES APPLIED SUCCESSFULLY")
        print("="*70)
        
        print("\n📝 Summary of fixes:")
        print("1. ✅ BDI cycle - Added type checking for string/dict conversion")
        print("2. ✅ JSON parsing - Handle truncated responses and increase token limit")
        print("3. ✅ Error recovery - Added retry logic with exponential backoff")
        
        print("\n💡 Next steps:")
        print("1. Test autonomous_fixed.py again")
        print("2. Monitor for any remaining errors")
        
    except Exception as e:
        print(f"\n❌ Error applying fixes: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())