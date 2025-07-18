"""
Service LLM amélioré avec meilleure gestion des timeouts et des erreurs
"""

import asyncio
import json
import logging
from typing import Optional, Dict, Any, List
from openai import AsyncOpenAI
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from ..config import settings

logger = logging.getLogger(__name__)

class ImprovedLLMService:
    """Service LLM amélioré avec gestion robuste des timeouts et du streaming"""
    
    # Configuration des timeouts selon le type de tâche
    TIMEOUT_CONFIG = {
        'simple': 60,      # 1 minute pour les tâches simples
        'normal': 120,     # 2 minutes pour les tâches normales
        'complex': 300,    # 5 minutes pour les tâches complexes
        'reasoning': 600,  # 10 minutes pour les tâches de raisonnement
        'default': 180     # 3 minutes par défaut
    }
    
    # Modèles qui nécessitent plus de temps de réflexion
    THINKING_MODELS = ['o1-preview', 'o1-mini', 'phi-4-mini-reasoning']
    
    def __init__(self):
        """Initialize the improved LLM service"""
        self.api_key = settings.OPENAI_API_KEY
        self.model = settings.OPENAI_MODEL
        self.max_tokens = settings.MAX_TOKENS
        
        # Client avec timeout adaptatif
        self.timeout = httpx.Timeout(
            connect=30.0,
            read=600.0,    # 10 minutes pour la lecture
            write=30.0,
            pool=30.0
        )
        
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            timeout=self.timeout
        )
        
        logger.info(f"Improved LLM Service initialized with model: {self.model}")
    
    def _get_timeout_for_task(self, task_type: str = 'default', 
                             model: Optional[str] = None) -> int:
        """Détermine le timeout approprié selon le type de tâche et le modèle"""
        if model and model in self.THINKING_MODELS:
            return self.TIMEOUT_CONFIG.get('reasoning', 600)
        return self.TIMEOUT_CONFIG.get(task_type, self.TIMEOUT_CONFIG['default'])
    
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=2, min=10, max=60)
    )
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        json_response: bool = True,
        task_type: str = 'normal',
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        Génère une réponse avec gestion améliorée des timeouts et du streaming
        
        Args:
            prompt: Le prompt utilisateur
            system_prompt: Le prompt système (optionnel)
            temperature: Température de génération
            max_tokens: Nombre maximum de tokens
            json_response: Si True, force une réponse JSON valide
            task_type: Type de tâche pour ajuster le timeout
            stream: Si True, utilise le streaming pour éviter les timeouts
        
        Returns:
            Dictionnaire contenant la réponse
        """
        try:
            messages = []
            
            # Ajout du prompt système avec contexte clair
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            else:
                # Prompt système par défaut pour assurer la cohérence
                messages.append({
                    "role": "system", 
                    "content": "You are a helpful AI assistant. Always provide clear, structured responses."
                })
            
            # Construction du prompt utilisateur
            user_content = prompt
            if json_response:
                user_content += "\n\nIMPORTANT: Respond with valid JSON only. Do not include any text before or after the JSON object."
            
            messages.append({"role": "user", "content": user_content})
            
            # Configuration de la requête
            timeout = self._get_timeout_for_task(task_type, self.model)
            logger.info(f"Generating response with timeout: {timeout}s, stream: {stream}")
            
            # Paramètres de génération
            generation_params = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens or self.max_tokens,
                "timeout": timeout
            }
            
            # Ajout du mode JSON si supporté
            if json_response and self.model in ['gpt-4-1106-preview', 'gpt-3.5-turbo-1106']:
                generation_params["response_format"] = {"type": "json_object"}
            
            # Génération avec ou sans streaming
            if stream:
                response_text = await self._generate_streaming(generation_params)
            else:
                response = await self.client.chat.completions.create(**generation_params)
                response_text = response.choices[0].message.content
            
            logger.info(f"Generated response length: {len(response_text)} characters")
            
            # Validation et parsing de la réponse JSON si nécessaire
            if json_response:
                try:
                    # Nettoyage de la réponse
                    cleaned_text = self._clean_json_response(response_text)
                    parsed_response = json.loads(cleaned_text)
                    return {
                        "success": True,
                        "response": parsed_response,
                        "raw_text": response_text
                    }
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON response: {e}")
                    logger.error(f"Raw response: {response_text[:500]}...")
                    
                    # Tentative de récupération
                    return {
                        "success": False,
                        "error": "Invalid JSON response",
                        "raw_text": response_text,
                        "fallback_response": self._create_fallback_response(prompt)
                    }
            
            return {
                "success": True,
                "response": response_text
            }
            
        except asyncio.TimeoutError:
            logger.error(f"Timeout after {timeout}s for task type: {task_type}")
            return {
                "success": False,
                "error": f"Request timeout after {timeout} seconds",
                "fallback_response": self._create_fallback_response(prompt)
            }
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "fallback_response": self._create_fallback_response(prompt)
            }
    
    async def _generate_streaming(self, params: Dict[str, Any]) -> str:
        """Génère une réponse en mode streaming pour éviter les timeouts"""
        params['stream'] = True
        params.pop('timeout', None)  # Le timeout est géré différemment en streaming
        
        response_text = ""
        try:
            stream = await self.client.chat.completions.create(**params)
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    response_text += chunk.choices[0].delta.content
                    
                    # Log périodique pour montrer la progression
                    if len(response_text) % 500 == 0:
                        logger.debug(f"Streaming progress: {len(response_text)} characters")
            
            return response_text
            
        except Exception as e:
            logger.error(f"Streaming error: {str(e)}")
            raise
    
    def _clean_json_response(self, text: str) -> str:
        """Nettoie la réponse pour extraire le JSON valide"""
        # Supprime les espaces en début/fin
        text = text.strip()
        
        # Recherche du premier { et du dernier }
        start_idx = text.find('{')
        end_idx = text.rfind('}')
        
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            return text[start_idx:end_idx + 1]
        
        # Si c'est un tableau JSON
        start_idx = text.find('[')
        end_idx = text.rfind(']')
        
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            return text[start_idx:end_idx + 1]
        
        return text
    
    def _create_fallback_response(self, prompt: str) -> Dict[str, Any]:
        """Crée une réponse de fallback en cas d'erreur"""
        return {
            "status": "fallback",
            "message": "Unable to generate proper response",
            "original_prompt": prompt[:200] + "..." if len(prompt) > 200 else prompt,
            "suggestions": [
                "Retry with simpler prompt",
                "Check LLM service status",
                "Verify prompt format"
            ]
        }
    
    async def validate_connection(self) -> bool:
        """Valide que la connexion au service LLM fonctionne"""
        try:
            response = await self.generate(
                "Say 'hello' in JSON format",
                json_response=True,
                task_type='simple',
                max_tokens=50
            )
            return response.get('success', False)
        except Exception as e:
            logger.error(f"Connection validation failed: {str(e)}")
            return False