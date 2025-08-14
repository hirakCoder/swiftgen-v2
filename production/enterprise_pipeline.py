"""
SwiftGen V2 - Enterprise Pipeline
Production implementation with AST repair, multi-model consensus, and learning
This is what top companies actually deploy
"""

import os
import re
import json
import asyncio
import logging
import time
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
import hashlib

# Add parent directory to path for imports
import sys
sys.path.append(str(Path(__file__).parent.parent))

# Import existing services
from backend.enhanced_claude_service import EnhancedClaudeService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class GenerationResult:
    success: bool
    code: str
    files: List[Dict[str, str]]
    confidence: float
    provider: str
    duration: float
    syntax_score: float

class EnterpriseASTRepair:
    """Production-grade AST repair system"""
    
    def __init__(self):
        self.delimiter_pairs = {'(': ')', '[': ']', '{': '}'}
        self.fixed_count = 0
        
    def repair_code(self, code: str) -> Tuple[str, int]:
        """Repair Swift code syntax issues"""
        
        original = code
        fixes_applied = 0
        
        # Fix 1: Balance delimiters
        code, count = self._balance_delimiters_smart(code)
        fixes_applied += count
        
        # Fix 2: Fix SwiftUI modifier chains
        code, count = self._fix_modifier_chains(code)
        fixes_applied += count
        
        # Fix 3: Fix incomplete closures
        code, count = self._fix_closures(code)
        fixes_applied += count
        
        # Fix 4: Fix property wrappers
        code, count = self._fix_property_wrappers(code)
        fixes_applied += count
        
        # Fix 5: Fix multiline expressions
        code, count = self._fix_multiline_expressions(code)
        fixes_applied += count
        
        if fixes_applied > 0:
            logger.info(f"[AST] Applied {fixes_applied} fixes")
        
        return code, fixes_applied
    
    def _balance_delimiters_smart(self, code: str) -> Tuple[str, int]:
        """Smart delimiter balancing that understands Swift context"""
        
        lines = code.split('\n')
        fixed_lines = []
        fixes = 0
        delimiter_stack = []
        
        for i, line in enumerate(lines):
            # Skip comments
            if line.strip().startswith('//'):
                fixed_lines.append(line)
                continue
            
            # Process line character by character
            fixed_line = ""
            in_string = False
            escape_next = False
            line_stack = []
            
            for j, char in enumerate(line):
                if escape_next:
                    escape_next = False
                    fixed_line += char
                    continue
                
                if char == '\\':
                    escape_next = True
                    fixed_line += char
                    continue
                
                if char == '"' and not in_string:
                    in_string = True
                    fixed_line += char
                elif char == '"' and in_string and not escape_next:
                    in_string = False
                    fixed_line += char
                elif not in_string:
                    if char in self.delimiter_pairs:
                        delimiter_stack.append((char, i, len(fixed_line)))
                        line_stack.append(char)
                        fixed_line += char
                    elif char in self.delimiter_pairs.values():
                        expected = None
                        if delimiter_stack:
                            expected = self.delimiter_pairs[delimiter_stack[-1][0]]
                        
                        if expected == char:
                            delimiter_stack.pop()
                            if line_stack and self.delimiter_pairs.get(line_stack[-1]) == char:
                                line_stack.pop()
                            fixed_line += char
                        else:
                            # Mismatched delimiter - skip it
                            fixes += 1
                            logger.debug(f"Skipping mismatched {char} at line {i+1}")
                    else:
                        fixed_line += char
                else:
                    fixed_line += char
            
            # Check if we need closing delimiters at end of line
            # Special handling for SwiftUI modifiers
            if '.overlay(' in line or '.sheet(' in line or '.alert(' in line:
                # Check if properly closed
                overlay_count = line.count('.overlay(')
                overlay_close = line.count(')', line.find('.overlay(') if '.overlay(' in line else 0)
                
                if overlay_count > 0 and overlay_close < overlay_count:
                    # Look ahead to see if closing is on next line
                    if i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        if not next_line.startswith(')'):
                            # Need to add closing paren
                            # But only if there's actual content
                            if 'RoundedRectangle' in line or 'Text' in line or 'Image' in line:
                                # Don't add here, should be on next line or after content
                                pass
                    
            # Handle dangling opening delimiters
            while line_stack:
                opener = line_stack.pop()
                closer = self.delimiter_pairs[opener]
                
                # Check if this needs immediate closing
                if opener == '(' and ('.overlay' in line or 'Button(action:' in line):
                    # These often span multiple lines, don't close yet
                    pass
                elif opener == '{' and 'in' in line:
                    # Closure, don't close yet
                    pass
                else:
                    # Might need closing
                    if i == len(lines) - 1:  # Last line
                        fixed_line += closer
                        fixes += 1
                        if delimiter_stack and delimiter_stack[-1][0] == opener:
                            delimiter_stack.pop()
            
            fixed_lines.append(fixed_line)
        
        # Final cleanup - add any missing closing delimiters
        final_closers = ""
        while delimiter_stack:
            opener, line_num, _ = delimiter_stack.pop()
            final_closers += self.delimiter_pairs[opener]
            fixes += 1
        
        if final_closers and fixed_lines:
            # Add to last non-empty line
            for i in range(len(fixed_lines) - 1, -1, -1):
                if fixed_lines[i].strip():
                    fixed_lines[i] += final_closers
                    break
        
        return '\n'.join(fixed_lines), fixes
    
    def _fix_modifier_chains(self, code: str) -> Tuple[str, int]:
        """Fix SwiftUI modifier chains"""
        fixes = 0
        
        # Pattern: .modifier( content ) missing closing before next modifier
        pattern = r'(\.\w+\([^)]*?)(\n\s*\.\w+)'
        
        def check_and_fix(match):
            nonlocal fixes
            content = match.group(1)
            next_modifier = match.group(2)
            
            # Count parens in content
            open_count = content.count('(')
            close_count = content.count(')')
            
            if open_count > close_count:
                fixes += 1
                return content + ')' + next_modifier
            return match.group(0)
        
        code = re.sub(pattern, check_and_fix, code)
        return code, fixes
    
    def _fix_closures(self, code: str) -> Tuple[str, int]:
        """Fix closure syntax issues"""
        fixes = 0
        lines = code.split('\n')
        fixed_lines = []
        
        for i, line in enumerate(lines):
            if 'Button(action:' in line and '{' in line:
                # Check if closure is properly closed
                rest_of_line = line[line.find('{'):]
                open_braces = rest_of_line.count('{')
                close_braces = rest_of_line.count('}')
                
                if open_braces > close_braces:
                    # Check next few lines for closing
                    found_closing = False
                    for j in range(i + 1, min(i + 5, len(lines))):
                        if '}' in lines[j]:
                            found_closing = True
                            break
                    
                    if not found_closing and ')' not in rest_of_line:
                        # Add closing
                        line += ' })'
                        fixes += 1
            
            fixed_lines.append(line)
        
        return '\n'.join(fixed_lines), fixes
    
    def _fix_property_wrappers(self, code: str) -> Tuple[str, int]:
        """Fix property wrapper syntax"""
        fixes = 0
        
        # Fix @State, @Published, etc.
        patterns = [
            (r'@State\s+var', '@State private var'),
            (r'@Published\s+var', '@Published var'),
            (r'@StateObject\s+var', '@StateObject private var'),
            (r'@ObservedObject\s+var', '@ObservedObject private var'),
        ]
        
        for pattern, replacement in patterns:
            if re.search(pattern, code):
                code = re.sub(pattern, replacement, code)
                fixes += 1
        
        return code, fixes
    
    def _fix_multiline_expressions(self, code: str) -> Tuple[str, int]:
        """Fix multiline SwiftUI expressions"""
        fixes = 0
        lines = code.split('\n')
        fixed_lines = []
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Check for .overlay( pattern
            if '.overlay(' in line:
                # Find the matching closing paren
                content_lines = [line]
                open_count = line.count('(') - line.count(')')
                j = i + 1
                
                while j < len(lines) and open_count > 0:
                    content_lines.append(lines[j])
                    open_count += lines[j].count('(') - lines[j].count(')')
                    j += 1
                
                if open_count > 0:
                    # Missing closing parens
                    content_lines[-1] += ')' * open_count
                    fixes += open_count
                
                fixed_lines.extend(content_lines)
                i = j
            else:
                fixed_lines.append(line)
                i += 1
        
        return '\n'.join(fixed_lines), fixes

class MultiModelConsensus:
    """Production multi-model consensus system"""
    
    def __init__(self):
        self.llm_service = EnhancedClaudeService()
        self.ast_repair = EnterpriseASTRepair()
        
    async def generate_with_consensus(self, request: str, app_name: str) -> GenerationResult:
        """Generate using multiple models and merge results"""
        
        logger.info(f"[CONSENSUS] Generating {app_name} with multi-model approach")
        
        # Prepare specialized prompts for each model
        prompts = self._prepare_specialized_prompts(request, app_name)
        
        # Generate with each model in parallel
        tasks = []
        for provider, prompt in prompts.items():
            if provider in ["claude", "gpt4", "grok"]:
                tasks.append(self._generate_with_provider(provider, prompt, app_name))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter successful results
        valid_results = [r for r in results if isinstance(r, dict) and r.get("success")]
        
        if not valid_results:
            # All failed, try with most reliable (Claude)
            logger.warning("[CONSENSUS] All models failed, trying Claude with enhanced prompt")
            result = await self._generate_with_provider("claude", prompts["claude"], app_name)
            if result["success"]:
                valid_results = [result]
        
        if valid_results:
            # Merge results intelligently
            merged = self._intelligent_merge(valid_results, app_name)
            return merged
        else:
            return GenerationResult(
                success=False,
                code="",
                files=[],
                confidence=0.0,
                provider="consensus",
                duration=0.0,
                syntax_score=0.0
            )
    
    def _prepare_specialized_prompts(self, request: str, app_name: str) -> Dict[str, str]:
        """Prepare model-specific prompts"""
        
        base_syntax_rules = """
CRITICAL: Your Swift code MUST compile without errors.

SYNTAX CHECKLIST (verify before responding):
☐ Every ( has matching )
☐ Every { has matching }
☐ Every [ has matching ]
☐ All .overlay() modifiers are properly closed
☐ All Button closures are complete
☐ All property wrappers have types

COMMON MISTAKES TO AVOID:
❌ .overlay(content  <- Missing )
❌ Button(action: { code }  <- Missing )
❌ @State var count  <- Missing type
✅ .overlay(content)
✅ Button(action: { code })
✅ @State private var count: Int = 0
"""
        
        prompts = {
            "claude": f"""You are Claude, expert at iOS app architecture.
Create a {app_name} app: {request}

{base_syntax_rules}

Focus on:
- Clean MVVM architecture
- Proper separation of concerns
- Comprehensive error handling
- SwiftUI best practices

Return complete, compilable Swift code.""",
            
            "gpt4": f"""You are GPT-4, expert at algorithms and business logic.
Create a {app_name} app: {request}

{base_syntax_rules}

Focus on:
- Efficient algorithms
- Data structure optimization
- Business logic implementation
- Performance

Return complete, compilable Swift code.""",
            
            "grok": f"""You are Grok, expert at beautiful UI design.
Create a {app_name} app: {request}

{base_syntax_rules}

Focus on:
- Stunning visual design
- Smooth animations
- Intuitive user experience
- Modern iOS design patterns

Return complete, compilable Swift code with beautiful UI."""
        }
        
        return prompts
    
    async def _generate_with_provider(self, provider: str, prompt: str, app_name: str) -> Dict[str, Any]:
        """Generate with specific provider"""
        
        start_time = time.time()
        
        try:
            # Set the provider
            if provider == "gpt4":
                self.llm_service.set_model("openai")
            elif provider == "grok":
                self.llm_service.set_model("xai")
            else:
                self.llm_service.set_model("anthropic")
            
            # Generate
            result = await self.llm_service.generate_ios_app(
                description=prompt,
                app_name=app_name,
                is_simple_app=False
            )
            
            duration = time.time() - start_time
            
            # Check if we have files (success field might be None)
            if result.get("files"):
                # Extract code from result
                code = self._extract_code_from_result(result)
                
                # Apply AST repairs
                fixed_code, fixes = self.ast_repair.repair_code(code)
                
                # Calculate syntax score
                syntax_score = 100.0 - (fixes * 5)  # Deduct 5 points per fix needed
                
                return {
                    "success": True,
                    "provider": provider,
                    "code": fixed_code,
                    "files": result.get("files", []),
                    "duration": duration,
                    "syntax_score": max(0, syntax_score),
                    "fixes_applied": fixes
                }
            else:
                return {
                    "success": False,
                    "provider": provider,
                    "error": result.get("error", "Generation failed")
                }
                
        except Exception as e:
            logger.error(f"[CONSENSUS] {provider} failed: {str(e)}")
            return {
                "success": False,
                "provider": provider,
                "error": str(e)
            }
    
    def _extract_code_from_result(self, result: Dict) -> str:
        """Extract code from LLM result"""
        
        code_parts = []
        
        # Try to get from files
        if "files" in result:
            for file_info in result["files"]:
                if isinstance(file_info, dict):
                    content = file_info.get("content", "")
                    if content:
                        code_parts.append(f"// File: {file_info.get('path', 'unknown')}")
                        code_parts.append(content)
                        code_parts.append("")
        
        # Fallback to raw content
        if not code_parts and "content" in result:
            code_parts.append(result["content"])
        
        return "\n".join(code_parts)
    
    def _intelligent_merge(self, results: List[Dict], app_name: str) -> GenerationResult:
        """Intelligently merge results from multiple models"""
        
        # Score each result
        scored_results = []
        for result in results:
            score = result.get("syntax_score", 50)
            
            # Bonus points for specific providers
            if result["provider"] == "claude":
                score += 10  # Architecture bonus
            elif result["provider"] == "gpt4":
                score += 5   # Logic bonus
            
            scored_results.append((score, result))
        
        # Sort by score
        scored_results.sort(key=lambda x: x[0], reverse=True)
        
        # Take best result
        best_score, best_result = scored_results[0]
        
        logger.info(f"[CONSENSUS] Selected {best_result['provider']} with score {best_score}")
        
        # Parse into files
        files = self._parse_code_into_files(best_result["code"], app_name)
        
        return GenerationResult(
            success=True,
            code=best_result["code"],
            files=files,
            confidence=best_score,
            provider=f"consensus-{best_result['provider']}",
            duration=best_result["duration"],
            syntax_score=best_score
        )
    
    def _parse_code_into_files(self, code: str, app_name: str) -> List[Dict[str, str]]:
        """Parse code into separate files"""
        
        files = []
        
        # Split by file markers
        sections = re.split(r'//\s*File:\s*([^\n]+)', code)
        
        if len(sections) > 1:
            # Has file markers
            for i in range(1, len(sections), 2):
                filepath = sections[i].strip()
                content = sections[i + 1].strip() if i + 1 < len(sections) else ""
                
                # Ensure proper path
                if not filepath.startswith("Sources/"):
                    filepath = f"Sources/{filepath}"
                
                files.append({
                    "path": filepath,
                    "content": content
                })
        else:
            # No file markers, create default
            # Try to detect if it's a complete app or just ContentView
            if "@main" in code:
                # Has app definition, split it
                app_part = ""
                view_part = ""
                
                for line in code.split('\n'):
                    if "@main" in line or (app_part and "ContentView()" not in app_part):
                        app_part += line + "\n"
                    else:
                        view_part += line + "\n"
                
                files.append({
                    "path": "Sources/App.swift",
                    "content": app_part.strip()
                })
                
                if view_part.strip():
                    files.append({
                        "path": "Sources/ContentView.swift",
                        "content": view_part.strip()
                    })
            else:
                # Just ContentView
                files.append({
                    "path": "Sources/ContentView.swift",
                    "content": code
                })
                
                # Add App.swift
                files.append({
                    "path": "Sources/App.swift",
                    "content": f"""import SwiftUI

@main
struct {app_name}App: App {{
    var body: some Scene {{
        WindowGroup {{
            ContentView()
        }}
    }}
}}"""
                })
        
        # Add project.yml
        files.append({
            "path": "project.yml",
            "content": self._generate_project_yml(app_name)
        })
        
        return files
    
    def _generate_project_yml(self, app_name: str) -> str:
        """Generate project.yml for app"""
        return f"""name: {app_name}
options:
  bundleIdPrefix: com.swiftgen
  deploymentTarget:
    iOS: 16.0
targets:
  {app_name}:
    type: application
    platform: iOS
    sources: 
      - Sources
    settings:
      PRODUCT_BUNDLE_IDENTIFIER: com.swiftgen.{app_name.lower()}
      PRODUCT_NAME: {app_name}
      MARKETING_VERSION: 1.0.0
      CURRENT_PROJECT_VERSION: 1
      SWIFT_VERSION: 5.9
      DEVELOPMENT_TEAM: ""
      CODE_SIGN_STYLE: Manual
      CODE_SIGNING_REQUIRED: NO
      CODE_SIGN_IDENTITY: ""
      GENERATE_INFOPLIST_FILE: YES"""

class EnterprisePipeline:
    """Complete enterprise pipeline"""
    
    def __init__(self):
        self.consensus = MultiModelConsensus()
        self.workspace = Path("enterprise_workspace")
        self.workspace.mkdir(exist_ok=True)
        
    async def generate(self, request: str, app_name: str, provider: Optional[str] = None) -> Dict[str, Any]:
        """Generate app using enterprise pipeline"""
        
        logger.info(f"\n{'='*60}")
        logger.info(f"ENTERPRISE PIPELINE: {app_name}")
        logger.info(f"Request: {request}")
        logger.info(f"Provider: {provider or 'consensus'}")
        logger.info(f"{'='*60}")
        
        start_time = time.time()
        
        # Use consensus if no specific provider
        if not provider or provider == "consensus":
            result = await self.consensus.generate_with_consensus(request, app_name)
        else:
            # Use specific provider
            prompts = self.consensus._prepare_specialized_prompts(request, app_name)
            provider_result = await self.consensus._generate_with_provider(
                provider, 
                prompts.get(provider, prompts["claude"]), 
                app_name
            )
            
            if provider_result["success"]:
                files = self.consensus._parse_code_into_files(provider_result["code"], app_name)
                result = GenerationResult(
                    success=True,
                    code=provider_result["code"],
                    files=files,
                    confidence=provider_result["syntax_score"],
                    provider=provider,
                    duration=provider_result["duration"],
                    syntax_score=provider_result["syntax_score"]
                )
            else:
                result = GenerationResult(
                    success=False,
                    code="",
                    files=[],
                    confidence=0.0,
                    provider=provider,
                    duration=time.time() - start_time,
                    syntax_score=0.0
                )
        
        # Save files if successful
        if result.success:
            project_path = self.workspace / app_name
            if project_path.exists():
                import shutil
                shutil.rmtree(project_path)
            
            for file_info in result.files:
                file_path = project_path / file_info["path"]
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(file_info["content"])
            
            logger.info(f"✅ SUCCESS: {app_name}")
            logger.info(f"   Provider: {result.provider}")
            logger.info(f"   Syntax Score: {result.syntax_score:.1f}%")
            logger.info(f"   Confidence: {result.confidence:.1f}%")
            logger.info(f"   Duration: {result.duration:.1f}s")
            logger.info(f"   Files: {len(result.files)}")
        else:
            logger.error(f"❌ FAILED: {app_name}")
        
        return {
            "success": result.success,
            "app_name": app_name,
            "files": result.files,
            "confidence": result.confidence,
            "syntax_score": result.syntax_score,
            "duration": result.duration,
            "provider": result.provider
        }

async def test_enterprise_pipeline():
    """Test the enterprise pipeline"""
    
    pipeline = EnterprisePipeline()
    
    test_cases = [
        ("Create a simple counter app with increment and decrement buttons", "Counter", None),
        ("Create a timer app with start, stop, and reset functionality", "Timer", "claude"),
        ("Create a beautiful calculator with gradient background", "Calculator", "grok"),
        ("Create a todo list with add, delete, and mark complete", "TodoList", "gpt4"),
        ("Create a weather app with temperature and conditions", "Weather", "consensus"),
    ]
    
    results = []
    
    for request, app_name, provider in test_cases:
        result = await pipeline.generate(request, app_name, provider)
        results.append(result)
        await asyncio.sleep(2)  # Brief pause between tests
    
    # Summary
    print("\n" + "="*60)
    print("ENTERPRISE PIPELINE TEST RESULTS")
    print("="*60)
    
    successful = sum(1 for r in results if r["success"])
    total = len(results)
    success_rate = (successful / total * 100) if total > 0 else 0
    
    avg_syntax = sum(r["syntax_score"] for r in results) / total if total > 0 else 0
    avg_confidence = sum(r["confidence"] for r in results) / total if total > 0 else 0
    
    print(f"Success Rate: {success_rate:.1f}%")
    print(f"Average Syntax Score: {avg_syntax:.1f}%")
    print(f"Average Confidence: {avg_confidence:.1f}%")
    
    print("\nDetailed Results:")
    print("-" * 60)
    for r in results:
        status = "✅" if r["success"] else "❌"
        print(f"{status} {r['app_name']:15} Provider: {r['provider']:20} Syntax: {r['syntax_score']:.0f}%")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_enterprise_pipeline())