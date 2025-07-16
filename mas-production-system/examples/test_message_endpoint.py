"""
Example script to test the message sending endpoint
"""

import asyncio
import httpx
from uuid import uuid4

# Configuration
API_BASE_URL = "http://localhost:8000/api/v1"
AUTH_TOKEN = "your-auth-token-here"  # Replace with actual token

# Example agent IDs (replace with actual IDs from your system)
SENDER_AGENT_ID = "123e4567-e89b-12d3-a456-426614174000"
RECEIVER_AGENT_ID = "550e8400-e29b-41d4-a716-446655440000"


async def send_message():
    """Test sending a message between agents"""
    
    # Create conversation ID
    conversation_id = str(uuid4())
    
    # Message data
    message_data = {
        "receiver_id": RECEIVER_AGENT_ID,
        "performative": "request",
        "content": {
            "action": "analyze_data",
            "params": {
                "dataset": "sales_2024",
                "metrics": ["revenue", "growth", "trends"]
            }
        },
        "conversation_id": conversation_id
    }
    
    # Send message
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {AUTH_TOKEN}"}
        
        # Send the message
        response = await client.post(
            f"{API_BASE_URL}/agents/{SENDER_AGENT_ID}/messages",
            json=message_data,
            headers=headers
        )
        
        if response.status_code == 201:
            result = response.json()
            print("Message sent successfully!")
            print(f"Message ID: {result['id']}")
            print(f"Conversation ID: {result['conversation_id']}")
            print(f"Performative: {result['performative']}")
            
            # Send a follow-up inform message
            inform_data = {
                "receiver_id": RECEIVER_AGENT_ID,
                "performative": "inform",
                "content": {
                    "status": "acknowledged",
                    "message": "Request received and being processed"
                },
                "conversation_id": conversation_id,
                "in_reply_to": result['id']
            }
            
            response2 = await client.post(
                f"{API_BASE_URL}/agents/{SENDER_AGENT_ID}/messages",
                json=inform_data,
                headers=headers
            )
            
            if response2.status_code == 201:
                print("\nFollow-up message sent!")
        else:
            print(f"Error: {response.status_code}")
            print(response.json())


async def get_messages():
    """Test retrieving messages for an agent"""
    
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {AUTH_TOKEN}"}
        
        # Get received messages
        response = await client.get(
            f"{API_BASE_URL}/agents/{RECEIVER_AGENT_ID}/messages",
            params={"message_type": "received", "per_page": 10},
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"\nReceived messages for agent {RECEIVER_AGENT_ID}:")
            print(f"Total: {result['total']}")
            
            for msg in result['items']:
                print(f"\n- Message ID: {msg['id']}")
                print(f"  From: {msg['sender_id']}")
                print(f"  Performative: {msg['performative']}")
                print(f"  Content: {msg['content']}")
                print(f"  Read: {msg['is_read']}")
                print(f"  Created: {msg['created_at']}")
                
                # Mark as read
                if not msg['is_read']:
                    read_response = await client.patch(
                        f"{API_BASE_URL}/agents/{RECEIVER_AGENT_ID}/messages/{msg['id']}/read",
                        headers=headers
                    )
                    if read_response.status_code == 200:
                        print(f"  ✓ Marked as read")
        else:
            print(f"Error getting messages: {response.status_code}")
            print(response.json())


async def main():
    """Run the tests"""
    print("Testing Agent Message Endpoints")
    print("=" * 50)
    
    # Send messages
    await send_message()
    
    # Wait a bit
    await asyncio.sleep(1)
    
    # Get messages
    await get_messages()


if __name__ == "__main__":
    asyncio.run(main())