"""
Service de livraison des messages aux agents actifs
"""

import asyncio
import json
from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from src.database.models import Message, Agent
from src.core.agents import get_agent_runtime
from src.utils.logger import get_logger
from src.cache import get as cache_get

logger = get_logger(__name__)


class MessageDeliveryService:
    """Service pour livrer les messages aux agents en cours d'exécution"""
    
    def __init__(self):
        self.runtime = get_agent_runtime()
        self._running = False
        self._delivery_task = None
        
    async def start(self):
        """Démarrer le service de livraison"""
        if self._running:
            logger.warning("Message delivery service already running")
            return
            
        self._running = True
        self._delivery_task = asyncio.create_task(self._delivery_loop())
        logger.info("Message delivery service started")
        
    async def stop(self):
        """Arrêter le service de livraison"""
        self._running = False
        if self._delivery_task:
            self._delivery_task.cancel()
            try:
                await self._delivery_task
            except asyncio.CancelledError:
                pass
        logger.info("Message delivery service stopped")
        
    async def _delivery_loop(self):
        """Boucle principale de livraison des messages"""
        while self._running:
            try:
                # Vérifier les messages dans le cache Redis
                await self._check_cached_messages()
                
                # Petit délai pour éviter de surcharger
                await asyncio.sleep(1.0)
                
            except Exception as e:
                logger.error(f"Error in message delivery loop: {e}")
                await asyncio.sleep(5.0)
                
    async def _check_cached_messages(self):
        """Vérifier et livrer les messages depuis le cache Redis"""
        # Récupérer tous les agents en cours d'exécution
        running_agents = self.runtime.list_running_agents()
        
        for agent_id in running_agents:
            try:
                # Vérifier s'il y a des messages dans le cache pour cet agent
                queue_key = f"agent_message_queue:{agent_id}"
                
                # Récupérer jusqu'à 10 messages à la fois
                for _ in range(10):
                    message_data = await cache_get(queue_key)
                    if not message_data:
                        break
                        
                    # Parser le message
                    try:
                        if isinstance(message_data, str):
                            message = json.loads(message_data)
                        else:
                            message = message_data
                            
                        # Livrer au runtime agent
                        await self.deliver_to_agent(agent_id, message)
                        
                    except json.JSONDecodeError:
                        logger.error(f"Invalid message format for agent {agent_id}")
                        
            except Exception as e:
                logger.error(f"Error processing messages for agent {agent_id}: {e}")
                
    async def deliver_to_agent(self, agent_id: UUID, message_data: dict):
        """Livrer un message à un agent spécifique"""
        agent = self.runtime.get_running_agent(agent_id)
        
        if not agent:
            logger.warning(f"Agent {agent_id} not running, cannot deliver message")
            return False
            
        try:
            # Créer un objet message-like pour l'agent
            class MessageWrapper:
                def __init__(self, data):
                    self.id = data.get('id')
                    self.sender = data.get('sender_id', 'Unknown')
                    self.receiver = data.get('receiver_id')
                    self.performative = data.get('performative', 'inform')
                    self.content = data.get('content', {})
                    self.conversation_id = data.get('conversation_id')
                    self.in_reply_to = data.get('in_reply_to')
                    
            message = MessageWrapper(message_data)
            
            # Appeler receive_message sur l'agent
            await agent.receive_message(message)
            
            logger.info(f"Delivered message to agent {agent_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to deliver message to agent {agent_id}: {e}")
            return False
            
    async def deliver_message_from_db(self, db: AsyncSession, message_id: UUID):
        """Livrer un message spécifique depuis la base de données"""
        # Récupérer le message
        stmt = select(Message).where(Message.id == message_id)
        result = await db.execute(stmt)
        message = result.scalar_one_or_none()
        
        if not message:
            logger.error(f"Message {message_id} not found")
            return False
            
        # Vérifier que l'agent destinataire est en cours d'exécution
        if not await self.runtime.is_agent_running(message.receiver_id):
            logger.warning(f"Receiver agent {message.receiver_id} is not running")
            # Stocker dans le cache pour livraison ultérieure
            queue_key = f"agent_message_queue:{message.receiver_id}"
            message_data = {
                "id": str(message.id),
                "sender_id": str(message.sender_id),
                "receiver_id": str(message.receiver_id),
                "performative": message.performative,
                "content": json.loads(message.content) if isinstance(message.content, str) else message.content,
                "conversation_id": str(message.conversation_id) if message.conversation_id else None,
                "in_reply_to": str(message.in_reply_to) if message.in_reply_to else None
            }
            # await cache_rpush(queue_key, json.dumps(message_data))
            return False
            
        # Livrer directement
        message_data = {
            "id": str(message.id),
            "sender_id": str(message.sender_id),
            "receiver_id": str(message.receiver_id),
            "performative": message.performative,
            "content": json.loads(message.content) if isinstance(message.content, str) else message.content,
            "conversation_id": str(message.conversation_id) if message.conversation_id else None,
            "in_reply_to": str(message.in_reply_to) if message.in_reply_to else None
        }
        
        return await self.deliver_to_agent(message.receiver_id, message_data)


# Instance globale
_delivery_service: Optional[MessageDeliveryService] = None


def get_delivery_service() -> MessageDeliveryService:
    """Obtenir l'instance du service de livraison"""
    global _delivery_service
    if _delivery_service is None:
        _delivery_service = MessageDeliveryService()
    return _delivery_service