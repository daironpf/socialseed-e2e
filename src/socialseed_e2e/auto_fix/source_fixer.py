"""
Autonomous Source Code Auto-Fixing - EPIC-018
AI-powered code fixes with GitHub/GitLab PR integration.
"""

import json
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx


class VCSProvider(str, Enum):
    """Version control system provider."""
    GITHUB = "github"
    GITLAB = "gitlab"
    BITBUCKET = "bitbucket"


class FixCategory(str, Enum):
    """Category of code fix."""
    NULL_CHECK = "null_check"
    INDEX_BOUNDS = "index_bounds"
    TYPE_MISMATCH = "type_mismatch"
    SYNTAX_ERROR = "syntax_error"
    MEMORY_LEAK = "memory_leak"
    RACE_CONDITION = "race_condition"
    UNHANDLED_EXCEPTION = "unhandled_exception"
    CUSTOM = "custom"


@dataclass
class CodePatch:
    """A code patch to apply."""
    file_path: str
    line_start: int
    line_end: int
    original_code: str
    fixed_code: str
    category: FixCategory
    confidence: float
    explanation: str


@dataclass
class SourceCodeFix:
    """A complete source code fix with PR."""
    id: str
    issue_id: str
    service_name: str
    patches: List[CodePatch]
    test_file: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    pr_url: Optional[str] = None
    status: str = "pending"


class SourceCodeAnalyzer:
    """Analyzes source code to find fix candidates."""
    
    def __init__(self, source_root: Optional[Path] = None):
        self.source_root = source_root or Path.cwd()
    
    def parse_stack_trace(self, stack_trace: str) -> Dict[str, Any]:
        """Parse a Python stack trace to find relevant code."""
        lines = stack_trace.strip().split("\n")
        
        for line in lines:
            if 'File "' in line and ".py" in line:
                parts = line.split('"')
                if len(parts) >= 2:
                    file_path = parts[1]
                    if "line" in line.lower():
                        try:
                            line_num = int([p for p in line.split() if p.isdigit()][0])
                            return {
                                "file": file_path,
                                "line": line_num,
                                "full_trace": stack_trace,
                            }
                        except:
                            pass
        
        return {"full_trace": stack_trace}
    
    def analyze_error(self, error_type: str, error_message: str) -> FixCategory:
        """Analyze error type to determine fix category."""
        error_lower = error_message.lower()
        
        if "index" in error_lower or "indexerror" in error_lower.lower():
            return FixCategory.INDEX_BOUNDS
        if "none" in error_lower or "null" in error_lower or "attributeerror" in error_lower:
            return FixCategory.NULL_CHECK
        if "type" in error_lower or "typeerror" in error_lower.lower():
            return FixCategory.TYPE_MISMATCH
        if "key" in error_lower or "keyerror" in error_lower.lower():
            return FixCategory.NULL_CHECK
        if "memory" in error_lower:
            return FixCategory.MEMORY_LEAK
        if "race" in error_lower or "concurrent" in error_lower:
            return FixCategory.RACE_CONDITION
        
        return FixCategory.UNHANDLED_EXCEPTION
    
    def generate_patch(
        self,
        file_path: str,
        line_num: int,
        category: FixCategory,
    ) -> Optional[CodePatch]:
        """Generate a code patch for the issue."""
        try:
            with open(file_path, "r") as f:
                lines = f.readlines()
            
            if line_num < 1 or line_num > len(lines):
                return None
            
            original_line = lines[line_num - 1]
            
            if category == FixCategory.NULL_CHECK:
                var_name = self._extract_variable_name(original_line)
                if var_name:
                    fixed_line = f"if {var_name} is not None:\n    {original_line}"
                    return CodePatch(
                        file_path=file_path,
                        line_start=line_num,
                        line_end=line_num,
                        original_code=original_line,
                        fixed_code=fixed_line,
                        category=category,
                        confidence=0.85,
                        explanation=f"Added null check for variable '{var_name}'",
                    )
            
            if category == FixCategory.INDEX_BOUNDS:
                if "[" in original_line:
                    fixed_line = original_line.replace("[", "[min(0, len(").replace("]", ") - 1)]")
                    return CodePatch(
                        file_path=file_path,
                        line_start=line_num,
                        line_end=line_num,
                        original_code=original_line,
                        fixed_code=fixed_line,
                        category=category,
                        confidence=0.7,
                        explanation="Added bounds checking to prevent IndexError",
                    )
                    
        except Exception as e:
            print(f"Failed to generate patch: {e}")
        
        return None
    
    def _extract_variable_name(self, line: str) -> Optional[str]:
        """Extract variable name from code line."""
        import re
        patterns = [
            r"(\w+)\s*=",
            r"\.(\w+)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, line)
            if match:
                return match.group(1)
        
        return None


class GitIntegration:
    """Git integration for creating branches and commits."""
    
    def __init__(self, repo_path: Path):
        self.repo_path = repo_path
    
    def create_branch(self, branch_name: str) -> bool:
        """Create a new branch."""
        try:
            subprocess.run(
                ["git", "checkout", "-b", branch_name],
                cwd=self.repo_path,
                capture_output=True,
                check=True,
            )
            return True
        except subprocess.CalledProcessError:
            return False
    
    def apply_patch(self, patch: CodePatch) -> bool:
        """Apply a patch to a file."""
        try:
            with open(patch.file_path, "r") as f:
                lines = f.readlines()
            
            start_idx = patch.line_start - 1
            end_idx = patch.line_end
            
            new_lines = lines[:start_idx]
            new_lines.append(patch.fixed_code)
            new_lines.extend(lines[end_idx:])
            
            with open(patch.file_path, "w") as f:
                f.writelines(new_lines)
            
            return True
        except Exception as e:
            print(f"Failed to apply patch: {e}")
            return False
    
    def commit_changes(self, message: str) -> bool:
        """Commit changes."""
        try:
            subprocess.run(
                ["git", "add", "-A"],
                cwd=self.repo_path,
                capture_output=True,
                check=True,
            )
            subprocess.run(
                ["git", "commit", "-m", message],
                cwd=self.repo_path,
                capture_output=True,
                check=True,
            )
            return True
        except subprocess.CalledProcessError:
            return False
    
    def push_branch(self, branch_name: str) -> bool:
        """Push branch to remote."""
        try:
            subprocess.run(
                ["git", "push", "-u", "origin", branch_name],
                cwd=self.repo_path,
                capture_output=True,
                check=True,
            )
            return True
        except subprocess.CalledProcessError:
            return False


class PRCreator:
    """Creates Pull Requests via API."""
    
    def __init__(
        self,
        provider: VCSProvider = VCSProvider.GITHUB,
        token: Optional[str] = None,
    ):
        self.provider = provider
        self.token = token
    
    async def create_pr(
        self,
        repo_owner: str,
        repo_name: str,
        branch: str,
        title: str,
        body: str,
        base_branch: str = "main",
    ) -> Optional[str]:
        """Create a pull request."""
        if self.provider == VCSProvider.GITHUB:
            return await self._create_github_pr(repo_owner, repo_name, branch, title, body, base_branch)
        elif self.provider == VCSProvider.GITLAB:
            return await self._create_gitlab_mr(repo_owner, repo_name, branch, title, body, base_branch)
        
        return None
    
    async def _create_github_pr(
        self,
        repo_owner: str,
        repo_name: str,
        branch: str,
        title: str,
        body: str,
        base_branch: str,
    ) -> Optional[str]:
        """Create a GitHub pull request."""
        if not self.token:
            return None
        
        url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/pulls"
        
        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json",
        }
        
        payload = {
            "title": title,
            "body": body,
            "head": branch,
            "base": base_branch,
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=payload, headers=headers)
                if response.status_code == 201:
                    data = response.json()
                    return data.get("html_url")
            except Exception as e:
                print(f"GitHub PR creation failed: {e}")
        
        return None
    
    async def _create_gitlab_mr(
        self,
        repo_owner: str,
        repo_name: str,
        branch: str,
        title: str,
        body: str,
        base_branch: str,
    ) -> Optional[str]:
        """Create a GitLab merge request."""
        if not self.token:
            return None
        
        url = f"https://gitlab.com/api/v4/projects/{repo_owner}%2F{repo_name}/merge_requests"
        
        headers = {"PRIVATE-TOKEN": self.token}
        
        payload = {
            "title": title,
            "description": body,
            "source_branch": branch,
            "target_branch": base_branch,
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=payload, headers=headers)
                if response.status_code == 201:
                    data = response.json()
                    return data.get("web_url")
            except Exception as e:
                print(f"GitLab MR creation failed: {e}")
        
        return None


class AutoFixOrchestrator:
    """Orchestrates the auto-fixing workflow."""
    
    def __init__(
        self,
        source_root: Path,
        vcs_provider: VCSProvider = VCSProvider.GITHUB,
        vcs_token: Optional[str] = None,
    ):
        self.analyzer = SourceCodeAnalyzer(source_root)
        self.git = GitIntegration(source_root)
        self.pr_creator = PRCreator(vcs_provider, vcs_token)
        self._fixes: Dict[str, SourceCodeFix] = {}
    
    async def create_fix(
        self,
        issue_id: str,
        service_name: str,
        error_type: str,
        error_message: str,
        stack_trace: str,
        test_file: Optional[str] = None,
    ) -> SourceCodeFix:
        """Create a code fix for an error."""
        import uuid
        fix_id = f"fix-{uuid.uuid4().hex[:8]}"
        
        parsed = self.analyzer.parse_stack_trace(stack_trace)
        category = self.analyzer.analyze_error(error_type, error_message)
        
        patches = []
        if "file" in parsed and "line" in parsed:
            patch = self.analyzer.generate_patch(
                parsed["file"],
                parsed["line"],
                category,
            )
            if patch:
                patches.append(patch)
        
        fix = SourceCodeFix(
            id=fix_id,
            issue_id=issue_id,
            service_name=service_name,
            patches=patches,
            test_file=test_file,
        )
        
        self._fixes[fix_id] = fix
        return fix
    
    def apply_fix(self, fix_id: str) -> bool:
        """Apply a fix to the source code."""
        fix = self._fixes.get(fix_id)
        if not fix:
            return False
        
        branch_name = f"auto-fix/{fix.issue_id}"
        
        self.git.create_branch(branch_name)
        
        for patch in fix.patches:
            self.git.apply_patch(patch)
        
        message = f"Auto-fix: {fix.issue_id}\n\n" + "\n".join(
            p.explanation for p in fix.patches
        )
        
        self.git.commit_changes(message)
        self.git.push_branch(branch_name)
        
        return True
    
    async def create_pr(
        self,
        fix_id: str,
        repo_owner: str,
        repo_name: str,
        base_branch: str = "main",
    ) -> Optional[str]:
        """Create a PR for the fix."""
        fix = self._fixes.get(fix_id)
        if not fix:
            return None
        
        if not self.apply_fix(fix_id):
            return None
        
        title = f"[Auto-Fix] {fix.issue_id}"
        
        body = f"""## Auto-Generated Fix

### Issue
{fix.issue_id}

### Service
{fix.service_name}

### Changes
"""
        for patch in fix.patches:
            body += f"""
#### {patch.category.value}
- **File**: `{patch.file_path}`
- **Lines**: {patch.line_start}-{patch.line_end}
- **Confidence**: {patch.confidence:.0%}
- **Explanation**: {patch.explanation}
```
--- Original
+{patch.fixed_code}
```
"""
        
        if fix.test_file:
            body += f"\n### Test\nA test file has been generated: `{fix.test_file}`\n"
        
        pr_url = await self.pr_creator.create_pr(
            repo_owner=repo_owner,
            repo_name=repo_name,
            branch=f"auto-fix/{fix.issue_id}",
            title=title,
            body=body,
            base_branch=base_branch,
        )
        
        if pr_url:
            fix.pr_url = pr_url
            fix.status = "pr_created"
        
        return pr_url
    
    def get_fix(self, fix_id: str) -> Optional[SourceCodeFix]:
        """Get a fix by ID."""
        return self._fixes.get(fix_id)
    
    def list_fixes(self) -> List[Dict[str, Any]]:
        """List all fixes."""
        return [
            {
                "id": f.id,
                "issue_id": f.issue_id,
                "service_name": f.service_name,
                "patches_count": len(f.patches),
                "test_file": f.test_file,
                "pr_url": f.pr_url,
                "status": f.status,
            }
            for f in self._fixes.values()
        ]


_global_orchestrator: Optional[AutoFixOrchestrator] = None


def get_auto_fix_orchestrator(
    source_root: Optional[Path] = None,
    vcs_provider: VCSProvider = VCSProvider.GITHUB,
    vcs_token: Optional[str] = None,
) -> AutoFixOrchestrator:
    """Get global auto-fix orchestrator."""
    global _global_orchestrator
    if _global_orchestrator is None:
        _global_orchestrator = AutoFixOrchestrator(
            source_root or Path.cwd(),
            vcs_provider,
            vcs_token,
        )
    return _global_orchestrator
