"""
Balanced Prompt Builder - Ensures App Store quality without over-restriction
Follows Apple HIG while allowing creative freedom
"""

class BalancedPromptBuilder:
    """
    Creates prompts that balance:
    - App Store approval requirements
    - Apple HIG guidelines
    - Creative freedom for unique apps
    - Technical best practices
    """
    
    @staticmethod
    def build_generation_prompt(requirements: dict) -> str:
        """
        Build a balanced prompt that ensures quality without being overly prescriptive
        """
        app_name = requirements['app_name']
        app_type = requirements.get('app_type', 'innovative')
        features = requirements.get('must_have_features', [])
        
        # Essential App Store requirements (non-negotiable)
        essential_requirements = """
ESSENTIAL APP STORE REQUIREMENTS:
• iOS 16.0+ minimum deployment (covers 95%+ of devices)
• Proper Info.plist configuration
• No crashes or memory leaks
• Responsive UI that works on all iPhone sizes
• Basic accessibility (VoiceOver labels)
• Privacy-compliant (no unauthorized data collection)
"""

        # HIG guidelines (important but flexible)
        hig_guidelines = """
APPLE HIG PRINCIPLES (interpret creatively):
• Clarity - Interface should be intuitive and focused
• Deference - Content is primary, UI supports it
• Depth - Use visual layers and motion to communicate hierarchy
• Use native controls where they make sense
• Respect platform conventions while innovating
"""

        # Technical best practices (recommended, not required)
        best_practices = """
RECOMMENDED BEST PRACTICES:
• State management: @State for view state, @StateObject for shared state
• Animations: Use .animation() for smooth transitions when it enhances UX
• Haptic feedback: Consider adding for important actions (optional)
• SF Symbols: Great for consistent iconography (but custom icons are fine too)
• Dark mode: Support if it makes sense for your app
• Performance: Lazy loading for lists, avoid unnecessary re-renders
"""

        # Creative freedom encouragement
        creative_freedom = """
CREATIVE FREEDOM:
• You're building something unique - don't just copy existing apps
• Innovate within the guidelines - Apple loves apps that push boundaries respectfully
• Focus on solving the user's problem in a delightful way
• Add personality that fits the app's purpose
• Surprise users with thoughtful details
"""

        # Build the final prompt
        prompt = f"""Create a SwiftUI iOS app: {app_name}

PURPOSE: {app_type} app{f' with {", ".join(features)}' if features else ''}

{essential_requirements}

{hig_guidelines}

{best_practices}

{creative_freedom}

DELIVERABLES:
1. ContentView.swift - Main UI implementation
2. {app_name}App.swift - App entry point

Focus on creating something that:
✓ Would pass App Store review
✓ Users would actually want to use
✓ Shows attention to detail
✓ Feels native to iOS while being unique

Return JSON: {{files: [{{path, content}}], app_name, bundle_id}}
"""
        return prompt
    
    @staticmethod
    def get_modification_prompt(existing_code: str, modification_request: str) -> str:
        """
        Balanced prompt for modifications
        """
        return f"""Modify this iOS app based on user request.

USER REQUEST: {modification_request}

MODIFICATION PRINCIPLES:
• Maintain existing app quality and style
• Ensure changes don't break App Store guidelines
• Keep the app's personality consistent
• Test that all existing features still work
• Add smooth transitions for any UI changes

CURRENT CODE TO MODIFY:
{existing_code[:2000]}...

Make the requested changes while:
1. Preserving what works well
2. Improving overall quality if possible
3. Maintaining iOS best practices
4. Ensuring backward compatibility

Return complete modified code, not just changes.
"""
    
    @staticmethod
    def validate_app_store_readiness(code: str, app_code: str = None) -> dict:
        """
        Check if generated code meets minimum App Store requirements
        Not overly strict, just the essentials
        """
        issues = []
        warnings = []
        
        # Combine both files for checking
        full_code = code
        if app_code:
            full_code = code + '\n' + app_code
        
        # Critical checks (would cause rejection)
        if '@main' not in full_code:
            issues.append("Missing @main app entry point")
        
        if 'struct ContentView' not in code and 'class ContentView' not in code:
            issues.append("Missing main ContentView")
        
        # Check for obvious crashes
        if 'fatalError(' in code and '// TODO' not in code:
            issues.append("Contains fatalError that could crash app")
        
        if 'force unwrap' in code.lower() or '!' in code:
            # Only warn, don't block - force unwrapping is sometimes OK
            warnings.append("Contains force unwrapping - verify it's safe")
        
        # Privacy checks
        if any(api in code for api in ['CLLocationManager', 'AVCaptureDevice', 'PHPhotoLibrary']):
            warnings.append("Uses privacy-sensitive APIs - ensure Info.plist has usage descriptions")
        
        # Performance warnings (not blockers)
        if 'ForEach' in code and 'id:' not in code:
            warnings.append("ForEach without explicit id - might cause performance issues")
        
        return {
            'ready': len(issues) == 0,
            'issues': issues,
            'warnings': warnings,
            'recommendation': 'Ready for App Store' if len(issues) == 0 else 'Fix critical issues first'
        }
    
    @staticmethod
    def get_hig_compliance_score(code: str) -> dict:
        """
        Score HIG compliance (informational, not blocking)
        """
        score = 100
        feedback = []
        
        # Check for good practices (bonus points)
        if '.accessibilityLabel' in code:
            feedback.append("✓ Good: Accessibility labels present")
        else:
            score -= 10
            feedback.append("Consider adding accessibility labels")
        
        if 'animation(' in code:
            feedback.append("✓ Good: Animations for better UX")
        
        if 'SF Symbols' in code or 'systemName:' in code:
            feedback.append("✓ Good: Using SF Symbols")
        
        if '@Environment(\\.colorScheme)' in code:
            feedback.append("✓ Good: Dark mode support")
        elif 'Color(' in code and not '.primary' in code:
            score -= 5
            feedback.append("Consider using semantic colors for dark mode")
        
        if '.sheet' in code or '.fullScreenCover' in code:
            feedback.append("✓ Good: Using native modal presentations")
        
        if 'NavigationStack' in code or 'NavigationView' in code:
            feedback.append("✓ Good: Standard navigation patterns")
        
        return {
            'score': max(score, 60),  # Don't be too harsh
            'feedback': feedback,
            'summary': 'Follows HIG well' if score >= 80 else 'Meets basic HIG requirements'
        }


class AppStoreReadinessChecker:
    """
    Practical checker for App Store readiness
    Focuses on what actually matters for approval
    """
    
    @staticmethod
    def check_technical_requirements(project_path: str) -> dict:
        """
        Check technical requirements that Apple actually enforces
        """
        import os
        import json
        
        results = {
            'minimum_ios': False,
            'info_plist': False,
            'app_icon': False,
            'launch_screen': False,
            'bundle_id': False
        }
        
        # Check for Info.plist or generation flag
        info_plist_path = os.path.join(project_path, 'build', 'Info.plist')
        project_yml = os.path.join(project_path, 'project.yml')
        
        if os.path.exists(info_plist_path):
            results['info_plist'] = True
        elif os.path.exists(project_yml):
            with open(project_yml, 'r') as f:
                if 'GENERATE_INFOPLIST_FILE: YES' in f.read():
                    results['info_plist'] = True
        
        # Check minimum iOS version
        if os.path.exists(project_yml):
            with open(project_yml, 'r') as f:
                content = f.read()
                if 'iOS: 16' in content or 'iOS: 17' in content:
                    results['minimum_ios'] = True
                if 'PRODUCT_BUNDLE_IDENTIFIER' in content:
                    results['bundle_id'] = True
        
        # App icon and launch screen can be added later
        # Not blocking for initial development
        results['app_icon'] = 'Can be added before submission'
        results['launch_screen'] = 'Can be added before submission'
        
        ready_count = sum(1 for v in results.values() if v is True)
        
        return {
            'ready': ready_count >= 3,  # Minimum viable
            'results': results,
            'message': f'{ready_count}/5 technical requirements met',
            'next_steps': [
                k.replace('_', ' ').title() 
                for k, v in results.items() 
                if v is False
            ]
        }
    
    @staticmethod
    def estimate_approval_chance(code: str, project_path: str) -> dict:
        """
        Realistic estimate of App Store approval chances
        """
        from balanced_prompt import BalancedPromptBuilder
        
        # Check code quality
        validation = BalancedPromptBuilder.validate_app_store_readiness(code)
        hig_score = BalancedPromptBuilder.get_hig_compliance_score(code)
        
        # Check technical requirements
        tech_check = AppStoreReadinessChecker.check_technical_requirements(project_path)
        
        # Calculate realistic approval chance
        base_score = 70  # Most apps that compile have a decent chance
        
        if validation['ready']:
            base_score += 10
        
        if hig_score['score'] >= 80:
            base_score += 10
        
        if tech_check['ready']:
            base_score += 10
        
        # Deductions for issues
        base_score -= len(validation['issues']) * 15
        base_score -= len(validation['warnings']) * 2
        
        approval_chance = max(min(base_score, 95), 30)  # Cap between 30-95%
        
        recommendations = []
        if approval_chance < 70:
            if validation['issues']:
                recommendations.append("Fix critical issues first")
            if hig_score['score'] < 70:
                recommendations.append("Improve UI/UX following HIG")
            recommendations.append("Add app icon and launch screen before submission")
            recommendations.append("Test thoroughly on real devices")
        else:
            recommendations.append("App has good foundation for App Store")
            recommendations.append("Add screenshots and app description")
            recommendations.append("Consider adding more features to stand out")
        
        return {
            'approval_chance': f"{approval_chance}%",
            'status': 'Ready with minor fixes' if approval_chance >= 70 else 'Needs work',
            'validation': validation,
            'hig_compliance': hig_score,
            'technical': tech_check,
            'recommendations': recommendations,
            'summary': f"""
App Store Readiness Assessment:
• Approval Chance: {approval_chance}%
• Code Quality: {'✓ Good' if validation['ready'] else '⚠️ Has issues'}
• HIG Compliance: {hig_score['summary']}
• Technical Setup: {tech_check['message']}

{'This app has a good foundation and could be approved with minor improvements.' if approval_chance >= 70 else 'This app needs some work before App Store submission.'}
"""
        }