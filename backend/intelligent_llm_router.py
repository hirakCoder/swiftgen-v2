"""
Intelligent LLM Router for SwiftGen
Routes requests to the most appropriate LLM based on request analysis
"""

import re
from typing import Dict, List, Tuple, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class RequestType(Enum):
    """Types of requests for routing"""
    UI_DESIGN = "ui_design"
    ALGORITHM = "algorithm"
    DATA_MODEL = "data_model"
    NAVIGATION = "navigation"
    SIMPLE_MODIFICATION = "simple_modification"
    COMPLEX_MODIFICATION = "complex_modification"
    BUG_FIX = "bug_fix"
    PERFORMANCE = "performance"
    ARCHITECTURE = "architecture"


class LLMStrength(Enum):
    """Known strengths of each LLM"""
    CLAUDE = {
        "strengths": ["ui_design", "context_understanding", "swiftui", "complex_reasoning"],
        "weaknesses": ["rate_limits"]
    }
    GPT4 = {
        "strengths": ["algorithms", "code_generation", "patterns", "debugging"],
        "weaknesses": ["ui_nuances"]
    }
    XAI = {
        "strengths": ["simple_tasks", "speed", "fresh_perspective"],
        "weaknesses": ["complex_ui"]
    }


class IntelligentLLMRouter:
    """Routes requests to appropriate LLMs based on analysis"""
    
    def __init__(self):
        self.request_history = []
        # CRITICAL FIX: Claude is much better at UI modifications like dark mode
        # xAI Grok was failing to properly implement features
        self.success_rates = {
            "anthropic": {"ui_design": 0.95, "algorithm": 0.75, "default": 0.80},
            "openai": {"ui_design": 0.70, "algorithm": 0.90, "default": 0.82},
            "xai": {"ui_design": 0.65, "algorithm": 0.78, "default": 0.85}
        }
        
        # Keywords for request classification
        self.ui_keywords = [
            'color', 'background', 'animation', 'animations', 'animate', 'layout', 'design', 'theme',
            'style', 'appearance', 'visual', 'look', 'ui', 'ux', 'interface',
            'button', 'view', 'screen', 'display', 'shade', 'gradient',
            'text', 'font', 'size', 'larger', 'smaller', 'dark mode', 'light mode',
            'tab', 'tab bar', 'navigation bar', 'toolbar', 'beautiful', 'pretty', 'modern'
        ]
        
        self.algorithm_keywords = [
            'algorithm', 'sort', 'search', 'calculate', 'compute', 'process',
            'optimize', 'performance', 'efficiency', 'logic', 'function',
            'implement'
        ]
        
        self.data_keywords = [
            'model', 'data', 'database', 'storage', 'cache', 'persist',
            'save', 'load', 'fetch', 'api', 'network'
        ]
        
        self.bug_keywords = [
            'fix', 'bug', 'error', 'crash', 'issue', 'problem',
            'resolve', 'repair', 'broken', 'fail', 'memory leak', 'leak'
        ]
    
    def analyze_request(self, description: str, modification_history: List[Dict] = None) -> RequestType:
        """Analyze request to determine its type"""
        desc_lower = description.lower()
        
        # Debug logging
        logger.info(f"Analyzing request: {description}")
        logger.info(f"Modification history present: {modification_history is not None}")
        
        # Check if this is app creation (not modification)
        # IMPORTANT: Don't match "build" in error messages like "Fix these build errors"
        creation_keywords = ['create', 'make', 'develop', 'design a', 'design an']
        # Special handling for "build" - only match if it's about building an app, not build errors
        is_creation = any(keyword in desc_lower for keyword in creation_keywords)
        if not is_creation and 'build' in desc_lower:
            # Only consider it creation if "build" is used in context of creating an app
            # Not when it's about build errors or build process
            is_creation = not any(error_word in desc_lower for error_word in ['error', 'fix', 'fail', 'timeout'])
        logger.info(f"Is creation request: {is_creation}")
        
        # ROBUST SOLUTION: If it's a creation request without a modification history,
        # it's app creation regardless of specific keywords. Let the complexity analyzer
        # determine if it's simple or complex based on the full description.
        #
        # Examples:
        # - "Create a calculator" -> App creation (simple or complex determined later)
        # - "Create a NASA-level scientific calculator with matrix operations" -> App creation (complex)
        # - "Build a photo editor with AI filters" -> App creation (complex)
        # - "Make something that tracks stocks" -> App creation
        #
        # The key insight: Creation intent + no existing project = app generation
        is_app_creation = is_creation and not modification_history
        logger.info(f"Is app creation: {is_app_creation} (creation request without existing project)")
        
        if is_app_creation and not modification_history:
            logger.info("Returning ARCHITECTURE for app creation")
            return RequestType.ARCHITECTURE
        
        # Count keyword matches - use word boundaries to avoid partial matches
        ui_score = sum(1 for keyword in self.ui_keywords if re.search(r'\b' + re.escape(keyword) + r'\b', desc_lower))
        algo_score = sum(1 for keyword in self.algorithm_keywords if re.search(r'\b' + re.escape(keyword) + r'\b', desc_lower))
        data_score = sum(1 for keyword in self.data_keywords if re.search(r'\b' + re.escape(keyword) + r'\b', desc_lower))
        
        # Check for specific patterns - but only for modifications, not creation
        if not is_creation:
            # Use keyword list for more accurate bug detection
            bug_score = sum(1 for keyword in self.bug_keywords if re.search(r'\b' + re.escape(keyword) + r'\b', desc_lower))
            if bug_score > 0:
                return RequestType.BUG_FIX
            
            # Check for navigation patterns only for modifications
            if re.search(r'(navigate|navigation|screen|page|route|tab bar|tabs)', desc_lower):
                logger.info("Returning NAVIGATION based on pattern match")
                return RequestType.NAVIGATION
        
        # Special case: "add search" is usually a feature, not algorithm
        if 'add search' in desc_lower and 'algorithm' not in desc_lower:
            return RequestType.SIMPLE_MODIFICATION
        
        # Determine primary type based on scores
        if ui_score > algo_score and ui_score > data_score:
            return RequestType.UI_DESIGN
        elif algo_score > ui_score and algo_score > data_score:
            return RequestType.ALGORITHM
        elif data_score > 0:
            return RequestType.DATA_MODEL
        
        # Check modification complexity
        if modification_history and len(modification_history) > 2:
            logger.info("Returning COMPLEX_MODIFICATION")
            return RequestType.COMPLEX_MODIFICATION
        
        logger.info(f"Returning SIMPLE_MODIFICATION (ui_score={ui_score}, algo_score={algo_score}, data_score={data_score})")
        return RequestType.SIMPLE_MODIFICATION
    
    def route_initial_request(self, description: str, app_type: str = None, available_providers: List[str] = None) -> str:
        """Route initial request to most appropriate LLM"""
        request_type = self.analyze_request(description)
        
        logger.info(f"Request analyzed as: {request_type.value}")
        
        # INTELLIGENT ROUTING: Use success rates to determine best LLM
        # This allows the system to learn and adapt based on actual performance
        request_type_key = request_type.value
        
        # Get current success rates for this request type
        claude_rate = self.success_rates["anthropic"].get(request_type_key, self.success_rates["anthropic"]["default"])
        gpt4_rate = self.success_rates["openai"].get(request_type_key, self.success_rates["openai"]["default"])
        xai_rate = self.success_rates["xai"].get(request_type_key, self.success_rates["xai"]["default"])
        
        # Select LLM with highest success rate for this type
        llm_scores = {
            "claude": claude_rate,
            "gpt4": gpt4_rate,
            "xai": xai_rate
        }
        
        # For UI tasks, temporarily boost Claude's score if xAI has been failing
        if request_type in [RequestType.UI_DESIGN, RequestType.NAVIGATION, RequestType.SIMPLE_MODIFICATION]:
            if xai_rate < 0.7:  # If xAI is performing poorly
                llm_scores["claude"] *= 1.2  # Boost Claude's score
        
        # For architecture tasks, prefer Claude
        if request_type == RequestType.ARCHITECTURE:
            llm_scores["claude"] *= 1.3  # Claude is best at architecture
        
        # Select the best LLM based on scores
        selected_llm = max(llm_scores.keys(), key=lambda k: llm_scores[k])
        
        # Log the selection reasoning
        logger.info(f"LLM Selection for {request_type_key}:")
        logger.info(f"  Claude: {claude_rate:.2f} (score: {llm_scores['claude']:.2f})")
        logger.info(f"  GPT-4: {gpt4_rate:.2f} (score: {llm_scores['gpt4']:.2f})")
        logger.info(f"  xAI: {xai_rate:.2f} (score: {llm_scores['xai']:.2f})")
        logger.info(f"  Selected: {selected_llm}")
        
        # If xAI is selected but not available, use fallback
        if selected_llm == "xai" and available_providers:
            if "xai" not in available_providers:
                # xAI not available, use Claude for UI/UX as second best
                logger.warning(f"xAI not available, falling back to Claude for {request_type.value}")
                selected_llm = "anthropic"
        
        # Map provider names correctly
        provider_map = {
            "claude": "anthropic",
            "gpt4": "openai",
            "xai": "xai"
        }
        
        selected_provider = provider_map.get(selected_llm, selected_llm)
        
        logger.info(f"Routing to: {selected_provider}")
        return selected_provider
    
    def get_fallback_strategy(self, 
                            failed_llm: str, 
                            request_type: RequestType,
                            failure_count: int) -> Tuple[str, str]:
        """Get fallback LLM and strategy after failure"""
        
        # Define fallback chains for different request types (using provider names)
        fallback_chains = {
            RequestType.UI_DESIGN: [
                ("anthropic", "standard approach"),  # Since xAI not implemented
                ("openai", "component-based approach"),
                ("anthropic", "step-by-step with examples")
            ],
            RequestType.ALGORITHM: [
                ("openai", "standard implementation"),
                ("anthropic", "explain then implement"),
                ("openai", "alternative algorithm")
            ],
            RequestType.SIMPLE_MODIFICATION: [
                ("anthropic", "direct modification"),  # Since xAI not implemented
                ("openai", "systematic changes"),
                ("anthropic", "contextual modification")
            ]
        }
        
        # Get the appropriate chain
        chain = fallback_chains.get(
            request_type, 
            [("claude", "standard"), ("gpt4", "alternative"), ("xai", "simple")]
        )
        
        # Find next in chain
        for i, (llm, strategy) in enumerate(chain):
            if llm == failed_llm and i == failure_count - 1:
                if i + 1 < len(chain):
                    next_llm, next_strategy = chain[i + 1]
                    logger.info(f"Fallback: {failed_llm} -> {next_llm} ({next_strategy})")
                    return next_llm, next_strategy
        
        # Default fallback - use provider names
        if failed_llm == "anthropic":
            return "openai", "alternative approach"
        elif failed_llm == "openai":
            return "anthropic", "comprehensive approach"
        else:
            return "anthropic", "comprehensive rewrite"
    
    def create_specialized_prompt(self, 
                                llm: str, 
                                strategy: str,
                                original_request: str,
                                previous_failures: List[str] = None) -> str:
        """Create specialized prompt based on LLM and strategy"""
        
        base_prompt = f"User request: {original_request}\n\n"
        
        if previous_failures:
            base_prompt += "Previous attempts failed with:\n"
            for failure in previous_failures[-2:]:  # Last 2 failures
                base_prompt += f"- {failure}\n"
            base_prompt += "\n"
        
        # LLM-specific prompt adjustments
        if llm == "claude" and strategy == "step-by-step with examples":
            base_prompt += """Please implement this step-by-step:
1. First, identify all files that need modification
2. For each file, explain what changes are needed
3. Implement the changes with clear comments
4. Provide usage examples in comments

IMPORTANT: For UI modifications, especially colors:
- Use .listRowBackground() for List items, not .background()
- Define colors clearly (e.g., Color.blue, Color("CustomColor"))
- Test with both light and dark modes in mind
"""
        
        elif llm == "gpt4" and strategy == "component-based approach":
            base_prompt += """Break this down into components:
1. Identify each component that needs modification
2. Implement changes component by component
3. Ensure proper data flow between components
4. Add appropriate comments explaining the implementation
"""
        
        elif llm == "xai" and strategy == "simplified implementation":
            base_prompt += """Implement this in the simplest way possible:
- Focus on making it work first
- Use standard SwiftUI patterns
- Avoid complex abstractions
- Add clear comments
"""
        
        return base_prompt
    
    def record_result(self, llm: str, request_type: RequestType, success: bool):
        """Record the result for learning"""
        self.request_history.append({
            "llm": llm,
            "type": request_type.value,
            "success": success
        })
        
        # Allow dynamic learning but with dampening for repeated failures
        # This prevents one success from overriding multiple failures
        if llm == "xai" and request_type.value in ["ui_design", "navigation", "simple_modification"]:
            # Apply stronger dampening for xAI on UI tasks due to recent failures
            dampening_factor = 0.05 if success else 0.15  # Learn slower from success, faster from failure
        else:
            dampening_factor = 0.1  # Normal learning rate
        
        # Update success rates with appropriate dampening
        key = request_type.value if request_type.value in self.success_rates[llm] else "default"
        current_rate = self.success_rates[llm][key]
        self.success_rates[llm][key] = (current_rate * (1 - dampening_factor)) + (1.0 if success else 0.0) * dampening_factor
        
        logger.info(f"Updated {llm} success rate for {key}: {self.success_rates[llm][key]:.2f}")
    
    def get_best_llm_for_type(self, request_type: RequestType) -> str:
        """Get the best performing LLM for a request type"""
        type_key = request_type.value if request_type.value in self.success_rates.get("anthropic", {}) else "default"
        
        best_llm = max(
            self.success_rates.keys(),
            key=lambda llm: self.success_rates[llm].get(type_key, self.success_rates[llm]["default"])
        )
        
        return best_llm


def create_intelligent_modification_prompt(description: str, 
                                         files: List[Dict],
                                         llm: str,
                                         strategy: str) -> str:
    """Create an intelligent modification prompt based on LLM and strategy"""
    
    prompt = f"""You are modifying an iOS app. LLM: {llm}, Strategy: {strategy}

User Request: {description}

Current Files:
"""
    
    for file in files:
        prompt += f"\n--- {file['path']} ---\n{file['content']}\n"
    
    prompt += "\n"
    
    # Add strategy-specific instructions
    if "color" in description.lower() and llm == "claude":
        prompt += """
IMPORTANT for color modifications in SwiftUI:
1. For List items, use .listRowBackground(Color.xxx) not .background()
2. Define colors in the model or as computed properties
3. Consider using Color assets for consistency
4. Example:
   List(items) { item in
       ItemRow(item: item)
           .listRowBackground(item.backgroundColor)
   }
"""
    
    return prompt