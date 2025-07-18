#!/usr/bin/env python3
"""
Test simple du FileSystemTool
"""

import sys
import os
sys.path.append('/app')

import asyncio
from datetime import datetime
from src.tools.filesystem_tool import FileSystemTool

async def test_filesystem():
    """Test les fonctionnalités de base du FileSystemTool"""
    print("🧪 Test du FileSystemTool")
    print("="*50)
    
    tool = FileSystemTool()
    agent_id = "test-agent-001"
    
    try:
        # 1. Créer un répertoire de projet
        print("\n1️⃣ Création d'un projet...")
        result = await tool.create_agent_directory(agent_id, "test_project")
        if result.success:
            print(f"✅ Projet créé: {result.data['project_path']}")
        else:
            print(f"❌ Erreur: {result.error}")
            return
        
        # 2. Écrire un fichier Python
        print("\n2️⃣ Création d'un fichier Python...")
        code_content = '''def hello_world():
    """Fonction de test générée par un agent"""
    print("Hello from agent workspace!")
    return "Success"

if __name__ == "__main__":
    result = hello_world()
    print(f"Result: {result}")
'''
        
        result = await tool.write_file(
            f"projects/{agent_id}/test_project/src/hello.py",
            code_content,
            agent_id
        )
        if result.success:
            print(f"✅ Fichier créé: {result.data['file_path']}")
        else:
            print(f"❌ Erreur: {result.error}")
        
        # 3. Lister le contenu du projet
        print("\n3️⃣ Contenu du projet...")
        result = await tool.list_directory(f"projects/{agent_id}/test_project")
        if result.success:
            print(f"📁 Répertoire: {result.data['directory']}")
            for item in result.data['items']:
                icon = "📁" if item['type'] == 'directory' else "📄"
                print(f"   {icon} {item['name']}")
        
        # 4. Lire le fichier créé
        print("\n4️⃣ Lecture du fichier...")
        result = await tool.read_file(f"projects/{agent_id}/test_project/src/hello.py")
        if result.success:
            print(f"📄 Contenu du fichier ({result.data['size']} octets):")
            print("-" * 40)
            print(result.data['content'])
            print("-" * 40)
        
        # 5. Créer un template
        print("\n5️⃣ Création d'un template...")
        template_data = {
            "main.py": '''"""{{project_name}} - {{description}}"""

def main():
    print("{{project_name}} is running!")

if __name__ == "__main__":
    main()
''',
            "README.md": '''# {{project_name}}

{{description}}

## Installation
```bash
pip install -r requirements.txt
```

## Usage
```bash
python main.py
```
''',
            "requirements.txt": "# Add your dependencies here\n"
        }
        
        result = await tool.create_template("python_basic", template_data)
        if result.success:
            print(f"✅ Template créé: {result.data['template_path']}")
        
        # 6. Utiliser le template
        print("\n6️⃣ Utilisation du template...")
        variables = {
            "project_name": "My Awesome Project",
            "description": "A project created from template"
        }
        
        result = await tool.use_template(
            "python_basic",
            f"projects/{agent_id}/from_template",
            variables
        )
        if result.success:
            print(f"✅ Template appliqué: {result.data['destination']}")
        
        # 7. Vérifier l'accès local
        print("\n7️⃣ Vérification de l'accès local...")
        local_path = "/app/agent_workspace"
        if os.path.exists(local_path):
            print(f"✅ Répertoire workspace accessible: {local_path}")
            print("   Contenu:")
            for item in os.listdir(local_path):
                print(f"   - {item}")
        
        print("\n✅ Tous les tests réussis!")
        print(f"\n💡 Les fichiers sont accessibles localement dans:")
        print(f"   ./agent_workspace/")
        
    except Exception as e:
        print(f"\n❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_filesystem())