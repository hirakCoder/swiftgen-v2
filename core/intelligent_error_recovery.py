"""
Intelligent Error Recovery System
Combines pattern-based fixes with LLM-powered recovery for unknown errors
"""

import re
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import asyncio

@dataclass
class ErrorContext:
    """Context for error recovery"""
    error_message: str
    file_path: str
    file_content: str
    line_number: Optional[int] = None
    error_type: Optional[str] = None

class IntelligentErrorRecovery:
    """
    Multi-tiered error recovery system:
    1. Pattern-based fixes (fast, deterministic)
    2. LLM-based fixes (smart, adaptive)
    3. Learning system (remembers successful fixes)
    """
    
    def __init__(self, llm_service=None):
        self.llm_service = llm_service
        self.fix_cache = {}  # Cache successful fixes
        self.pattern_fixer = None  # Will import existing error_handler
        
    async def recover_from_error(self, error_output: str, project_path: str) -> Dict:
        """
        Main entry point for intelligent error recovery
        """
        print("🧠 Intelligent Error Recovery Started...")
        
        # Phase 1: Try pattern-based fixes (fast)
        from core.error_handler import error_fixer
        pattern_result = error_fixer.auto_fix_compilation_errors(error_output, project_path)
        
        if pattern_result["success"]:
            print(f"✅ Fixed with patterns: {pattern_result['fixed_count']} errors")
            return pattern_result
        
        # Phase 2: Analyze unfixed errors
        print("🤔 Pattern matching failed, analyzing with LLM...")
        unfixed_errors = self._extract_unfixed_errors(error_output)
        
        if not unfixed_errors:
            return {
                "success": False,
                "message": "No errors could be extracted",
                "fixed_count": 0
            }
        
        # Phase 3: Check cache for similar errors
        for error in unfixed_errors:
            cached_fix = self._check_cache(error)
            if cached_fix:
                print(f"📦 Found cached fix for: {error[:50]}...")
                success = self._apply_cached_fix(cached_fix, project_path)
                if success:
                    return {
                        "success": True,
                        "message": "Fixed with cached solution",
                        "fixed_count": 1
                    }
        
        # Phase 4: Use LLM for intelligent fix
        if self.llm_service:
            llm_result = await self._llm_error_recovery(unfixed_errors, project_path)
            if llm_result["success"]:
                # Cache the successful fix
                self._cache_fix(unfixed_errors[0], llm_result["fix"])
                return llm_result
        
        # Phase 5: Fallback strategies
        return self._apply_fallback_strategies(error_output, project_path)
    
    def _extract_unfixed_errors(self, error_output: str) -> List[str]:
        """Extract individual errors from compiler output"""
        errors = []
        
        # Swift error pattern: file:line:column: error: message
        error_pattern = r'([^:]+\.swift):(\d+):(\d+): error: (.+?)(?=\n[^\s]|\Z)'
        matches = re.finditer(error_pattern, error_output, re.MULTILINE | re.DOTALL)
        
        for match in matches:
            file_path = match.group(1)
            line_num = match.group(2)
            error_msg = match.group(4).strip()
            errors.append(f"{file_path}:{line_num}: {error_msg}")
        
        return errors
    
    async def _llm_error_recovery(self, errors: List[str], project_path: str) -> Dict:
        """Use LLM to intelligently fix errors"""
        
        # Read the problematic files
        file_contents = {}
        for error in errors:
            if '.swift:' in error:
                file_path = error.split(':')[0]
                if file_path not in file_contents:
                    try:
                        full_path = f"{project_path}/Sources/{file_path.split('/')[-1]}"
                        with open(full_path, 'r') as f:
                            file_contents[file_path] = f.read()
                    except:
                        pass
        
        # Build prompt for LLM
        prompt = self._build_llm_fix_prompt(errors, file_contents)
        
        try:
            # Call LLM for fix with intelligent routing for error/compilation tasks
            if hasattr(self.llm_service, 'generate'):
                # Check if the service supports task_type parameter
                import inspect
                sig = inspect.signature(self.llm_service.generate)
                if 'task_type' in sig.parameters:
                    # Use intelligent routing for compilation errors
                    response = await self.llm_service.generate(
                        prompt,
                        task_type='compilation_error'  # This will route to Claude/GPT-4
                    )
                else:
                    response = await self.llm_service.generate(prompt)
            else:
                response = await self.llm_service.generate(prompt)
            
            # Parse and apply fix
            fix_data = self._parse_llm_response(response)
            
            if fix_data:
                success = self._apply_llm_fix(fix_data, project_path)
                
                if success:
                    return {
                        "success": True,
                        "message": "Fixed with LLM assistance",
                        "fixed_count": len(fix_data.get("fixes", [])),
                        "fix": fix_data
                    }
        except Exception as e:
            print(f"❌ LLM error recovery failed: {e}")
        
        return {"success": False, "message": "LLM recovery failed"}
    
    def _build_llm_fix_prompt(self, errors: List[str], file_contents: Dict[str, str]) -> str:
        """Build prompt for LLM to fix errors"""
        prompt = """You are a Swift/SwiftUI expert. Fix the following compilation errors.

ERRORS:
"""
        for error in errors[:5]:  # Limit to first 5 errors
            prompt += f"- {error}\n"
        
        prompt += "\n\nFILE CONTENTS:\n"
        for file_path, content in file_contents.items():
            prompt += f"\n// {file_path}\n{content}\n"
        
        prompt += """
TASK: Analyze these errors and provide fixes. Return JSON:
{
    "fixes": [
        {
            "file": "filename.swift",
            "error": "description of error",
            "fix_type": "add_import|modify_code|add_function|fix_syntax",
            "changes": [
                {
                    "old": "exact text to replace",
                    "new": "replacement text"
                }
            ]
        }
    ],
    "explanation": "Brief explanation of what was fixed"
}

Focus on:
1. Missing imports (UIKit, SwiftUI, Foundation)
2. Syntax errors
3. Type mismatches
4. Missing protocol conformances
5. Undefined symbols

Ensure your fixes are valid Swift code."""
        
        return prompt
    
    def _parse_llm_response(self, response) -> Optional[Dict]:
        """Parse LLM response into actionable fixes"""
        try:
            # Handle different response types
            if hasattr(response, 'content'):
                content = response.content
            elif isinstance(response, dict):
                content = json.dumps(response)
            else:
                content = str(response)
            
            # Extract JSON from response
            if '```json' in content:
                json_start = content.index('```json') + 7
                json_end = content.index('```', json_start)
                content = content[json_start:json_end]
            elif '{' in content:
                # Find JSON boundaries
                json_start = content.index('{')
                json_end = content.rindex('}') + 1
                content = content[json_start:json_end]
            
            return json.loads(content)
        except Exception as e:
            print(f"Failed to parse LLM response: {e}")
            return None
    
    def _apply_llm_fix(self, fix_data: Dict, project_path: str) -> bool:
        """Apply fixes suggested by LLM"""
        import os
        
        try:
            for fix in fix_data.get("fixes", []):
                file_name = fix["file"]
                file_path = os.path.join(project_path, "Sources", file_name)
                
                if not os.path.exists(file_path):
                    # Try without Sources directory
                    file_path = os.path.join(project_path, file_name)
                
                if os.path.exists(file_path):
                    with open(file_path, 'r') as f:
                        content = f.read()
                    
                    # Apply changes
                    for change in fix.get("changes", []):
                        old_text = change.get("old", "")
                        new_text = change.get("new", "")
                        
                        if old_text and old_text in content:
                            content = content.replace(old_text, new_text)
                        elif fix["fix_type"] == "add_import":
                            # Add import at the beginning
                            import_line = new_text if new_text else f"import {fix.get('module', 'SwiftUI')}"
                            if import_line not in content:
                                content = import_line + "\n" + content
                    
                    # Write back
                    with open(file_path, 'w') as f:
                        f.write(content)
                    
                    print(f"✅ Applied LLM fix to {file_name}")
            
            return True
        except Exception as e:
            print(f"Failed to apply LLM fix: {e}")
            return False
    
    def _apply_fallback_strategies(self, error_output: str, project_path: str) -> Dict:
        """Apply last-resort fallback strategies"""
        strategies_applied = []
        
        # Strategy 1: Add common missing imports
        if "cannot find" in error_output or "no member" in error_output:
            self._add_common_imports(project_path)
            strategies_applied.append("Added common imports")
        
        # Strategy 2: Fix obvious syntax issues
        if "expected" in error_output:
            self._fix_basic_syntax(project_path)
            strategies_applied.append("Fixed basic syntax")
        
        # Strategy 3: Ensure main app structure
        if "@main" in error_output:
            self._ensure_app_structure(project_path)
            strategies_applied.append("Fixed app structure")
        
        return {
            "success": len(strategies_applied) > 0,
            "message": f"Applied fallback strategies: {', '.join(strategies_applied)}",
            "fixed_count": len(strategies_applied)
        }
    
    def _add_common_imports(self, project_path: str):
        """Add commonly needed imports to all Swift files"""
        import os
        
        sources_dir = os.path.join(project_path, "Sources")
        if not os.path.exists(sources_dir):
            return
        
        for file_name in os.listdir(sources_dir):
            if file_name.endswith('.swift'):
                file_path = os.path.join(sources_dir, file_name)
                with open(file_path, 'r') as f:
                    content = f.read()
                
                # Add SwiftUI if it's a View file
                if 'View {' in content and 'import SwiftUI' not in content:
                    content = 'import SwiftUI\n' + content
                
                # Add UIKit if haptic feedback is used
                if 'UIImpactFeedbackGenerator' in content and 'import UIKit' not in content:
                    content = 'import UIKit\n' + content
                
                # Add Foundation for basic types
                if any(t in content for t in ['Timer', 'Date', 'URL']) and 'import Foundation' not in content:
                    content = 'import Foundation\n' + content
                
                with open(file_path, 'w') as f:
                    f.write(content)
    
    def _fix_basic_syntax(self, project_path: str):
        """Fix basic syntax issues"""
        import os
        
        sources_dir = os.path.join(project_path, "Sources")
        if not os.path.exists(sources_dir):
            return
        
        for file_name in os.listdir(sources_dir):
            if file_name.endswith('.swift'):
                file_path = os.path.join(sources_dir, file_name)
                with open(file_path, 'r') as f:
                    content = f.read()
                
                # Balance braces
                open_braces = content.count('{')
                close_braces = content.count('}')
                if open_braces > close_braces:
                    content += '\n' + ('}' * (open_braces - close_braces))
                
                with open(file_path, 'w') as f:
                    f.write(content)
    
    def _ensure_app_structure(self, project_path: str):
        """Ensure proper app structure for SwiftUI apps"""
        import os
        
        sources_dir = os.path.join(project_path, "Sources")
        if not os.path.exists(sources_dir):
            return
        
        # Find the @main file
        for file_name in os.listdir(sources_dir):
            if 'App.swift' in file_name:
                file_path = os.path.join(sources_dir, file_name)
                with open(file_path, 'r') as f:
                    content = f.read()
                
                # Ensure SwiftUI import
                if 'import SwiftUI' not in content:
                    content = 'import SwiftUI\n' + content
                
                # Ensure proper App protocol
                if ': App' in content and 'some Scene' in content:
                    # Structure looks correct, just missing import
                    pass
                
                with open(file_path, 'w') as f:
                    f.write(content)
    
    def _check_cache(self, error: str) -> Optional[Dict]:
        """Check if we've seen and fixed this error before"""
        # Simple cache lookup (could be enhanced with fuzzy matching)
        error_key = self._normalize_error(error)
        return self.fix_cache.get(error_key)
    
    def _cache_fix(self, error: str, fix: Dict):
        """Cache a successful fix for future use"""
        error_key = self._normalize_error(error)
        self.fix_cache[error_key] = fix
    
    def _normalize_error(self, error: str) -> str:
        """Normalize error for caching"""
        # Remove file paths and line numbers
        normalized = re.sub(r'[\w/]+\.swift:\d+:\d+:', '', error)
        # Remove specific identifiers
        normalized = re.sub(r"'[^']+'", "'IDENTIFIER'", normalized)
        return normalized.strip()
    
    def _apply_cached_fix(self, fix: Dict, project_path: str) -> bool:
        """Apply a previously cached fix"""
        return self._apply_llm_fix(fix, project_path)

# Global instance
intelligent_recovery = IntelligentErrorRecovery()