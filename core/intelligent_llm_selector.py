"""
Intelligent LLM Selector - Routes to best LLM based on task characteristics
Properly utilizes all 3 LLMs according to their strengths
"""

from typing import Dict, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
import re

class LLMProvider(Enum):
    CLAUDE = "claude"   # Best for: Architecture, complex logic, SwiftUI structure
    GPT4 = "gpt4"       # Best for: Algorithms, data structures, business logic
    GROK = "grok"       # Best for: UI/UX, animations, visual design, simple apps
    HYBRID = "hybrid"   # Use all 3 based on task components

@dataclass
class TaskAnalysis:
    """Detailed analysis of what the task requires"""
    has_complex_architecture: bool = False
    has_ui_focus: bool = False
    has_animations: bool = False
    has_algorithms: bool = False
    has_data_structures: bool = False
    has_networking: bool = False
    has_authentication: bool = False
    has_visual_design: bool = False
    has_simple_ui: bool = False
    complexity_score: int = 0
    
    @property
    def primary_focus(self) -> str:
        """Determine primary focus of the task"""
        if self.has_ui_focus or self.has_animations or self.has_visual_design:
            return "ui_ux"
        elif self.has_algorithms or self.has_data_structures:
            return "logic"
        elif self.has_complex_architecture or self.has_authentication:
            return "architecture"
        elif self.has_simple_ui:
            return "simple"
        else:
            return "general"

class IntelligentLLMSelector:
    """Selects the best LLM or combination based on task analysis"""
    
    def __init__(self):
        # Define LLM strengths
        self.llm_strengths = {
            LLMProvider.CLAUDE: {
                'strengths': ['architecture', 'complex_logic', 'swiftui_structure', 'state_management', 'mvvm'],
                'complexity_range': (30, 100),  # Good for medium to complex
                'best_for': ['full_app_generation', 'architectural_decisions', 'complex_features']
            },
            LLMProvider.GPT4: {
                'strengths': ['algorithms', 'data_structures', 'business_logic', 'api_integration', 'optimization'],
                'complexity_range': (20, 80),   # Good for simple to medium-complex
                'best_for': ['logic_implementation', 'data_processing', 'algorithmic_solutions']
            },
            LLMProvider.GROK: {
                'strengths': ['ui_design', 'animations', 'user_experience', 'visual_polish', 'simple_apps'],
                'complexity_range': (0, 40),    # Best for simple to medium UI
                'best_for': ['ui_components', 'visual_effects', 'user_interactions', 'simple_utilities']
            }
        }
        
        # Task patterns for detection
        self.task_patterns = {
            'ui_focus': [
                r'\b(ui|interface|design|layout|screen|view|button|animation|gesture|transition)\b',
                r'\b(beautiful|elegant|smooth|polished|modern|clean)\b',
                r'\b(user experience|ux|interaction|visual)\b'
            ],
            'animations': [
                r'\b(animat\w+|transition|bounce|fade|slide|spring|gesture|drag|swipe)\b',
                r'\b(smooth|fluid|dynamic|interactive)\b'
            ],
            'algorithms': [
                r'\b(algorithm|sort|search|filter|calculate|compute|optimize|process)\b',
                r'\b(data structure|array|list|tree|graph|queue|stack)\b'
            ],
            'architecture': [
                r'\b(architect\w+|mvvm|mvc|coordinator|dependency injection|modular)\b',
                r'\b(scalable|maintainable|production|enterprise|professional)\b'
            ],
            'networking': [
                r'\b(api|rest|graphql|network|http|websocket|sync|async|fetch)\b',
                r'\b(backend|server|cloud|remote|endpoint)\b'
            ],
            'authentication': [
                r'\b(auth\w+|login|logout|sign\s?in|sign\s?up|oauth|biometric|security)\b',
                r'\b(user\s+management|session|token|credential)\b'
            ]
        }
    
    def analyze_task(self, description: str, complexity_score: int) -> TaskAnalysis:
        """Analyze task requirements from description"""
        description_lower = description.lower()
        
        analysis = TaskAnalysis(complexity_score=complexity_score)
        
        # Check for UI/UX focus
        ui_matches = sum(1 for pattern in self.task_patterns['ui_focus'] 
                        if re.search(pattern, description_lower))
        analysis.has_ui_focus = ui_matches >= 2
        
        # Check for animations
        animation_matches = sum(1 for pattern in self.task_patterns['animations']
                              if re.search(pattern, description_lower))
        analysis.has_animations = animation_matches >= 1
        
        # Check for algorithms
        algo_matches = sum(1 for pattern in self.task_patterns['algorithms']
                         if re.search(pattern, description_lower))
        analysis.has_algorithms = algo_matches >= 1
        
        # Check for architecture
        arch_matches = sum(1 for pattern in self.task_patterns['architecture']
                         if re.search(pattern, description_lower))
        analysis.has_complex_architecture = arch_matches >= 1 or complexity_score > 60
        
        # Check for networking
        network_matches = sum(1 for pattern in self.task_patterns['networking']
                            if re.search(pattern, description_lower))
        analysis.has_networking = network_matches >= 1
        
        # Check for authentication
        auth_matches = sum(1 for pattern in self.task_patterns['authentication']
                         if re.search(pattern, description_lower))
        analysis.has_authentication = auth_matches >= 1
        
        # Determine if it's visual design focused
        visual_keywords = ['beautiful', 'elegant', 'polished', 'modern', 'design', 'visual']
        analysis.has_visual_design = any(keyword in description_lower for keyword in visual_keywords)
        
        # Check if it's a simple UI app
        simple_keywords = ['simple', 'basic', 'minimal', 'straightforward']
        analysis.has_simple_ui = any(keyword in description_lower for keyword in simple_keywords) and complexity_score < 30
        
        return analysis
    
    def select_provider(
        self, 
        description: str,
        complexity_score: int,
        user_preference: Optional[str] = None
    ) -> Tuple[LLMProvider, str]:
        """
        Select the best LLM provider based on task analysis
        
        Returns:
            Tuple of (provider, reason)
        """
        # If user specified a provider, use it
        if user_preference:
            if user_preference.lower() == 'claude':
                return LLMProvider.CLAUDE, "User requested Claude"
            elif user_preference.lower() in ['gpt4', 'gpt-4', 'openai']:
                return LLMProvider.GPT4, "User requested GPT-4"
            elif user_preference.lower() in ['grok', 'xai']:
                return LLMProvider.GROK, "User requested Grok"
            elif user_preference.lower() == 'hybrid':
                return LLMProvider.HYBRID, "User requested hybrid mode"
        
        # Analyze the task
        analysis = self.analyze_task(description, complexity_score)
        
        # Decision logic based on task characteristics
        
        # GROK: UI/UX focused or simple apps
        if analysis.has_simple_ui or (analysis.has_ui_focus and complexity_score < 40):
            return LLMProvider.GROK, f"UI/UX focused task (score: {complexity_score})"
        
        if analysis.has_animations and analysis.has_visual_design:
            return LLMProvider.GROK, "Animation and visual design task"
        
        # GPT-4: Algorithm/logic focused or medium complexity
        if analysis.has_algorithms or analysis.has_data_structures:
            return LLMProvider.GPT4, "Algorithm/data structure implementation"
        
        if analysis.has_networking and not analysis.has_complex_architecture:
            return LLMProvider.GPT4, "API integration and networking"
        
        if 30 <= complexity_score <= 60 and not analysis.has_ui_focus:
            return LLMProvider.GPT4, f"Medium complexity logic task (score: {complexity_score})"
        
        # CLAUDE: Complex architecture or high complexity
        if analysis.has_complex_architecture:
            return LLMProvider.CLAUDE, "Complex architectural requirements"
        
        if analysis.has_authentication and complexity_score > 40:
            return LLMProvider.CLAUDE, "Authentication with complex requirements"
        
        if complexity_score > 70:  # Raised threshold so GPT-4 gets more medium tasks
            return LLMProvider.CLAUDE, f"High complexity task (score: {complexity_score})"
        
        # Default based on complexity alone
        if complexity_score < 30:
            return LLMProvider.GROK, f"Simple task (score: {complexity_score})"
        elif complexity_score < 60:
            return LLMProvider.GPT4, f"Medium complexity (score: {complexity_score})"
        else:
            return LLMProvider.CLAUDE, f"Complex task (score: {complexity_score})"
    
    def get_hybrid_strategy(
        self,
        description: str,
        complexity_score: int
    ) -> Dict[str, LLMProvider]:
        """
        Determine how to use all 3 LLMs in hybrid mode
        
        Returns dict mapping task components to LLMs
        """
        analysis = self.analyze_task(description, complexity_score)
        
        strategy = {}
        
        # Always use Claude for overall architecture
        strategy['architecture'] = LLMProvider.CLAUDE
        strategy['app_structure'] = LLMProvider.CLAUDE
        
        # Use Grok for UI/UX components
        if analysis.has_ui_focus or analysis.has_animations or analysis.has_visual_design:
            strategy['ui_design'] = LLMProvider.GROK
            strategy['animations'] = LLMProvider.GROK
            strategy['user_experience'] = LLMProvider.GROK
        
        # Use GPT-4 for business logic
        if analysis.has_algorithms or analysis.has_data_structures or analysis.has_networking:
            strategy['business_logic'] = LLMProvider.GPT4
            strategy['data_processing'] = LLMProvider.GPT4
            strategy['api_integration'] = LLMProvider.GPT4
        
        # Special cases
        if analysis.has_authentication:
            strategy['authentication'] = LLMProvider.CLAUDE  # Security-critical
        
        if complexity_score < 30:
            # For simple apps, just use Grok
            strategy = {'full_app': LLMProvider.GROK}
        
        return strategy
    
    def get_provider_prompt_style(self, provider: LLMProvider) -> Dict[str, any]:
        """Get prompt style optimized for each provider"""
        styles = {
            LLMProvider.CLAUDE: {
                'temperature': 0.7,
                'max_tokens': 8192,
                'style': 'detailed',
                'focus': 'architecture and correctness',
                'instruction_style': 'comprehensive'
            },
            LLMProvider.GPT4: {
                'temperature': 0.6,
                'max_tokens': 4096,
                'style': 'balanced',
                'focus': 'logic and algorithms',
                'instruction_style': 'structured'
            },
            LLMProvider.GROK: {
                'temperature': 0.8,
                'max_tokens': 8192,
                'style': 'creative',
                'focus': 'UI/UX and visual polish',
                'instruction_style': 'concise'
            }
        }
        return styles.get(provider, styles[LLMProvider.GPT4])


