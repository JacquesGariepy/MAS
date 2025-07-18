"""
Version améliorée de CognitiveAgent avec des prompts structurés et sécurisés
"""

import json
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from ...database.models import Agent, Task, Message
from ...schemas.messages import MessageCreate, MessageType
from ...schemas.tasks import TaskStatus
from ...services.llm_service_improved import ImprovedLLMService
from ..templates import build_agent_prompt, get_task_prompt
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

class ImprovedCognitiveAgent(BaseAgent):
    """Agent cognitif amélioré avec gestion robuste des prompts"""
    
    def __init__(self, agent_data: Agent, db: AsyncSession):
        super().__init__(agent_data, db)
        self.agent_type = "cognitive"
        self.llm_service = ImprovedLLMService()
        
        # Configuration améliorée
        self.max_context_size = 2000  # Limite pour éviter les prompts trop longs
        self.max_history_items = 10
        self.json_retry_attempts = 3
        
        # Templates de réponse pour validation
        self.response_schemas = {
            "task_analysis": {
                "can_complete": "boolean",
                "confidence": "float (0-1)",
                "requirements": "list of strings",
                "estimated_steps": "integer",
                "collaboration_needed": "boolean"
            },
            "message_interpretation": {
                "sender_intent": "string",
                "relevance_to_goals": "string",
                "belief_updates": "dict",
                "suggested_response": "dict",
                "priority": "high|medium|low"
            }
        }
    
    async def handle_task(self, task: Task) -> Dict[str, Any]:
        """Gère une tâche avec des prompts améliorés et validation robuste"""
        try:
            # 1. Préparer le contexte de manière sécurisée
            safe_context = self._prepare_safe_context(task)
            
            # 2. Construire le prompt système
            system_prompt = build_agent_prompt(
                agent_name=self.name,
                agent_type="cognitive",
                agent_role=self.capabilities.get("role", "Cognitive Analyst"),
                capabilities=self.capabilities.get("skills", []),
                current_task=task.description[:200],  # Limiter la longueur
                team_members=[],  # À remplir selon le contexte
                active_goals=self.bdi.desires[:3] if hasattr(self, 'bdi') else []
            )
            
            # 3. Construire le prompt utilisateur avec template structuré
            user_prompt = self._build_task_analysis_prompt(task, safe_context)
            
            # 4. Appeler le LLM avec retry et validation
            analysis = await self._get_llm_response_with_validation(
                user_prompt=user_prompt,
                system_prompt=system_prompt,
                expected_schema=self.response_schemas["task_analysis"],
                task_type="complex" if task.priority == "high" else "normal"
            )
            
            # 5. Traiter la réponse et décider de l'action
            if analysis and analysis.get("can_complete", False):
                # Créer un plan d'exécution
                execution_plan = await self._create_execution_plan(task, analysis)
                
                # Mettre à jour les désirs si nécessaire
                if hasattr(self, 'bdi'):
                    self.bdi.desires.append(f"Complete task: {task.id}")
                
                # Retourner le résultat structuré
                return {
                    "status": "accepted",
                    "task_id": task.id,
                    "confidence": analysis.get("confidence", 0.5),
                    "execution_plan": execution_plan,
                    "requirements": analysis.get("requirements", []),
                    "collaboration_needed": analysis.get("collaboration_needed", False)
                }
            else:
                # Tâche ne peut pas être complétée
                return {
                    "status": "rejected",
                    "task_id": task.id,
                    "reason": "Insufficient capabilities or resources",
                    "missing_requirements": analysis.get("requirements", [])
                }
                
        except Exception as e:
            logger.error(f"Error handling task {task.id}: {str(e)}")
            return {
                "status": "error",
                "task_id": task.id,
                "error": str(e)
            }
    
    async def handle_message(self, message: Message) -> Optional[MessageCreate]:
        """Gère un message avec interprétation améliorée et réponse contextuelle"""
        try:
            # 1. Valider et sécuriser le contenu du message
            safe_message_content = self._sanitize_message_content(message)
            
            # 2. Construire le contexte de conversation
            conversation_context = await self._build_conversation_context(message)
            
            # 3. Construire les prompts
            system_prompt = build_agent_prompt(
                agent_name=self.name,
                agent_type="cognitive",
                agent_role=self.capabilities.get("role", "Cognitive Communicator"),
                capabilities=self.capabilities.get("communication_skills", ["analysis", "reasoning"]),
                current_task=self.context.current_task.description if self.context and self.context.current_task else "None",
                team_members=conversation_context.get("participants", []),
                active_goals=self.bdi.intentions[:3] if hasattr(self, 'bdi') else []
            )
            
            user_prompt = self._build_message_interpretation_prompt(
                message=safe_message_content,
                context=conversation_context
            )
            
            # 4. Obtenir l'interprétation du message
            interpretation = await self._get_llm_response_with_validation(
                user_prompt=user_prompt,
                system_prompt=system_prompt,
                expected_schema=self.response_schemas["message_interpretation"],
                task_type="normal"
            )
            
            if not interpretation:
                logger.warning(f"Failed to interpret message from {message.sender}")
                return None
            
            # 5. Mettre à jour les croyances si nécessaire
            if hasattr(self, 'bdi') and interpretation.get("belief_updates"):
                await self._update_beliefs_safely(interpretation["belief_updates"])
            
            # 6. Générer une réponse appropriée
            response_data = interpretation.get("suggested_response", {})
            
            if response_data:
                return MessageCreate(
                    sender=self.id,
                    recipient=message.sender,
                    performative=response_data.get("performative", MessageType.INFORM),
                    content=response_data.get("content", {"acknowledged": True}),
                    conversation_id=message.conversation_id,
                    in_reply_to=message.id,
                    metadata={
                        "confidence": interpretation.get("confidence", 0.5),
                        "intent_understood": interpretation.get("sender_intent", "unclear")
                    }
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error handling message {message.id}: {str(e)}")
            # Réponse d'erreur minimale
            return MessageCreate(
                sender=self.id,
                recipient=message.sender,
                performative=MessageType.FAILURE,
                content={"error": "Failed to process message"},
                conversation_id=message.conversation_id,
                in_reply_to=message.id
            )
    
    def _prepare_safe_context(self, task: Task) -> Dict[str, Any]:
        """Prépare un contexte sécurisé et limité en taille pour les prompts"""
        context = {
            "task_type": task.task_type,
            "priority": task.priority,
            "created_at": task.created_at.isoformat() if task.created_at else None
        }
        
        # Limiter les métadonnées
        if task.metadata:
            safe_metadata = {}
            for key, value in task.metadata.items():
                if isinstance(value, (str, int, float, bool)):
                    safe_metadata[key] = value
                elif isinstance(value, list) and len(value) < 10:
                    safe_metadata[key] = value[:10]
            context["metadata"] = safe_metadata
        
        # Ajouter le contexte de l'agent
        context["agent_capabilities"] = list(self.capabilities.get("skills", []))[:10]
        context["current_workload"] = getattr(self, "active_tasks_count", 0)
        
        return context
    
    def _sanitize_message_content(self, message: Message) -> Dict[str, Any]:
        """Nettoie et limite le contenu du message pour éviter les injections"""
        return {
            "sender": str(message.sender)[:100],
            "performative": str(message.performative),
            "content": self._truncate_content(message.content, max_size=500),
            "timestamp": message.created_at.isoformat() if message.created_at else None
        }
    
    def _truncate_content(self, content: Any, max_size: int = 500) -> Any:
        """Tronque le contenu pour respecter les limites de taille"""
        if isinstance(content, str):
            return content[:max_size] + "..." if len(content) > max_size else content
        elif isinstance(content, dict):
            truncated = {}
            current_size = 0
            for key, value in content.items():
                key_str = str(key)[:50]
                value_str = str(value)[:200]
                if current_size + len(key_str) + len(value_str) < max_size:
                    truncated[key_str] = value_str
                    current_size += len(key_str) + len(value_str)
                else:
                    break
            return truncated
        else:
            return str(content)[:max_size]
    
    async def _build_conversation_context(self, message: Message) -> Dict[str, Any]:
        """Construit le contexte de conversation de manière sécurisée"""
        context = {
            "conversation_id": message.conversation_id,
            "message_count": 1,  # À implémenter: compter les messages dans la conversation
            "participants": []  # À implémenter: lister les participants
        }
        
        # Ajouter l'historique récent si disponible
        if hasattr(self, 'conversation_history'):
            recent_messages = self.conversation_history.get(message.conversation_id, [])[-5:]
            context["recent_exchanges"] = [
                {
                    "sender": msg.get("sender", "unknown"),
                    "type": msg.get("performative", "unknown"),
                    "summary": str(msg.get("content", ""))[:100]
                }
                for msg in recent_messages
            ]
        
        return context
    
    def _build_task_analysis_prompt(self, task: Task, context: Dict[str, Any]) -> str:
        """Construit un prompt structuré pour l'analyse de tâche"""
        return f"""Analyze the following task assignment:

Task Information:
- ID: {task.id}
- Type: {task.task_type}
- Priority: {task.priority}
- Description: {task.description[:500]}

Context:
- Your capabilities: {json.dumps(context.get('agent_capabilities', []))}
- Current workload: {context.get('current_workload', 0)} active tasks
- Task metadata: {json.dumps(context.get('metadata', {}), indent=2)}

Please analyze this task and provide a response in the following JSON format:
{{
    "can_complete": true/false,
    "confidence": 0.0-1.0,
    "requirements": ["list", "of", "requirements"],
    "estimated_steps": number,
    "collaboration_needed": true/false,
    "reasoning": "Brief explanation of your analysis"
}}

Consider:
1. Do you have the necessary capabilities?
2. What resources or tools would be needed?
3. Is the task within your current capacity?
4. Would collaboration improve the outcome?"""
    
    def _build_message_interpretation_prompt(self, message: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Construit un prompt structuré pour l'interprétation de message"""
        return f"""Interpret the following message in context:

Message Details:
- From: {message['sender']}
- Type: {message['performative']}
- Content: {json.dumps(message['content'], indent=2)}
- Time: {message.get('timestamp', 'unknown')}

Conversation Context:
- Conversation ID: {context.get('conversation_id', 'unknown')}
- Participants: {json.dumps(context.get('participants', []))}
- Recent exchanges: {json.dumps(context.get('recent_exchanges', []), indent=2)}

Current State:
- Active goals: {json.dumps(getattr(self, 'bdi', {}).get('intentions', [])[:3])}
- Current task: {self.context.current_task.id if self.context and self.context.current_task else 'None'}

Provide your interpretation in the following JSON format:
{{
    "sender_intent": "What is the sender trying to achieve?",
    "relevance_to_goals": "How does this relate to your current goals?",
    "belief_updates": {{"key": "value updates for your belief system"}},
    "suggested_response": {{
        "performative": "inform/request/propose/etc",
        "content": {{"your": "response content"}}
    }},
    "priority": "high/medium/low",
    "confidence": 0.0-1.0
}}"""
    
    async def _get_llm_response_with_validation(
        self, 
        user_prompt: str, 
        system_prompt: str,
        expected_schema: Dict[str, str],
        task_type: str = "normal"
    ) -> Optional[Dict[str, Any]]:
        """Obtient une réponse du LLM avec validation et retry"""
        
        for attempt in range(self.json_retry_attempts):
            try:
                # Ajouter le schéma attendu au prompt si c'est un retry
                if attempt > 0:
                    user_prompt += f"\n\nIMPORTANT: Please ensure your response follows this exact schema:\n{json.dumps(expected_schema, indent=2)}"
                
                # Appeler le service LLM
                response = await self.llm_service.generate(
                    prompt=user_prompt,
                    system_prompt=system_prompt,
                    json_response=True,
                    task_type=task_type,
                    temperature=0.3,  # Basse température pour plus de cohérence
                    stream=True
                )
                
                if response.get("success") and response.get("response"):
                    # Valider la structure de la réponse
                    validated_response = self._validate_response_structure(
                        response["response"], 
                        expected_schema
                    )
                    if validated_response:
                        return validated_response
                    else:
                        logger.warning(f"Response validation failed on attempt {attempt + 1}")
                else:
                    # Utiliser la réponse de fallback si disponible
                    if response.get("fallback_response"):
                        return response["fallback_response"]
                        
            except Exception as e:
                logger.error(f"LLM call failed on attempt {attempt + 1}: {str(e)}")
                
            # Attendre avant de réessayer
            if attempt < self.json_retry_attempts - 1:
                await asyncio.sleep(2 ** attempt)  # Backoff exponentiel
        
        # Retourner None si tous les essais ont échoué
        logger.error("All LLM response attempts failed")
        return None
    
    def _validate_response_structure(self, response: Dict[str, Any], schema: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """Valide que la réponse correspond au schéma attendu"""
        try:
            # Vérifier les clés requises
            for key in schema:
                if key not in response:
                    logger.warning(f"Missing required key: {key}")
                    return None
            
            # Valider les types basiques
            for key, expected_type in schema.items():
                if key in response:
                    value = response[key]
                    if "boolean" in expected_type and not isinstance(value, bool):
                        response[key] = bool(value)
                    elif "float" in expected_type and not isinstance(value, (int, float)):
                        response[key] = float(value)
                    elif "integer" in expected_type and not isinstance(value, int):
                        response[key] = int(value)
                    elif "list" in expected_type and not isinstance(value, list):
                        response[key] = [value] if value else []
            
            return response
            
        except Exception as e:
            logger.error(f"Response validation error: {str(e)}")
            return None
    
    async def _update_beliefs_safely(self, belief_updates: Dict[str, Any]):
        """Met à jour les croyances de manière sécurisée"""
        if not hasattr(self, 'bdi') or not hasattr(self.bdi, 'beliefs'):
            return
        
        for key, value in belief_updates.items():
            # Limiter la taille des clés et valeurs
            safe_key = str(key)[:50]
            safe_value = self._truncate_content(value, max_size=200)
            
            # Mettre à jour seulement si c'est sûr
            if isinstance(safe_value, (str, int, float, bool, list, dict)):
                self.bdi.beliefs[safe_key] = safe_value
                logger.debug(f"Updated belief: {safe_key}")
    
    async def _create_execution_plan(self, task: Task, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Crée un plan d'exécution basé sur l'analyse de la tâche"""
        steps = []
        estimated_steps = analysis.get("estimated_steps", 3)
        
        # Créer des étapes basiques basées sur l'analyse
        if analysis.get("collaboration_needed"):
            steps.append({
                "step": 1,
                "action": "request_collaboration",
                "description": "Request assistance from specialized agents",
                "estimated_duration": "5m"
            })
        
        for i in range(min(estimated_steps, 10)):  # Limiter à 10 étapes
            steps.append({
                "step": len(steps) + 1,
                "action": "process_subtask",
                "description": f"Execute subtask {i+1} of the main task",
                "estimated_duration": "10m"
            })
        
        steps.append({
            "step": len(steps) + 1,
            "action": "validate_results",
            "description": "Validate the task completion and results",
            "estimated_duration": "5m"
        })
        
        return steps