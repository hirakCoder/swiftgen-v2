"""
iOS 16 Compatibility Validator
Prevents generation of iOS 17+ only features and validates code before sending to LLM
"""

import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

@dataclass
class CompatibilityIssue:
    """Represents a compatibility issue found in code"""
    feature: str
    ios_version_required: str
    replacement: str
    line_number: Optional[int] = None
    severity: str = "error"  # error, warning

class iOS16CompatibilityValidator:
    """
    Validates Swift/SwiftUI code for iOS 16 compatibility
    Prevents iOS 17+ features from being generated or used
    """
    
    def __init__(self):
        self.forbidden_features = self._init_forbidden_features()
        self.replacement_patterns = self._init_replacement_patterns()
        
    def _init_forbidden_features(self) -> Dict[str, Dict]:
        """Initialize list of iOS 17+ only features that should not be used"""
        return {
            # iOS 17+ Views
            "ContentUnavailableView": {
                "ios_version": "17.0",
                "replacement": "Custom VStack with Image and Text",
                "pattern": r'ContentUnavailableView[^)]*\)',
                "severity": "error"
            },
            
            # iOS 17+ Modifiers
            ".symbolEffect": {
                "ios_version": "17.0",
                "replacement": ".scaleEffect or animation",
                "pattern": r'\.symbolEffect\([^)]*\)',
                "severity": "error"
            },
            ".bounce": {
                "ios_version": "17.0",
                "replacement": ".animation(.spring())",
                "pattern": r'\.bounce(?:\([^)]*\))?',
                "severity": "error"
            },
            ".scrollBounceBehavior": {
                "ios_version": "17.0",
                "replacement": "Use ScrollView default behavior",
                "pattern": r'\.scrollBounceBehavior\([^)]*\)',
                "severity": "error"
            },
            ".contentTransition": {
                "ios_version": "17.0",
                "replacement": ".transition",
                "pattern": r'\.contentTransition\([^)]*\)',
                "severity": "error"
            },
            ".typesettingLanguage": {
                "ios_version": "17.0",
                "replacement": "Remove or use .environment",
                "pattern": r'\.typesettingLanguage\([^)]*\)',
                "severity": "error"
            },
            ".scrollPosition": {
                "ios_version": "17.0",
                "replacement": "Use ScrollViewReader",
                "pattern": r'\.scrollPosition\([^)]*\)',
                "severity": "error"
            },
            
            # iOS 17+ Property Wrappers
            "@Observable": {
                "ios_version": "17.0",
                "replacement": "@ObservableObject with @Published",
                "pattern": r'@Observable\s+(?:class|struct)',
                "severity": "error"
            },
            "@Bindable": {
                "ios_version": "17.0",
                "replacement": "@ObservedObject or @StateObject",
                "pattern": r'@Bindable\s+',
                "severity": "error"
            },
            
            # iOS 17+ onChange syntax
            "onChange_two_params": {
                "ios_version": "17.0",
                "replacement": ".onChange(of: value) { newValue in",
                "pattern": r'\.onChange\(of:[^)]+\)\s*\{\s*\w+\s*,\s*\w+\s+in',
                "severity": "error"
            },
            
            # iOS 17+ Animation
            ".phaseAnimator": {
                "ios_version": "17.0",
                "replacement": "Use @State with animation",
                "pattern": r'\.phaseAnimator\([^)]*\)',
                "severity": "error"
            },
            ".keyframeAnimator": {
                "ios_version": "17.0",
                "replacement": "Use withAnimation",
                "pattern": r'\.keyframeAnimator\([^)]*\)',
                "severity": "error"
            },
            
            # Incorrect patterns
            ".dropShadow": {
                "ios_version": "Never existed",
                "replacement": ".shadow()",
                "pattern": r'\.dropShadow\([^)]*\)',
                "severity": "error"
            }
        }
    
    def _init_replacement_patterns(self) -> List[Tuple[str, str]]:
        """Initialize automatic replacement patterns"""
        return [
            # ContentUnavailableView replacements
            (
                r'ContentUnavailableView\s*\(\s*"([^"]+)"\s*,\s*systemImage:\s*"([^"]+)"\s*\)',
                r'''VStack(spacing: 20) {
                    Image(systemName: "\2")
                        .font(.system(size: 50))
                        .foregroundColor(.gray)
                    Text("\1")
                        .font(.title2)
                        .foregroundColor(.gray)
                }'''
            ),
            
            # onChange fix
            (
                r'\.onChange\(of:\s*([^)]+)\)\s*\{\s*(\w+)\s*,\s*(\w+)\s+in',
                r'.onChange(of: \1) { \3 in'
            ),
            
            # @Observable to ObservableObject
            (
                r'@Observable\s+class\s+(\w+)',
                r'class \1: ObservableObject'
            ),
            
            # .symbolEffect removal
            (
                r'\.symbolEffect\([^)]*\)',
                ''
            ),
            
            # .dropShadow to .shadow
            (
                r'\.dropShadow\(([^)]*)\)',
                r'.shadow(\1)'
            )
        ]
    
    def validate_code(self, code: str) -> List[CompatibilityIssue]:
        """
        Validate code for iOS 16 compatibility
        Returns list of compatibility issues found
        """
        issues = []
        lines = code.split('\n')
        
        for feature_name, feature_info in self.forbidden_features.items():
            pattern = re.compile(feature_info["pattern"], re.IGNORECASE)
            
            for line_num, line in enumerate(lines, 1):
                if pattern.search(line):
                    issues.append(CompatibilityIssue(
                        feature=feature_name,
                        ios_version_required=feature_info["ios_version"],
                        replacement=feature_info["replacement"],
                        line_number=line_num,
                        severity=feature_info["severity"]
                    ))
        
        return issues
    
    def fix_compatibility_issues(self, code: str) -> Tuple[str, List[str]]:
        """
        Automatically fix iOS 17+ features in code
        Returns: (fixed_code, list_of_fixes_applied)
        """
        fixed_code = code
        fixes_applied = []
        
        # Apply replacement patterns
        for pattern, replacement in self.replacement_patterns:
            if re.search(pattern, fixed_code):
                fixed_code = re.sub(pattern, replacement, fixed_code)
                fixes_applied.append(f"Replaced iOS 17+ pattern: {pattern[:30]}...")
        
        # Remove any remaining forbidden features
        for feature_name, feature_info in self.forbidden_features.items():
            pattern = feature_info["pattern"]
            if re.search(pattern, fixed_code, re.IGNORECASE):
                # For some features, we can't auto-fix, just remove
                if feature_name in [".symbolEffect", ".bounce", ".contentTransition"]:
                    fixed_code = re.sub(pattern, '', fixed_code, flags=re.IGNORECASE)
                    fixes_applied.append(f"Removed {feature_name}")
        
        return fixed_code, fixes_applied
    
    def validate_prompt(self, prompt: str) -> str:
        """
        Add iOS 16 compatibility requirements to prompt
        """
        compatibility_requirements = """

CRITICAL iOS 16 COMPATIBILITY REQUIREMENTS:
1. Target iOS 16.0 - DO NOT use iOS 17+ features
2. FORBIDDEN features (will cause compilation errors):
   - ContentUnavailableView (use VStack with Image and Text)
   - .symbolEffect() (does not exist)
   - .bounce (use .animation(.spring()))
   - @Observable (use ObservableObject + @Published)
   - .onChange with two parameters (use single newValue parameter)
   - .scrollBounceBehavior, .contentTransition, .typesettingLanguage
3. ALWAYS use:
   - NavigationStack (not NavigationView)
   - ObservableObject + @Published (not @Observable)
   - .shadow() (not .dropShadow())
   - .onChange(of: value) { newValue in } (not oldValue, newValue)
"""
        
        # Add requirements if not already present
        if "iOS 16" not in prompt and "ios 16" not in prompt.lower():
            prompt += compatibility_requirements
        
        return prompt
    
    def generate_validation_report(self, code: str) -> str:
        """Generate a detailed compatibility report"""
        issues = self.validate_code(code)
        
        if not issues:
            return "✅ Code is iOS 16 compatible"
        
        report = "⚠️ iOS Compatibility Issues Found:\n"
        report += "=" * 40 + "\n"
        
        for issue in issues:
            report += f"\n❌ {issue.feature}\n"
            report += f"   Line: {issue.line_number}\n"
            report += f"   Requires: iOS {issue.ios_version_required}\n"
            report += f"   Fix: {issue.replacement}\n"
        
        report += "\n" + "=" * 40
        report += f"\nTotal issues: {len(issues)}"
        
        return report
    
    def pre_generation_check(self, description: str) -> Dict:
        """
        Check if user request might trigger iOS 17+ features
        Returns warnings and suggestions
        """
        warnings = []
        
        # Check for problematic keywords
        problematic_keywords = {
            "unavailable": "May trigger ContentUnavailableView - use empty state instead",
            "symbol animation": "Symbol animations are iOS 17+ - use regular animations",
            "observable": "May trigger @Observable - use ObservableObject",
            "phase": "Phase animations are iOS 17+ - use standard animations",
            "content transition": "Content transitions are iOS 17+ - use regular transitions"
        }
        
        description_lower = description.lower()
        for keyword, warning in problematic_keywords.items():
            if keyword in description_lower:
                warnings.append(warning)
        
        return {
            "has_warnings": len(warnings) > 0,
            "warnings": warnings,
            "suggestion": "Consider rephrasing to avoid iOS 17+ features" if warnings else None
        }

# Global instance for easy access
ios16_validator = iOS16CompatibilityValidator()

def validate_and_fix(code: str) -> Tuple[str, str]:
    """
    Convenience function to validate and fix code
    Returns: (fixed_code, report)
    """
    # First validate
    issues = ios16_validator.validate_code(code)
    
    if issues:
        # Fix the issues
        fixed_code, fixes = ios16_validator.fix_compatibility_issues(code)
        
        # Generate report
        report = f"Fixed {len(fixes)} iOS compatibility issues:\n"
        for fix in fixes:
            report += f"  - {fix}\n"
        
        return fixed_code, report
    
    return code, "No iOS compatibility issues found"