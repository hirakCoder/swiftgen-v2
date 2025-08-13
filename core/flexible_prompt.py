"""
Flexible Prompt System - Handles ANY app type and modification with balanced quality
Ensures App Store readiness while maximizing creativity
"""

import re
import random
import uuid
from datetime import datetime
from typing import Dict, List, Optional

class FlexiblePromptBuilder:
    """
    Intelligent prompt builder that:
    - Adapts to ANY app type request
    - Maintains quality without rigid templates
    - Supports creative interpretations
    - Handles modifications intelligently
    """
    
    @staticmethod
    def build_generation_prompt(requirements: dict, raw_description: str = None) -> str:
        """
        Build adaptive prompt based on user's actual request
        No rigid categories - interprets intent intelligently
        NOW WITH VARIATION for unique outputs each time
        """
        app_name = requirements.get('app_name', 'App')
        app_type = requirements.get('app_type', '')
        features = requirements.get('must_have_features', [])
        
        # Use raw description if available for better context
        if raw_description:
            context = f"User wants: {raw_description}"
        else:
            context = f"Create a {app_type} app" if app_type else "Create an innovative app"
            if features:
                context += f" with {', '.join(features)}"
        
        # Add unique variation to each generation
        unique_seed = str(uuid.uuid4())[:8]
        timestamp = datetime.now().isoformat()
        
        # Random creative suggestions to ensure uniqueness
        creative_suggestions = FlexiblePromptBuilder._get_random_creative_suggestions()
        
        # Core requirements that ensure App Store approval
        core_requirements = """
APP STORE ESSENTIALS (Required):
• iOS 16.0+ deployment target
• Crash-free, memory-safe code
• Works on all iPhone sizes
• Basic accessibility support
• Privacy-compliant implementation
"""

        # Flexible guidelines that encourage quality
        quality_guidelines = """
QUALITY GUIDELINES (Flexible):
• Follow Apple HIG in your own creative way
• Make it intuitive and delightful
• Add polish that makes it feel premium
• Use animations and feedback where it improves UX
• Support dark mode if it makes sense
• Make it feel native while being unique
"""

        # Interpret context to provide helpful hints (not restrictions)
        context_hints = FlexiblePromptBuilder._get_contextual_hints(
            app_type, features, raw_description
        )
        
        prompt = f"""Create a SwiftUI iOS app: {app_name}

{context}

UNIQUE GENERATION ID: {unique_seed}
Be creative and make this implementation unique! 

{creative_suggestions}

{core_requirements}

{quality_guidelines}

{context_hints}

CREATIVE FREEDOM:
• This is YOUR interpretation - be creative and UNIQUE!
• Each generation should be different - explore various approaches
• Add features that make sense for this type of app
• Use any SwiftUI features that enhance the experience
• Make design choices that fit the app's purpose
• Innovation within Apple's ecosystem is encouraged

TECHNICAL NOTES:
• Use SwiftUI 4.0+ and iOS 16.0+
• Include ContentView.swift and {app_name}App.swift
• For haptic feedback: import UIKit and use UIImpactFeedbackGenerator
• For persistence: Use @AppStorage or UserDefaults for simple data
• For networking: Use URLSession with async/await
• Handle errors gracefully with user-friendly messages

Return JSON with your creative implementation:
{{
  "files": [
    {{"path": "Sources/ContentView.swift", "content": "..."}},
    {{"path": "Sources/{app_name}App.swift", "content": "..."}}
  ],
  "app_name": "{app_name}",
  "bundle_id": "com.swiftgen.{app_name.lower()}"
}}
"""
        return prompt
    
    @staticmethod
    def _get_random_creative_suggestions() -> str:
        """
        Generate random creative suggestions to ensure unique outputs
        """
        color_schemes = [
            "vibrant gradient backgrounds",
            "subtle pastel colors",
            "bold monochrome design",
            "dynamic color themes",
            "elegant minimalist palette",
            "playful rainbow accents",
            "sophisticated dark theme",
            "nature-inspired colors"
        ]
        
        animation_styles = [
            "smooth spring animations",
            "playful bounce effects",
            "subtle fade transitions",
            "dynamic scaling effects",
            "elegant slide animations",
            "creative rotation effects",
            "fluid morphing transitions",
            "delightful micro-interactions"
        ]
        
        layout_approaches = [
            "card-based layout",
            "full-screen immersive design",
            "compact information density",
            "spacious breathing room",
            "asymmetric creative layout",
            "grid-based organization",
            "flowing organic shapes",
            "geometric precision"
        ]
        
        special_features = [
            "surprise delighter animations",
            "hidden easter eggs",
            "contextual haptic feedback",
            "adaptive UI based on time of day",
            "playful sound effects",
            "gesture-based shortcuts",
            "pull-to-refresh with custom animation",
            "long-press context menus"
        ]
        
        # Randomly select suggestions
        suggestions = f"""
CREATIVE INSPIRATION (Make it unique!):
• Try {random.choice(color_schemes)} for visual appeal
• Consider {random.choice(animation_styles)} for interactions
• Explore {random.choice(layout_approaches)} for structure
• Add {random.choice(special_features)} for delight
• Focus on {random.choice(['accessibility', 'performance', 'visual polish', 'user delight', 'intuitive flow'])}
"""
        return suggestions
    
    @staticmethod
    def _get_contextual_hints(app_type: str, features: List[str], description: str = None) -> str:
        """
        Provide contextual hints based on request WITHOUT being prescriptive
        These are suggestions, not requirements
        """
        hints = []
        
        # Analyze the full context
        full_context = f"{app_type} {' '.join(features)} {description or ''}".lower()
        
        # Provide helpful hints based on common patterns
        # These are SUGGESTIONS only, not requirements
        
        if any(word in full_context for word in ['game', 'play', 'puzzle', 'fun']):
            hints.append("• Consider: Engaging animations, sound effects, game state")
        
        if any(word in full_context for word in ['social', 'chat', 'message', 'share']):
            hints.append("• Consider: User profiles, real-time updates, sharing features")
        
        if any(word in full_context for word in ['health', 'fitness', 'workout', 'medical']):
            hints.append("• Consider: HealthKit integration, progress tracking, charts")
        
        if any(word in full_context for word in ['photo', 'camera', 'image', 'gallery']):
            hints.append("• Consider: PhotosUI, image editing, filters, albums")
        
        if any(word in full_context for word in ['music', 'audio', 'sound', 'podcast']):
            hints.append("• Consider: AVFoundation, playback controls, playlists")
        
        if any(word in full_context for word in ['map', 'location', 'navigation', 'travel']):
            hints.append("• Consider: MapKit, location services, route planning")
        
        if any(word in full_context for word in ['shop', 'store', 'buy', 'commerce', 'payment']):
            hints.append("• Consider: Product catalogs, cart, payment flow, orders")
        
        if any(word in full_context for word in ['learn', 'education', 'study', 'quiz']):
            hints.append("• Consider: Progress tracking, quizzes, content organization")
        
        if any(word in full_context for word in ['productivity', 'task', 'todo', 'organize']):
            hints.append("• Consider: Lists, reminders, categories, sync")
        
        if any(word in full_context for word in ['finance', 'money', 'budget', 'expense']):
            hints.append("• Consider: Charts, categories, trends, data export")
        
        if any(word in full_context for word in ['news', 'article', 'blog', 'read']):
            hints.append("• Consider: Feed updates, categories, bookmarks, reading mode")
        
        if any(word in full_context for word in ['weather', 'forecast', 'temperature']):
            hints.append("• Consider: Live data, forecasts, locations, weather animations")
        
        if any(word in full_context for word in ['ar', 'augmented', '3d', 'reality']):
            hints.append("• Consider: ARKit, 3D models, spatial interactions")
        
        # Only return hints if we found relevant patterns
        if hints:
            return "CONTEXTUAL SUGGESTIONS (Optional):\n" + "\n".join(hints)
        else:
            return "INTERPRETATION:\n• Build what makes most sense for this use case\n• Add features that users would expect and appreciate"
    
    @staticmethod
    def build_modification_prompt(
        existing_code: str, 
        modification_request: str,
        app_name: str = "App"
    ) -> str:
        """
        Balanced modification prompt that maintains quality while allowing flexibility
        """
        # Analyze modification intent
        mod_hints = FlexiblePromptBuilder._analyze_modification_intent(modification_request)
        
        prompt = f"""⚠️ MODIFICATION REQUEST - DO NOT CREATE A NEW APP ⚠️

You are MODIFYING an existing iOS app. The user wants to ADD or CHANGE specific features while keeping everything else the same.

USER'S REQUEST: {modification_request}

{mod_hints}

🔴 CRITICAL MODIFICATION RULES:
1. This is an EXISTING app - preserve its identity and functionality
2. ONLY modify what the user explicitly asks for
3. When user says "add X" - they mean ADD it to existing app, not replace anything
4. When user says "add option/toggle for X" - add a CONTROL, don't force the feature
5. Keep ALL existing features working exactly as before

MODIFICATION PRINCIPLES:
• ONLY make the changes explicitly requested - nothing more, nothing less
• Preserve ALL existing UI, colors, layouts, and styling unless specifically asked to change them
• Keep the existing code structure and patterns exactly as they are
• Ensure all existing features continue to work exactly as before
• If adding a new feature, integrate it minimally without redesigning existing UI
• Follow Apple HIG for any new components

STRICT REQUIREMENTS:
• NO changes to existing UI elements unless explicitly requested
• NO color scheme changes unless explicitly requested  
• NO layout changes unless explicitly requested
• NO style changes unless explicitly requested
• NO refactoring unless explicitly requested
• NO removing existing features unless explicitly requested
• Maintain iOS 16.0+ compatibility
• Keep accessibility support
• Ensure responsive layout on all devices

CRITICAL SWIFT SYNTAX RULES TO PREVENT COMPILATION ERRORS:
• For Codable structs with UUID: Use 'var id = UUID()' NOT 'let id = UUID()'
• For date formatting: Use '.formatted(.relative(presentation: .numeric))' NOT '.formatted(.relative)'
• When passing Bindings: Use '$propertyName' NOT 'propertyName'
• Match parameter names EXACTLY: Check existing function signatures
• For iOS 16 target: NO ContentUnavailableView, NO .symbolEffect, NO @Observable
• Import required modules: UIKit for UI components, Foundation for Date/UUID/Timer
• ViewModels need @ObservedObject or @StateObject, not plain properties
• Check ALL function calls match expected parameter names and types

WHAT TO CHANGE:
• ONLY the specific feature/fix requested
• Make minimal code changes to achieve the request
• If the user asks to "enhance UI" or "improve UX", then and only then make broader changes
• Default to conservative modifications unless user explicitly asks for creativity

CURRENT CODE STRUCTURE (COMPLETE):
{existing_code}

IMPORTANT:
• Return the COMPLETE modified code for all affected files
• Maintain all imports and dependencies
• Test that your changes compile and work
• Keep the same file structure
• DO NOT create a duplicate App.swift file - only modify the existing {app_name}App.swift
• Never include both App.swift and {app_name}App.swift - use only {app_name}App.swift

Return JSON with the modified implementation:
{{
  "files": [
    {{"path": "Sources/ContentView.swift", "content": "complete modified code"}},
    {{"path": "Sources/{app_name}App.swift", "content": "complete modified code"}}
  ],
  "app_name": "{app_name}",
  "bundle_id": "com.swiftgen.{app_name.lower()}"
}}
"""
        return prompt
    
    @staticmethod
    def _analyze_modification_intent(request: str) -> str:
        """
        Analyze what type of modification is being requested
        Provide appropriate guidance without being restrictive
        """
        request_lower = request.lower()
        hints = []
        
        # ALWAYS add this critical instruction first
        hints.append("⚠️ CRITICAL: THIS IS A MODIFICATION REQUEST")
        hints.append("• You are MODIFYING an existing app, NOT creating a new one")
        hints.append("• PRESERVE all existing functionality")
        hints.append("• ONLY change what is explicitly requested")
        hints.append("")
        
        # Check for common modification patterns that indicate adding controls/options
        if any(phrase in request_lower for phrase in ['add toggle', 'add option', 'add switch', 'add button', 'add control', 'allow user to', 'let user', 'give option']):
            hints.append("USER CONTROL REQUESTED:")
            hints.append("• User wants to ADD a control/option, not force a change")
            hints.append("• Add UI element that gives user choice")
            hints.append("• Do NOT automatically apply the feature")
            hints.append("")
        
        # Common modification phrases that should NEVER create a new app
        if any(phrase in request_lower for phrase in ['change the', 'modify the', 'update the', 'improve the', 'fix the', 'adjust the', 'make it', 'can you add', 'please add']):
            hints.append("MODIFICATION KEYWORDS DETECTED:")
            hints.append("• These phrases indicate modifying EXISTING app")
            hints.append("• NOT creating something new")
            hints.append("")
        
        # UI modifications
        if any(word in request_lower for word in ['color', 'theme', 'style', 'design', 'look']):
            hints.append("UI/DESIGN CHANGE DETECTED:")
            hints.append("• Maintain visual hierarchy")
            hints.append("• Ensure contrast ratios for accessibility")
            hints.append("• Keep consistent styling throughout")
        
        # Dark mode toggle specific
        if any(phrase in request_lower for phrase in ['dark mode', 'night mode', 'theme toggle', 'appearance']):
            if 'toggle' in request_lower or 'option' in request_lower or 'switch' in request_lower or 'choose' in request_lower:
                hints.append("DARK MODE TOGGLE REQUESTED:")
                hints.append("• Add a UI control (toggle/switch) that lets users choose")
                hints.append("• Use @AppStorage to persist the preference")
                hints.append("• Apply .preferredColorScheme() based on user's choice")
                hints.append("• DO NOT force dark mode - give users control")
                hints.append("• Example: @AppStorage('darkMode') var darkMode = false")
                hints.append("• Then use: .preferredColorScheme(darkMode ? .dark : .light)")
        
        # Feature additions - be very careful here
        elif any(word in request_lower for word in ['add', 'new', 'feature', 'include']):
            # Check if UI/UX enhancement is also requested
            if any(word in request_lower for word in ['enhance', 'improve', 'redesign', 'modern', 'better ui', 'better ux']):
                hints.append("FEATURE ADDITION WITH UI ENHANCEMENT DETECTED:")
                hints.append("• Feel free to improve the overall design")
                hints.append("• Enhance user experience while adding the feature")
                hints.append("• Make creative improvements")
            else:
                hints.append("FEATURE ADDITION DETECTED (MINIMAL CHANGE):")
                hints.append("• Add ONLY the requested feature")
                hints.append("• DO NOT change existing UI elements")
                hints.append("• DO NOT change the app's purpose or core functionality")
                hints.append("• Integrate with minimal visual impact")
                hints.append("• Preserve existing styles and layouts")
                hints.append("• Example: 'add a button' means ADD a new button, keep all existing buttons")
        
        # Bug fixes
        elif any(word in request_lower for word in ['fix', 'bug', 'error', 'crash', 'broken']):
            hints.append("BUG FIX DETECTED:")
            hints.append("• Identify root cause")
            hints.append("• Fix without introducing new issues")
            hints.append("• Add safeguards to prevent recurrence")
        
        # Performance improvements
        elif any(word in request_lower for word in ['slow', 'performance', 'optimize', 'faster']):
            hints.append("PERFORMANCE OPTIMIZATION DETECTED:")
            hints.append("• Profile before optimizing")
            hints.append("• Use lazy loading where appropriate")
            hints.append("• Minimize unnecessary re-renders")
        
        # Data/State changes
        elif any(word in request_lower for word in ['save', 'persist', 'store', 'cache', 'data']):
            hints.append("DATA MANAGEMENT CHANGE DETECTED:")
            hints.append("• Use appropriate persistence method")
            hints.append("• Handle migration if needed")
            hints.append("• Ensure data integrity")
        
        # Navigation changes
        elif any(word in request_lower for word in ['navigate', 'screen', 'page', 'tab', 'menu']):
            hints.append("NAVIGATION CHANGE DETECTED:")
            hints.append("• Maintain navigation consistency")
            hints.append("• Preserve navigation state")
            hints.append("• Use standard iOS patterns")
        
        # General modification
        else:
            hints.append("MODIFICATION APPROACH:")
            hints.append("• Understand the user's intent")
            hints.append("• Make changes that improve the app")
            hints.append("• Maintain code quality")
        
        return "\n".join(hints) if hints else ""
    
    @staticmethod
    def handle_complex_request(request: str) -> Dict:
        """
        Handle complex or ambiguous requests intelligently
        """
        # Extract key information
        app_name_match = re.search(r'(?:app called|app named|application called)\s+(\w+)', request, re.I)
        app_name = app_name_match.group(1) if app_name_match else "InnovativeApp"
        
        # Don't try to categorize - let the LLM interpret
        return {
            'app_name': app_name,
            'app_type': 'custom',  # Always use custom to avoid restrictions
            'must_have_features': [],  # Don't extract features, let LLM interpret
            'description': request  # Pass full request for context
        }
    
    @staticmethod
    def validate_modification_response(response: dict, original_files: List[Dict]) -> dict:
        """
        Validate that modification response properly modifies existing app
        """
        issues = []
        warnings = []
        
        # Check that we still have the core files
        if 'files' not in response:
            issues.append("Missing files in response")
            return {'valid': False, 'issues': issues, 'warnings': warnings}
        
        # Get original app name
        original_app_name = None
        for file in original_files:
            if 'App.swift' in file.get('filename', ''):
                content = file.get('content', '')
                import re
                match = re.search(r'struct\s+(\w+)App\s*:', content)
                if match:
                    original_app_name = match.group(1)
                    break
        
        # Check that app name hasn't changed (indicating a new app)
        for file in response['files']:
            if 'App.swift' in file.get('path', ''):
                content = file.get('content', '')
                import re
                match = re.search(r'struct\s+(\w+)App\s*:', content)
                if match and original_app_name:
                    new_app_name = match.group(1)
                    if new_app_name != original_app_name:
                        issues.append(f"App name changed from {original_app_name} to {new_app_name} - this created a new app!")
        
        # Ensure we have the same core structure
        original_file_count = len(original_files)
        new_file_count = len(response['files'])
        
        # Allow adding files, but warn if too many files removed
        if new_file_count < original_file_count - 2:
            warnings.append(f"Significant file reduction: {original_file_count} -> {new_file_count}")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'warnings': warnings
        }
    
    @staticmethod
    def validate_response(response: dict) -> dict:
        """
        Validate LLM response for quality without being overly strict
        """
        issues = []
        warnings = []
        
        # Check for required files
        if 'files' not in response:
            issues.append("Missing files in response")
        else:
            files = response['files']
            has_content_view = any('ContentView' in f.get('path', '') for f in files)
            has_app_file = any('App.swift' in f.get('path', '') for f in files)
            
            if not has_content_view:
                issues.append("Missing ContentView.swift")
            if not has_app_file:
                issues.append("Missing App.swift file")
            
            # Check for basic code quality
            for file in files:
                content = file.get('content', '')
                if 'TODO' in content or 'FIXME' in content:
                    warnings.append(f"Incomplete code in {file.get('path', 'unknown')}")
                if 'fatalError' in content and 'NotImplemented' in content:
                    warnings.append(f"Unimplemented features in {file.get('path', 'unknown')}")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'warnings': warnings,
            'can_proceed': len(issues) == 0  # Warnings don't block
        }


class UniversalAppHandler:
    """
    Handles ANY type of app request without artificial limitations
    """
    
    # App categories for reference, but NOT restrictive
    KNOWN_PATTERNS = {
        'utility': ['calculator', 'converter', 'timer', 'counter', 'tracker'],
        'productivity': ['todo', 'notes', 'calendar', 'reminder', 'planner'],
        'entertainment': ['game', 'quiz', 'trivia', 'puzzle', 'music'],
        'social': ['chat', 'feed', 'share', 'profile', 'message'],
        'business': ['invoice', 'inventory', 'crm', 'analytics', 'reports'],
        'education': ['flashcard', 'course', 'tutorial', 'quiz', 'learn'],
        'lifestyle': ['recipe', 'fitness', 'meditation', 'journal', 'habit'],
        'finance': ['budget', 'expense', 'investment', 'crypto', 'banking'],
        'health': ['symptom', 'medication', 'appointment', 'vitals', 'workout'],
        'travel': ['itinerary', 'booking', 'guide', 'map', 'translation'],
        'shopping': ['cart', 'product', 'wishlist', 'deals', 'comparison'],
        'media': ['photo', 'video', 'editor', 'gallery', 'stream'],
        'developer': ['api', 'debug', 'monitor', 'deploy', 'test'],
        'creative': ['drawing', 'design', 'music', 'writing', 'art']
    }
    
    @staticmethod
    def interpret_request(description: str) -> dict:
        """
        Interpret ANY request without forcing it into rigid categories
        """
        # Always return flexible interpretation
        return {
            'interpretation': 'custom',
            'approach': 'creative',
            'restrictions': 'none',
            'guidance': 'Build what makes sense for this specific request'
        }
    
    @staticmethod
    def can_handle(request: str) -> bool:
        """
        Can handle ANY request - no limitations
        """
        return True  # We can handle anything!
    
    @staticmethod
    def enhance_request(request: str) -> str:
        """
        Enhance request with helpful context without restricting
        """
        enhanced = request
        
        # Add helpful context if request is very brief
        if len(request.split()) < 5:
            enhanced += "\n\nNote: Interpret this request creatively and build something useful and delightful."
        
        return enhanced