#!/usr/bin/env python3
"""
Test simple LMStudio connection
"""

import asyncio
import httpx

async def test_lmstudio():
    """Test LMStudio directly"""
    url = "http://host.docker.internal:1234/v1/chat/completions"
    
    print("Testing LMStudio connection...")
    print(f"URL: {url}")
    
    payload = {
        "model": "phi-4-mini-reasoning",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say hello"}
        ],
        "temperature": 0.7,
        "max_tokens": 50
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, timeout=30)
            print(f"\nStatus: {response.status_code}")
            print(f"Response: {response.text}")
            
            if response.status_code == 200:
                data = response.json()
                if 'choices' in data and data['choices']:
                    content = data['choices'][0]['message']['content']
                    print(f"\n✅ LMStudio responded: {content}")
                else:
                    print("❌ No choices in response")
            else:
                print(f"❌ Error: {response.status_code}")
                
    except httpx.ConnectError as e:
        print(f"\n❌ Connection error: {e}")
        print("Make sure LMStudio is running on port 1234")
    except Exception as e:
        print(f"\n❌ Error: {type(e).__name__}: {e}")

if __name__ == "__main__":
    asyncio.run(test_lmstudio())