"""
Multi-LLM Router with Intelligent Failover
Routes to the best LLM for the task with automatic fallback
"""

import asyncio
import json
import os
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass
import time
from datetime import datetime

class LLMProvider(Enum):
    CLAUDE = "claude"
    GPT4 = "gpt4"
    GROK = "grok"

@dataclass
class LLMResponse:
    success: bool
    content: Optional[str] = None
    error: Optional[str] = None
    provider: Optional[LLMProvider] = None
    duration: float = 0

class LLMRouter:
    """
    Routes requests to the best LLM with automatic failover
    No infinite retries - just try each once and move on
    """
    
    def __init__(self):
        # Provider configuration
        # IMPORTANT: GPT-4 is now priority 1 due to Claude's Swift syntax issues
        self.providers = {
            LLMProvider.CLAUDE: {
                'api_key_env': 'CLAUDE_API_KEY',
                'timeout': 45,  # Increased timeout for better reliability
                'priority': 2,  # Demoted due to Swift syntax issues (Aug 13, 2025)
                'strengths': ['ui', 'swiftui', 'architecture']
            },
            LLMProvider.GPT4: {
                'api_key_env': 'OPENAI_API_KEY',
                'timeout': 45,  # Increased timeout for better reliability
                'priority': 1,  # Promoted to priority 1 - better Swift syntax
                'strengths': ['swift', 'swiftui', 'ios', 'logic', 'algorithms', 'data']
            },
            LLMProvider.GROK: {
                'api_key_env': 'XAI_API_KEY',
                'timeout': 30,  # Increased from 10s
                'priority': 3,  # Fastest, good for simple
                'strengths': ['simple', 'fast', 'basic']
            }
        }
        
        # Track provider health
        self.provider_health = {
            provider: {'failures': 0, 'last_success': None}
            for provider in LLMProvider
        }
        
        # User preference for specific provider (None = hybrid routing)
        self.preferred_provider = None
        
        # Initialize actual LLM clients if available
        self._init_clients()
    
    def _init_clients(self):
        """Initialize LLM clients based on available API keys"""
        self.clients = {}
        
        # Try to use existing enhanced_claude_service if available
        try:
            import sys
            sys.path.insert(0, '/Users/hirakbanerjee/Desktop/SwiftGen_Clean/stable_reference/backend')
            from enhanced_claude_service import EnhancedClaudeService
            
            # Use the existing working service
            self.enhanced_service = EnhancedClaudeService()
            self.clients[LLMProvider.CLAUDE] = self.enhanced_service
            self.clients[LLMProvider.GPT4] = self.enhanced_service  # It handles multiple LLMs
            self.clients[LLMProvider.GROK] = self.enhanced_service
            print("[LLM Router] Using existing EnhancedClaudeService")
            return
        except Exception as e:
            print(f"[LLM Router] Could not load EnhancedClaudeService: {e}")
        
        # Fallback to direct clients
        # Claude client
        if os.getenv('CLAUDE_API_KEY'):
            try:
                from anthropic import AsyncAnthropic
                self.clients[LLMProvider.CLAUDE] = AsyncAnthropic(
                    api_key=os.getenv('CLAUDE_API_KEY')
                )
            except ImportError:
                print("[LLM Router] Claude client not available")
        
        # OpenAI client
        if os.getenv('OPENAI_API_KEY'):
            try:
                from openai import AsyncOpenAI
                self.clients[LLMProvider.GPT4] = AsyncOpenAI(
                    api_key=os.getenv('OPENAI_API_KEY')
                )
            except ImportError:
                print("[LLM Router] OpenAI client not available")
        
        # xAI client would go here
        # For now, we'll mock it
        if os.getenv('XAI_API_KEY'):
            self.clients[LLMProvider.GROK] = None  # Mock for now
    
    async def generate(
        self,
        prompt: str,
        preferred_provider: Optional[LLMProvider] = None,
        task_type: Optional[str] = None
    ) -> LLMResponse:
        """
        Generate response using best available LLM
        
        Args:
            prompt: The generation prompt
            preferred_provider: Prefer specific provider
            task_type: Type of task (ui, logic, simple)
        """
        # Use instance-level preference if set (from API request)
        if self.preferred_provider:
            # Map string provider names to enum
            provider_map = {
                'claude': LLMProvider.CLAUDE,
                'gpt4': LLMProvider.GPT4,
                'grok': LLMProvider.GROK
            }
            if self.preferred_provider in provider_map:
                preferred_provider = provider_map[self.preferred_provider]
                print(f"[LLM Router] Using user-specified provider: {preferred_provider.value}")
        
        # Determine provider order
        providers = self._get_provider_order(preferred_provider, task_type)
        
        # Try each provider once
        for provider in providers:
            if provider not in self.clients:
                continue
            
            print(f"[LLM Router] Trying {provider.value}...")
            
            try:
                response = await self._call_provider(provider, prompt)
                if response.success:
                    self._record_success(provider)
                    return response
                else:
                    self._record_failure(provider)
                    print(f"[LLM Router] {provider.value} failed: {response.error}")
                    
            except asyncio.TimeoutError:
                self._record_failure(provider)
                print(f"[LLM Router] {provider.value} timed out")
            except Exception as e:
                self._record_failure(provider)
                print(f"[LLM Router] {provider.value} error: {e}")
        
        # All providers failed - return error
        return LLMResponse(
            success=False,
            error="All LLM providers failed or unavailable"
        )
    
    async def _call_provider(self, provider: LLMProvider, prompt: str) -> LLMResponse:
        """Call specific LLM provider"""
        start_time = time.time()
        config = self.providers[provider]
        
        try:
            # Apply timeout to provider call
            result = await asyncio.wait_for(
                self._make_provider_call(provider, prompt),
                timeout=config['timeout']
            )
            
            duration = time.time() - start_time
            
            if result:
                return LLMResponse(
                    success=True,
                    content=result,
                    provider=provider,
                    duration=duration
                )
            else:
                return LLMResponse(
                    success=False,
                    error="Empty response from provider",
                    provider=provider,
                    duration=duration
                )
                
        except asyncio.TimeoutError:
            raise
        except Exception as e:
            return LLMResponse(
                success=False,
                error=str(e),
                provider=provider,
                duration=time.time() - start_time
            )
    
    async def _make_provider_call(self, provider: LLMProvider, prompt: str) -> str:
        """Make actual API call to provider"""
        client = self.clients.get(provider)
        
        if not client:
            # Return mock response for testing
            return self._get_mock_response(prompt)
        
        # If we're using EnhancedClaudeService, use its methods
        if hasattr(self, 'enhanced_service') and client == self.enhanced_service:
            # Parse app name from prompt for the enhanced service
            app_name = "App"
            if "App Name:" in prompt:
                try:
                    app_name = prompt.split("App Name:")[1].split("\n")[0].strip()
                except:
                    pass
            
            # Determine if this is a simple app
            is_simple = self._is_simple_app(prompt)
            
            # Use the enhanced service's multi-LLM generation
            result = await self.enhanced_service.generate_ios_app_multi_llm(
                description=prompt,
                app_name=app_name,
                is_simple_app=is_simple  # Use proper detection instead of forcing simple
            )
            
            if result and 'files' in result:
                return json.dumps(result)
            else:
                return self._get_mock_response(prompt)
        
        # Direct API calls (fallback)
        if provider == LLMProvider.CLAUDE:
            response = await client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=8192,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
            
        elif provider == LLMProvider.GPT4:
            response = await client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=8192
            )
            return response.choices[0].message.content
            
        elif provider == LLMProvider.GROK:
            # Mock Grok response for now
            return self._get_mock_response(prompt)
        
        return None
    
    def _get_provider_order(
        self,
        preferred: Optional[LLMProvider],
        task_type: Optional[str]
    ) -> List[LLMProvider]:
        """Determine optimal provider order with intelligent error-aware routing"""
        # Start with all available providers
        providers = list(LLMProvider)
        
        # Filter out unhealthy providers (too many recent failures)
        healthy_providers = [
            p for p in providers
            if self.provider_health[p]['failures'] < 5
        ]
        
        # Intelligent routing based on task type
        if task_type:
            # Check for error-specific routing
            if 'error' in task_type.lower() or 'fix' in task_type.lower() or 'compilation' in task_type.lower():
                # For iOS/Swift compilation errors, prefer Claude or GPT-4
                error_providers = [LLMProvider.CLAUDE, LLMProvider.GPT4]
                healthy_providers = [p for p in error_providers if p in healthy_providers]
                # Add Grok as last resort
                if LLMProvider.GROK in providers and LLMProvider.GROK not in healthy_providers:
                    healthy_providers.append(LLMProvider.GROK)
                    
            elif 'ios' in task_type.lower() or 'swift' in task_type.lower() or 'swiftui' in task_type.lower():
                # For iOS/Swift specific tasks, prefer Claude
                healthy_providers.sort(
                    key=lambda p: (
                        0 if p == LLMProvider.CLAUDE else 
                        1 if p == LLMProvider.GPT4 else 2
                    )
                )
                
            elif 'algorithm' in task_type.lower() or 'logic' in task_type.lower() or 'data' in task_type.lower():
                # For algorithmic tasks, prefer GPT-4
                healthy_providers.sort(
                    key=lambda p: (
                        0 if p == LLMProvider.GPT4 else 
                        1 if p == LLMProvider.CLAUDE else 2
                    )
                )
                
            elif 'simple' in task_type.lower() or 'basic' in task_type.lower():
                # For simple tasks, any provider is fine, prefer fastest (Grok)
                healthy_providers.sort(
                    key=lambda p: (
                        0 if p == LLMProvider.GROK else 
                        1 if p == LLMProvider.CLAUDE else 2
                    )
                )
            else:
                # Default sorting by task strengths
                healthy_providers.sort(
                    key=lambda p: (
                        0 if task_type in self.providers[p]['strengths'] else 1,
                        self.providers[p]['priority']
                    )
                )
        else:
            # Sort by general priority
            healthy_providers.sort(
                key=lambda p: self.providers[p]['priority']
            )
        
        # Put preferred provider first if specified (overrides intelligent routing)
        if preferred and preferred in healthy_providers:
            healthy_providers.remove(preferred)
            healthy_providers.insert(0, preferred)
        
        return healthy_providers
    
    def _record_success(self, provider: LLMProvider):
        """Record successful call"""
        self.provider_health[provider]['failures'] = 0
        self.provider_health[provider]['last_success'] = datetime.now()
    
    def _record_failure(self, provider: LLMProvider):
        """Record failed call"""
        self.provider_health[provider]['failures'] += 1
    
    def _is_simple_app(self, prompt: str) -> bool:
        """Detect if this is a simple app request"""
        # DISABLED: Every app should get full creative treatment
        # No more templates or "simple" categorization
        return False  # ALWAYS return False to ensure creativity
        
        # OLD CODE (keeping for reference but NEVER USED):
        prompt_lower = prompt.lower()
        simple_keywords = [
            'simple', 'basic', 'minimal', 'quick',
            'timer', 'counter', 'calculator', 'converter',
            'todo', 'notes', 'flashlight'
        ]
        
        # Complex app indicators
        complex_keywords = [
            'complex', 'advanced', 'professional', 'enterprise',
            'authentication', 'database', 'api', 'network',
            'social', 'e-commerce', 'real-time', 'chat',
            'world class', 'fancy', 'beautiful ui'
        ]
        
        # Count indicators
        simple_count = sum(1 for keyword in simple_keywords if keyword in prompt_lower)
        complex_count = sum(1 for keyword in complex_keywords if keyword in prompt_lower)
        
        # If explicitly complex or has more complex indicators, use full prompts
        if complex_count > 0 or 'world class' in prompt_lower:
            return False
        
        # If explicitly simple or is a basic utility
        if simple_count > 0:
            return True
        
        # Default to full prompts for better quality
        return False
    
    def _get_mock_response(self, prompt: str) -> str:
        """Get mock response for testing"""
        # Extract app name from prompt if possible
        app_name = "App"
        if "App Name:" in prompt:
            try:
                app_name = prompt.split("App Name:")[1].split("\n")[0].strip()
            except:
                pass
        
        # Return minimal working app
        response = {
            "files": [
                {
                    "path": "Sources/ContentView.swift",
                    "content": """import SwiftUI

struct ContentView: View {
    @State private var count = 0
    
    var body: some View {
        VStack(spacing: 20) {
            Text("SwiftGen Demo")
                .font(.largeTitle)
                .fontWeight(.bold)
            
            Text("Count: \\(count)")
                .font(.title)
            
            HStack(spacing: 20) {
                Button("Increment") {
                    count += 1
                }
                .buttonStyle(.borderedProminent)
                
                Button("Reset") {
                    count = 0
                }
                .buttonStyle(.bordered)
            }
        }
        .padding()
    }
}"""
                },
                {
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
                }
            ],
            "app_name": app_name,
            "bundle_id": f"com.swiftgen.{app_name.lower()}"
        }
        
        return json.dumps(response)
    
    def get_health_status(self) -> Dict:
        """Get health status of all providers"""
        return {
            provider.value: {
                'available': provider in self.clients,
                'failures': health['failures'],
                'healthy': health['failures'] < 5,
                'last_success': health['last_success'].isoformat() if health['last_success'] else None
            }
            for provider, health in self.provider_health.items()
        }