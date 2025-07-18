# Analyse des Capacités d'Exécution de Scripts dans MAS

## Résumé Exécutif

Cette analyse examine les mécanismes actuels d'exécution de scripts dans le système MAS et propose des améliorations pour une exécution sécurisée et flexible.

## 1. Capacités Actuelles

### 1.1 Outils de Codage (CodingTools)

Le système dispose actuellement de 4 outils principaux pour l'exécution de code :

- **git_clone** : Clone des dépôts Git via `subprocess.run`
- **git_commit** : Effectue des commits Git (add + commit)
- **compile_code** : Compile uniquement du code Python via `compile()`
- **run_tests** : Exécute du code Python avec un timeout de 30 secondes

### 1.2 Service d'Outils (ToolService)

Architecture modulaire permettant :
- Enregistrement de fonctions comme outils
- Exécution asynchrone avec validation des paramètres
- Outils intégrés : web_search, file_read, file_write, db_query, http_request
- Mapping capacités → outils (ex: coding → git_clone, compile_code)

### 1.3 Intégration Docker

- **Conteneur** : Python 3.11-slim comme image de base
- **Isolation** : Isolation au niveau conteneur uniquement
- **Volumes** : Code source, logs, et exemples montés
- **Sécurité** : Headers CSP basiques, pas de sandbox spécifique

## 2. Limitations Identifiées

### 2.1 Sécurité
- ❌ Pas de sandbox pour l'exécution de scripts
- ❌ Pas de limites de ressources (CPU/mémoire)
- ❌ Accès réseau non contrôlé
- ❌ Pas de validation du code avant exécution

### 2.2 Support Linguistique
- ❌ Seul Python est supporté pour la compilation
- ❌ Pas de support pour Node.js, Java, Go, Rust, etc.
- ❌ Pas de gestion des dépendances (pip, npm, etc.)

### 2.3 Fonctionnalités
- ❌ Exécution synchrone uniquement (blocage)
- ❌ Pas de streaming de sortie en temps réel
- ❌ Pas de sessions interactives (REPL)
- ❌ Timeout limité à run_tests uniquement

## 3. Mécanismes d'Exécution Actuels

### 3.1 Flow d'Exécution

```python
Agent → ToolService → CodingTools → subprocess.run → Résultat
```

### 3.2 Exemple d'Utilisation

```python
# Agent demande l'exécution d'un test
action = {
    "type": "tool_call",
    "tool": "run_tests",
    "params": {"test_code": "print('Hello World')"}
}

# ToolService valide et exécute
result = await tool_service.execute_tool(
    agent_id=agent.id,
    tool_name="run_tests",
    parameters={"test_code": "print('Hello World')"}
)
```

## 4. Améliorations Proposées

### 4.1 Sécurité Renforcée

#### Sandboxing Docker
```yaml
# docker-compose.sandbox.yml
sandbox_executor:
  image: mas-sandbox-executor
  security_opt:
    - no-new-privileges
    - apparmor=docker-default
  cap_drop:
    - ALL
  cap_add:
    - NET_BIND_SERVICE
  read_only: true
  tmpfs:
    - /tmp
    - /var/run
  mem_limit: 512m
  cpus: 0.5
  network_mode: none
```

#### Validation du Code
```python
class SecureCodeValidator:
    def validate_code(self, code: str, language: str) -> bool:
        # Analyse statique
        # Détection de patterns dangereux
        # Vérification des imports autorisés
        pass
```

### 4.2 Support Multi-Langage

```python
class LanguageExecutor:
    executors = {
        "python": PythonExecutor(),
        "javascript": NodeExecutor(),
        "java": JavaExecutor(),
        "go": GoExecutor(),
        "rust": RustExecutor()
    }
    
    async def execute(self, code: str, language: str, **kwargs):
        executor = self.executors.get(language)
        if not executor:
            raise ValueError(f"Language {language} not supported")
        return await executor.run(code, **kwargs)
```

### 4.3 Exécution Asynchrone avec Streaming

```python
class AsyncScriptExecutor:
    async def execute_stream(self, script: str, language: str):
        """Exécute un script et stream la sortie en temps réel"""
        async with self.create_sandbox() as sandbox:
            process = await sandbox.start_process(script, language)
            
            async for line in process.stdout:
                yield {"type": "stdout", "data": line}
                
            async for line in process.stderr:
                yield {"type": "stderr", "data": line}
                
            exit_code = await process.wait()
            yield {"type": "exit", "code": exit_code}
```

### 4.4 Architecture Proposée

```
┌─────────────────┐
│     Agent       │
└────────┬────────┘
         │
┌────────▼────────┐
│  ScriptManager  │ ← Nouvelle couche
├─────────────────┤
│ - Validation    │
│ - Sandboxing    │
│ - Monitoring    │
└────────┬────────┘
         │
┌────────▼────────┐
│ LanguageExecutor│ ← Multi-langage
├─────────────────┤
│ - Python        │
│ - Node.js       │
│ - Java          │
│ - Go            │
└────────┬────────┘
         │
┌────────▼────────┐
│ DockerSandbox   │ ← Isolation
├─────────────────┤
│ - Resource limits│
│ - Network isolation│
│ - FS isolation  │
└─────────────────┘
```

## 5. Implémentation Recommandée

### Phase 1 : Sécurisation (Priorité Haute)
1. Implémenter le sandboxing Docker
2. Ajouter la validation de code
3. Mettre en place les limites de ressources
4. Créer un système d'audit

### Phase 2 : Multi-Langage (Priorité Moyenne)
1. Ajouter le support Node.js
2. Intégrer Java et Go
3. Gérer les package managers
4. Créer des templates par langage

### Phase 3 : Fonctionnalités Avancées (Priorité Basse)
1. Exécution asynchrone avec streaming
2. Sessions interactives (REPL)
3. Exécution distribuée
4. Interface de monitoring

## 6. Exemple d'Utilisation Future

```python
# Agent cognitif exécute du code de manière sécurisée
async def execute_user_code(self, code: str, language: str = "python"):
    script_manager = ScriptManager()
    
    # Validation
    if not await script_manager.validate(code, language):
        return {"error": "Code validation failed"}
    
    # Exécution dans sandbox
    async with script_manager.create_sandbox() as sandbox:
        # Limites de ressources
        sandbox.set_limits(cpu=0.5, memory="256m", timeout=60)
        
        # Exécution avec streaming
        result = []
        async for output in sandbox.execute_stream(code, language):
            result.append(output)
            # Notifier l'agent en temps réel
            await self.update_beliefs({"execution_output": output})
        
        return {
            "success": True,
            "outputs": result,
            "metrics": sandbox.get_metrics()
        }
```

## 7. Bénéfices Attendus

- **Sécurité** : Isolation complète et validation du code
- **Flexibilité** : Support de multiples langages
- **Performance** : Exécution non-bloquante
- **Monitoring** : Traçabilité complète
- **Scalabilité** : Exécution distribuée possible

## 8. Conclusion

Le système MAS dispose d'une base solide pour l'exécution de scripts, mais nécessite des améliorations significatives en termes de sécurité et de flexibilité. Les améliorations proposées permettront aux agents d'exécuter du code de manière sûre et efficace dans plusieurs langages, ouvrant la voie à des capacités d'automatisation avancées.