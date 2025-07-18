#!/usr/bin/env python3
"""
Test a simple agent to debug the run loop
"""

import asyncio
from asyncio import Queue
import sys
sys.path.append('/app')

from src.utils.logger import get_logger

logger = get_logger(__name__)

class SimpleAgent:
    def __init__(self, name):
        self.name = name
        self._message_queue = Queue()
        self._running = False
        self.messages_processed = 0
        
    async def receive_message(self, message):
        logger.info(f"{self.name}: Received message")
        await self._message_queue.put(message)
        logger.info(f"{self.name}: Queue size = {self._message_queue.qsize()}")
        
    async def run(self):
        logger.info(f"{self.name}: Starting run loop")
        self._running = True
        
        try:
            while self._running:
                logger.debug(f"{self.name}: Loop iteration, queue empty = {self._message_queue.empty()}")
                
                # Process messages
                while not self._message_queue.empty():
                    logger.info(f"{self.name}: Processing message from queue")
                    message = await self._message_queue.get()
                    logger.info(f"{self.name}: Got message: {message}")
                    self.messages_processed += 1
                
                # Small delay
                await asyncio.sleep(0.1)
                
        except Exception as e:
            logger.error(f"{self.name}: Error in run loop: {e}")
        finally:
            logger.info(f"{self.name}: Run loop ended")
            
    async def stop(self):
        logger.info(f"{self.name}: Stopping")
        self._running = False

async def test_simple_agent():
    print("Testing simple agent loop...")
    
    # Create agent
    agent = SimpleAgent("TestAgent")
    
    # Start agent in background
    task = asyncio.create_task(agent.run())
    
    # Wait for startup
    await asyncio.sleep(0.5)
    
    # Send message
    print("\nSending message...")
    await agent.receive_message({"text": "Hello"})
    
    # Check processing
    print("\nWaiting for processing...")
    for i in range(5):
        await asyncio.sleep(0.5)
        print(f"Check {i+1}: Messages processed = {agent.messages_processed}, Queue size = {agent._message_queue.qsize()}")
        if agent.messages_processed > 0:
            print("✅ Message was processed!")
            break
    
    # Stop agent
    await agent.stop()
    await task
    
    print("\nTest completed")

if __name__ == "__main__":
    # Enable debug logging
    import logging
    logging.getLogger("src").setLevel(logging.DEBUG)
    
    asyncio.run(test_simple_agent())