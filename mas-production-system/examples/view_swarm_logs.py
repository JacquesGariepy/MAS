#!/usr/bin/env python3
"""
View Swarm Logs - Utility to parse and display swarm logs in a readable format
"""

import sys
import os
import json
from datetime import datetime
from collections import defaultdict

def parse_llm_log(filename):
    """Parse LLM communications log"""
    print(f"\n📡 LLM Communications from {filename}")
    print("=" * 60)
    
    with open(filename, 'r') as f:
        lines = f.readlines()
    
    current_block = []
    blocks = []
    
    for line in lines:
        if "=== LLM REQUEST ===" in line:
            if current_block:
                blocks.append(current_block)
            current_block = [line]
        else:
            current_block.append(line)
    
    if current_block:
        blocks.append(current_block)
    
    for i, block in enumerate(blocks):
        if any("=== LLM REQUEST ===" in line for line in block):
            print(f"\n🔹 Request #{i+1}")
            agent = None
            prompt = None
            response = None
            
            for j, line in enumerate(block):
                if "Agent:" in line:
                    agent = line.split("Agent:", 1)[1].strip()
                elif "Prompt:" in line:
                    prompt = line.split("Prompt:", 1)[1].strip()
                elif "Response:" in line and j < len(block) - 1:
                    # Try to parse JSON response
                    try:
                        response_text = block[j+1].strip()
                        if response_text.startswith('{'):
                            response = json.loads(response_text)
                    except:
                        response = block[j+1].strip()
            
            if agent:
                print(f"   Agent: {agent}")
            if prompt:
                print(f"   Prompt preview: {prompt[:100]}...")
            if response:
                if isinstance(response, dict):
                    print(f"   Response type: JSON")
                    if 'actions' in response:
                        print(f"   Actions: {len(response['actions'])}")
                else:
                    print(f"   Response preview: {str(response)[:100]}...")

def parse_agent_messages_log(filename):
    """Parse agent messages log"""
    print(f"\n💬 Agent Messages from {filename}")
    print("=" * 60)
    
    with open(filename, 'r') as f:
        lines = f.readlines()
    
    message_count = defaultdict(int)
    message_types = defaultdict(int)
    
    current_message = {}
    for line in lines:
        if "=== MESSAGE RECEIVED ===" in line:
            current_message = {"type": "received"}
        elif "=== MESSAGE SENT ===" in line:
            current_message = {"type": "sent"}
        elif "From:" in line and current_message:
            sender = line.split("From:", 1)[1].strip()
            message_count[f"received_by_{sender}"] += 1
        elif "To:" in line and current_message:
            receiver = line.split("To:", 1)[1].strip()
            message_count[f"sent_to_{receiver}"] += 1
        elif "Type:" in line and current_message:
            msg_type = line.split("Type:", 1)[1].strip()
            message_types[msg_type] += 1
    
    print("\n📊 Message Statistics:")
    for key, count in sorted(message_count.items()):
        print(f"   - {key}: {count}")
    
    print("\n📋 Message Types:")
    for msg_type, count in sorted(message_types.items()):
        print(f"   - {msg_type}: {count}")

def parse_swarm_operations_log(filename):
    """Parse swarm operations log"""
    print(f"\n🐝 Swarm Operations from {filename}")
    print("=" * 60)
    
    with open(filename, 'r') as f:
        lines = f.readlines()
    
    agents_created = []
    phases_executed = []
    errors = []
    
    for line in lines:
        if "Successfully created and started agent:" in line:
            agent = line.split("Successfully created and started agent:", 1)[1].strip()
            agents_created.append(agent)
        elif "Executing phase:" in line:
            phase = line.split("Executing phase:", 1)[1].strip()
            phases_executed.append(phase)
        elif "ERROR" in line or "Error" in line:
            errors.append(line.strip())
    
    print(f"\n✅ Agents Created: {len(agents_created)}")
    for agent in agents_created[:5]:  # Show first 5
        print(f"   - {agent}")
    if len(agents_created) > 5:
        print(f"   ... and {len(agents_created) - 5} more")
    
    print(f"\n📋 Phases Executed: {len(phases_executed)}")
    for phase in phases_executed:
        print(f"   - {phase}")
    
    if errors:
        print(f"\n❌ Errors Found: {len(errors)}")
        for error in errors[:3]:  # Show first 3
            print(f"   - {error[:100]}...")

def find_latest_logs():
    """Find the most recent log files"""
    log_files = {
        'llm': [],
        'agent': [],
        'swarm_ops': [],
        'swarm': []
    }
    
    for f in os.listdir('.'):
        if f.startswith('llm_communications_') and f.endswith('.log'):
            log_files['llm'].append(f)
        elif f.startswith('agent_messages_') and f.endswith('.log'):
            log_files['agent'].append(f)
        elif f.startswith('swarm_operations_') and f.endswith('.log'):
            log_files['swarm_ops'].append(f)
        elif f.startswith('swarm_log_') and f.endswith('.log'):
            log_files['swarm'].append(f)
    
    # Sort by modification time
    for key in log_files:
        log_files[key].sort(key=lambda x: os.path.getmtime(x), reverse=True)
    
    return log_files

def main():
    """Main function"""
    print("\n🔍 SWARM LOG VIEWER")
    print("=" * 60)
    
    # Find log files
    log_files = find_latest_logs()
    
    if not any(log_files.values()):
        print("❌ No log files found. Run the swarm first!")
        return
    
    # Parse latest logs
    if log_files['llm']:
        parse_llm_log(log_files['llm'][0])
    
    if log_files['agent']:
        parse_agent_messages_log(log_files['agent'][0])
    
    if log_files['swarm_ops']:
        parse_swarm_operations_log(log_files['swarm_ops'][0])
    
    # Summary
    print("\n📁 Available Log Files:")
    all_logs = []
    for category, files in log_files.items():
        for f in files:
            size = os.path.getsize(f)
            all_logs.append((f, size))
    
    all_logs.sort()
    for f, size in all_logs:
        print(f"   - {f} ({size:,} bytes)")
    
    print("\n💡 Tip: View individual log files for more details")

if __name__ == "__main__":
    main()