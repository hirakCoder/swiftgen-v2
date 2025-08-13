import os
import json
import logging
import time
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import anthropic
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging FIRST before any logger usage
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import intelligent router
try:
    from intelligent_llm_router import IntelligentLLMRouter, RequestType
except ImportError:
    IntelligentLLMRouter = None
    RequestType = None
    logger.warning("IntelligentLLMRouter not available - using fallback mode")

# Import LLM modification fixer
try:
    from fix_llm_modification_response import LLMModificationFixer
except ImportError:
    LLMModificationFixer = None
    logger.warning("LLMModificationFixer not available - using fallback mode")

# Import token aware handler
try:
    from token_aware_request_handler import TokenAwareRequestHandler, check_and_prepare_request
except ImportError:
    TokenAwareRequestHandler = None
    check_and_prepare_request = None
    logger.warning("TokenAwareRequestHandler not available - using fallback mode")

@dataclass
class LLMModel:
    """Data class for LLM model configuration"""
    name: str
    provider: str
    api_key_env: str
    model_id: str
    max_tokens: int = 4096
    temperature: float = 0.7
    timeout: int = 30

class EnhancedClaudeService:
    """Enhanced service for managing multiple LLM providers"""

    def __init__(self):
        """Initialize the enhanced Claude service with all available LLMs"""
        self.models = {}
        self.available_models = []
        self.current_model = None
        self.api_keys = {}
        self._clients = {}
        
        # Initialize intelligent router
        self.router = IntelligentLLMRouter() if IntelligentLLMRouter else None
        self.failure_count = {}  # Track failures per request

        # Define ALL supported models - UPDATED WITH CORRECT MODEL NAMES
        self.supported_models = [
            LLMModel(
                name="Claude 3.5 Sonnet",
                provider="anthropic",
                api_key_env="CLAUDE_API_KEY",
                model_id="claude-3-5-sonnet-latest",  # Use latest Claude model for better Swift syntax
                max_tokens=8192  # Increased for complete app generation
            ),
            LLMModel(
                name="GPT-4 Turbo",
                provider="openai",
                api_key_env="OPENAI_API_KEY",
                model_id="gpt-4-turbo-preview",
                max_tokens=4096,  # GPT-4 Turbo max completion tokens
                temperature=0.7
            ),
            LLMModel(
                name="xAI Grok",
                provider="xai",
                api_key_env="XAI_API_KEY",
                model_id="grok-beta",
                max_tokens=8192  # Increased to match Claude
            )
        ]

        # Initialize all available models
        self._initialize_models()

        # Log initialization results
        logger.info(f"Initialized {len(self.available_models)} LLM models out of {len(self.supported_models)} supported")
        for model in self.available_models:
            logger.info(f"  - {model.name} ({model.provider}) ✓")

        # Set default model if available
        if self.available_models:
            self.current_model = self.available_models[0]
            logger.info(f"Default model set to: {self.current_model.name}")

    def _initialize_models(self):
        """Initialize all models that have valid API keys"""
        for model in self.supported_models:
            api_key = os.getenv(model.api_key_env, "").strip()
            if api_key:
                self.api_keys[model.provider] = api_key
                self.models[model.provider] = model
                self.available_models.append(model)
                logger.info(f"✓ Initialized {model.name}")
            else:
                logger.warning(f"✗ Skipped {model.name} - No API key found ({model.api_key_env})")

    def _initialize_client(self, provider: str):
        """Initialize API client for the given provider"""
        try:
            if provider == "anthropic" and provider not in self._clients:
                self._clients["anthropic"] = anthropic.Anthropic(api_key=self.api_keys["anthropic"])
                return True
            elif provider == "openai" and provider not in self._clients:
                openai.api_key = self.api_keys["openai"]
                self._clients["openai"] = openai
                return True
            elif provider == "xai" and provider not in self._clients:
                # xAI client initialization would go here
                self._clients["xai"] = None  # Placeholder
                return True
            return provider in self._clients
        except Exception as e:
            logger.error(f"Failed to initialize {provider} client: {str(e)}")
            return False

    def get_available_models(self) -> List[LLMModel]:
        """Get list of all available models"""
        return self.available_models

    def set_model(self, provider: str) -> bool:
        """Set the current model by provider name"""
        if provider in self.models:
            self.current_model = self.models[provider]
            logger.info(f"Switched to model: {self.current_model.name}")
            return True
        else:
            logger.error(f"Provider {provider} not available")
            return False

    async def generate_ios_app(self, description: str, app_name: str = None, is_simple_app: bool = False) -> Dict[str, Any]:
        """Generate iOS app code using the best available LLM"""
        if not self.available_models:
            raise Exception("No LLM model available")
        
        app_name = app_name or "MyApp"
        
        # Check if this is explicitly marked as a simple app
        if is_simple_app:
            logger.info(f"[ENHANCED_CLAUDE] Generating SIMPLE app - bypassing complex architecture")
        else:
            # Check if this is a complex app and use architect if needed
            try:
                from complex_app_architect import ComplexAppArchitect
                architect = ComplexAppArchitect()
                complexity = architect.analyze_complexity(description)
                
                if complexity == "high":
                    logger.info(f"[ARCHITECT] Detected high-complexity app. Using architectural planning...")
                    # Use architect to create enhanced prompt
                    enhanced_description = architect.create_enhanced_prompt(description, app_name)
                    # Override the description with the architect's detailed plan
                    description = enhanced_description
                    logger.info(f"[ARCHITECT] Created detailed architecture plan for {architect.identify_app_type(description)} app")
            except ImportError:
                logger.warning("ComplexAppArchitect not available, using standard generation")
        
        # Use intelligent routing if available
        if self.router:
            available_providers = [model.provider for model in self.available_models]
            selected_provider = self.router.route_initial_request(description, app_type="ios", available_providers=available_providers)
            if selected_provider in self.models:
                self.current_model = self.models[selected_provider]
                logger.info(f"[ROUTER] Selected {self.current_model.name} for app generation")
            else:
                logger.warning(f"[ROUTER] Provider {selected_provider} not available, using default")
                self.current_model = self.available_models[0]
        else:
            # Fallback to first available model
            if not self.current_model:
                self.current_model = self.available_models[0]

        # Create the prompt for iOS app generation
        # Use simple prompts for simple apps
        if is_simple_app:
            try:
                from enhanced_prompts import get_simple_app_prompt
                system_prompt, user_prompt = get_simple_app_prompt(app_name or "MyApp", description)
                use_enhanced = True
                logger.info("[ENHANCED_CLAUDE] Using simple app prompts")
            except ImportError:
                logger.warning("Simple app prompts not available, falling back to standard")
                use_enhanced = False
        else:
            # Try to use enhanced prompts for better syntax
            try:
                from enhanced_prompts import get_generation_prompts
                system_prompt, user_prompt = get_generation_prompts(app_name or "MyApp", description)
                # Skip the old user_prompt generation
                use_enhanced = True
            except ImportError:
                use_enhanced = False
        
        if not use_enhanced:
            system_prompt = """You are SwiftGen AI, an expert iOS developer. Create UNIQUE, production-ready SwiftUI apps.

CRITICAL RULES:
1. Each app must be UNIQUE - use creative approaches, unique UI designs, innovative features
2. Use @Environment(\\.dismiss) NOT @Environment(\\.presentationMode) 
3. ALWAYS use double quotes " for strings, NEVER single quotes '
4. Return ONLY valid JSON - no explanatory text before or after
5. Make apps exceptional, not just functional
6. NEVER use generic names like "MyApp" - always use the actual app name provided
7. Only include actual Swift source files in the files array - no JSON, PDF, or asset files
8. Use the EXACT bundle ID format: com.swiftgen.{app_name_lowercase_no_spaces}
9. ENSURE all files have actual Swift code content - never return empty content strings
10. ALWAYS import SwiftUI in every Swift file
11. ALWAYS import Combine when using @Published or ObservableObject

Focus on: Elegant architecture, smooth animations, thoughtful UX, accessibility."""

        if not use_enhanced:
            user_prompt = f"""Create a complete iOS app with these requirements:
App Name: {app_name or "MyApp"}
Description: {description}

Return a JSON response with this EXACT structure:
{{
    "files": [
        {{
            "path": "Sources/App.swift",
            "content": "// Full Swift code here"
        }},
        {{
            "path": "Sources/ContentView.swift", 
            "content": "// Full Swift code here"
        }}
    ],
    "bundle_id": "com.swiftgen.{app_name.lower().replace(' ', '') if app_name else 'app'}",
    "features": ["Feature 1", "Feature 2"],
    "unique_aspects": "What makes this implementation unique",
    "app_name": "{app_name or 'MyApp'}",
    "product_name": "{app_name.replace(' ', '') if app_name else 'MyApp'}"
}}"""

        try:
            logger.info(f"[ENHANCED_CLAUDE] Calling LLM for generation...")
            result = await self._generate_with_current_model(system_prompt, user_prompt)
            logger.info(f"[ENHANCED_CLAUDE] Got LLM response, type: {type(result)}, length: {len(str(result))}")
            
            # DEBUG: Log the first 500 chars of raw response to check for JSON issues
            if isinstance(result, str):
                logger.debug(f"[RAW RESPONSE] First 500 chars: {result[:500]}")
                # Check for common JSON issues
                if '\\"' in result[:500]:
                    logger.warning("[JSON WARNING] Response contains escaped quotes that may cause parsing issues")
                if '\\n' in result[:500] and not '\\\\n' in result[:500]:
                    logger.warning("[JSON WARNING] Response contains unescaped newlines")

            # Parse JSON response
            if isinstance(result, str):
                # Clean the response to ensure it's valid JSON
                result = result.strip()
                if result.startswith("```json"):
                    result = result[7:]
                if result.endswith("```"):
                    result = result[:-3]
                
                # CRITICAL: Fix common JSON issues BEFORE parsing
                original_result = result
                try:
                    result = json.loads(result)
                except json.JSONDecodeError as e:
                    logger.warning(f"[JSON FIX] Initial parse failed at pos {e.pos}: {e.msg}")
                    
                    # Try to fix common JSON escaping issues from LLMs
                    fixed_json = result
                    
                    # Fix unescaped newlines and tabs in JSON strings
                    import re
                    # This pattern finds string values and fixes escape sequences
                    def fix_string_escapes(text):
                        # Find all string values in JSON
                        in_string = False
                        fixed = []
                        i = 0
                        while i < len(text):
                            if text[i] == '"' and (i == 0 or text[i-1] != '\\'):
                                in_string = not in_string
                                fixed.append(text[i])
                            elif in_string:
                                if text[i] == '\n':
                                    fixed.append('\\n')
                                elif text[i] == '\r':
                                    fixed.append('\\r')
                                elif text[i] == '\t':
                                    fixed.append('\\t')
                                elif text[i] == '\\' and i + 1 < len(text) and text[i+1] not in 'nrt"\\':
                                    # Escape lone backslashes
                                    fixed.append('\\\\')
                                else:
                                    fixed.append(text[i])
                            else:
                                fixed.append(text[i])
                            i += 1
                        return ''.join(fixed)
                    
                    try:
                        fixed_json = fix_string_escapes(fixed_json)
                        result = json.loads(fixed_json)
                        logger.info("[JSON FIX] Successfully fixed escape sequences and parsed JSON")
                    except json.JSONDecodeError as e2:
                        logger.error(f"[JSON FIX] Still failed: {e2}")
                        # Last resort: try to extract valid JSON
                        json_match = re.search(r'\{[\s\S]*\}', original_result)
                        if json_match:
                            try:
                                result = json.loads(json_match.group(0))
                            except:
                                raise e  # Re-raise original error
                        else:
                            raise e
            
            # Check for truncated code
            if "files" in result:
                for file in result["files"]:
                    content = file.get("content", "")
                    if "..." in content and re.search(r'(class|struct|enum)\s+\w+\.\.\.', content):
                        logger.warning(f"Detected truncated code in {file.get('path', 'unknown')}")
                        raise Exception("Generated code appears to be truncated. Retrying with higher token limit...")
            
            # Add LLM provider info to result
            if self.current_model:
                result["generated_by_llm"] = self.current_model.provider

            logger.info(f"[ENHANCED_CLAUDE] Successfully parsed response with {len(result.get('files', []))} files")
            return result

        except Exception as e:
            logger.error(f"Generation failed with {self.current_model.name}: {str(e)}")
            
            # Import positive messages if available
            try:
                from positive_recovery_messages import transform_error_to_positive
                positive_msg = transform_error_to_positive(str(e), "generation")
                logger.info(f"[POSITIVE] {positive_msg}")
            except:
                pass
            
            # Track failure
            request_id = f"gen_{app_name}_{description[:20]}"
            self.failure_count[request_id] = self.failure_count.get(request_id, 0) + 1
            
            # Use intelligent fallback if router available
            if self.router and self.current_model:
                request_type = self.router.analyze_request(description)
                next_provider, strategy = self.router.get_fallback_strategy(
                    self.current_model.provider,
                    request_type,
                    self.failure_count[request_id]
                )
                
                if next_provider in self.models:
                    self.current_model = self.models[next_provider]
                    logger.info(f"[ROUTER] Retrying with {self.current_model.name} using {strategy}")
                    
                    # Record failure for learning
                    self.router.record_result(
                        self.current_model.provider,
                        request_type,
                        success=False
                    )
                    
                    try:
                        return await self.generate_ios_app(description, app_name)
                    except:
                        pass
            
            # Fallback to sequential retry
            for model in self.available_models:
                if model != self.current_model:
                    self.current_model = model
                    logger.info(f"Retrying with {model.name}")
                    try:
                        return await self.generate_ios_app(description, app_name)
                    except:
                        continue

            raise Exception(f"All LLM models failed. Last error: {str(e)}")

    async def _generate_with_current_model(self, system_prompt: str, user_prompt: str) -> str:
        """Generate text using the current model"""
        if self.current_model.provider == "anthropic":
            return await self._generate_claude(system_prompt, user_prompt)
        elif self.current_model.provider == "openai":
            return await self._generate_openai(system_prompt, user_prompt)
        elif self.current_model.provider == "xai":
            return await self._generate_xai(system_prompt, user_prompt)
        else:
            raise Exception(f"Unknown provider: {self.current_model.provider}")

    async def _generate_claude(self, system_prompt: str, user_prompt: str) -> str:
        """Generate text using Claude"""
        import anthropic

        client = anthropic.Anthropic(api_key=self.api_keys["anthropic"])

        message = client.messages.create(
            model=self.current_model.model_id,
            max_tokens=self.current_model.max_tokens,
            temperature=self.current_model.temperature,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )

        return message.content[0].text

    async def _generate_openai(self, system_prompt: str, user_prompt: str) -> str:
        """Generate text using OpenAI"""
        from openai import OpenAI
        
        client = OpenAI(api_key=self.api_keys["openai"])
        
        response = client.chat.completions.create(
            model=self.current_model.model_id,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=self.current_model.max_tokens,
            temperature=self.current_model.temperature
        )

        return response.choices[0].message.content

    async def _generate_xai(self, system_prompt: str, user_prompt: str) -> str:
        """Generate text using xAI"""
        try:
            # Use httpx for xAI API calls
            import httpx
            
            if not hasattr(self, 'xai_client'):
                self.xai_client = httpx.AsyncClient(
                    base_url="https://api.x.ai/v1",
                    headers={
                        "Authorization": f"Bearer {self.api_keys['xai']}",
                        "Content-Type": "application/json"
                    },
                    timeout=120.0
                )
            
            # Prepare messages
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            # Generate with xAI
            payload = {
                "model": "grok-2",
                "messages": messages,
                "temperature": self.current_model.temperature,
                "max_tokens": self.current_model.max_tokens,
                "stream": False
            }
            
            response = await self.xai_client.post("/chat/completions", json=payload)
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                raise Exception(f"xAI API error: {response.status_code} - {response.text}")
            
        except Exception as e:
            logger.error(f"xAI generation failed: {e}")
            logger.warning("Falling back to Claude")
            
            # Use Claude as fallback
            if "anthropic" in self.models:
                self.current_model = self.models["anthropic"]
                return await self._generate_claude(system_prompt, user_prompt)
            elif "openai" in self.models:
                self.current_model = self.models["openai"]
                return await self._generate_openai(system_prompt, user_prompt)
            else:
                raise NotImplementedError("No fallback LLM available")

    def generate_text(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Synchronous wrapper for compatibility"""
        import asyncio

        async def _async_generate():
            result = await self._generate_with_current_model("You are a helpful assistant.", prompt)
            return {"success": True, "text": result}

        try:
            # Check if we're already in an event loop
            try:
                loop = asyncio.get_running_loop()
                # We're in an async context, can't use run_until_complete
                # Create a task and return a placeholder
                task = asyncio.create_task(_async_generate())
                # This is a hack but necessary for sync/async compatibility
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    future = pool.submit(asyncio.run, _async_generate())
                    return future.result()
            except RuntimeError:
                # No event loop running, create one
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                return loop.run_until_complete(_async_generate())
        except Exception as e:
            return {"success": False, "error": str(e), "text": ""}
        finally:
            if 'loop' in locals() and not asyncio.get_event_loop().is_running():
                loop.close()
    
    async def generate_text_async(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Async version of generate_text for use in async contexts"""
        try:
            result = await self._generate_with_current_model("You are a helpful assistant.", prompt)
            return {"success": True, "text": result}
        except Exception as e:
            return {"success": False, "error": str(e), "text": ""}
    
    async def get_completion(self, system_prompt: str, user_prompt: str, max_tokens: int = 4096, temperature: float = 0.7) -> str:
        """Get completion from current LLM model - for chat handler compatibility"""
        try:
            # Use the current model with provided prompts
            response = await self._generate_with_current_model(system_prompt, user_prompt)
            return response
        except Exception as e:
            print(f"Error in get_completion: {e}")
            raise
    
    async def extract_app_name(self, description: str) -> str:
        """Use LLM to extract a proper app name from description"""
        prompt = f"""Given this iOS app description, provide a proper app name.

Description: {description}

Requirements:
- The name should be 1-4 words maximum
- It should be descriptive and memorable
- Avoid generic names like "MyApp" or "App"
- Don't include "iOS" or "App" in the name unless essential
- Make it suitable for the App Store

Return ONLY the app name, nothing else. No explanation or quotes."""

        try:
            # Use a low temperature for consistent naming
            response = await self._generate_with_current_model("You are an app naming expert.", prompt)
            if response:
                app_name = response.strip().strip('"').strip("'")
                # Limit length
                if len(app_name) > 30:
                    app_name = app_name[:30].rsplit(' ', 1)[0]
                return app_name
            else:
                return None
        except Exception as e:
            print(f"[LLM] Failed to extract app name: {e}")
            return None

    # Optional: Add these methods if your main.py expects them
    async def generate_ios_app_multi_llm(self, description: str, app_name: str = None, is_simple_app: bool = False) -> Dict[str, Any]:
        """Alias for compatibility"""
        return await self.generate_ios_app(description, app_name, is_simple_app)

    async def modify_ios_app(self, app_name: str, description: str, modification: str,
                             files: List[Dict], existing_bundle_id: str = None,
                             project_tracking_id: str = None) -> Dict[str, Any]:
        """Modify an existing iOS app with intelligent modification handling"""
        
        # Import modification handler
        try:
            from modification_handler import ModificationHandler
            mod_handler = ModificationHandler()
        except:
            mod_handler = None
        
        # Use intelligent routing for modifications
        if self.router:
            # Analyze modification to determine best LLM
            available_providers = [model.provider for model in self.available_models]
            selected_provider = self.router.route_initial_request(modification, available_providers=available_providers, is_modification=True)
            if selected_provider in self.models:
                self.current_model = self.models[selected_provider]
                logger.info(f"[ROUTER] Selected {self.current_model.name} for modification: {modification[:50]}...")
            
            # Create specialized prompt if router available
            strategy = "standard approach"
            if self.router:
                request_type = self.router.analyze_request(modification, is_modification_context=True)
                specialized_prompt = self.router.create_specialized_prompt(
                    self.current_model.provider,
                    strategy,
                    modification,
                    []  # No previous failures yet
                )
                logger.info(f"[ROUTER] Using specialized prompt for {request_type.value}")
        
        # Analyze modification request
        modification_type = self._analyze_modification_type(modification)
        
        system_prompt = f"""You are SwiftGen AI, an expert iOS developer. 
{modification_type['guidance']}

IMPORTANT RULES:
1. ONLY modify what is requested - do NOT rebuild the entire app
2. Keep all existing functionality unless explicitly asked to change it
3. Maintain the same app structure and architecture
4. Return ALL files with their complete content (modified or unchanged)
5. Do NOT change the app name or bundle ID
6. If fixing "cannot find X in scope" errors, CREATE the missing file/type
7. When creating new files, add them to the files array in your response

⚠️ CRITICAL iOS VERSION CONSTRAINTS - MUST FOLLOW:
- Target iOS: 16.0 ONLY (NOT 17.0)
- DO NOT use ANY iOS 17+ features:
  * NO .symbolEffect() of any kind - use .scaleEffect or .rotationEffect instead
  * NO .bounce animations - use .spring() instead
  * NO iOS 17+ modifiers or APIs
  * Always check feature availability before using
- If you're unsure about iOS version, use the iOS 16 approach
  * NO .bounce effects - use .animation(.spring()) instead
  * NO @Observable macro - use ObservableObject + @Published
  * NO .scrollBounceBehavior modifier
  * NO .contentTransition modifier
- If unsure about iOS availability, use iOS 16-compatible alternatives

MODERN SWIFT PATTERNS (MANDATORY):
1. Navigation: Use NavigationStack, NOT NavigationView (deprecated)
2. State Management: ObservableObject + @Published for iOS 16
3. Async/Await: ALWAYS use async/await, NEVER completion handlers
4. UI Updates: Mark UI classes/methods with @MainActor
5. Modifiers: Use .foregroundStyle NOT .foregroundColor
6. Concurrency: NEVER use DispatchSemaphore with async/await

MODULE IMPORT RULES - CRITICAL FOR SWIFTUI:
- NEVER import local folders: NO import Components, Views, Models, ViewModels, Services
- ONLY import system frameworks: import SwiftUI, Foundation, Combine, CoreData, etc.
- SwiftUI uses direct type references, NOT module imports
- Access types directly: ContentView NOT Components.ContentView
- WRONG: import Components; Components.MyView()
- RIGHT: MyView() // direct reference"""

        # Use LLMModificationFixer for enhanced prompt if available
        if LLMModificationFixer:
            fixer = LLMModificationFixer(max_tokens=self.current_model.max_tokens if self.current_model else 8192)
            user_prompt = fixer.prepare_enhanced_modification_prompt(app_name, modification, files, existing_bundle_id or "com.example.app")
        elif mod_handler:
            user_prompt = mod_handler.prepare_modification_prompt(app_name, modification, files)
        else:
            # Fallback to simpler prompt with more content
            user_prompt = f"""Current iOS App: {app_name}
Modification Request: {modification}

CRITICAL: Return ALL {len(files)} files, even if unchanged.
Only modify files that need to change for: "{modification}"

Current files:
"""
            for file in files:
                # Show more content - 2000 chars instead of 500
                user_prompt += f"\n--- {file['path']} ---\n{file['content'][:2000]}...\n"
            
            user_prompt += f"""

Return JSON with ALL {len(files)} files:
{{
    "files": [ALL {len(files)} files with path and content],
    "bundle_id": "{existing_bundle_id}",
    "modification_summary": "Brief summary of what changed",
    "changes_made": [
        "SPECIFIC change 1 (e.g., Added dark mode toggle to settings)",
        "SPECIFIC change 2 (e.g., Updated color scheme to support dark theme)",
        "SPECIFIC change 3 (e.g., Added UserDefaults to persist theme preference)",
        "List each concrete change made to implement the modification"
    ],
    "files_modified": ["List of files that were actually modified"]
}}

IMPORTANT: The "changes_made" array must contain SPECIFIC, CONCRETE changes you made to the code, not generic statements."""

        # Check token limits before making request
        if check_and_prepare_request and self.current_model:
            prepared_prompt, needs_splitting, token_estimate = check_and_prepare_request(
                'modification', 
                user_prompt, 
                files,
                self.current_model.model_id
            )
            
            if needs_splitting:
                logger.warning(f"[TOKEN_HANDLER] Request too large ({token_estimate.total_tokens} tokens), using optimized prompt")
                user_prompt = prepared_prompt
            else:
                logger.info(f"[TOKEN_HANDLER] Request within limits ({token_estimate.total_tokens} tokens)")
        
        # Try generation with intelligent error handling
        request_id = f"mod_{app_name}_{modification[:20]}"
        self.failure_count[request_id] = self.failure_count.get(request_id, 0)
        
        try:
            result = await self._generate_with_current_model(system_prompt, user_prompt)
        except Exception as gen_error:
            logger.error(f"[ROUTER] Modification generation failed: {gen_error}")
            
            # Intelligent fallback for modifications
            if self.router and self.current_model:
                self.failure_count[request_id] += 1
                request_type = self.router.analyze_request(modification, is_modification_context=True)
                
                # Get fallback strategy
                next_provider, strategy = self.router.get_fallback_strategy(
                    self.current_model.provider,
                    request_type,
                    self.failure_count[request_id]
                )
                
                if next_provider in self.models:
                    logger.info(f"[ROUTER] Falling back to {next_provider} with {strategy}")
                    self.current_model = self.models[next_provider]
                    
                    # Create specialized prompt for fallback
                    if self.router:
                        specialized_user_prompt = self.router.create_specialized_prompt(
                            next_provider,
                            strategy,
                            modification,
                            [str(gen_error)]
                        )
                        # Append existing context
                        specialized_user_prompt += "\n\n" + user_prompt.split("Current files:")[1] if "Current files:" in user_prompt else user_prompt
                        user_prompt = specialized_user_prompt
                    
                    # Retry with fallback
                    result = await self._generate_with_current_model(system_prompt, user_prompt)
                else:
                    raise gen_error
            else:
                raise gen_error

        # CRITICAL FIX: Check if result is empty or invalid
        if not result or (isinstance(result, str) and len(result.strip()) < 10):
            print(f"[ERROR] LLM returned empty or invalid response for modification")
            # Create a minimal valid response
            if mod_handler:
                result = mod_handler.create_minimal_modification(files, modification)
            else:
                result = {
                    "files": files,  # Return original files unchanged
                    "modification_summary": "Failed to apply modification - LLM returned empty response",
                    "changes_made": [],
                    "files_modified": []
                }
        elif isinstance(result, str):
            result = result.strip()
            if result.startswith("```json"):
                result = result[7:]
            if result.endswith("```"):
                result = result[:-3]
            
            # Clean up common JSON issues before parsing
            try:
                # First attempt - direct parsing
                result = json.loads(result)
            except json.JSONDecodeError as e:
                print(f"[ERROR] Initial JSON parse failed: {e}")
                print(f"[ERROR] Error at position: {e.pos if hasattr(e, 'pos') else 'unknown'}")
                
                # Use modification handler to fix JSON if available
                if mod_handler:
                    fixed_result = mod_handler.fix_json_response(result)
                    if fixed_result:
                        result = fixed_result
                    else:
                        # Create minimal modification response
                        result = mod_handler.create_minimal_modification(files, modification)
                else:
                    # Fallback parsing attempts
                    try:
                        # Extract JSON object
                        json_match = re.search(r'\{[\s\S]*\}', result)
                        if json_match:
                            result = json.loads(json_match.group(0))
                        else:
                            raise ValueError("No JSON object found")
                    except Exception as e3:
                        print(f"[ERROR] All JSON parsing failed: {e3}")
                        # Return minimal response
                        return {
                            "app_name": app_name,
                            "bundle_id": existing_bundle_id,
                            "files": files,  # Return original files unchanged
                            "modification_summary": f"Failed to apply: {modification}",
                            "changes_made": ["Error: Could not parse LLM response"],
                            "modified_by_llm": self.current_model.provider if self.current_model else "claude"
                        }
                    else:
                        print("[ERROR] No JSON object found in response")
                        return {
                            "app_name": app_name,
                            "bundle_id": existing_bundle_id,
                            "files": [],  # Empty files = clear failure signal
                            "modification_summary": "Failed to parse modification response",
                            "changes_made": ["Error: No valid JSON in response"],
                            "modified_by_llm": self.current_model.provider if self.current_model else "claude"
                        }

        # Record success if using router
        if self.router and isinstance(result, dict):
            request_type = self.router.analyze_request(modification, is_modification_context=True)
            self.router.record_result(
                self.current_model.provider,
                request_type,
                success=True
            )
            logger.info(f"[ROUTER] Recorded success for {self.current_model.provider} on {request_type.value}")
        
        # Ensure consistency
        if isinstance(result, dict):
            # Use LLMModificationFixer for enhanced validation if available
            if LLMModificationFixer and 'fixer' in locals():
                # Normalize file paths first
                if 'files' in result and isinstance(result['files'], list):
                    result['files'] = fixer.normalize_file_paths(result['files'], files)
                
                # Validate the response
                is_valid, issues = fixer.validate_modification_response(result, files)
                if not is_valid:
                    logger.warning(f"[LLM_FIXER] Modification response has issues: {issues}")
                    result = fixer.fix_incomplete_response(result, files)
                    
                    # Re-validate after fix
                    is_valid, issues = fixer.validate_modification_response(result, files)
                    if not is_valid:
                        logger.error(f"[LLM_FIXER] Failed to fix response: {issues}")
                    else:
                        logger.info("[LLM_FIXER] Successfully fixed modification response")
            elif mod_handler:
                # Fallback to original validation
                is_valid, issues = mod_handler.validate_modification_response(result, files)
                if not is_valid:
                    print(f"[ERROR] Modification response validation failed: {issues}")
                    # Try to fix by ensuring all files are present
                    if 'files' not in result or len(result.get('files', [])) != len(files):
                        print(f"[WARNING] Fixing incomplete file list - ensuring all {len(files)} files are included")
                        # Create a mapping of returned files
                        returned_files = {f['path']: f for f in result.get('files', [])}
                        # Fill in missing files with originals
                        complete_files = []
                        for orig_file in files:
                            if orig_file['path'] in returned_files:
                                complete_files.append(returned_files[orig_file['path']])
                            else:
                                print(f"[WARNING] File {orig_file['path']} was missing - including original")
                                complete_files.append(orig_file)
                        result['files'] = complete_files
            
            result["bundle_id"] = existing_bundle_id
            result["app_name"] = app_name
            result["modified_by_llm"] = self.current_model.provider if self.current_model else "claude"
            
            # Ensure we have modification summary
            if "modification_summary" not in result:
                result["modification_summary"] = modification[:100]
            
            # Ensure we have specific changes listed
            if "changes_made" not in result or not result.get("changes_made") or result.get("changes_made") == ["Changes applied as requested"]:
                # Try to infer changes from modification request
                inferred_changes = []
                mod_lower = modification.lower()
                
                # Common modification patterns
                if "dark mode" in mod_lower or "dark theme" in mod_lower:
                    inferred_changes.extend([
                        "Added dark mode support to the app",
                        "Updated color scheme for dark theme compatibility",
                        "Added theme toggle functionality"
                    ])
                elif "color" in mod_lower:
                    inferred_changes.append(f"Updated color scheme as requested: {modification[:80]}")
                elif "add" in mod_lower:
                    inferred_changes.append(f"Added new functionality: {modification[:80]}")
                elif "fix" in mod_lower:
                    inferred_changes.append(f"Fixed issue: {modification[:80]}")
                elif "update" in mod_lower or "change" in mod_lower:
                    inferred_changes.append(f"Updated: {modification[:80]}")
                else:
                    inferred_changes.append(f"Applied modification: {modification[:80]}")
                
                # Add file count info
                files_modified = result.get("files_modified", [])
                if files_modified:
                    inferred_changes.append(f"Modified {len(files_modified)} files: {', '.join(files_modified[:3])}")
                elif "files" in result:
                    inferred_changes.append(f"Updated {len(result['files'])} files")
                
                result["changes_made"] = inferred_changes
                
        else:
            # If result is not a dict at this point, something went wrong
            print(f"[ERROR] Result is not a dict: {type(result)}")
            return {
                "app_name": app_name,
                "bundle_id": existing_bundle_id,
                "files": files,  # Return original files
                "modification_summary": "Failed to process modification",
                "changes_made": ["Error: Invalid response format"],
                "modified_by_llm": self.current_model.provider if self.current_model else "claude"
            }
        
        return result

    async def modify_ios_app_multi_llm(self, *args, **kwargs):
        """Alias for compatibility"""
        return await self.modify_ios_app(*args, **kwargs)
    
    def _analyze_modification_type(self, modification: str) -> Dict[str, str]:
        """Analyze the modification request to provide better guidance"""
        mod_lower = modification.lower()
        
        if any(word in mod_lower for word in ["theme", "dark", "color", "style"]):
            return {
                "type": "ui_theme",
                "guidance": "You're modifying UI theme/colors. Focus on Color assets, view modifiers, and appearance settings. Do NOT change app functionality."
            }
        elif any(word in mod_lower for word in ["add button", "add feature", "new screen"]):
            return {
                "type": "feature_addition",
                "guidance": "You're adding a new feature. Integrate it smoothly with existing code without disrupting current functionality."
            }
        elif any(word in mod_lower for word in ["fix", "bug", "error", "crash"]):
            return {
                "type": "bug_fix",
                "guidance": "You're fixing a bug. Focus on the specific issue without changing unrelated code."
            }
        elif any(word in mod_lower for word in ["improve", "enhance", "optimize"]):
            return {
                "type": "enhancement",
                "guidance": "You're enhancing existing functionality. Make targeted improvements without rebuilding."
            }
        else:
            return {
                "type": "general",
                "guidance": "Make the requested modification while preserving all existing functionality."
            }