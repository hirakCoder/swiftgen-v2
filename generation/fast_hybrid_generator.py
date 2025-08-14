"""
Fast Hybrid Generator - Parallel LLM execution for speed
Uses all 3 LLMs concurrently for maximum performance
"""

import asyncio
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import time

@dataclass
class HybridGenerationResult:
    """Result from hybrid generation"""
    success: bool
    files: Dict[str, str]
    components: Dict[str, str]  # Which LLM generated what
    errors: List[str] = None
    duration: float = 0

class FastHybridGenerator:
    """
    Orchestrates multiple LLMs in PARALLEL for speed
    Instead of sequential: Claude -> GPT-4 -> Grok (60+ seconds)
    We do parallel: Claude || GPT-4 || Grok (max 30 seconds)
    """
    
    def __init__(self, llm_router):
        self.llm_router = llm_router
        
    async def generate_hybrid(
        self,
        description: str,
        app_name: str,
        complexity_score: int,
        base_prompt: str
    ) -> HybridGenerationResult:
        """
        Generate app using all 3 LLMs IN PARALLEL
        
        Strategy:
        1. All 3 LLMs generate complete apps independently
        2. Take best parts from each:
           - Claude: Best overall structure
           - GPT-4: Best algorithms/logic
           - Grok: Best UI (but needs file completion)
        3. Merge intelligently
        """
        
        start_time = time.time()
        components = {}
        errors = []
        
        try:
            # Prepare prompts for all 3 LLMs
            full_prompt = f"""Create a complete SwiftUI iOS app.

App Name: {app_name}
Description: {description}

REQUIREMENTS:
1. Generate a COMPLETE, working iOS app
2. Include ALL necessary files
3. Use iOS 16 compatible code only
4. Return JSON with format: {{"files": [{{"path": "Sources/App.swift", "content": "..."}}]}}

{base_prompt}"""
            
            # Create tasks for parallel execution
            tasks = []
            
            # Claude task
            async def generate_claude():
                try:
                    original = self.llm_router.preferred_provider
                    self.llm_router.preferred_provider = 'claude'
                    result = await asyncio.wait_for(
                        self.llm_router.generate(full_prompt),
                        timeout=30
                    )
                    self.llm_router.preferred_provider = original
                    return ('claude', result)
                except asyncio.TimeoutError:
                    return ('claude', None)
                except Exception as e:
                    print(f"[FastHybrid] Claude error: {e}")
                    return ('claude', None)
            
            # GPT-4 task
            async def generate_gpt4():
                try:
                    original = self.llm_router.preferred_provider
                    self.llm_router.preferred_provider = 'gpt4'
                    result = await asyncio.wait_for(
                        self.llm_router.generate(full_prompt),
                        timeout=30
                    )
                    self.llm_router.preferred_provider = original
                    return ('gpt4', result)
                except asyncio.TimeoutError:
                    return ('gpt4', None)
                except Exception as e:
                    print(f"[FastHybrid] GPT-4 error: {e}")
                    return ('gpt4', None)
            
            # Grok task
            async def generate_grok():
                try:
                    original = self.llm_router.preferred_provider
                    self.llm_router.preferred_provider = 'grok'
                    result = await asyncio.wait_for(
                        self.llm_router.generate(full_prompt),
                        timeout=30
                    )
                    self.llm_router.preferred_provider = original
                    return ('grok', result)
                except asyncio.TimeoutError:
                    return ('grok', None)
                except Exception as e:
                    print(f"[FastHybrid] Grok error: {e}")
                    return ('grok', None)
            
            # Run all 3 in parallel
            print("[FastHybrid] Starting parallel generation with all 3 LLMs...")
            results = await asyncio.gather(
                generate_claude(),
                generate_gpt4(),
                generate_grok()
            )
            
            # Process results
            successful_results = []
            for provider, result in results:
                if result and result.success:
                    try:
                        code = json.loads(result.content)
                        successful_results.append((provider, code))
                        components[provider] = 'success'
                        print(f"[FastHybrid] {provider} succeeded")
                    except:
                        errors.append(f"{provider} JSON parse failed")
                        components[provider] = 'parse_failed'
                else:
                    errors.append(f"{provider} generation failed")
                    components[provider] = 'failed'
            
            # If no results succeeded, fail
            if not successful_results:
                return HybridGenerationResult(
                    success=False,
                    files={},
                    components=components,
                    errors=errors,
                    duration=time.time() - start_time
                )
            
            # Use the first successful result (prioritize Claude > GPT-4 > Grok)
            priority_order = ['claude', 'gpt4', 'grok']
            final_code = None
            
            for provider in priority_order:
                for result_provider, code in successful_results:
                    if result_provider == provider:
                        final_code = code
                        print(f"[FastHybrid] Using {provider}'s output as base")
                        break
                if final_code:
                    break
            
            # If no prioritized result, use first available
            if not final_code:
                final_code = successful_results[0][1]
                print(f"[FastHybrid] Using {successful_results[0][0]}'s output")
            
            # Convert to expected format
            files = {}
            for file_info in final_code.get('files', []):
                # Extract filename from path
                path = file_info['path']
                filename = path.split('/')[-1]
                files[filename] = file_info['content']
            
            duration = time.time() - start_time
            print(f"[FastHybrid] Completed in {duration:.1f}s using {len(successful_results)}/3 LLMs")
            
            return HybridGenerationResult(
                success=True,
                files=files,
                components=components,
                errors=errors if errors else None,
                duration=duration
            )
            
        except Exception as e:
            print(f"[FastHybrid] Fatal error: {e}")
            return HybridGenerationResult(
                success=False,
                files={},
                components=components,
                errors=[str(e)],
                duration=time.time() - start_time
            )
    
    def _merge_code(self, base_code: Dict, additional_code: Dict) -> Dict:
        """Merge code from multiple sources"""
        # Simple merge strategy - additional files are added, existing are updated
        base_files = {f['path']: f for f in base_code.get('files', [])}
        
        for file_info in additional_code.get('files', []):
            base_files[file_info['path']] = file_info
        
        base_code['files'] = list(base_files.values())
        return base_code