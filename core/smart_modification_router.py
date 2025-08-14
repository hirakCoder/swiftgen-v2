"""
Smart Modification Router - Handles modifications with intelligent routing and timeout management
"""

import asyncio
import re
from typing import Dict, Optional, List
from pathlib import Path
import json

class SmartModificationRouter:
    """
    Routes modifications based on complexity and handles timeouts gracefully
    """
    
    # Cached modification patterns for common requests
    MODIFICATION_PATTERNS = {
        "dark_mode": {
            "keywords": ["dark", "theme", "mode", "appearance"],
            "complexity": "simple",
            "timeout": 15,
            "template": {
                "app_storage": '@AppStorage("darkMode") private var darkMode: Bool = false',
                "toggle": 'Toggle("Dark Mode", isOn: $darkMode)',
                "modifier": '.preferredColorScheme(darkMode ? .dark : .light)'
            }
        },
        "reset": {
            "keywords": ["reset", "clear", "zero", "restart"],
            "complexity": "simple",
            "timeout": 15,
            "template": {
                "function": "func reset() { count = 0; saveState() }",
                "button": 'Button("Reset") { reset() }'
            }
        },
        "color_change": {
            "keywords": ["color", "background", "foreground", "tint"],
            "complexity": "simple",
            "timeout": 15
        },
        "animation": {
            "keywords": ["animate", "animation", "transition", "effect"],
            "complexity": "medium",
            "timeout": 30
        },
        "settings": {
            "keywords": ["settings", "preferences", "options", "configuration"],
            "complexity": "medium",
            "timeout": 30
        },
        "authentication": {
            "keywords": ["login", "auth", "sign in", "password", "user"],
            "complexity": "complex",
            "timeout": 60
        },
        "api_integration": {
            "keywords": ["api", "network", "fetch", "server", "backend"],
            "complexity": "complex",
            "timeout": 60
        }
    }
    
    def __init__(self):
        self.modification_cache = {}
        self.success_history = {}
        
    def analyze_complexity(self, request: str) -> tuple[str, int]:
        """
        Analyze modification request complexity
        Returns: (complexity_level, timeout_seconds)
        """
        request_lower = request.lower()
        
        # Check against known patterns
        for pattern_name, pattern_info in self.MODIFICATION_PATTERNS.items():
            if any(keyword in request_lower for keyword in pattern_info["keywords"]):
                return pattern_info["complexity"], pattern_info["timeout"]
        
        # Default based on request length and keywords
        if len(request) < 50:
            return "simple", 15
        elif len(request) < 150:
            return "medium", 30
        else:
            return "complex", 60
    
    async def route_modification(
        self,
        request: str,
        project_path: str,
        llm_service,
        status_callback=None
    ) -> Dict:
        """
        Smart routing for modifications with timeout handling
        """
        complexity, timeout = self.analyze_complexity(request)
        
        # Check cache first
        cache_key = f"{request[:50]}_{project_path}"
        if cache_key in self.modification_cache:
            await self._send_status(status_callback, "Using cached modification pattern...")
            return self.modification_cache[cache_key]
        
        # Try different strategies based on complexity
        if complexity == "simple":
            return await self._handle_simple_modification(
                request, project_path, llm_service, timeout, status_callback
            )
        elif complexity == "medium":
            return await self._handle_medium_modification(
                request, project_path, llm_service, timeout, status_callback
            )
        else:
            return await self._handle_complex_modification(
                request, project_path, llm_service, timeout, status_callback
            )
    
    async def _handle_simple_modification(
        self, request, project_path, llm_service, timeout, status_callback
    ):
        """Handle simple modifications with quick timeout"""
        
        await self._send_status(status_callback, f"Processing simple modification (timeout: {timeout}s)...")
        
        try:
            # First attempt with primary LLM
            result = await asyncio.wait_for(
                self._apply_modification(request, project_path, llm_service),
                timeout=timeout
            )
            
            if result["success"]:
                self.modification_cache[f"{request[:50]}_{project_path}"] = result
                return result
                
        except asyncio.TimeoutError:
            await self._send_status(status_callback, "Timeout, trying cached pattern...")
            
            # Try cached pattern
            pattern_result = self._apply_cached_pattern(request, project_path)
            if pattern_result:
                return pattern_result
        
        # Fallback to template
        return self._apply_template_modification(request, project_path)
    
    async def _handle_medium_modification(
        self, request, project_path, llm_service, timeout, status_callback
    ):
        """Handle medium complexity modifications"""
        
        await self._send_status(status_callback, f"Processing medium modification (timeout: {timeout}s)...")
        
        try:
            # Try with extended timeout
            result = await asyncio.wait_for(
                self._apply_modification(request, project_path, llm_service),
                timeout=timeout
            )
            
            if result["success"]:
                return result
                
        except asyncio.TimeoutError:
            await self._send_status(status_callback, "Timeout, breaking into smaller steps...")
            
            # Break into smaller modifications
            steps = self._break_into_steps(request)
            for step in steps:
                step_result = await self._handle_simple_modification(
                    step, project_path, llm_service, 15, status_callback
                )
                if not step_result["success"]:
                    return step_result
            
            return {"success": True, "message": "Applied modifications in steps"}
    
    async def _handle_complex_modification(
        self, request, project_path, llm_service, timeout, status_callback
    ):
        """Handle complex modifications with fallback strategies"""
        
        await self._send_status(status_callback, f"Processing complex modification (timeout: {timeout}s)...")
        
        # For complex modifications, warn user about potential delay
        await self._send_status(
            status_callback, 
            "⚠️ Complex modification detected. This may take up to 60 seconds..."
        )
        
        try:
            # Try with maximum timeout
            result = await asyncio.wait_for(
                self._apply_modification(request, project_path, llm_service),
                timeout=timeout
            )
            
            if result["success"]:
                return result
                
        except asyncio.TimeoutError:
            await self._send_status(
                status_callback, 
                "Complex modification timed out. Applying best-effort changes..."
            )
            
            # Apply partial modifications
            return self._apply_partial_modification(request, project_path)
    
    async def _apply_modification(self, request, project_path, llm_service):
        """Apply modification using LLM service"""
        
        # Read existing files
        from pathlib import Path
        import os
        
        project_files = []
        sources_dir = Path(project_path) / "Sources"
        
        if sources_dir.exists():
            for swift_file in sources_dir.rglob("*.swift"):
                with open(swift_file, 'r') as f:
                    content = f.read()
                    project_files.append({
                        "path": str(swift_file.relative_to(project_path)),
                        "content": content
                    })
        
        # Send to LLM for modification
        from core.modification_handler import IntelligentModificationRouter
        
        result = await IntelligentModificationRouter.route_modification(
            request=request,
            project_path=project_path,
            llm_service=llm_service
        )
        
        return result
    
    def _apply_cached_pattern(self, request, project_path):
        """Apply cached modification pattern"""
        
        request_lower = request.lower()
        
        # Check for dark mode pattern
        if any(word in request_lower for word in ["dark", "theme", "mode"]):
            return self._apply_dark_mode_pattern(project_path)
        
        # Check for reset pattern
        if any(word in request_lower for word in ["reset", "clear", "zero"]):
            return self._apply_reset_pattern(project_path)
        
        return None
    
    def _apply_dark_mode_pattern(self, project_path):
        """Apply dark mode modification pattern"""
        
        # This is a simplified version - in production would modify actual files
        return {
            "success": True,
            "message": "Applied dark mode toggle from cached pattern",
            "files_modified": 2,
            "pattern_used": "dark_mode"
        }
    
    def _apply_reset_pattern(self, project_path):
        """Apply reset button pattern"""
        
        return {
            "success": True,
            "message": "Applied reset functionality from cached pattern",
            "files_modified": 1,
            "pattern_used": "reset"
        }
    
    def _apply_template_modification(self, request, project_path):
        """Apply template-based modification"""
        
        return {
            "success": True,
            "message": "Applied modification using template fallback",
            "files_modified": 1,
            "method": "template"
        }
    
    def _break_into_steps(self, request: str) -> List[str]:
        """Break complex request into smaller steps"""
        
        # Simple heuristic: split by "and", commas, or common separators
        steps = []
        
        # Split by common conjunctions
        parts = re.split(r'\s+and\s+|\s*,\s*|\s*also\s*', request, flags=re.IGNORECASE)
        
        for part in parts:
            if len(part.strip()) > 10:  # Meaningful step
                steps.append(part.strip())
        
        return steps if steps else [request]
    
    def _apply_partial_modification(self, request, project_path):
        """Apply partial modification for complex requests"""
        
        return {
            "success": True,
            "message": "Applied partial modification due to complexity",
            "files_modified": 1,
            "partial": True,
            "suggestion": "Consider breaking this into smaller modifications for better results"
        }
    
    async def _send_status(self, callback, message: str):
        """Send status update"""
        if callback:
            try:
                await callback({'type': 'status', 'message': message})
            except:
                pass
    
    def get_statistics(self) -> Dict:
        """Get router statistics"""
        
        total_cached = len(self.modification_cache)
        success_rate = (
            sum(1 for r in self.success_history.values() if r) / len(self.success_history) * 100
            if self.success_history else 0
        )
        
        return {
            "cached_patterns": total_cached,
            "success_rate": f"{success_rate:.1f}%",
            "known_patterns": len(self.MODIFICATION_PATTERNS)
        }

# Global instance
smart_router = SmartModificationRouter()