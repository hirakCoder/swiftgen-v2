"""
SwiftGen V2 - Optimized Enterprise Pipeline
Production implementation with parallel execution and timeout prevention
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
from concurrent.futures import ThreadPoolExecutor, TimeoutError

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
    method: str = "optimized"

class OptimizedASTRepair:
    """Optimized AST repair with caching and parallel processing"""
    
    def __init__(self):
        self.delimiter_pairs = {'(': ')', '[': ']', '{': '}'}
        self.repair_cache = {}
        
    def repair_code(self, code: str) -> Tuple[str, int]:
        """Repair Swift code with caching"""
        
        # Check cache
        code_hash = hashlib.md5(code.encode()).hexdigest()
        if code_hash in self.repair_cache:
            logger.info("[AST] Using cached repair")
            return self.repair_cache[code_hash]
        
        fixes_applied = 0
        
        # Apply fixes in parallel where possible
        fixes = [
            self._balance_delimiters_fast,
            self._fix_modifier_chains_fast,
            self._fix_closures_fast,
            self._fix_property_wrappers_fast
        ]
        
        for fix_func in fixes:
            code, count = fix_func(code)
            fixes_applied += count
        
        # Cache result
        result = (code, fixes_applied)
        self.repair_cache[code_hash] = result
        
        if fixes_applied > 0:
            logger.info(f"[AST] Applied {fixes_applied} fixes (cached)")
        
        return result
    
    def _balance_delimiters_fast(self, code: str) -> Tuple[str, int]:
        """Fast delimiter balancing"""
        
        lines = code.split('\n')
        fixed_lines = []
        fixes = 0
        stack = []
        
        for line in lines:
            if line.strip().startswith('//'):
                fixed_lines.append(line)
                continue
            
            fixed_line = ""
            in_string = False
            
            i = 0
            while i < len(line):
                char = line[i]
                
                if char == '\\' and i + 1 < len(line):
                    fixed_line += char + line[i + 1]
                    i += 2
                    continue
                
                if char == '"':
                    in_string = not in_string
                    fixed_line += char
                elif not in_string:
                    if char in self.delimiter_pairs:
                        stack.append(char)
                        fixed_line += char
                    elif char in self.delimiter_pairs.values():
                        if stack and self.delimiter_pairs.get(stack[-1]) == char:
                            stack.pop()
                            fixed_line += char
                        else:
                            fixes += 1  # Skip orphaned closer
                    else:
                        fixed_line += char
                else:
                    fixed_line += char
                
                i += 1
            
            fixed_lines.append(fixed_line)
        
        # Add missing closers at end
        while stack:
            fixed_lines[-1] += self.delimiter_pairs[stack.pop()]
            fixes += 1
        
        return '\n'.join(fixed_lines), fixes
    
    def _fix_modifier_chains_fast(self, code: str) -> Tuple[str, int]:
        """Fast modifier chain fixing"""
        fixes = 0
        
        # Pattern for unclosed modifiers
        pattern = r'(\.\w+\([^)]*?)(\n\s*\.\w+)'
        
        def fix(match):
            nonlocal fixes
            if match.group(1).count('(') > match.group(1).count(')'):
                fixes += 1
                return match.group(1) + ')' + match.group(2)
            return match.group(0)
        
        code = re.sub(pattern, fix, code)
        return code, fixes
    
    def _fix_closures_fast(self, code: str) -> Tuple[str, int]:
        """Fast closure fixing"""
        fixes = 0
        
        # Fix Button closures
        pattern = r'(Button\(action:\s*\{[^}]*?)(\n\s*\.)'
        code = re.sub(pattern, r'\1 })\2', code)
        fixes += len(re.findall(pattern, code))
        
        return code, fixes
    
    def _fix_property_wrappers_fast(self, code: str) -> Tuple[str, int]:
        """Fast property wrapper fixing"""
        fixes = 0
        
        replacements = [
            (r'@State\s+var', '@State private var'),
            (r'@StateObject\s+var', '@StateObject private var'),
            (r'@ObservedObject\s+var', '@ObservedObject private var')
        ]
        
        for pattern, replacement in replacements:
            if re.search(pattern, code):
                code = re.sub(pattern, replacement, code)
                fixes += 1
        
        return code, fixes

class OptimizedConsensus:
    """Optimized consensus with parallel execution and timeouts"""
    
    def __init__(self):
        self.llm_service = EnhancedClaudeService()
        self.ast_repair = OptimizedASTRepair()
        self.executor = ThreadPoolExecutor(max_workers=3)
        
    async def generate_with_consensus(self, request: str, app_name: str, timeout: int = 30) -> GenerationResult:
        """Generate using consensus with timeout protection"""
        
        logger.info(f"[CONSENSUS] Generating {app_name} with optimized approach")
        
        # Try individual providers first with shorter timeout
        providers = ["claude", "gpt4", "grok"]
        
        for provider in providers:
            try:
                result = await self._generate_with_timeout(provider, request, app_name, timeout=15)
                if result.success:
                    logger.info(f"[CONSENSUS] Quick success with {provider}")
                    return result
            except Exception as e:
                logger.warning(f"[CONSENSUS] {provider} failed: {e}")
                continue
        
        # If all fail individually, try parallel generation with longer timeout
        logger.info("[CONSENSUS] Trying parallel generation")
        try:
            result = await self._parallel_generation(request, app_name, timeout=timeout)
            return result
        except Exception as e:
            logger.error(f"[CONSENSUS] Parallel generation failed: {e}")
            return GenerationResult(
                success=False,
                code="",
                files=[],
                confidence=0.0,
                provider="consensus",
                duration=0.0,
                syntax_score=0.0
            )
    
    async def _generate_with_timeout(self, provider: str, request: str, app_name: str, timeout: int) -> GenerationResult:
        """Generate with specific provider and timeout"""
        
        start_time = time.time()
        
        try:
            # Create task with timeout
            task = asyncio.create_task(self._generate_single(provider, request, app_name))
            result = await asyncio.wait_for(task, timeout=timeout)
            
            duration = time.time() - start_time
            result.duration = duration
            
            return result
            
        except asyncio.TimeoutError:
            logger.warning(f"[TIMEOUT] {provider} exceeded {timeout}s limit")
            raise
        except Exception as e:
            logger.error(f"[ERROR] {provider}: {e}")
            raise
    
    async def _generate_single(self, provider: str, request: str, app_name: str) -> GenerationResult:
        """Generate with single provider"""
        
        # Prepare prompt
        prompt = self._get_provider_prompt(provider, request, app_name)
        
        # Set model
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
            is_simple_app=True  # Use simple mode for speed
        )
        
        if result.get("files"):
            # Extract and repair code
            code = self._extract_code(result)
            fixed_code, fixes = self.ast_repair.repair_code(code)
            
            # Parse files
            files = self._parse_files(fixed_code, app_name)
            
            syntax_score = 100.0 - (fixes * 5)
            
            return GenerationResult(
                success=True,
                code=fixed_code,
                files=files,
                confidence=max(0, syntax_score),
                provider=provider,
                duration=0.0,  # Will be set by caller
                syntax_score=max(0, syntax_score)
            )
        else:
            return GenerationResult(
                success=False,
                code="",
                files=[],
                confidence=0.0,
                provider=provider,
                duration=0.0,
                syntax_score=0.0
            )
    
    async def _parallel_generation(self, request: str, app_name: str, timeout: int) -> GenerationResult:
        """Generate with multiple providers in parallel"""
        
        start_time = time.time()
        
        # Create tasks for parallel execution
        tasks = [
            self._generate_single("claude", request, app_name),
            self._generate_single("gpt4", request, app_name),
            self._generate_single("grok", request, app_name)
        ]
        
        # Wait for first successful result
        done, pending = await asyncio.wait(
            tasks,
            return_when=asyncio.FIRST_COMPLETED,
            timeout=timeout
        )
        
        # Cancel pending tasks
        for task in pending:
            task.cancel()
        
        # Get best result
        for task in done:
            try:
                result = await task
                if result.success:
                    result.duration = time.time() - start_time
                    result.provider = f"parallel-{result.provider}"
                    return result
            except Exception:
                continue
        
        # All failed
        return GenerationResult(
            success=False,
            code="",
            files=[],
            confidence=0.0,
            provider="parallel",
            duration=time.time() - start_time,
            syntax_score=0.0
        )
    
    def _get_provider_prompt(self, provider: str, request: str, app_name: str) -> str:
        """Get optimized prompt for provider"""
        
        base = f"""Create {app_name}: {request}

CRITICAL: Generate COMPLETE, COMPILABLE Swift code.

Required structure:
1. App.swift with @main
2. ContentView.swift with UI
3. All delimiters balanced
4. All statements complete"""
        
        if provider == "claude":
            return base + "\n\nFocus on clean architecture and best practices."
        elif provider == "gpt4":
            return base + "\n\nFocus on efficient algorithms and logic."
        elif provider == "grok":
            return base + "\n\nFocus on beautiful UI and animations."
        else:
            return base
    
    def _extract_code(self, result: Dict) -> str:
        """Extract code from result"""
        
        if "files" in result:
            parts = []
            for file_info in result["files"]:
                if isinstance(file_info, dict):
                    content = file_info.get("content", "")
                    if content:
                        parts.append(content)
            return "\n\n".join(parts)
        return result.get("content", "")
    
    def _parse_files(self, code: str, app_name: str) -> List[Dict[str, str]]:
        """Parse code into files"""
        
        files = []
        
        # Check if code has file markers
        if "// File:" in code or "File:" in code:
            sections = re.split(r'(?://\s*)?File:\s*([^\n]+)', code)
            
            for i in range(1, len(sections), 2):
                if i + 1 < len(sections):
                    filename = sections[i].strip()
                    content = sections[i + 1].strip()
                    
                    if not filename.startswith("Sources/"):
                        filename = f"Sources/{filename}"
                    
                    files.append({
                        "path": filename,
                        "content": content
                    })
        else:
            # Create default structure
            if "@main" in code:
                # Split into App and ContentView
                app_code = ""
                view_code = ""
                
                in_app = False
                for line in code.split('\n'):
                    if "@main" in line:
                        in_app = True
                    
                    if in_app and "struct ContentView" in line:
                        in_app = False
                    
                    if in_app:
                        app_code += line + "\n"
                    else:
                        view_code += line + "\n"
                
                if app_code:
                    files.append({
                        "path": "Sources/App.swift",
                        "content": app_code.strip()
                    })
                
                if view_code:
                    files.append({
                        "path": "Sources/ContentView.swift",
                        "content": view_code.strip()
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
        """Generate project.yml"""
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

class OptimizedPipeline:
    """Optimized pipeline with fast execution"""
    
    def __init__(self):
        self.consensus = OptimizedConsensus()
        self.workspace = Path("optimized_workspace")
        self.workspace.mkdir(exist_ok=True)
        
    async def generate(self, request: str, app_name: str, provider: Optional[str] = None) -> Dict[str, Any]:
        """Generate app with optimized pipeline"""
        
        logger.info(f"\n{'='*60}")
        logger.info(f"OPTIMIZED PIPELINE: {app_name}")
        logger.info(f"Request: {request}")
        logger.info(f"Provider: {provider or 'auto'}")
        logger.info(f"{'='*60}")
        
        start_time = time.time()
        
        # Use optimized consensus
        if provider and provider in ["claude", "gpt4", "grok"]:
            # Direct provider with timeout
            result = await self.consensus._generate_with_timeout(
                provider, request, app_name, timeout=20
            )
        else:
            # Auto-select best provider
            result = await self.consensus.generate_with_consensus(
                request, app_name, timeout=30
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
            
            duration = time.time() - start_time
            
            logger.info(f"✅ SUCCESS: {app_name}")
            logger.info(f"   Provider: {result.provider}")
            logger.info(f"   Syntax Score: {result.syntax_score:.1f}%")
            logger.info(f"   Duration: {duration:.1f}s")
            logger.info(f"   Files: {len(result.files)}")
        else:
            duration = time.time() - start_time
            logger.error(f"❌ FAILED: {app_name} after {duration:.1f}s")
        
        return {
            "success": result.success,
            "app_name": app_name,
            "files": result.files,
            "confidence": result.confidence,
            "syntax_score": result.syntax_score,
            "duration": duration,
            "provider": result.provider,
            "method": result.method
        }

async def test_optimized_pipeline():
    """Test the optimized pipeline"""
    
    pipeline = OptimizedPipeline()
    
    # Quick tests with timeout protection
    test_cases = [
        ("Create a simple counter app", "Counter", None),
        ("Create a timer with start/stop", "Timer", "claude"),
        ("Create a calculator", "Calculator", "gpt4"),
    ]
    
    results = []
    
    for request, app_name, provider in test_cases:
        try:
            result = await asyncio.wait_for(
                pipeline.generate(request, app_name, provider),
                timeout=35
            )
            results.append(result)
        except asyncio.TimeoutError:
            logger.error(f"Test timeout: {app_name}")
            results.append({
                "success": False,
                "app_name": app_name,
                "duration": 35,
                "error": "timeout"
            })
    
    # Summary
    print("\n" + "="*60)
    print("OPTIMIZED PIPELINE TEST RESULTS")
    print("="*60)
    
    successful = sum(1 for r in results if r.get("success", False))
    total = len(results)
    
    print(f"Success Rate: {successful}/{total}")
    
    for r in results:
        status = "✅" if r.get("success", False) else "❌"
        duration = r.get("duration", 0)
        provider = r.get("provider", "unknown")
        syntax = r.get("syntax_score", 0)
        print(f"{status} {r['app_name']:15} Duration: {duration:5.1f}s Provider: {provider:20} Syntax: {syntax:.0f}%")

if __name__ == "__main__":
    asyncio.run(test_optimized_pipeline())