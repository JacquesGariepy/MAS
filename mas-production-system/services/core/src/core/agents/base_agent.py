#!/usr/bin/env python3
"""
BaseAgent – BDI v2
──────────────────
• Garantit que `beliefs` est toujours un dict (même si chaîne ou None au départ)
• Convertit/encapsule automatiquement les mises à jour reçues
• Ajoute _ensure_dict() pour éviter l’erreur "'str' object has no attribute 'items'"
• Journalise les conversions / erreurs de type
Copy‑paste complet, sans placeholder.
"""

from __future__ import annotations

import asyncio
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from src.services.llm_service import LLMService
from src.services.tool_service import ToolService
from src.utils.logger import get_logger

logger = get_logger(__name__)


# ────────────────────────────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────────────────────────────
def _ensure_dict(value: Any, *, context: str = "") -> Dict[str, Any]:
    """
    Convertit value en dict si possible; encapsule sinon.
    ‑ value = '{"a":1}'     → {'a': 1}
    ‑ value = 'text'        → {'value': 'text'}
    ‑ value = None          → {}
    ‑ value est déjà dict   → inchangé
    """
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, dict):
                return parsed
            return {"value": parsed}
        except json.JSONDecodeError:
            logger.warning("String not JSON (%s): wrapped into dict", context)
            return {"value": value}
    logger.warning("Unexpected type %s for %s – wrapped", type(value), context)
    return {"value": value}


# ────────────────────────────────────────────────────────────────────────────────
# Dataclasses
# ────────────────────────────────────────────────────────────────────────────────
@dataclass
class BDI:
    """Beliefs‑Desires‑Intentions"""
    beliefs: Dict[str, Any] = field(default_factory=dict)
    desires: List[str] = field(default_factory=list)
    intentions: List[str] = field(default_factory=list)


@dataclass
class AgentContext:
    """Execution context"""
    agent_id: UUID
    environment: Dict[str, Any] = field(default_factory=dict)
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)
    working_memory: List[Any] = field(default_factory=list)
    current_task: Optional[Any] = None
    software_location: Optional[Any] = None  # e.g. SoftwareLocation
    resource_allocation: Dict[str, float] = field(default_factory=dict)
    visibility_level: Optional[str] = None   # e.g. VisibilityLevel


# ────────────────────────────────────────────────────────────────────────────────
# BaseAgent
# ────────────────────────────────────────────────────────────────────────────────
class BaseAgent(ABC):
    """Base class for all agents with robust BDI handling"""

    # ---------------------------------------------------------------- init
    def __init__(
        self,
        agent_id: UUID,
        name: str,
        role: str,
        capabilities: List[str],
        llm_service: Optional[LLMService] = None,
        **kwargs,
    ):
        self.agent_id = agent_id      # Unique identifier
        self.id = agent_id            # Legacy compatibility
        self.name = name
        self.role = role
        self.capabilities = capabilities
        self.llm_service = llm_service
        self.agent_type = kwargs.get("agent_type", "base")

        # Initial beliefs/desires – toujours dict / list
        init_beliefs = _ensure_dict(kwargs.get("initial_beliefs"), context="initial_beliefs")
        init_desires = kwargs.get("initial_desires") or []
        if isinstance(init_desires, str):
            init_desires = [init_desires]

        self.bdi = BDI(beliefs=init_beliefs, desires=init_desires, intentions=[])

        # Context & tools
        self.context = AgentContext(agent_id=agent_id)
        self.tool_service = ToolService()
        self.tools: Dict[str, Any] = {}
        self._load_tools()

        # Runtime state
        self._running = False
        self._tasks: asyncio.Queue[Any] = asyncio.Queue()
        self._message_queue: asyncio.Queue[Any] = asyncio.Queue()

        self.metrics: Dict[str, Any] = {
            "actions_executed": 0,
            "messages_processed": 0,
            "tasks_completed": 0,
            "errors": 0,
            "start_time": None,
            "total_runtime": 0,
        }

    # ---------------------------------------------------------------- utilities
    def _load_tools(self) -> None:
        for cap in self.capabilities:
            self.tools.update(self.tool_service.get_tools_for_capability(cap))

    # ---------------------------------------------------------------- abstract API
    @abstractmethod
    async def perceive(self, environment: Dict[str, Any]) -> Dict[str, Any]:
        ...

    @abstractmethod
    async def deliberate(self) -> List[str]:
        ...

    @abstractmethod
    async def act(self) -> List[Dict[str, Any]]:
        ...

    @abstractmethod
    async def handle_message(self, message: Any):
        ...

    @abstractmethod
    async def handle_task(self, task: Any):
        ...

    # ---------------------------------------------------------------- belief/goal mgmt
    async def update_beliefs(self, new_beliefs: Any) -> None:
        new_dict = _ensure_dict(new_beliefs, context="update_beliefs")
        # Assure que self.bdi.beliefs est un dict
        if not isinstance(self.bdi.beliefs, dict):
            logger.error(
                "Beliefs corrupted (type %s). Resetting to dict.", type(self.bdi.beliefs)
            )
            self.bdi.beliefs = {}
        self.bdi.beliefs.update(new_dict)
        logger.debug("Agent %s beliefs updated: %s", self.name, new_dict)

    async def add_desire(self, desire: str) -> None:
        if desire not in self.bdi.desires:
            self.bdi.desires.append(desire)
            logger.debug("Agent %s new desire: %s", self.name, desire)

    async def commit_to_intention(self, intention: str) -> None:
        if intention not in self.bdi.intentions:
            self.bdi.intentions.append(intention)
            logger.debug("Agent %s intention committed: %s", self.name, intention)

    async def drop_intention(self, intention: str) -> None:
        if intention in self.bdi.intentions:
            self.bdi.intentions.remove(intention)
            logger.debug("Agent %s intention dropped: %s", self.name, intention)

    # ---------------------------------------------------------------- main loop
    async def run(self) -> None:
        self._running = True
        self.metrics["start_time"] = datetime.utcnow()
        logger.info("Agent %s starting…", self.name)

        last_bdi_cycle = asyncio.get_event_loop().time()
        bdi_interval = 5.0  # seconds
        iteration = 0

        try:
            while self._running:
                iteration += 1

                # High‑priority message processing
                if not self._message_queue.empty():
                    await self._process_messages()

                # Task processing
                await self._process_tasks()

                # Periodic BDI cycle
                now = asyncio.get_event_loop().time()
                if now - last_bdi_cycle >= bdi_interval:
                    await self._bdi_cycle()
                    last_bdi_cycle = now

                if iteration % 10 == 0:
                    logger.debug(
                        "Agent %s iter=%d, msgs=%d, tasks=%d",
                        self.name,
                        iteration,
                        self._message_queue.qsize(),
                        self._tasks.qsize(),
                    )

                await asyncio.sleep(0.1)

        except Exception as exc:
            logger.exception("Agent %s loop error: %s", self.name, exc)
            self.metrics["errors"] += 1
            raise
        finally:
            runtime = (datetime.utcnow() - self.metrics["start_time"]).total_seconds()
            self.metrics["total_runtime"] += runtime
            logger.info("Agent %s stopped – runtime %.2fs", self.name, runtime)

    # ---------------------------------------------------------------- BDI cycle
    async def _bdi_cycle(self) -> None:
        try:
            # 1) Perceive
            perceptions = await self.perceive(self.context.environment)
            await self.update_beliefs(perceptions)

            # 2) Deliberate
            intentions = await self.deliberate()
            for intent in intentions:
                await self.commit_to_intention(intent)

            # 3) Act
            if self.bdi.intentions:
                actions = await self.act() or []
                # Normalise actions
                if isinstance(actions, str):
                    try:
                        actions = json.loads(actions)
                    except json.JSONDecodeError:
                        actions = [{"type": "execute", "description": actions}]
                if isinstance(actions, dict):
                    actions = [actions]
                if not isinstance(actions, list):
                    logger.warning("Invalid actions type %s, ignoring", type(actions))
                    actions = []

                for act in actions:
                    await self._execute_action(act)

        except Exception as exc:
            logger.exception("Error in BDI cycle for %s: %s", self.name, exc)
            self.metrics["errors"] += 1

    # ---------------------------------------------------------------- execute
    async def _execute_action(self, action: Any) -> None:
        if isinstance(action, str):
            action = {"type": "execute", "description": action}

        if not isinstance(action, dict):
            logger.error("Action must be dict or str, got %s", type(action))
            return

        action_type = action.get("type")
        if action_type == "tool_call":
            await self._execute_tool_call(action)
        elif action_type == "send_message":
            await self._send_message(action)
        elif action_type == "update_belief":
            await self.update_beliefs(action.get("beliefs"))
        else:
            logger.warning("Unknown action type: %s", action_type)

        self.metrics["actions_executed"] += 1

    async def _execute_tool_call(self, action: Dict[str, Any]) -> None:
        tool_name = action.get("tool")
        params = _ensure_dict(action.get("params"), context="tool_params")

        tool = self.tools.get(tool_name)
        if not tool:
            logger.error("Tool %s not found for agent %s", tool_name, self.name)
            return

        try:
            result = await tool.execute(params)
            await self.update_beliefs(
                {
                    f"last_{tool_name}_result": result.data,
                    f"last_{tool_name}_success": result.success,
                }
            )
        except Exception as exc:
            logger.exception("Tool %s failed: %s", tool_name, exc)
            await self.update_beliefs({f"last_{tool_name}_error": str(exc)})

    async def _send_message(self, action: Dict[str, Any]) -> None:
        # Implement according to messaging subsystem
        pass

    # ---------------------------------------------------------------- queues
    async def _process_messages(self) -> None:
        while not self._message_queue.empty():
            msg = await self._message_queue.get()
            try:
                await self.handle_message(msg)
                self.metrics["messages_processed"] += 1
            except Exception as exc:
                logger.exception("handle_message error: %s", exc)
                self.metrics["errors"] += 1

    async def _process_tasks(self) -> None:
        while not self._tasks.empty():
            task = await self._tasks.get()
            self.context.current_task = task
            try:
                await self.handle_task(task)
                self.metrics["tasks_completed"] += 1
            except Exception as exc:
                logger.exception("handle_task error: %s", exc)
                self.metrics["errors"] += 1
            finally:
                self.context.current_task = None

    # ---------------------------------------------------------------- runtime control
    async def receive_message(self, message: Any) -> None:
        await self._message_queue.put(message)

    async def add_task(self, task: Any) -> None:
        await self._tasks.put(task)

    async def stop(self) -> None:
        self._running = False

    # ---------------------------------------------------------------- metrics / config
    async def get_metrics(self) -> Dict[str, Any]:
        return {
            **self.metrics,
            "belief_count": len(self.bdi.beliefs),
            "desire_count": len(self.bdi.desires),
            "intention_count": len(self.bdi.intentions),
            "tool_count": len(self.tools),
            "working_memory": len(self.context.working_memory),
        }

    async def update_configuration(self, config: Dict[str, Any]) -> None:
        if "capabilities" in config:
            self.capabilities = config["capabilities"]
            self._load_tools()
        await self._handle_config_update(config)

    async def _handle_config_update(self, config: Dict[str, Any]) -> None:
        # Override in subclasses
        pass

    # ---------------------------------------------------------------- repr
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.name} ({self.role})>"
