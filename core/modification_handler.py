"""
Flexible Modification Handler - Handles ANY modification with balanced quality
"""

import json
import os
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class ModificationRequest:
    """Represents a modification request"""
    project_id: str
    description: str
    app_name: str
    existing_files: List[Dict]
    
class FlexibleModificationHandler:
    """
    Handles modifications with:
    - Creative interpretation
    - Quality maintenance
    - Flexible implementation
    """
    
    def __init__(self, llm_service=None):
        self.llm_service = llm_service
    
    async def handle_modification(
        self,
        project_id: str,
        modification_request: str,
        project_path: str
    ) -> Dict:
        """
        Handle ANY modification request flexibly
        """
        # Read existing project files
        existing_files = self._read_project_files(project_path)
        
        if not existing_files:
            return {
                'success': False,
                'error': 'No existing project files found'
            }
        
        # Get app name from existing files
        app_name = self._extract_app_name(existing_files)
        
        # Build modification prompt
        from .flexible_prompt import FlexiblePromptBuilder
        
        # Combine existing code for context
        existing_code = self._combine_code(existing_files)
        
        prompt = FlexiblePromptBuilder.build_modification_prompt(
            existing_code=existing_code,
            modification_request=modification_request,
            app_name=app_name
        )
        
        # Call LLM for modification
        if self.llm_service:
            try:
                # Check if this is enhanced_claude_service with modify_ios_app method
                if hasattr(self.llm_service, 'modify_ios_app'):
                    # Use the modification-specific method
                    response = await self.llm_service.modify_ios_app(
                        app_name=app_name,
                        description="",  # Not used in our context
                        modification=modification_request,
                        files=existing_files,
                        existing_bundle_id=f"com.swiftgen.{app_name.lower()}",
                        project_tracking_id=project_id
                    )
                    modified_code = response
                else:
                    # Fallback to generic generate for other LLM services
                    response = await self.llm_service.generate(prompt)
                    
                    # Parse and validate response
                    if hasattr(response, 'content'):
                        modified_code = json.loads(response.content)
                    elif isinstance(response, dict):
                        modified_code = response
                    else:
                        modified_code = json.loads(str(response))
                
                # Validate the modification
                validation = FlexiblePromptBuilder.validate_response(modified_code)
                
                if validation['valid']:
                    # Save modified files
                    self._save_modified_files(project_path, modified_code['files'])
                    
                    return {
                        'success': True,
                        'project_id': project_id,
                        'files_modified': len(modified_code['files']),
                        'warnings': validation['warnings']
                    }
                else:
                    return {
                        'success': False,
                        'error': f"Invalid modification: {', '.join(validation['issues'])}"
                    }
                    
            except Exception as e:
                return {
                    'success': False,
                    'error': f"Modification failed: {str(e)}"
                }
        else:
            return {
                'success': False,
                'error': 'No LLM service available'
            }
    
    def _read_project_files(self, project_path: str) -> List[Dict]:
        """Read existing project files"""
        files = []
        sources_dir = os.path.join(project_path, 'Sources')
        
        if not os.path.exists(sources_dir):
            # Try root directory
            sources_dir = project_path
        
        for filename in os.listdir(sources_dir):
            if filename.endswith('.swift'):
                filepath = os.path.join(sources_dir, filename)
                with open(filepath, 'r') as f:
                    content = f.read()
                files.append({
                    'path': f"Sources/{filename}",
                    'content': content,
                    'filename': filename
                })
        
        return files
    
    def _extract_app_name(self, files: List[Dict]) -> str:
        """Extract app name from existing files"""
        for file in files:
            if 'App.swift' in file['filename']:
                # Extract from @main struct name
                content = file['content']
                import re
                match = re.search(r'struct\s+(\w+)App\s*:', content)
                if match:
                    return match.group(1)
        
        return 'App'
    
    def _combine_code(self, files: List[Dict]) -> str:
        """Combine code files for context"""
        combined = ""
        for file in files:
            combined += f"\n// File: {file['path']}\n"
            combined += file['content']
            combined += "\n\n"
        return combined
    
    def _save_modified_files(self, project_path: str, files: List[Dict]):
        """Save modified files to disk"""
        # First check for duplicate @main files
        sources_dir = os.path.join(project_path, 'Sources')
        existing_app_files = []
        
        if os.path.exists(sources_dir):
            # Find existing app files with @main
            for filename in os.listdir(sources_dir):
                if filename.endswith('App.swift') and filename != 'App.swift':
                    existing_app_files.append(filename)
        
        # Filter out duplicate App.swift if we have a specific app file
        files_to_save = []
        for file_info in files:
            file_name = os.path.basename(file_info['path'])
            
            # Skip generic App.swift if we already have a specific app file
            if file_name == 'App.swift' and existing_app_files:
                print(f"[MODIFY] Skipping duplicate App.swift (keeping {existing_app_files[0]})")
                continue
            
            files_to_save.append(file_info)
        
        # Now save the filtered files
        for file_info in files_to_save:
            file_path = os.path.join(project_path, file_info['path'])
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Write file
            with open(file_path, 'w') as f:
                f.write(file_info['content'])
    
    @staticmethod
    def analyze_modification_complexity(request: str) -> str:
        """
        Analyze modification complexity for intelligent handling
        """
        request_lower = request.lower()
        
        # Simple modifications
        simple_keywords = ['color', 'text', 'label', 'size', 'font', 'spacing']
        if any(word in request_lower for word in simple_keywords):
            return 'simple'
        
        # Medium modifications
        medium_keywords = ['add button', 'add field', 'new section', 'change layout']
        if any(word in request_lower for word in medium_keywords):
            return 'medium'
        
        # Complex modifications
        complex_keywords = ['refactor', 'architecture', 'database', 'api', 'authentication']
        if any(word in request_lower for word in complex_keywords):
            return 'complex'
        
        return 'medium'  # Default

class IntelligentModificationRouter:
    """
    Routes modifications to appropriate handler based on complexity
    """
    
    @staticmethod
    async def route_modification(
        request: str,
        project_path: str,
        llm_service=None
    ) -> Dict:
        """
        Route modification to appropriate handler
        """
        # Always use flexible handler for maximum capability
        handler = FlexibleModificationHandler(llm_service)
        
        # Extract project ID from path
        project_id = os.path.basename(project_path)
        
        return await handler.handle_modification(
            project_id=project_id,
            modification_request=request,
            project_path=project_path
        )
    
    @staticmethod
    def can_modify(project_path: str) -> bool:
        """
        Check if project can be modified
        """
        sources_dir = os.path.join(project_path, 'Sources')
        if os.path.exists(sources_dir):
            # Check for Swift files
            swift_files = [f for f in os.listdir(sources_dir) if f.endswith('.swift')]
            return len(swift_files) > 0
        
        # Check root directory
        swift_files = [f for f in os.listdir(project_path) if f.endswith('.swift')]
        return len(swift_files) > 0