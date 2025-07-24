"""
Git Version Control Tool for MAS Agents
Provides Git operations and repository management
"""

import subprocess
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import logging
import os

from .base_tool import BaseTool, ToolResult

logger = logging.getLogger(__name__)


class GitTool(BaseTool):
    """Tool for Git version control operations"""
    
    def __init__(self, agent_id: str, workspace_root: str = "/app/agent_workspace"):
        super().__init__(
            name="GitTool",
            description="Perform Git version control operations",
            parameters={
                "action": {
                    "type": "string",
                    "enum": ["init", "clone", "status", "add", "commit", "push", "pull", 
                            "branch", "checkout", "merge", "log", "diff", "remote"],
                    "description": "Git action to perform"
                },
                "repository": {
                    "type": "string",
                    "description": "Repository path or URL"
                },
                "branch": {
                    "type": "string",
                    "description": "Branch name"
                },
                "message": {
                    "type": "string",
                    "description": "Commit message"
                },
                "files": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Files to add or commit"
                },
                "remote": {
                    "type": "string",
                    "description": "Remote name"
                }
            },
            required=["action"]
        )
        self.agent_id = agent_id
        self.workspace_root = Path(workspace_root)
        self.repos_dir = self.workspace_root / "repositories"
        self.repos_dir.mkdir(exist_ok=True)
        
    async def execute(self, **kwargs) -> ToolResult:
        """Execute Git tool action"""
        action = kwargs.get("action")
        
        try:
            if action == "init":
                return await self._init_repo(kwargs)
            elif action == "clone":
                return await self._clone_repo(kwargs)
            elif action == "status":
                return await self._get_status(kwargs)
            elif action == "add":
                return await self._add_files(kwargs)
            elif action == "commit":
                return await self._commit_changes(kwargs)
            elif action == "push":
                return await self._push_changes(kwargs)
            elif action == "pull":
                return await self._pull_changes(kwargs)
            elif action == "branch":
                return await self._manage_branch(kwargs)
            elif action == "checkout":
                return await self._checkout(kwargs)
            elif action == "merge":
                return await self._merge_branch(kwargs)
            elif action == "log":
                return await self._get_log(kwargs)
            elif action == "diff":
                return await self._get_diff(kwargs)
            elif action == "remote":
                return await self._manage_remote(kwargs)
            else:
                return ToolResult(
                    success=False,
                    error=f"Unknown action: {action}"
                )
        except Exception as e:
            logger.error(f"Git tool error: {e}")
            return ToolResult(
                success=False,
                error=str(e)
            )
            
    def _run_git_command(self, cmd: List[str], cwd: Optional[Path] = None) -> Tuple[bool, str, str]:
        """Run a git command and return success, stdout, stderr"""
        try:
            result = subprocess.run(
                ["git"] + cmd,
                cwd=cwd or self.workspace_root,
                capture_output=True,
                text=True,
                check=True
            )
            return True, result.stdout, result.stderr
        except subprocess.CalledProcessError as e:
            return False, e.stdout, e.stderr
            
    async def _init_repo(self, params: Dict[str, Any]) -> ToolResult:
        """Initialize a new Git repository"""
        repo_name = params.get("repository", "new_repo")
        repo_path = self.repos_dir / repo_name
        
        # Create directory
        repo_path.mkdir(exist_ok=True)
        
        # Initialize git
        success, stdout, stderr = self._run_git_command(["init"], cwd=repo_path)
        
        if success:
            # Set default branch to main
            self._run_git_command(["branch", "-M", "main"], cwd=repo_path)
            
            # Configure user
            self._run_git_command(
                ["config", "user.name", f"Agent-{self.agent_id}"], 
                cwd=repo_path
            )
            self._run_git_command(
                ["config", "user.email", f"agent-{self.agent_id}@mas.local"], 
                cwd=repo_path
            )
            
            return ToolResult(
                success=True,
                data={
                    "message": f"Repository initialized at {repo_path}",
                    "path": str(repo_path)
                }
            )
        else:
            return ToolResult(
                success=False,
                error=f"Failed to initialize repository: {stderr}"
            )
            
    async def _clone_repo(self, params: Dict[str, Any]) -> ToolResult:
        """Clone a Git repository"""
        repo_url = params.get("repository")
        if not repo_url:
            return ToolResult(success=False, error="Repository URL required")
            
        # Extract repo name from URL
        repo_name = repo_url.split("/")[-1].replace(".git", "")
        repo_path = self.repos_dir / repo_name
        
        success, stdout, stderr = self._run_git_command(
            ["clone", repo_url, str(repo_path)]
        )
        
        if success:
            return ToolResult(
                success=True,
                data={
                    "message": f"Repository cloned to {repo_path}",
                    "path": str(repo_path)
                }
            )
        else:
            return ToolResult(
                success=False,
                error=f"Failed to clone repository: {stderr}"
            )
            
    async def _get_status(self, params: Dict[str, Any]) -> ToolResult:
        """Get repository status"""
        repo_path = self._get_repo_path(params)
        
        success, stdout, stderr = self._run_git_command(
            ["status", "--porcelain", "-b"], 
            cwd=repo_path
        )
        
        if success:
            lines = stdout.strip().split("\n")
            branch_info = lines[0] if lines else ""
            
            # Parse status
            files = {
                "modified": [],
                "added": [],
                "deleted": [],
                "untracked": []
            }
            
            for line in lines[1:]:
                if not line:
                    continue
                    
                status = line[:2]
                filename = line[3:]
                
                if status == "??":
                    files["untracked"].append(filename)
                elif "M" in status:
                    files["modified"].append(filename)
                elif "A" in status:
                    files["added"].append(filename)
                elif "D" in status:
                    files["deleted"].append(filename)
                    
            return ToolResult(
                success=True,
                data={
                    "branch": branch_info,
                    "files": files,
                    "clean": len(files["modified"]) == 0 and len(files["untracked"]) == 0
                }
            )
        else:
            return ToolResult(
                success=False,
                error=f"Failed to get status: {stderr}"
            )
            
    async def _add_files(self, params: Dict[str, Any]) -> ToolResult:
        """Add files to staging area"""
        repo_path = self._get_repo_path(params)
        files = params.get("files", ["."])
        
        success, stdout, stderr = self._run_git_command(
            ["add"] + files,
            cwd=repo_path
        )
        
        if success:
            # Get updated status
            status_result = await self._get_status(params)
            
            return ToolResult(
                success=True,
                data={
                    "message": f"Added {len(files)} file(s) to staging",
                    "status": status_result.data if status_result.success else None
                }
            )
        else:
            return ToolResult(
                success=False,
                error=f"Failed to add files: {stderr}"
            )
            
    async def _commit_changes(self, params: Dict[str, Any]) -> ToolResult:
        """Commit staged changes"""
        repo_path = self._get_repo_path(params)
        message = params.get("message", "Automated commit by MAS agent")
        
        success, stdout, stderr = self._run_git_command(
            ["commit", "-m", message],
            cwd=repo_path
        )
        
        if success:
            # Get commit hash
            hash_success, hash_out, _ = self._run_git_command(
                ["rev-parse", "HEAD"],
                cwd=repo_path
            )
            
            return ToolResult(
                success=True,
                data={
                    "message": "Changes committed successfully",
                    "commit_hash": hash_out.strip() if hash_success else None,
                    "commit_message": message
                }
            )
        else:
            if "nothing to commit" in stderr:
                return ToolResult(
                    success=True,
                    data={"message": "No changes to commit"}
                )
            return ToolResult(
                success=False,
                error=f"Failed to commit: {stderr}"
            )
            
    async def _push_changes(self, params: Dict[str, Any]) -> ToolResult:
        """Push changes to remote"""
        repo_path = self._get_repo_path(params)
        remote = params.get("remote", "origin")
        branch = params.get("branch", "main")
        
        success, stdout, stderr = self._run_git_command(
            ["push", remote, branch],
            cwd=repo_path
        )
        
        if success:
            return ToolResult(
                success=True,
                data={
                    "message": f"Pushed to {remote}/{branch}",
                    "output": stdout
                }
            )
        else:
            return ToolResult(
                success=False,
                error=f"Failed to push: {stderr}"
            )
            
    async def _pull_changes(self, params: Dict[str, Any]) -> ToolResult:
        """Pull changes from remote"""
        repo_path = self._get_repo_path(params)
        remote = params.get("remote", "origin")
        branch = params.get("branch", "main")
        
        success, stdout, stderr = self._run_git_command(
            ["pull", remote, branch],
            cwd=repo_path
        )
        
        if success:
            return ToolResult(
                success=True,
                data={
                    "message": f"Pulled from {remote}/{branch}",
                    "output": stdout
                }
            )
        else:
            return ToolResult(
                success=False,
                error=f"Failed to pull: {stderr}"
            )
            
    async def _manage_branch(self, params: Dict[str, Any]) -> ToolResult:
        """Create, list, or delete branches"""
        repo_path = self._get_repo_path(params)
        branch_name = params.get("branch")
        
        if not branch_name:
            # List branches
            success, stdout, stderr = self._run_git_command(
                ["branch", "-a"],
                cwd=repo_path
            )
            
            if success:
                branches = [b.strip() for b in stdout.split("\n") if b.strip()]
                current = next((b[2:] for b in branches if b.startswith("*")), None)
                
                return ToolResult(
                    success=True,
                    data={
                        "branches": branches,
                        "current": current
                    }
                )
        else:
            # Create branch
            success, stdout, stderr = self._run_git_command(
                ["branch", branch_name],
                cwd=repo_path
            )
            
            if success:
                return ToolResult(
                    success=True,
                    data={"message": f"Created branch {branch_name}"}
                )
                
        return ToolResult(
            success=False,
            error=f"Branch operation failed: {stderr}"
        )
        
    async def _checkout(self, params: Dict[str, Any]) -> ToolResult:
        """Checkout a branch or commit"""
        repo_path = self._get_repo_path(params)
        target = params.get("branch") or params.get("commit")
        
        if not target:
            return ToolResult(success=False, error="Branch or commit required")
            
        success, stdout, stderr = self._run_git_command(
            ["checkout", target],
            cwd=repo_path
        )
        
        if success:
            return ToolResult(
                success=True,
                data={
                    "message": f"Checked out {target}",
                    "output": stdout
                }
            )
        else:
            return ToolResult(
                success=False,
                error=f"Failed to checkout: {stderr}"
            )
            
    async def _merge_branch(self, params: Dict[str, Any]) -> ToolResult:
        """Merge a branch"""
        repo_path = self._get_repo_path(params)
        branch = params.get("branch")
        
        if not branch:
            return ToolResult(success=False, error="Branch name required")
            
        success, stdout, stderr = self._run_git_command(
            ["merge", branch],
            cwd=repo_path
        )
        
        if success:
            return ToolResult(
                success=True,
                data={
                    "message": f"Merged {branch}",
                    "output": stdout
                }
            )
        else:
            if "CONFLICT" in stdout:
                # Get conflict files
                status_result = await self._get_status(params)
                return ToolResult(
                    success=False,
                    error="Merge conflicts detected",
                    data={
                        "conflicts": True,
                        "status": status_result.data if status_result.success else None
                    }
                )
            return ToolResult(
                success=False,
                error=f"Failed to merge: {stderr}"
            )
            
    async def _get_log(self, params: Dict[str, Any]) -> ToolResult:
        """Get commit log"""
        repo_path = self._get_repo_path(params)
        limit = params.get("limit", 10)
        
        success, stdout, stderr = self._run_git_command(
            ["log", f"-{limit}", "--oneline", "--graph"],
            cwd=repo_path
        )
        
        if success:
            commits = []
            for line in stdout.strip().split("\n"):
                if line:
                    parts = line.split(" ", 2)
                    if len(parts) >= 2:
                        commits.append({
                            "hash": parts[1][:7] if len(parts) > 1 else "",
                            "message": parts[2] if len(parts) > 2 else ""
                        })
                        
            return ToolResult(
                success=True,
                data={
                    "commits": commits,
                    "count": len(commits)
                }
            )
        else:
            return ToolResult(
                success=False,
                error=f"Failed to get log: {stderr}"
            )
            
    async def _get_diff(self, params: Dict[str, Any]) -> ToolResult:
        """Get file differences"""
        repo_path = self._get_repo_path(params)
        files = params.get("files", [])
        
        cmd = ["diff"]
        if params.get("staged"):
            cmd.append("--cached")
            
        cmd.extend(files)
        
        success, stdout, stderr = self._run_git_command(cmd, cwd=repo_path)
        
        if success:
            return ToolResult(
                success=True,
                data={
                    "diff": stdout,
                    "has_changes": bool(stdout.strip())
                }
            )
        else:
            return ToolResult(
                success=False,
                error=f"Failed to get diff: {stderr}"
            )
            
    async def _manage_remote(self, params: Dict[str, Any]) -> ToolResult:
        """Manage remote repositories"""
        repo_path = self._get_repo_path(params)
        remote_name = params.get("remote", "origin")
        remote_url = params.get("url")
        
        if not remote_url:
            # List remotes
            success, stdout, stderr = self._run_git_command(
                ["remote", "-v"],
                cwd=repo_path
            )
            
            if success:
                remotes = {}
                for line in stdout.strip().split("\n"):
                    if line:
                        parts = line.split("\t")
                        if len(parts) >= 2:
                            name = parts[0]
                            url = parts[1].split(" ")[0]
                            remotes[name] = url
                            
                return ToolResult(
                    success=True,
                    data={"remotes": remotes}
                )
        else:
            # Add remote
            success, stdout, stderr = self._run_git_command(
                ["remote", "add", remote_name, remote_url],
                cwd=repo_path
            )
            
            if success:
                return ToolResult(
                    success=True,
                    data={"message": f"Added remote {remote_name}"}
                )
                
        return ToolResult(
            success=False,
            error=f"Remote operation failed: {stderr}"
        )
        
    def _get_repo_path(self, params: Dict[str, Any]) -> Path:
        """Get repository path from params or use default"""
        repo = params.get("repository")
        if repo and "/" not in repo:
            return self.repos_dir / repo
        elif repo:
            return Path(repo)
        else:
            # Try to find a repo in current directory
            return self.workspace_root