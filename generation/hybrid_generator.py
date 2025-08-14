"""
Hybrid Generator - Uses all 3 LLMs for their strengths
Claude: Architecture & Structure
GPT-4: Business Logic & Algorithms  
Grok: UI/UX & Visual Design
"""

import asyncio
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

@dataclass
class HybridGenerationResult:
    """Result from hybrid generation"""
    success: bool
    files: Dict[str, str]
    components: Dict[str, str]  # Which LLM generated what
    errors: List[str] = None

class HybridGenerator:
    """Orchestrates multiple LLMs to generate different parts of the app"""
    
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
        Generate app using all 3 LLMs for their strengths
        
        Process:
        1. Claude: Generate overall architecture and app structure
        2. GPT-4: Implement business logic and data processing
        3. Grok: Polish UI/UX and add animations
        """
        
        components = {}
        errors = []
        
        try:
            # Step 1: Claude generates architecture
            print("[Hybrid] Step 1: Claude generating architecture...")
            architecture_prompt = self._get_architecture_prompt(description, app_name, base_prompt)
            
            # Force Claude
            original_provider = self.llm_router.preferred_provider
            self.llm_router.preferred_provider = 'claude'
            
            architecture_result = await self.llm_router.generate(architecture_prompt)
            
            if not architecture_result.success:
                errors.append(f"Claude architecture generation failed: {architecture_result.error}")
                return HybridGenerationResult(success=False, files={}, components={}, errors=errors)
            
            # Parse Claude's output
            try:
                architecture_code = json.loads(architecture_result.content)
                components['architecture'] = 'Claude'
            except:
                # If not JSON, treat as raw code
                architecture_code = {'files': [{'path': 'Sources/App.swift', 'content': architecture_result.content}]}
            
            # Step 2: GPT-4 adds business logic
            print("[Hybrid] Step 2: GPT-4 implementing business logic...")
            logic_prompt = self._get_logic_prompt(description, app_name, architecture_code)
            
            # Force GPT-4
            self.llm_router.preferred_provider = 'gpt4'
            
            logic_result = await self.llm_router.generate(logic_prompt)
            
            if logic_result.success:
                try:
                    logic_code = json.loads(logic_result.content)
                    # Merge with architecture
                    architecture_code = self._merge_code(architecture_code, logic_code)
                    components['business_logic'] = 'GPT-4'
                except:
                    errors.append("GPT-4 logic parsing failed")
            else:
                errors.append(f"GPT-4 logic generation failed: {logic_result.error}")
            
            # Step 3: Grok polishes UI/UX
            print("[Hybrid] Step 3: Grok polishing UI/UX...")
            ui_prompt = self._get_ui_prompt(description, app_name, architecture_code)
            
            # Force Grok
            self.llm_router.preferred_provider = 'grok'
            
            ui_result = await self.llm_router.generate(ui_prompt)
            
            if ui_result.success:
                try:
                    ui_code = json.loads(ui_result.content)
                    # Final merge
                    final_code = self._merge_code(architecture_code, ui_code)
                    components['ui_polish'] = 'Grok'
                except:
                    errors.append("Grok UI parsing failed")
                    final_code = architecture_code
            else:
                errors.append(f"Grok UI generation failed: {ui_result.error}")
                final_code = architecture_code
            
            # Restore original provider
            self.llm_router.preferred_provider = original_provider
            
            # Convert to files dict
            files = {}
            for file_info in final_code.get('files', []):
                filename = file_info['path'].split('/')[-1]
                files[filename] = file_info['content']
            
            return HybridGenerationResult(
                success=True,
                files=files,
                components=components,
                errors=errors if errors else None
            )
            
        except Exception as e:
            return HybridGenerationResult(
                success=False,
                files={},
                components=components,
                errors=[str(e)]
            )
    
    def _get_architecture_prompt(self, description: str, app_name: str, base_prompt: str) -> str:
        """Prompt for Claude to generate architecture"""
        return f"""As Claude, you excel at SwiftUI architecture and app structure.

Generate the ARCHITECTURE and STRUCTURE for this app:
{description}

App Name: {app_name}

Focus on:
1. Overall app architecture (use MVVM if appropriate)
2. Main app structure and navigation
3. Core data models
4. State management
5. View hierarchy

Create a well-architected foundation that other components can build upon.

Target iOS 16.0. Use SwiftUI.

Return JSON with this structure:
{{
    "files": [
        {{
            "path": "Sources/App.swift",
            "content": "// Complete Swift code"
        }},
        {{
            "path": "Sources/Views/ContentView.swift",
            "content": "// Complete Swift code"
        }}
        // Add other architectural files as needed
    ]
}}

Focus on STRUCTURE, not full implementation. Leave placeholders for business logic."""
    
    def _get_logic_prompt(self, description: str, app_name: str, current_code: Dict) -> str:
        """Prompt for GPT-4 to add business logic"""
        
        # Show current structure
        current_structure = "\n".join([f"- {f['path']}" for f in current_code.get('files', [])])
        
        return f"""As GPT-4, you excel at algorithms, business logic, and data processing.

Current app structure:
{current_structure}

Original request: {description}

ADD BUSINESS LOGIC to this app:
1. Implement data processing functions
2. Add calculation/algorithm logic
3. Implement data validation
4. Add business rules
5. Handle data transformations

Focus on the LOGIC and ALGORITHMS, not UI.

Return JSON with files that need logic additions:
{{
    "files": [
        {{
            "path": "Sources/ViewModels/AppViewModel.swift",
            "content": "// Complete implementation with business logic"
        }}
        // Add or modify files as needed
    ]
}}"""
    
    def _get_ui_prompt(self, description: str, app_name: str, current_code: Dict) -> str:
        """Prompt for Grok to polish UI/UX"""
        
        current_structure = "\n".join([f"- {f['path']}" for f in current_code.get('files', [])])
        
        return f"""As Grok, you excel at creating beautiful UI/UX with smooth animations.

Current app structure:
{current_structure}

Original request: {description}

POLISH THE UI/UX:
1. Add beautiful animations and transitions
2. Improve visual design and layout
3. Add gesture interactions
4. Enhance user experience
5. Make the UI modern and polished

Focus on making it VISUALLY STUNNING and SMOOTH.

Return JSON with UI improvements:
{{
    "files": [
        {{
            "path": "Sources/Views/ContentView.swift",
            "content": "// Enhanced UI with animations"
        }}
        // Modify views for better UX
    ]
}}

Use SwiftUI's latest features for iOS 16.0."""
    
    def _merge_code(self, base_code: Dict, new_code: Dict) -> Dict:
        """Merge code from different LLMs"""
        # Create a file map
        file_map = {}
        
        # Add base files
        for file_info in base_code.get('files', []):
            file_map[file_info['path']] = file_info
        
        # Merge or add new files
        for file_info in new_code.get('files', []):
            file_map[file_info['path']] = file_info
        
        # Convert back to list
        return {'files': list(file_map.values())}