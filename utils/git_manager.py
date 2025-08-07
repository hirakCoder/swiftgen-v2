"""
GitHub Management Agent for SwiftGen V2
Handles all Git operations and branch management
"""

import subprocess
import os
from typing import Optional, Dict, List
from datetime import datetime

class GitHubAgent:
    """
    Manages Git operations for feature development workflow
    """
    
    def __init__(self, repo_path: str = "."):
        self.repo_path = repo_path
        self.remote = "origin"
        self.main_branch = "main"
        
    def execute_git_command(self, command: List[str]) -> Dict:
        """Execute a git command and return result"""
        try:
            result = subprocess.run(
                ["git"] + command,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            return {
                "success": True,
                "output": result.stdout.strip(),
                "command": " ".join(["git"] + command)
            }
        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "error": e.stderr.strip(),
                "command": " ".join(["git"] + command)
            }
    
    def current_branch(self) -> str:
        """Get current branch name"""
        result = self.execute_git_command(["branch", "--show-current"])
        return result["output"] if result["success"] else "unknown"
    
    def create_feature_branch(self, feature_name: str) -> Dict:
        """Create and checkout a new feature branch"""
        branch_name = f"feature/{feature_name}"
        
        # Ensure we're on main and up to date
        self.execute_git_command(["checkout", self.main_branch])
        self.execute_git_command(["pull", self.remote, self.main_branch])
        
        # Create and checkout new branch
        result = self.execute_git_command(["checkout", "-b", branch_name])
        
        if result["success"]:
            print(f"✅ Created feature branch: {branch_name}")
        else:
            print(f"❌ Failed to create branch: {result['error']}")
        
        return result
    
    def commit_changes(self, message: str, files: Optional[List[str]] = None) -> Dict:
        """Stage and commit changes"""
        # Stage files
        if files:
            for file in files:
                self.execute_git_command(["add", file])
        else:
            self.execute_git_command(["add", "-A"])
        
        # Commit
        result = self.execute_git_command(["commit", "-m", message])
        
        if result["success"]:
            print(f"✅ Committed: {message}")
        else:
            print(f"❌ Commit failed: {result['error']}")
        
        return result
    
    def push_branch(self, branch_name: Optional[str] = None) -> Dict:
        """Push current or specified branch to remote"""
        if not branch_name:
            branch_name = self.current_branch()
        
        result = self.execute_git_command(["push", "-u", self.remote, branch_name])
        
        if result["success"]:
            print(f"✅ Pushed branch: {branch_name}")
        else:
            print(f"❌ Push failed: {result['error']}")
        
        return result
    
    def create_pull_request_url(self) -> str:
        """Generate GitHub PR URL for current branch"""
        current = self.current_branch()
        if current and current != self.main_branch:
            return f"https://github.com/hirakCoder/swiftgen-v2/compare/{self.main_branch}...{current}?expand=1"
        return ""
    
    def merge_to_main(self, branch_name: str, delete_branch: bool = True) -> Dict:
        """Merge feature branch to main"""
        # Checkout main
        self.execute_git_command(["checkout", self.main_branch])
        self.execute_git_command(["pull", self.remote, self.main_branch])
        
        # Merge feature branch
        result = self.execute_git_command(["merge", branch_name, "--no-ff"])
        
        if result["success"]:
            print(f"✅ Merged {branch_name} to {self.main_branch}")
            
            # Push main
            self.execute_git_command(["push", self.remote, self.main_branch])
            
            # Delete feature branch if requested
            if delete_branch:
                self.execute_git_command(["branch", "-d", branch_name])
                self.execute_git_command(["push", self.remote, "--delete", branch_name])
                print(f"🗑️ Deleted branch: {branch_name}")
        else:
            print(f"❌ Merge failed: {result['error']}")
        
        return result
    
    def status(self) -> Dict:
        """Get repository status"""
        status = self.execute_git_command(["status", "--short"])
        branch = self.current_branch()
        
        return {
            "branch": branch,
            "changes": status["output"].split("\n") if status["output"] else [],
            "clean": not bool(status["output"])
        }
    
    def run_tests(self) -> bool:
        """Run tests before merging (placeholder for actual tests)"""
        print("🧪 Running tests...")
        
        # Add actual test commands here
        tests = [
            # Test that server starts
            ["python", "-c", "import main; print('✓ Main module loads')"],
            # Test imports
            ["python", "-c", "from core.intent import IntentParser; print('✓ Intent parser loads')"],
            ["python", "-c", "from build.direct_build import DirectBuildSystem; print('✓ Build system loads')"],
        ]
        
        for test in tests:
            try:
                subprocess.run(test, cwd=self.repo_path, check=True, capture_output=True)
            except subprocess.CalledProcessError:
                print(f"❌ Test failed: {' '.join(test)}")
                return False
        
        print("✅ All tests passed!")
        return True
    
    def workflow_status(self) -> str:
        """Get current workflow status and next steps"""
        current = self.current_branch()
        status = self.status()
        
        report = f"""
📊 Git Workflow Status
=====================
Current Branch: {current}
Clean Working Directory: {status['clean']}
"""
        
        if current.startswith("feature/"):
            report += """
Next Steps:
1. Complete feature implementation
2. Run tests: git_agent.run_tests()
3. Commit changes: git_agent.commit_changes("message")
4. Push branch: git_agent.push_branch()
5. Create PR: Visit the URL from git_agent.create_pull_request_url()
6. After review, merge: git_agent.merge_to_main(branch_name)
"""
        elif current == self.main_branch:
            report += """
Next Steps:
1. Create feature branch: git_agent.create_feature_branch("feature-name")
2. Implement feature
3. Follow feature workflow
"""
        
        if status['changes']:
            report += f"\nUncommitted changes:\n"
            for change in status['changes'][:5]:
                report += f"  {change}\n"
            if len(status['changes']) > 5:
                report += f"  ... and {len(status['changes']) - 5} more\n"
        
        return report

# Global instance for easy access
git_agent = GitHubAgent()

if __name__ == "__main__":
    # Example usage
    agent = GitHubAgent()
    print(agent.workflow_status())
    
    # Show PR URL if on feature branch
    pr_url = agent.create_pull_request_url()
    if pr_url:
        print(f"\n🔗 Create PR at: {pr_url}")