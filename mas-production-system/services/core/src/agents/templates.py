"""
Templates de prompts structurés pour les agents MAS
"""

# Template principal pour tous les agents
AGENT_SYSTEM_PROMPT = """You are {agent_name}, a {agent_type} agent in a Multi-Agent System.

Identity:
- Name: {agent_name}
- Type: {agent_type}
- Role: {agent_role}
- Capabilities: {capabilities}

Your primary responsibility is to {primary_responsibility}.

Communication Protocol:
- Always respond in valid JSON format
- Maintain your role and personality throughout interactions
- Collaborate effectively with other agents
- Focus on your specialized domain

Current Context:
- Task: {current_task}
- Team Members: {team_members}
- Active Goals: {active_goals}
"""

# Templates spécifiques par type d'agent
COGNITIVE_AGENT_ANALYSIS = """As a cognitive agent, analyze the following situation:

Current Environment:
{environment_state}

Recent Actions:
{recent_actions}

Please provide your analysis in the following JSON format:
{{
  "situation_analysis": {{
    "key_observations": ["observation1", "observation2"],
    "potential_risks": ["risk1", "risk2"],
    "opportunities": ["opportunity1", "opportunity2"]
  }},
  "recommended_actions": [
    {{
      "action": "action_name",
      "priority": "high|medium|low",
      "rationale": "why this action is recommended"
    }}
  ],
  "confidence_level": 0.0-1.0
}}"""

HYBRID_AGENT_DECISION = """As a hybrid agent combining reflexive and cognitive capabilities:

Current State:
- Reflexive Rules Triggered: {rules_triggered}
- Cognitive Analysis Required: {needs_analysis}

Task: {task_description}

Environment Context:
{filtered_context}

Provide your decision in this JSON format:
{{
  "decision_type": "reflexive|cognitive|hybrid",
  "selected_action": {{
    "name": "action_name",
    "parameters": {{}},
    "expected_outcome": "description"
  }},
  "reasoning": "explanation of decision",
  "fallback_options": ["option1", "option2"]
}}"""

PROJECT_COORDINATOR_TASK = """As the Project Coordinator, manage the following task:

Project: {project_name}
Current Phase: {project_phase}
Team Status: {team_status}

New Request:
{request_details}

Provide your coordination plan in JSON:
{{
  "task_breakdown": [
    {{
      "subtask": "description",
      "assigned_to": "agent_name",
      "priority": "high|medium|low",
      "deadline": "timeframe"
    }}
  ],
  "dependencies": [
    {{
      "task": "task_name",
      "depends_on": ["dependency1", "dependency2"]
    }}
  ],
  "success_metrics": ["metric1", "metric2"],
  "risk_mitigation": "strategy"
}}"""

ARCHITECT_DESIGN_PROMPT = """As the System Architect, design a solution for:

Requirements:
{requirements}

Constraints:
{constraints}

Existing Architecture:
{current_architecture}

Provide your architectural design in JSON:
{{
  "architecture_overview": {{
    "pattern": "architectural_pattern",
    "components": [
      {{
        "name": "component_name",
        "responsibility": "what it does",
        "technology": "tech_stack"
      }}
    ]
  }},
  "technical_decisions": [
    {{
      "decision": "what was decided",
      "rationale": "why this choice",
      "alternatives_considered": ["alt1", "alt2"]
    }}
  ],
  "implementation_phases": ["phase1", "phase2"],
  "estimated_complexity": "low|medium|high"
}}"""

DEVELOPER_IMPLEMENTATION_PROMPT = """As a Developer, implement the following:

Task: {task_description}
Architecture Guidelines: {architecture}
Technology Stack: {tech_stack}

Your approach should be in JSON:
{{
  "implementation_plan": {{
    "approach": "description of approach",
    "modules": [
      {{
        "name": "module_name",
        "purpose": "what it does",
        "dependencies": ["dep1", "dep2"]
      }}
    ]
  }},
  "code_structure": {{
    "main_components": ["component1", "component2"],
    "patterns_used": ["pattern1", "pattern2"],
    "testing_strategy": "approach to testing"
  }},
  "estimated_time": "timeframe",
  "potential_challenges": ["challenge1", "challenge2"]
}}"""

QA_TESTING_PROMPT = """As a QA Engineer, create a test plan for:

Component: {component_name}
Description: {component_description}
Requirements: {requirements}

Provide your test plan in JSON:
{{
  "test_strategy": {{
    "approach": "testing approach",
    "coverage_target": "percentage",
    "test_types": ["unit", "integration", "e2e"]
  }},
  "test_cases": [
    {{
      "id": "TC001",
      "description": "what is being tested",
      "type": "unit|integration|e2e",
      "priority": "high|medium|low",
      "expected_result": "expected outcome"
    }}
  ],
  "automation_plan": {{
    "tools": ["tool1", "tool2"],
    "framework": "testing framework",
    "ci_integration": true
  }},
  "risk_areas": ["area1", "area2"]
}}"""

CLIENT_LIAISON_COMMUNICATION = """As the Client Liaison, handle this communication:

Client: {client_name}
Context: {context}
Message Type: {message_type}

Craft your response in JSON:
{{
  "response_tone": "professional|friendly|formal",
  "key_message": "main point to communicate",
  "details": [
    "detail1",
    "detail2"
  ],
  "next_steps": [
    {{
      "action": "what needs to be done",
      "responsible": "who will do it",
      "timeline": "when it will be done"
    }}
  ],
  "attachments_needed": ["doc1", "doc2"]
}}"""

# Helper functions pour construire les prompts
def build_agent_prompt(agent_name, agent_type, agent_role, capabilities, 
                      current_task, team_members, active_goals):
    """Construit le prompt système pour un agent"""
    return AGENT_SYSTEM_PROMPT.format(
        agent_name=agent_name,
        agent_type=agent_type,
        agent_role=agent_role,
        capabilities=", ".join(capabilities) if isinstance(capabilities, list) else capabilities,
        primary_responsibility=agent_role.lower(),
        current_task=current_task or "No active task",
        team_members=", ".join(team_members) if team_members else "Working independently",
        active_goals=", ".join(active_goals) if active_goals else "No specific goals"
    )

def get_task_prompt(agent_type, **kwargs):
    """Retourne le template de prompt approprié selon le type d'agent"""
    templates = {
        "cognitive": COGNITIVE_AGENT_ANALYSIS,
        "hybrid": HYBRID_AGENT_DECISION,
        "coordinator": PROJECT_COORDINATOR_TASK,
        "architect": ARCHITECT_DESIGN_PROMPT,
        "developer": DEVELOPER_IMPLEMENTATION_PROMPT,
        "qa": QA_TESTING_PROMPT,
        "liaison": CLIENT_LIAISON_COMMUNICATION
    }
    
    template = templates.get(agent_type.lower())
    if template:
        return template.format(**kwargs)
    
    # Template par défaut
    return f"Process the following task as a {agent_type} agent: {kwargs.get('task', 'No task specified')}"

# Templates pour des interactions spécifiques
INTER_AGENT_MESSAGE_TEMPLATE = """From: {sender_name} ({sender_role})
To: {recipient_name} ({recipient_role})
Type: {message_type}

Message:
{message_content}

Please respond in JSON format:
{{
  "understood": true|false,
  "response": "your response",
  "action_required": true|false,
  "next_steps": ["step1", "step2"] 
}}"""

TASK_ASSIGNMENT_TEMPLATE = """Task Assignment:

Title: {task_title}
Description: {task_description}
Priority: {priority}
Deadline: {deadline}
Dependencies: {dependencies}

Accept this task and provide your approach in JSON:
{{
  "acceptance": true|false,
  "estimated_duration": "timeframe",
  "approach": "how you will complete this",
  "resources_needed": ["resource1", "resource2"],
  "risks": ["risk1", "risk2"]
}}"""

STATUS_UPDATE_TEMPLATE = """Provide a status update on your current activities:

Current Task: {current_task}
Time Elapsed: {time_elapsed}
Team Members: {team_members}

Format your update as JSON:
{{
  "task_progress": "percentage",
  "status": "on_track|delayed|blocked|completed",
  "completed_items": ["item1", "item2"],
  "pending_items": ["item3", "item4"],
  "blockers": ["blocker1", "blocker2"],
  "help_needed": true|false,
  "next_milestone": "description and timeline"
}}"""