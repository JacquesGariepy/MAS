# Structure Enforcement in Autonomous Agents

## Problem Statement

Previously, when autonomous agents worked on tasks, each agent would create its own separate project directory (e.g., `task_12345678/`) for their specific subtask. This led to:
- Scattered code across multiple directories
- Difficulty in integrating code from different agents
- No consistent project structure
- Poor code organization

## Solution Overview

The solution implements a centralized project structure management system that ensures all agents work within the same well-organized project structure.

## Key Components

### 1. Project Initialization

When a new request is processed, the main autonomous agent:
- Creates a single project directory for the entire request
- Initializes a standard Python project structure
- Shares this structure with all sub-agents

```python
async def _initialize_project_structure(self, main_task: Task):
    # Creates project_XXXXXXXX directory with standard structure
    self.project_structure = {
        "src/": {
            "core/": {},
            "models/": {},
            "services/": {},
            "utils/": {}
        },
        "tests/": {
            "unit/": {},
            "integration/": {}
        },
        "docs/": {},
        "config/": {},
        "scripts/": {}
    }
```

### 2. File Location Determination

The `_determine_file_location()` method intelligently places files based on their type and purpose:

- **Test files** → `tests/unit/` or `tests/integration/`
- **Model files** → `src/models/`
- **Service files** → `src/services/`
- **Utility files** → `src/utils/`
- **Core logic** → `src/core/`
- **Documentation** → `docs/`
- **Configuration** → `config/`
- **Scripts** → `scripts/`

### 3. Agent Coordination

All agents receive:
- The project structure information
- Rules about file placement
- Clear instructions in their prompts

```python
await agent['agent'].update_beliefs({
    "project_structure": project_info,
    "working_directory": self.current_project_path,
    "project_structure_rules": {
        "message": "RESPECTER LA STRUCTURE DU PROJET",
        "src_for_code": True,
        "tests_for_tests": True,
        "no_task_specific_dirs": True,
        "use_relative_paths": True
    }
})
```

### 4. LLM Prompt Enhancement

The LLM service includes explicit instructions about project structure in the prompts:

```
IMPORTANT - STRUCTURE DU PROJET:
Tous les fichiers doivent respecter la structure Python standard:
- src/ : code source principal
  - src/core/ : logique métier principale
  - src/models/ : modèles de données
  - src/services/ : services et intégrations
  - src/utils/ : utilitaires et helpers
- tests/ : tests unitaires et d'intégration
- docs/ : documentation
- config/ : fichiers de configuration
- scripts/ : scripts utilitaires
```

## Benefits

1. **Consistent Structure**: All code follows the same organizational pattern
2. **Easy Integration**: Code from different agents naturally fits together
3. **Better Maintainability**: Clear separation of concerns
4. **Professional Output**: Generated projects follow Python best practices
5. **Scalability**: Structure supports growth and additional features

## Testing

Use `test_structure_enforcement.py` to verify that:
- All files are placed in appropriate directories
- No task-specific directories are created
- The structure follows Python conventions
- Agents respect the shared project structure

## Usage Example

When an autonomous agent processes a request like "Create a calculator with tests and API":

```
project_12345678/
├── src/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   └── calculator.py
│   ├── services/
│   │   ├── __init__.py
│   │   └── api_service.py
│   └── models/
│       ├── __init__.py
│       └── calculation_history.py
├── tests/
│   ├── __init__.py
│   └── unit/
│       ├── __init__.py
│       └── test_calculator.py
├── docs/
│   └── API.md
├── README.md
├── requirements.txt
└── setup.py
```

## Future Enhancements

1. **Template System**: Support for different project types (web app, CLI, library)
2. **Language Support**: Extend to other languages with appropriate structures
3. **Custom Structures**: Allow users to define their preferred structure
4. **Validation Rules**: More sophisticated file placement validation
5. **Structure Evolution**: Adapt structure based on project complexity