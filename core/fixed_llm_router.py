"""
SwiftGen V2 - Fixed LLM Routing System
Ensures correct LLM is selected based on task type
"""

import logging
from typing import Optional, Dict, Any
from enum import Enum

logger = logging.getLogger(__name__)

class TaskType(Enum):
    UI_DESIGN = "ui_design"
    BUSINESS_LOGIC = "business_logic"
    ARCHITECTURE = "architecture"
    SIMPLE = "simple"
    HYBRID = "hybrid"

class FixedLLMRouter:
    """Production routing that actually works"""
    
    def __init__(self):
        self.routing_rules = {
            TaskType.UI_DESIGN: "grok",
            TaskType.BUSINESS_LOGIC: "gpt4",
            TaskType.ARCHITECTURE: "claude",
            TaskType.SIMPLE: "grok",  # Grok is fastest for simple apps
            TaskType.HYBRID: "hybrid"
        }
        
        # Keywords for task detection
        self.ui_keywords = [
            "beautiful", "design", "ui", "interface", "animation",
            "gradient", "color", "theme", "layout", "responsive"
        ]
        
        self.logic_keywords = [
            "algorithm", "calculate", "compute", "process", "analyze",
            "sort", "search", "optimize", "data structure", "performance"
        ]
        
        self.architecture_keywords = [
            "mvvm", "architecture", "pattern", "scalable", "modular",
            "dependency", "injection", "coordinator", "navigation"
        ]
    
    def analyze_task_type(self, description: str) -> TaskType:
        """Determine task type from description"""
        desc_lower = description.lower()
        
        # Count keyword matches
        ui_score = sum(1 for kw in self.ui_keywords if kw in desc_lower)
        logic_score = sum(1 for kw in self.logic_keywords if kw in desc_lower)
        arch_score = sum(1 for kw in self.architecture_keywords if kw in desc_lower)
        
        # Determine primary task type
        if arch_score > 0 and (ui_score > 0 or logic_score > 0):
            return TaskType.HYBRID
        elif arch_score > logic_score and arch_score > ui_score:
            return TaskType.ARCHITECTURE
        elif logic_score > ui_score:
            return TaskType.BUSINESS_LOGIC
        elif ui_score > 0:
            return TaskType.UI_DESIGN
        else:
            # Default to simple for basic apps
            return TaskType.SIMPLE
    
    def select_provider(self, 
                       description: str, 
                       user_preference: Optional[str] = None) -> str:
        """Select the best provider for the task"""
        
        # Honor user preference if specified
        if user_preference:
            if user_preference.lower() in ["claude", "gpt4", "grok", "hybrid"]:
                logger.info(f"Using user-specified provider: {user_preference}")
                return user_preference.lower()
        
        # Analyze task and route appropriately
        task_type = self.analyze_task_type(description)
        provider = self.routing_rules[task_type]
        
        logger.info(f"Task type: {task_type.value} → Provider: {provider}")
        return provider
    
    def get_specialized_prompt(self, 
                              provider: str, 
                              description: str, 
                              app_name: str) -> Dict[str, str]:
        """Get provider-specific optimized prompts"""
        
        base_requirements = """
CRITICAL SWIFT SYNTAX REQUIREMENTS:
1. EVERY opening delimiter MUST have a closing delimiter
2. NEVER leave parentheses, brackets, or braces unclosed
3. Complete ALL ternary operators with both ? and :
4. Ensure ALL method calls have proper parentheses
5. DO NOT put closing delimiters on separate lines alone
"""
        
        if provider == "grok":
            return {
                "system": f"""You are Grok, specialized in creating beautiful SwiftUI interfaces.
{base_requirements}

Focus on:
- Stunning visual design with gradients and animations
- Smooth user interactions and transitions
- Modern iOS 16+ design patterns
- Clean, intuitive layouts""",
                "user": f"Create a visually stunning {app_name} app: {description}"
            }
        
        elif provider == "gpt4":
            return {
                "system": f"""You are GPT-4, specialized in algorithms and business logic.
{base_requirements}

Focus on:
- Efficient algorithms and data structures
- Clean separation of concerns
- Robust error handling
- Performance optimization""",
                "user": f"Create {app_name} with optimized logic: {description}"
            }
        
        elif provider == "claude":
            return {
                "system": f"""You are Claude, specialized in software architecture.
{base_requirements}

Focus on:
- MVVM architecture with clear separation
- Dependency injection where appropriate
- Scalable and maintainable code structure
- Comprehensive error handling""",
                "user": f"Create {app_name} with solid architecture: {description}"
            }
        
        else:  # hybrid or fallback
            return {
                "system": f"""You are an expert iOS developer.
{base_requirements}

Create a complete, working iOS app with proper architecture and beautiful UI.""",
                "user": f"Create {app_name}: {description}"
            }
