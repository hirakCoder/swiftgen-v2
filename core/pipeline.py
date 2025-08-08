"""
Main Pipeline Orchestrator - The brain of SwiftGen
Coordinates all components with proper timeouts and fallbacks
"""

import asyncio
import time
import json
from typing import Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import os
import uuid

from .intent import IntentParser, AppIntent
from .circuit_breaker import CircuitBreaker, CircuitBreakerError

@dataclass
class PipelineResult:
    """Result of the entire pipeline"""
    success: bool
    project_id: str
    app_path: Optional[str] = None
    error: Optional[str] = None
    fallback_action: Optional[str] = None
    duration: float = 0
    metrics: Dict = None

class SwiftGenPipeline:
    """
    Main orchestrator - coordinates the entire flow
    with proper timeouts, circuit breakers, and fallbacks
    """
    
    # Intelligent timeouts based on real-world data
    TIMEOUTS = {
        'total': 180,       # Total request timeout (3 minutes for complex apps)
        'intent': 2,        # Intent parsing
        'generation': 20,   # LLM generation (allow for retries)
        'validation': 3,    # Code validation
        'build': 120,       # Xcode build (2 minutes for medium apps)
        'deploy': 30        # Simulator deployment
    }
    
    def __init__(self, llm_service=None, build_service=None, status_callback=None):
        self.intent_parser = IntentParser()
        self.llm_service = llm_service
        self.build_service = build_service
        self.status_callback = status_callback  # WebSocket status callback
        
        # Circuit breakers for each component
        self.generation_circuit = CircuitBreaker(
            'generation', 
            failure_threshold=3,
            timeout=self.TIMEOUTS['generation']
        )
        self.build_circuit = CircuitBreaker(
            'build',
            failure_threshold=3,  # Allow 3 failures before opening
            timeout=self.TIMEOUTS['build'],
            reset_timeout=120  # Reset after 2 minutes
        )
        
        # Metrics tracking
        self.metrics = {
            'requests_total': 0,
            'requests_success': 0,
            'requests_failed': 0,
            'avg_duration': 0
        }
    
    async def send_status(self, message: str, stage: str = None):
        """Send status update via callback if available"""
        print(f"[Pipeline] {message}")
        if self.status_callback:
            print(f"[Pipeline] Sending WebSocket message for stage: {stage}")
            await self.status_callback({
                'type': 'status',
                'message': message,
                'stage': stage
            })
        else:
            print(f"[Pipeline] No WebSocket callback set")
    
    async def process_request(
        self,
        description: str,
        app_name: str,
        project_id: Optional[str] = None
    ) -> PipelineResult:
        """
        Main entry point - process user request end-to-end
        """
        start_time = time.time()
        project_id = project_id or str(uuid.uuid4())[:8]
        
        try:
            # Apply total timeout to entire request
            result = await asyncio.wait_for(
                self._process_request_internal(description, app_name, project_id),
                timeout=self.TIMEOUTS['total']
            )
            
            # Update metrics
            self.metrics['requests_total'] += 1
            if result.success:
                self.metrics['requests_success'] += 1
            else:
                self.metrics['requests_failed'] += 1
            
            result.duration = time.time() - start_time
            return result
            
        except asyncio.TimeoutError:
            print(f"[Pipeline] Total timeout exceeded ({self.TIMEOUTS['total']}s)")
            return PipelineResult(
                success=False,
                project_id=project_id,
                error=f"Request timeout after {self.TIMEOUTS['total']} seconds",
                fallback_action="open_in_xcode",
                duration=time.time() - start_time
            )
        except Exception as e:
            print(f"[Pipeline] Unexpected error: {e}")
            return PipelineResult(
                success=False,
                project_id=project_id,
                error=str(e),
                fallback_action="retry_or_open_xcode",
                duration=time.time() - start_time
            )
    
    async def _process_request_internal(
        self,
        description: str,
        app_name: str,
        project_id: str
    ) -> PipelineResult:
        """
        Internal processing with stage-by-stage timeout
        """
        await self.send_status(f"Starting request: {app_name} ({project_id})", "analyze")
        
        # Stage 1: Parse Intent (2s timeout)
        try:
            intent = await asyncio.wait_for(
                self._parse_intent(description, app_name),
                timeout=self.TIMEOUTS['intent']
            )
            await self.send_status(f"Intent parsed: {intent.app_type.value}, features: {intent.core_features}", "analyze")
        except asyncio.TimeoutError:
            await self.send_status("Intent parsing timeout", "analyze")
            # Use basic defaults if parsing times out
            intent = AppIntent(
                raw_request=description,
                app_name=app_name,
                app_type='custom',
                core_features=[],
                ui_elements=['single_view'],
                data_needs=[]
            )
        
        # Stage 2: Generate Code (15s timeout with circuit breaker)
        try:
            code = await self.generation_circuit.call(
                self._generate_code,
                intent
            )
            await self.send_status(f"Code generated: {len(code.get('files', []))} files", "generate")
        except CircuitBreakerError as e:
            await self.send_status(f"Generation circuit open: {e}", "generate")
            return PipelineResult(
                success=False,
                project_id=project_id,
                error="Generation service temporarily unavailable",
                fallback_action="try_again_later"
            )
        except Exception as e:
            await self.send_status(f"Generation failed: {e}", "generate")
            return PipelineResult(
                success=False,
                project_id=project_id,
                error=f"Failed to generate code: {str(e)}",
                fallback_action="use_template"
            )
        
        # Stage 3: Save Project Files
        project_path = await self._save_project(project_id, code)
        await self.send_status(f"Project saved: {project_path}", "build")
        
        # Stage 4: Build Project (30s timeout with circuit breaker)
        try:
            build_result = await self.build_circuit.call(
                self._build_project,
                project_path,
                project_id
            )
            
            if build_result['success']:
                await self.send_status(f"Build successful: {build_result.get('app_path')}", "launch")
                return PipelineResult(
                    success=True,
                    project_id=project_id,
                    app_path=build_result.get('app_path'),
                    metrics={
                        'intent_type': intent.app_type.value,
                        'features': len(intent.core_features),
                        'files': len(code.get('files', []))
                    }
                )
            else:
                await self.send_status(f"Build failed: {build_result.get('error')}", "build")
                return PipelineResult(
                    success=False,
                    project_id=project_id,
                    error=build_result.get('error'),
                    fallback_action="open_in_xcode",
                    app_path=project_path
                )
                
        except CircuitBreakerError as e:
            await self.send_status(f"Build circuit open: {e}", "build")
            return PipelineResult(
                success=False,
                project_id=project_id,
                error="Build service temporarily unavailable",
                fallback_action="open_in_xcode",
                app_path=project_path
            )
        except Exception as e:
            await self.send_status(f"Build error: {e}", "build")
            return PipelineResult(
                success=False,
                project_id=project_id,
                error=f"Build failed: {str(e)}",
                fallback_action="open_in_xcode",
                app_path=project_path
            )
    
    async def _parse_intent(self, description: str, app_name: str) -> AppIntent:
        """Parse user intent - runs synchronously but wrapped for consistency"""
        return self.intent_parser.parse(description, app_name)
    
    async def _generate_code(self, intent: AppIntent) -> Dict:
        """Generate code based on intent"""
        # Try simple generator first for basic apps
        if intent.app_type in ['counter', 'timer', 'todo', 'calculator']:
            from generation.simple_generator import simple_generator
            
            project_path = f"workspaces/temp_{intent.app_name.lower()}"
            result = await simple_generator.generate_app(
                intent.raw_request,
                intent.core_features,
                project_path
            )
            
            if result['success']:
                # Convert to expected format
                files = []
                for filename, content in result['files'].items():
                    files.append({
                        'path': f"Sources/{filename}",
                        'content': content
                    })
                return {
                    'files': files,
                    'app_name': intent.app_name
                }
        
        if not self.llm_service:
            # Return minimal template if no LLM service
            return self._get_minimal_template(intent)
        
        # Build prompt based on intent
        requirements = self.intent_parser.get_minimal_requirements(intent)
        prompt = self._build_generation_prompt(requirements)
        
        # Generate with LLM
        result = await self.llm_service.generate(prompt)
        
        # Handle LLMResponse object from our router
        if hasattr(result, 'success'):
            if result.success:
                return json.loads(result.content)
            else:
                raise Exception(f"LLM generation failed: {result.error}")
        # Handle dict response
        elif isinstance(result, dict):
            if result.get('success'):
                return json.loads(result['content'])
            else:
                raise Exception(f"LLM generation failed: {result.get('error')}")
        else:
            raise Exception(f"Unexpected response type: {type(result)}")
    
    async def _save_project(self, project_id: str, code: Dict) -> str:
        """Save project files to disk"""
        project_path = f"workspaces/{project_id}"
        os.makedirs(project_path, exist_ok=True)
        
        # Ensure Sources directory exists
        sources_dir = os.path.join(project_path, 'Sources')
        os.makedirs(sources_dir, exist_ok=True)
        
        # Save each file
        for file_info in code.get('files', []):
            file_path = os.path.join(project_path, file_info['path'])
            
            # Ensure file goes in Sources if not already specified
            if not file_path.startswith(os.path.join(project_path, 'Sources')):
                # Extract just the filename if it has a path
                filename = os.path.basename(file_info['path'])
                file_path = os.path.join(sources_dir, filename)
            
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'w') as f:
                f.write(file_info['content'])
        
        # Save project.yml for xcodegen
        project_yml = self._generate_project_yml(code.get('app_name', 'App'))
        with open(os.path.join(project_path, 'project.yml'), 'w') as f:
            f.write(project_yml)
        
        return project_path
    
    async def _build_project(self, project_path: str, project_id: str) -> Dict:
        """Build the project"""
        if not self.build_service:
            # Return mock success if no build service
            return {'success': True, 'app_path': project_path}
        
        # Use production builder if it has the build_and_launch method
        if hasattr(self.build_service, 'build_and_launch'):
            return await self.build_service.build_and_launch(project_path, project_id)
        else:
            return await self.build_service.build(project_path, project_id)
    
    def _build_generation_prompt(self, requirements: Dict) -> str:
        """Build prompt for LLM based on requirements"""
        # Use flexible prompt system for maximum creativity
        try:
            from .flexible_prompt import FlexiblePromptBuilder
            # Pass raw description if available for better context
            raw_description = requirements.get('raw_description', '')
            return FlexiblePromptBuilder.build_generation_prompt(requirements, raw_description)
        except Exception as e:
            print(f"[Pipeline] Using balanced prompt fallback: {e}")
            try:
                from .balanced_prompt import BalancedPromptBuilder
                return BalancedPromptBuilder.build_generation_prompt(requirements)
            except:
                # Final fallback to simple prompt
                return self._build_simple_prompt(requirements)
    
    def _build_simple_prompt(self, requirements: Dict) -> str:
        """Fallback simple prompt"""
        app_type = requirements['app_type']
        features = requirements['must_have_features']
        app_name = requirements['app_name']
        
        return f"""Create a SwiftUI iOS app: {app_name}

Purpose: {app_type} app{f' with {", ".join(features)}' if features else ''}

DESIGN PHILOSOPHY:
- Be creative and unique in your implementation
- Follow Apple Human Interface Guidelines
- Create a delightful user experience with smooth animations
- Use modern iOS 17+ features where appropriate
- Make it feel like a premium app worth downloading

TECHNICAL REQUIREMENTS:
1. iOS 16.0+ minimum deployment target
2. SwiftUI 4.0+ with latest best practices
3. Include ContentView.swift and {requirements['app_name']}App.swift
4. Implement haptic feedback using UIImpactFeedbackGenerator:
   - Light feedback for taps
   - Medium for confirmations
   - Heavy for important actions
5. Use SF Symbols 5.0 for icons
6. Implement smooth animations with .animation(.spring())
7. Support both light and dark mode with .preferredColorScheme
8. Use gradient backgrounds and materials for depth
9. Add subtle shadows with .shadow(radius:)

UI/UX EXCELLENCE:
- Custom color schemes with Color(hex:) or gradient backgrounds
- Smooth transitions between states
- Responsive layout that works on all iPhone sizes
- Accessibility support with proper labels
- Visual feedback for all interactions
- Professional typography with Dynamic Type support
- Use materials like .ultraThinMaterial for overlays

HAPTIC FEEDBACK IMPLEMENTATION:
```swift
import UIKit

func hapticFeedback(_ style: UIImpactFeedbackGenerator.FeedbackStyle = .light) {{
    let generator = UIImpactFeedbackGenerator(style: style)
    generator.prepare()
    generator.impactOccurred()
}}

// Usage in buttons:
Button(action: {{
    hapticFeedback(.medium)
    // Your action here
}}) {{
    // Button content
}}
```

QUALITY STANDARDS:
- Every interaction should feel responsive and polished
- Use loading states where appropriate
- Error handling with user-friendly messages
- Smooth scrolling with proper insets
- Edge-to-edge design with safe area handling
- Performance optimized with @StateObject where needed

BE CREATIVE - Don't just make a basic {app_type}. Add unique touches like:
- Custom animations
- Delightful micro-interactions
- Unique visual design
- Innovative features that surprise and delight
- Thoughtful details that make it memorable

Return JSON with:
- files: array of {{path: string, content: string}}
- app_name: string
- bundle_id: string

Create something that would be featured on the App Store!
"""
    
    def _get_minimal_template(self, intent: AppIntent) -> Dict:
        """Get minimal template when LLM is unavailable"""
        return {
            'files': [
                {
                    'path': 'Sources/ContentView.swift',
                    'content': '''import SwiftUI

struct ContentView: View {
    var body: some View {
        VStack {
            Text("Hello, World!")
                .padding()
        }
    }
}'''
                },
                {
                    'path': 'Sources/App.swift',
                    'content': f'''import SwiftUI

@main
struct {intent.app_name}App: App {{
    var body: some Scene {{
        WindowGroup {{
            ContentView()
        }}
    }}
}}'''
                }
            ],
            'app_name': intent.app_name,
            'bundle_id': f'com.swiftgen.{intent.app_name.lower()}'
        }
    
    def _generate_project_yml(self, app_name: str) -> str:
        """Generate project.yml for xcodegen"""
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
      GENERATE_INFOPLIST_FILE: YES
"""
    
    def get_metrics(self) -> Dict:
        """Get pipeline metrics"""
        return {
            **self.metrics,
            'generation_circuit': self.generation_circuit.get_status(),
            'build_circuit': self.build_circuit.get_status()
        }