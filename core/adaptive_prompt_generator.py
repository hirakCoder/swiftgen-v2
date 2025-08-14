"""
Adaptive Prompt Generator - Dynamic prompts based on complexity analysis
Generates minimal prompts for simple apps, comprehensive for complex ones
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
import json

from .complexity_analyzer import ComplexityScore

class AdaptivePromptGenerator:
    """Generate prompts that scale with app complexity"""
    
    def __init__(self):
        # Base prompt templates for different complexity levels
        self.base_templates = {
            'simple': self._get_simple_template(),
            'medium': self._get_medium_template(),
            'complex': self._get_complex_template()
        }
        
        # Feature-specific requirements
        self.feature_requirements = {
            'authentication': """
- Implement secure user authentication
- Include login/logout functionality
- Handle authentication state properly
- Store credentials securely (never in plain text)""",
            
            'networking': """
- Implement proper error handling for network requests
- Use async/await for all network calls
- Include appropriate loading states
- Handle offline scenarios gracefully""",
            
            'persistence': """
- Implement data persistence appropriately
- Use UserDefaults for simple settings
- Consider Core Data for complex data models
- Ensure data integrity""",
            
            'real-time': """
- Implement real-time updates efficiently
- Use appropriate update intervals
- Handle connection state changes
- Minimize battery impact""",
            
            'animations': """
- Use smooth, natural animations
- Follow Apple's animation guidelines
- Ensure animations are performant
- Provide reduced motion alternatives"""
        }
    
    def generate(self, 
                 description: str,
                 app_name: str,
                 complexity: ComplexityScore,
                 for_modification: bool = False) -> str:
        """
        Generate adaptive prompt based on complexity
        
        Args:
            description: User's app description
            app_name: Name of the app
            complexity: Complexity analysis result
            for_modification: Whether this is for modifying existing app
        """
        if for_modification:
            return self._generate_modification_prompt(description, app_name, complexity)
        
        # Choose base template based on complexity
        if complexity.total < 30:
            prompt = self._generate_simple_prompt(description, app_name, complexity)
        elif complexity.total < 60:
            prompt = self._generate_medium_prompt(description, app_name, complexity)
        else:
            prompt = self._generate_complex_prompt(description, app_name, complexity)
        
        return prompt
    
    def _generate_simple_prompt(self, description: str, app_name: str, complexity: ComplexityScore) -> str:
        """Generate minimal prompt for simple apps"""
        safe_name = self._sanitize_name(app_name)
        
        prompt = f"""Create a Swift/SwiftUI iOS app based on this description:

{description}

App Name: {app_name}
Product Name: {safe_name}

REQUIREMENTS:
- Target iOS 16.0
- Use SwiftUI only
- Keep it simple and functional
- Focus on core functionality
- Use semantic colors for automatic dark mode support

CRITICAL: Return ONLY valid Swift code. No explanations, no comments about the code.

Create these files:

1. Sources/App.swift - Main app file with @main
2. Sources/ContentView.swift - Main view
"""
        
        # Add minimal feature requirements if detected
        if complexity.detected_features:
            prompt += "\nCore Features to Include:\n"
            for feature in complexity.detected_features[:3]:  # Limit features for simple apps
                prompt += f"- {feature}\n"
        
        prompt += """
OUTPUT FORMAT:
```swift
// App.swift
[Complete Swift code for App.swift]
```

```swift
// ContentView.swift
[Complete Swift code for ContentView.swift]
```

Remember: Keep it simple, make it work, no unnecessary complexity."""
        
        return prompt
    
    def _generate_medium_prompt(self, description: str, app_name: str, complexity: ComplexityScore) -> str:
        """Generate balanced prompt for medium complexity apps"""
        safe_name = self._sanitize_name(app_name)
        
        prompt = f"""Create a professional Swift/SwiftUI iOS app:

{description}

App Name: {app_name}
Product Name: {safe_name}

TECHNICAL REQUIREMENTS:
- Target iOS 16.0 or later
- Use SwiftUI with proper state management
- Implement MVVM architecture for better organization
- Include proper error handling
- Support dark mode with semantic colors
- Use async/await for any asynchronous operations

FEATURES TO IMPLEMENT:
"""
        
        # Add detected features
        for feature in complexity.detected_features:
            prompt += f"- {feature}\n"
        
        # Add specific requirements based on complexity analysis
        if complexity.has_authentication:
            prompt += self.feature_requirements['authentication']
        
        if complexity.has_networking:
            prompt += self.feature_requirements['networking']
        
        if complexity.has_persistence:
            prompt += self.feature_requirements['persistence']
        
        prompt += """

FILE STRUCTURE:
Create organized, maintainable code with these files:

1. Sources/App.swift - Main app entry point
2. Sources/Views/ContentView.swift - Main view
3. Sources/Models/[ModelName].swift - Data models as needed
4. Sources/ViewModels/[ViewModelName].swift - View models for business logic
5. Additional views and components as needed

SWIFT CODE REQUIREMENTS:
- All code must be syntactically correct
- Use proper Swift naming conventions
- Include all necessary imports
- Ensure all types are defined
- No placeholder code or TODO comments

OUTPUT FORMAT:
```swift
// App.swift
[Complete code]
```

```swift
// Views/ContentView.swift
[Complete code]
```

[Additional files as needed]

Focus on clean, working code that follows iOS best practices."""
        
        return prompt
    
    def _generate_complex_prompt(self, description: str, app_name: str, complexity: ComplexityScore) -> str:
        """Generate comprehensive prompt for complex apps"""
        safe_name = self._sanitize_name(app_name)
        
        prompt = f"""Create a production-ready, professional Swift/SwiftUI iOS application:

PROJECT DESCRIPTION:
{description}

App Name: {app_name}
Product Name: {safe_name}
Complexity Level: High ({complexity.total}/100)

ARCHITECTURE REQUIREMENTS:
- Target iOS 16.0 or later
- Implement clean MVVM architecture
- Use dependency injection where appropriate
- Separate concerns properly (UI, Business Logic, Data)
- Implement proper error handling and recovery
- Include comprehensive state management
- Support landscape and portrait orientations where appropriate

DETECTED FEATURES TO IMPLEMENT:
"""
        
        # List all detected features with priority
        for i, feature in enumerate(complexity.detected_features, 1):
            prompt += f"{i}. {feature}\n"
        
        # Add all relevant feature requirements
        if complexity.has_authentication:
            prompt += "\nAUTHENTICATION REQUIREMENTS:"
            prompt += self.feature_requirements['authentication']
        
        if complexity.has_networking:
            prompt += "\nNETWORKING REQUIREMENTS:"
            prompt += self.feature_requirements['networking']
        
        if complexity.has_persistence:
            prompt += "\nDATA PERSISTENCE:"
            prompt += self.feature_requirements['persistence']
        
        if complexity.has_real_time:
            prompt += "\nREAL-TIME FEATURES:"
            prompt += self.feature_requirements['real-time']
        
        if complexity.has_animations:
            prompt += "\nANIMATION REQUIREMENTS:"
            prompt += self.feature_requirements['animations']
        
        # Add technical requirements if detected
        if complexity.technical_requirements:
            prompt += "\n\nTECHNICAL COMPONENTS DETECTED:\n"
            for req in complexity.technical_requirements:
                prompt += f"- {req}\n"
        
        prompt += """

PROJECT STRUCTURE:
Organize the code professionally with clear separation:

Core Files:
- Sources/App.swift - App entry point with proper configuration
- Sources/Views/ContentView.swift - Main navigation structure

Architecture:
- Sources/Models/ - All data models and entities
- Sources/ViewModels/ - Business logic and state management
- Sources/Views/ - All SwiftUI views organized by feature
- Sources/Services/ - API, Database, and other services
- Sources/Utilities/ - Helper functions and extensions
- Sources/Resources/ - Assets and configuration files

QUALITY REQUIREMENTS:
1. Production-ready code with no placeholders
2. Comprehensive error handling
3. Proper memory management
4. Accessibility support (VoiceOver labels)
5. Performance optimizations
6. Proper documentation for complex logic

UI/UX REQUIREMENTS:
- Follow Apple Human Interface Guidelines
- Implement smooth transitions and animations
- Provide loading states for async operations
- Show appropriate error messages to users
- Support Dynamic Type for accessibility
- Include haptic feedback where appropriate

CODE STANDARDS:
- Use Swift 5.5+ features (async/await, actors where needed)
- Follow Swift API Design Guidelines
- Implement proper access control (private, public, etc.)
- Use computed properties where appropriate
- Leverage SwiftUI property wrappers correctly
- Write self-documenting code with clear naming

OUTPUT FORMAT:
Generate complete, production-ready code for each file:

```swift
// App.swift
import SwiftUI

@main
struct {safe_name}App: App {{
    [Complete implementation]
}}
```

```swift
// Views/ContentView.swift
import SwiftUI

struct ContentView: View {{
    [Complete implementation]
}}
```

[Continue with all necessary files...]

CRITICAL: 
- Every file must be complete and functional
- No stub implementations or placeholders
- All features must be fully implemented
- Code must compile without errors
- Follow iOS 16 compatibility strictly"""
        
        return prompt
    
    def _generate_modification_prompt(self, modification: str, app_name: str, complexity: ComplexityScore) -> str:
        """Generate prompt for modifying existing app"""
        
        # Adaptive modification prompt based on complexity
        if complexity.total < 30:
            context_needed = "minimal"
            instruction_detail = "simple"
        elif complexity.total < 60:
            context_needed = "moderate"
            instruction_detail = "detailed"
        else:
            context_needed = "comprehensive"
            instruction_detail = "exhaustive"
        
        prompt = f"""Modify the existing {app_name} iOS app according to this request:

{modification}

MODIFICATION REQUIREMENTS:
- Maintain existing app structure and style
- Preserve all existing functionality
- Ensure changes integrate seamlessly
- Follow the same coding patterns used in the app
- Keep iOS 16.0 compatibility

APPROACH:
1. Analyze what needs to be changed
2. Identify affected files
3. Make minimal necessary changes
4. Ensure no breaking changes
5. Test integration points

"""
        
        if complexity.detected_features:
            prompt += "FEATURES TO ADD/MODIFY:\n"
            for feature in complexity.detected_features:
                prompt += f"- {feature}\n"
        
        prompt += """
OUTPUT REQUIREMENTS:
- Return complete modified files
- Include ONLY files that need changes
- Preserve exact formatting and style
- No placeholder code
- All changes must be functional

OUTPUT FORMAT:
For each modified file:

```swift
// [Filename]
[Complete updated code for the file]
```

Remember: Modify only what's necessary, preserve everything else."""
        
        return prompt
    
    def get_stage_prompt(self, stage: str, context: Dict, complexity: ComplexityScore) -> str:
        """Generate prompts for staged generation"""
        
        if stage == "core":
            return self._get_core_stage_prompt(context, complexity)
        elif stage == "features":
            return self._get_features_stage_prompt(context, complexity)
        elif stage == "polish":
            return self._get_polish_stage_prompt(context, complexity)
        else:
            return ""
    
    def _get_core_stage_prompt(self, context: Dict, complexity: ComplexityScore) -> str:
        """Generate prompt for core structure generation"""
        return f"""Create the core structure for a {context['app_name']} iOS app.

Focus on:
1. Basic app setup with @main
2. Main navigation structure
3. Core data models
4. Basic views without full functionality

Target iOS 16.0. Keep it minimal but extensible.

Create:
- App.swift
- ContentView.swift
- Basic model files

Return complete, valid Swift code."""
    
    def _get_features_stage_prompt(self, context: Dict, complexity: ComplexityScore) -> str:
        """Generate prompt for adding features"""
        feature = context.get('current_feature', 'unknown')
        existing_code = context.get('existing_code', '')
        
        return f"""Add the {feature} feature to the existing code.

Current code structure:
{existing_code[:1000]}...

Integrate {feature} by:
1. Adding necessary models
2. Updating views
3. Adding required functionality
4. Ensuring proper state management

Return only the files that need modification or addition."""
    
    def _get_polish_stage_prompt(self, context: Dict, complexity: ComplexityScore) -> str:
        """Generate prompt for polishing and optimization"""
        return """Review and polish the app:

1. Add proper error handling
2. Optimize performance
3. Ensure accessibility
4. Add loading states
5. Improve UI/UX

Return improved versions of files that need enhancement."""
    
    def _sanitize_name(self, name: str) -> str:
        """Sanitize app name for use as identifier"""
        # Remove special characters and spaces
        safe = ''.join(c for c in name if c.isalnum() or c == '_')
        # Ensure it starts with a letter
        if safe and not safe[0].isalpha():
            safe = 'App' + safe
        return safe or 'MyApp'
    
    def _get_simple_template(self) -> str:
        """Base template for simple apps"""
        return """Create a simple, functional iOS app.
Focus on core functionality only.
No unnecessary complexity."""
    
    def _get_medium_template(self) -> str:
        """Base template for medium apps"""
        return """Create a well-structured iOS app.
Implement proper architecture.
Include error handling and state management."""
    
    def _get_complex_template(self) -> str:
        """Base template for complex apps"""
        return """Create a production-ready iOS app.
Implement comprehensive architecture.
Include all professional features and optimizations."""

