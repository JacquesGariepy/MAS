"""
Agent hybride amélioré avec meilleure gestion des prompts et du contexte
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from ...database.models import Agent, Task
from ...schemas.tasks import TaskStatus
from ...services.llm_service_improved import ImprovedLLMService
from ..base_agent import BaseAgent
from ..templates import build_agent_prompt, get_task_prompt

class ImprovedHybridAgent(BaseAgent):
    """Agent hybride amélioré combinant capacités réflexives et cognitives"""
    
    def __init__(self, agent_data: Agent, db: AsyncSession):
        super().__init__(agent_data, db)
        self.agent_type = "hybrid"
        self.llm_service = ImprovedLLMService()
        
        # Configuration des règles réflexives
        self.reflexive_rules = self._initialize_rules()
        
        # État interne amélioré
        self.working_memory = []
        self.decision_history = []
        self.context_buffer = []
        self.max_memory_size = 20
        
        # Seuils de confiance
        self.reflexive_confidence_threshold = 0.8
        self.cognitive_confidence_threshold = 0.6
        
        # Informations d'équipe
        self.team_members = []
        self.active_goals = []
    
    def _initialize_rules(self) -> Dict[str, Dict[str, Any]]:
        """Initialise les règles réflexives avec des conditions améliorées"""
        return {
            "emergency_response": {
                "condition": lambda ctx: ctx.get("priority") == "critical" or ctx.get("emergency", False),
                "action": self._handle_emergency,
                "confidence": 0.95
            },
            "routine_task": {
                "condition": lambda ctx: ctx.get("task_type") == "routine" and ctx.get("complexity", 0) < 3,
                "action": self._handle_routine_task,
                "confidence": 0.9
            },
            "collaboration_needed": {
                "condition": lambda ctx: ctx.get("requires_collaboration", False) or len(ctx.get("required_skills", [])) > 3,
                "action": self._initiate_collaboration,
                "confidence": 0.85
            },
            "status_update": {
                "condition": lambda ctx: ctx.get("message_type") == "status_request",
                "action": self._provide_status_update,
                "confidence": 0.9
            }
        }
    
    async def process_task(self, task: Task) -> Dict[str, Any]:
        """Traite une tâche avec approche hybride améliorée"""
        try:
            # Mise à jour du contexte
            context = await self._prepare_context(task)
            
            # Décision hybride : réflexive d'abord, cognitive si nécessaire
            decision = await self._make_hybrid_decision(context)
            
            # Exécution de l'action décidée
            result = await self._execute_decision(decision, task)
            
            # Mise à jour de la mémoire et de l'historique
            await self._update_memory(task, decision, result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error processing task: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "task_id": task.id
            }
    
    async def _prepare_context(self, task: Task) -> Dict[str, Any]:
        """Prépare le contexte enrichi pour la prise de décision"""
        # Contexte de base
        context = {
            "task_id": task.id,
            "task_type": task.task_type,
            "priority": task.priority,
            "description": task.description,
            "metadata": task.metadata or {},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Ajout des informations d'équipe
        context["team_members"] = await self._get_team_members()
        context["active_collaborations"] = await self._get_active_collaborations()
        
        # Ajout de l'historique récent
        context["recent_actions"] = self.decision_history[-5:] if self.decision_history else []
        context["working_memory"] = self.working_memory[-10:] if self.working_memory else []
        
        # Analyse de complexité
        context["complexity"] = self._evaluate_complexity(task)
        context["requires_collaboration"] = self._needs_collaboration(task)
        
        return context
    
    async def _make_hybrid_decision(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Prend une décision en utilisant l'approche hybride"""
        # Tentative réflexive d'abord
        reflexive_decision = self._attempt_reflexive_decision(context)
        
        if reflexive_decision and reflexive_decision.get("confidence", 0) >= self.reflexive_confidence_threshold:
            self.logger.info(f"Using reflexive decision with confidence {reflexive_decision['confidence']}")
            return reflexive_decision
        
        # Si la décision réflexive n'est pas suffisamment confiante, utiliser l'approche cognitive
        self.logger.info("Reflexive decision not confident enough, using cognitive approach")
        cognitive_decision = await self._make_cognitive_decision(context)
        
        # Combiner les insights si disponibles
        if reflexive_decision and cognitive_decision:
            return self._combine_decisions(reflexive_decision, cognitive_decision)
        
        return cognitive_decision or self._create_default_decision(context)
    
    def _attempt_reflexive_decision(self, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Tente une décision réflexive basée sur les règles"""
        for rule_name, rule in self.reflexive_rules.items():
            if rule["condition"](context):
                self.logger.debug(f"Reflexive rule triggered: {rule_name}")
                return {
                    "type": "reflexive",
                    "rule": rule_name,
                    "action": rule["action"],
                    "confidence": rule["confidence"],
                    "reasoning": f"Triggered by rule: {rule_name}"
                }
        return None
    
    async def _make_cognitive_decision(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Prend une décision cognitive en utilisant le LLM avec des prompts améliorés"""
        try:
            # Construction du prompt système
            system_prompt = build_agent_prompt(
                agent_name=self.name,
                agent_type="hybrid",
                agent_role=self.capabilities.get("role", "Hybrid Decision Maker"),
                capabilities=self.capabilities.get("skills", []),
                current_task=context.get("description", ""),
                team_members=[m.get("name", "") for m in context.get("team_members", [])],
                active_goals=self.active_goals
            )
            
            # Construction du prompt utilisateur
            user_prompt = get_task_prompt(
                agent_type="hybrid",
                rules_triggered=[r for r, rule in self.reflexive_rules.items() 
                               if rule["condition"](context)],
                needs_analysis=True,
                task_description=context.get("description", ""),
                filtered_context=self._filter_context_for_llm(context)
            )
            
            # Appel au LLM avec gestion améliorée
            response = await self.llm_service.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                json_response=True,
                task_type="complex" if context.get("complexity", 0) > 5 else "normal",
                stream=True  # Utiliser le streaming pour éviter les timeouts
            )
            
            if response.get("success"):
                decision_data = response["response"]
                return {
                    "type": "cognitive",
                    "decision": decision_data.get("selected_action", {}),
                    "reasoning": decision_data.get("reasoning", ""),
                    "confidence": float(decision_data.get("confidence_level", 0.7)),
                    "fallback_options": decision_data.get("fallback_options", [])
                }
            else:
                # Utiliser la réponse de fallback si disponible
                self.logger.warning(f"LLM response failed: {response.get('error')}")
                return self._create_fallback_decision(context, response.get("fallback_response"))
                
        except Exception as e:
            self.logger.error(f"Cognitive decision error: {str(e)}")
            return self._create_default_decision(context)
    
    def _filter_context_for_llm(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Filtre le contexte pour ne garder que les informations pertinentes pour le LLM"""
        filtered = {
            "task_summary": context.get("description", "")[:200],
            "priority": context.get("priority", "normal"),
            "complexity_score": context.get("complexity", 0),
            "team_available": len(context.get("team_members", [])),
            "recent_success_rate": self._calculate_recent_success_rate(),
            "active_issues": self._get_active_issues()
        }
        
        # Ajouter des métadonnées spécifiques si présentes
        if "deadline" in context.get("metadata", {}):
            filtered["deadline"] = context["metadata"]["deadline"]
        
        if "required_skills" in context.get("metadata", {}):
            filtered["required_skills"] = context["metadata"]["required_skills"]
        
        return filtered
    
    def _combine_decisions(self, reflexive: Dict[str, Any], cognitive: Dict[str, Any]) -> Dict[str, Any]:
        """Combine les décisions réflexive et cognitive"""
        # Prendre la décision avec la plus haute confiance
        if reflexive.get("confidence", 0) > cognitive.get("confidence", 0):
            decision = reflexive
            decision["hybrid_mode"] = "reflexive_primary"
        else:
            decision = cognitive
            decision["hybrid_mode"] = "cognitive_primary"
        
        # Ajouter les insights de l'autre approche
        decision["alternative_approach"] = {
            "type": "reflexive" if decision["type"] == "cognitive" else "cognitive",
            "confidence": reflexive.get("confidence", 0) if decision["type"] == "cognitive" else cognitive.get("confidence", 0)
        }
        
        return decision
    
    async def _execute_decision(self, decision: Dict[str, Any], task: Task) -> Dict[str, Any]:
        """Exécute la décision prise"""
        try:
            if decision["type"] == "reflexive":
                # Exécuter l'action réflexive
                action = decision.get("action")
                if callable(action):
                    result = await action(task, decision)
                else:
                    result = {"status": "completed", "method": "reflexive"}
            else:
                # Exécuter l'action cognitive
                result = await self._execute_cognitive_action(decision, task)
            
            # Mettre à jour le statut de la tâche
            await self._update_task_status(task, TaskStatus.COMPLETED)
            
            return {
                "status": "success",
                "task_id": task.id,
                "decision_type": decision["type"],
                "confidence": decision.get("confidence", 0),
                "result": result
            }
            
        except Exception as e:
            self.logger.error(f"Execution error: {str(e)}")
            await self._update_task_status(task, TaskStatus.FAILED)
            return {
                "status": "error",
                "error": str(e),
                "task_id": task.id
            }
    
    async def _update_memory(self, task: Task, decision: Dict[str, Any], result: Dict[str, Any]):
        """Met à jour la mémoire de travail et l'historique"""
        memory_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "task_id": task.id,
            "decision_type": decision["type"],
            "confidence": decision.get("confidence", 0),
            "success": result.get("status") == "success"
        }
        
        # Ajouter à la mémoire de travail
        self.working_memory.append(memory_entry)
        if len(self.working_memory) > self.max_memory_size:
            self.working_memory.pop(0)
        
        # Ajouter à l'historique de décisions
        self.decision_history.append({
            **memory_entry,
            "reasoning": decision.get("reasoning", ""),
            "execution_time": datetime.utcnow().isoformat()
        })
    
    def _create_default_decision(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Crée une décision par défaut en cas d'échec"""
        return {
            "type": "default",
            "decision": {
                "action": "acknowledge_and_queue",
                "parameters": {"task_id": context.get("task_id")}
            },
            "reasoning": "Unable to make specific decision, queuing for later processing",
            "confidence": 0.3
        }
    
    def _create_fallback_decision(self, context: Dict[str, Any], fallback_info: Dict[str, Any]) -> Dict[str, Any]:
        """Crée une décision de fallback basée sur les informations disponibles"""
        return {
            "type": "fallback",
            "decision": {
                "action": "basic_processing",
                "parameters": {"task_id": context.get("task_id")}
            },
            "reasoning": f"Using fallback due to: {fallback_info.get('message', 'Unknown error')}",
            "confidence": 0.5,
            "suggestions": fallback_info.get("suggestions", [])
        }
    
    # Méthodes auxiliaires
    async def _get_team_members(self) -> List[Dict[str, Any]]:
        """Récupère la liste des membres de l'équipe"""
        # Implémentation simplifiée - à adapter selon vos besoins
        return self.team_members
    
    async def _get_active_collaborations(self) -> List[str]:
        """Récupère les collaborations actives"""
        # Implémentation simplifiée
        return []
    
    def _evaluate_complexity(self, task: Task) -> int:
        """Évalue la complexité d'une tâche (0-10)"""
        complexity = 0
        
        # Facteurs de complexité
        if task.priority == "high":
            complexity += 2
        if task.priority == "critical":
            complexity += 4
            
        # Vérifier les métadonnées
        metadata = task.metadata or {}
        if metadata.get("requires_collaboration"):
            complexity += 2
        if len(metadata.get("required_skills", [])) > 2:
            complexity += 1
        if metadata.get("deadline"):
            complexity += 1
            
        return min(complexity, 10)
    
    def _needs_collaboration(self, task: Task) -> bool:
        """Détermine si une tâche nécessite une collaboration"""
        metadata = task.metadata or {}
        return (
            metadata.get("requires_collaboration", False) or
            len(metadata.get("required_skills", [])) > len(self.capabilities.get("skills", [])) or
            task.priority == "critical"
        )
    
    def _calculate_recent_success_rate(self) -> float:
        """Calcule le taux de succès récent"""
        if not self.decision_history:
            return 0.5
        
        recent = self.decision_history[-10:]
        successes = sum(1 for d in recent if d.get("success", False))
        return successes / len(recent) if recent else 0.5
    
    def _get_active_issues(self) -> List[str]:
        """Récupère la liste des problèmes actifs"""
        issues = []
        for entry in self.working_memory[-5:]:
            if not entry.get("success", True):
                issues.append(f"Failed task: {entry.get('task_id', 'unknown')}")
        return issues
    
    # Handlers pour les actions réflexives
    async def _handle_emergency(self, task: Task, decision: Dict[str, Any]) -> Dict[str, Any]:
        """Gère les situations d'urgence"""
        self.logger.warning(f"Emergency handler activated for task {task.id}")
        # Implémentation spécifique pour les urgences
        return {"action": "emergency_response", "status": "handled"}
    
    async def _handle_routine_task(self, task: Task, decision: Dict[str, Any]) -> Dict[str, Any]:
        """Gère les tâches routinières"""
        self.logger.info(f"Routine handler for task {task.id}")
        # Implémentation spécifique pour les tâches routinières
        return {"action": "routine_completion", "status": "completed"}
    
    async def _initiate_collaboration(self, task: Task, decision: Dict[str, Any]) -> Dict[str, Any]:
        """Initie une collaboration avec d'autres agents"""
        self.logger.info(f"Initiating collaboration for task {task.id}")
        # Implémentation de la collaboration
        return {"action": "collaboration_initiated", "status": "pending"}
    
    async def _provide_status_update(self, task: Task, decision: Dict[str, Any]) -> Dict[str, Any]:
        """Fournit une mise à jour de statut"""
        status_info = {
            "agent": self.name,
            "working_memory_size": len(self.working_memory),
            "recent_success_rate": self._calculate_recent_success_rate(),
            "active_issues": self._get_active_issues()
        }
        return {"action": "status_provided", "status_info": status_info}
    
    async def _execute_cognitive_action(self, decision: Dict[str, Any], task: Task) -> Dict[str, Any]:
        """Exécute une action décidée cognitivement"""
        action_info = decision.get("decision", {})
        action_name = action_info.get("action", "process")
        
        # Log de l'action
        self.logger.info(f"Executing cognitive action: {action_name} for task {task.id}")
        
        # Implémentation basique - à étendre selon vos besoins
        return {
            "action": action_name,
            "parameters": action_info.get("parameters", {}),
            "status": "executed"
        }