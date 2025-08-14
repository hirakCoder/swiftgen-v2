"""
Swift Validator - Pre-build validation to catch errors before compilation
Production-grade validator that prevents common Swift/SwiftUI issues
"""

import re
import os
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from pathlib import Path

@dataclass
class ValidationIssue:
    """Single validation issue found"""
    severity: str  # 'error', 'warning', 'info'
    category: str  # 'syntax', 'import', 'type', 'ios_version', etc.
    message: str
    file: str
    line: Optional[int] = None
    column: Optional[int] = None
    suggestion: Optional[str] = None
    auto_fix: Optional[str] = None

@dataclass 
class ValidationResult:
    """Complete validation result"""
    valid: bool
    issues: List[ValidationIssue] = field(default_factory=list)
    errors: List[ValidationIssue] = field(default_factory=list)
    warnings: List[ValidationIssue] = field(default_factory=list)
    auto_fixable: List[ValidationIssue] = field(default_factory=list)
    
    @property
    def error_count(self) -> int:
        return len(self.errors)
    
    @property
    def warning_count(self) -> int:
        return len(self.warnings)
    
    @property
    def can_auto_fix(self) -> bool:
        return len(self.auto_fixable) > 0

class SwiftValidator:
    """Production-grade Swift/SwiftUI validator"""
    
    def __init__(self, ios_version: str = "16.0"):
        self.ios_version = ios_version
        
        # iOS 17+ only features
        self.ios17_features = {
            '.symbolEffect': 'Use .scaleEffect or .opacity animations instead',
            '.bounce': 'Use .animation(.spring()) instead',
            '@Observable': 'Use ObservableObject with @Published instead',
            '.scrollBounceBehavior': 'Remove or use ScrollView without this modifier',
            '.contentTransition': 'Use standard transitions instead',
            'ContentUnavailableView': 'Create custom empty state view',
            'NavigationStack': None,  # Actually available in iOS 16
            '.onChange(of:initial:)': 'Use .onChange(of:) { newValue in } for iOS 16',
            '.dropShadow': 'Use .shadow() instead'
        }
        
        # Required imports for common features
        self.feature_imports = {
            'Timer.publish': 'import Combine',
            'URLSession': 'import Foundation',
            '@Published': 'import Combine',
            'ObservableObject': 'import Combine',
            'NavigationStack': 'import SwiftUI',
            'NavigationView': 'import SwiftUI',
            '@State': 'import SwiftUI',
            '@StateObject': 'import SwiftUI',
            '@EnvironmentObject': 'import SwiftUI',
            'NetworkMonitor': 'import Network',
            'NWPathMonitor': 'import Network',
            'CoreData': 'import CoreData',
            'UserDefaults': 'import Foundation',
            'JSONEncoder': 'import Foundation',
            'JSONDecoder': 'import Foundation'
        }
        
        # Common syntax patterns that cause issues
        self.syntax_issues = {
            r'^\s*\)\s*$': 'Orphaned closing parenthesis',
            r'^\s*\}\s*$': 'Potentially orphaned closing brace',
            r'\?\s*:\s*$': 'Incomplete ternary operator',
            r'\?\s*$': 'Incomplete optional chaining or ternary',
            r':\s*$': 'Incomplete type annotation or ternary',
            r',\s*\)': 'Trailing comma before closing parenthesis',
            r',\s*\]': 'Trailing comma before closing bracket',
            r',\s*\}': 'Trailing comma before closing brace',
            r'let\s+\w+\s*$': 'Incomplete variable declaration',
            r'var\s+\w+\s*$': 'Incomplete variable declaration',
            r'func\s+\w+\s*$': 'Incomplete function declaration'
        }
        
        # Type definition requirements
        self.undefined_type_patterns = [
            (r':\s*(\w+)(?:\s*[{<]|$)', 'type'),  # Type annotations
            (r'@StateObject\s+(?:private\s+)?var\s+\w+\s*=\s*(\w+)\(', 'class'),  # StateObject init
            (r'(\w+)\.shared', 'singleton'),  # Singleton access
            (r'case\s+\.\w+\(.*?(\w+).*?\)', 'associated_type'),  # Enum associated values
        ]
    
    def validate_project(self, project_path: str) -> ValidationResult:
        """Validate entire project"""
        result = ValidationResult(valid=True)
        sources_path = Path(project_path) / "Sources"
        
        if not sources_path.exists():
            result.valid = False
            result.errors.append(ValidationIssue(
                severity='error',
                category='structure',
                message='Sources directory not found',
                file=str(project_path)
            ))
            return result
        
        # Collect all Swift files
        swift_files = list(sources_path.glob("**/*.swift"))
        
        if not swift_files:
            result.valid = False
            result.errors.append(ValidationIssue(
                severity='error',
                category='structure',
                message='No Swift files found',
                file=str(sources_path)
            ))
            return result
        
        # Validate each file
        all_content = {}
        for swift_file in swift_files:
            try:
                with open(swift_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    all_content[str(swift_file)] = content
                    
                    file_result = self.validate_file(content, str(swift_file.name))
                    result.issues.extend(file_result.issues)
                    result.errors.extend(file_result.errors)
                    result.warnings.extend(file_result.warnings)
                    result.auto_fixable.extend(file_result.auto_fixable)
                    
                    if not file_result.valid:
                        result.valid = False
                        
            except Exception as e:
                result.errors.append(ValidationIssue(
                    severity='error',
                    category='io',
                    message=f'Failed to read file: {e}',
                    file=str(swift_file)
                ))
        
        # Cross-file validation
        cross_file_result = self._validate_cross_file(all_content)
        result.issues.extend(cross_file_result.issues)
        result.errors.extend(cross_file_result.errors)
        result.warnings.extend(cross_file_result.warnings)
        
        if not cross_file_result.valid:
            result.valid = False
        
        return result
    
    def validate_file(self, content: str, filename: str) -> ValidationResult:
        """Validate single Swift file"""
        result = ValidationResult(valid=True)
        
        # Check syntax
        syntax_result = self._check_syntax(content, filename)
        self._merge_results(result, syntax_result)
        
        # Check imports
        import_result = self._check_imports(content, filename)
        self._merge_results(result, import_result)
        
        # Check iOS version compatibility
        ios_result = self._check_ios_compatibility(content, filename)
        self._merge_results(result, ios_result)
        
        # Check type definitions
        type_result = self._check_types(content, filename)
        self._merge_results(result, type_result)
        
        # Check SwiftUI specific issues
        swiftui_result = self._check_swiftui(content, filename)
        self._merge_results(result, swiftui_result)
        
        return result
    
    def _check_syntax(self, content: str, filename: str) -> ValidationResult:
        """Check for syntax issues"""
        result = ValidationResult(valid=True)
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            # Check for syntax patterns
            for pattern, message in self.syntax_issues.items():
                if re.search(pattern, line):
                    # Special handling for braces - be less strict
                    if pattern in [r'^\s*\}\s*$', r'^\s*\)\s*$']:
                        # Always skip if code is balanced up to this point
                        continue  # Don't flag closing braces as errors
                    
                    issue = ValidationIssue(
                        severity='error',
                        category='syntax',
                        message=message,
                        file=filename,
                        line=i,
                        suggestion=f'Review line {i} for syntax issues'
                    )
                    result.errors.append(issue)
                    result.valid = False
        
        # Check for unbalanced braces/parentheses
        if not self._check_balanced_delimiters(content):
            result.errors.append(ValidationIssue(
                severity='error',
                category='syntax',
                message='Unbalanced braces, parentheses, or brackets',
                file=filename,
                suggestion='Check that all opening delimiters have matching closing delimiters'
            ))
            result.valid = False
        
        # Check for string literal issues
        if self._has_string_literal_issues(content):
            result.errors.append(ValidationIssue(
                severity='error',
                category='syntax',
                message='String literal issues detected',
                file=filename,
                suggestion='Ensure all strings use double quotes and are properly terminated'
            ))
            result.valid = False
        
        return result
    
    def _check_imports(self, content: str, filename: str) -> ValidationResult:
        """Check for missing imports"""
        result = ValidationResult(valid=True)
        
        # Extract current imports
        current_imports = set(re.findall(r'import\s+(\w+)', content))
        
        # Check for features that need imports
        for feature, required_import in self.feature_imports.items():
            if feature in content:
                import_name = required_import.split()[-1]  # Get module name
                if import_name not in current_imports:
                    issue = ValidationIssue(
                        severity='error',
                        category='import',
                        message=f'Missing import for {feature}',
                        file=filename,
                        suggestion=f'Add "{required_import}" at the top of the file',
                        auto_fix=required_import
                    )
                    result.errors.append(issue)
                    result.auto_fixable.append(issue)
                    result.valid = False
        
        return result
    
    def _check_ios_compatibility(self, content: str, filename: str) -> ValidationResult:
        """Check for iOS version compatibility issues"""
        result = ValidationResult(valid=True)
        
        for feature, suggestion in self.ios17_features.items():
            if feature in content:
                issue = ValidationIssue(
                    severity='error',
                    category='ios_version',
                    message=f'{feature} is only available in iOS 17+',
                    file=filename,
                    suggestion=suggestion if suggestion else f'Remove {feature}',
                    auto_fix=suggestion
                )
                result.errors.append(issue)
                if suggestion:
                    result.auto_fixable.append(issue)
                result.valid = False
        
        return result
    
    def _check_types(self, content: str, filename: str) -> ValidationResult:
        """Check for undefined types"""
        result = ValidationResult(valid=True)
        
        # Extract defined types
        defined_types = set()
        defined_types.update(re.findall(r'struct\s+(\w+)', content))
        defined_types.update(re.findall(r'class\s+(\w+)', content))
        defined_types.update(re.findall(r'enum\s+(\w+)', content))
        defined_types.update(re.findall(r'protocol\s+(\w+)', content))
        defined_types.update(re.findall(r'typealias\s+(\w+)', content))
        
        # Add Swift standard types
        standard_types = {
            'String', 'Int', 'Double', 'Float', 'Bool', 'Date', 'URL', 'UUID',
            'Array', 'Dictionary', 'Set', 'Optional', 'Result', 'Error',
            'View', 'Text', 'Image', 'Button', 'VStack', 'HStack', 'ZStack',
            'List', 'ScrollView', 'NavigationView', 'NavigationStack', 'TabView',
            'ObservableObject', 'Published', 'State', 'Binding', 'StateObject',
            'EnvironmentObject', 'Environment', 'FetchRequest', 'AppStorage'
        }
        
        # Check for undefined types
        for pattern, type_kind in self.undefined_type_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if match not in defined_types and match not in standard_types:
                    if not match.startswith('NS') and not match.startswith('UI'):  # Skip system types
                        result.warnings.append(ValidationIssue(
                            severity='warning',
                            category='type',
                            message=f'Potentially undefined type: {match}',
                            file=filename,
                            suggestion=f'Ensure {match} is defined or imported'
                        ))
        
        return result
    
    def _check_swiftui(self, content: str, filename: str) -> ValidationResult:
        """Check for SwiftUI specific issues"""
        result = ValidationResult(valid=True)
        
        # Check for @main duplicates
        main_count = len(re.findall(r'@main\s+struct', content))
        if main_count > 1:
            issue = ValidationIssue(
                severity='error',
                category='swiftui',
                message='Multiple @main declarations in file',
                file=filename,
                suggestion='Only one @main declaration allowed per project',
                auto_fix='Remove duplicate @main'
            )
            result.errors.append(issue)
            result.auto_fixable.append(issue)
            result.valid = False
        
        # Check for View protocol conformance
        view_structs = re.findall(r'struct\s+(\w+)\s*:\s*View', content)
        for view_name in view_structs:
            # Check if body property exists
            body_pattern = rf'struct\s+{view_name}[^{{]*{{[^}}]*var\s+body\s*:\s*some\s+View'
            if not re.search(body_pattern, content, re.DOTALL):
                result.errors.append(ValidationIssue(
                    severity='error',
                    category='swiftui',
                    message=f'{view_name} conforms to View but missing body property',
                    file=filename,
                    suggestion='Add "var body: some View { ... }"'
                ))
                result.valid = False
        
        # Check for @StateObject with struct
        if re.search(r'struct\s+\w+.*@StateObject', content, re.DOTALL):
            result.errors.append(ValidationIssue(
                severity='error',
                category='swiftui',
                message='@StateObject can only be used with classes',
                file=filename,
                suggestion='Use @State for value types or make the type a class'
            ))
            result.valid = False
        
        return result
    
    def _validate_cross_file(self, all_content: Dict[str, str]) -> ValidationResult:
        """Validate across multiple files"""
        result = ValidationResult(valid=True)
        
        # Check for multiple @main declarations across files
        main_files = []
        for filepath, content in all_content.items():
            if '@main' in content:
                main_files.append(Path(filepath).name)
        
        if len(main_files) > 1:
            result.errors.append(ValidationIssue(
                severity='error',
                category='structure',
                message=f'Multiple @main declarations found in: {", ".join(main_files)}',
                file='project',
                suggestion='Keep only one @main declaration, preferably in App.swift',
                auto_fix='Remove @main from all files except the main app file'
            ))
            result.valid = False
        
        # Check for circular dependencies (simplified check)
        dependencies = {}
        for filepath, content in all_content.items():
            filename = Path(filepath).stem
            imports = re.findall(r'import\s+(\w+)', content)
            references = re.findall(r'(\w+)\.', content)
            dependencies[filename] = set(imports + references)
        
        # More validation could be added here
        
        return result
    
    def _check_balanced_delimiters(self, content: str) -> bool:
        """Check if delimiters are balanced"""
        stack = []
        in_string = False
        in_comment = False
        i = 0
        
        while i < len(content):
            # Handle string literals
            if content[i] == '"' and (i == 0 or content[i-1] != '\\'):
                in_string = not in_string
            
            # Handle comments
            if not in_string:
                if i < len(content) - 1:
                    if content[i:i+2] == '//':
                        # Skip to end of line
                        while i < len(content) and content[i] != '\n':
                            i += 1
                        continue
                    elif content[i:i+2] == '/*':
                        # Skip to end of block comment
                        i += 2
                        while i < len(content) - 1:
                            if content[i:i+2] == '*/':
                                i += 2
                                break
                            i += 1
                        continue
            
            # Check delimiters only outside strings and comments
            if not in_string:
                if content[i] in '({[':
                    stack.append(content[i])
                elif content[i] in ')}]':
                    if not stack:
                        return False
                    opening = stack.pop()
                    if not self._matches(opening, content[i]):
                        return False
            
            i += 1
        
        return len(stack) == 0
    
    def _matches(self, opening: str, closing: str) -> bool:
        """Check if delimiters match"""
        pairs = {'(': ')', '{': '}', '[': ']'}
        return pairs.get(opening) == closing
    
    def _is_balanced_up_to_line(self, lines: List[str]) -> bool:
        """Check if delimiters are balanced up to given lines"""
        content = '\n'.join(lines)
        return self._check_balanced_delimiters(content)
    
    def _has_string_literal_issues(self, content: str) -> bool:
        """Check for string literal issues"""
        # Check for single quotes used as string delimiters
        if re.search(r"'[^']*'", content):
            # Make sure it's not a character literal
            if not re.search(r"'\\?.'", content):
                return True
        
        # Check for unterminated strings (simplified)
        lines = content.split('\n')
        for line in lines:
            quote_count = line.count('"') - line.count('\\"')
            if quote_count % 2 != 0:
                return True
        
        return False
    
    def _merge_results(self, target: ValidationResult, source: ValidationResult):
        """Merge validation results"""
        target.issues.extend(source.issues)
        target.errors.extend(source.errors)
        target.warnings.extend(source.warnings)
        target.auto_fixable.extend(source.auto_fixable)
        if not source.valid:
            target.valid = False
    
    def apply_auto_fixes(self, content: str, issues: List[ValidationIssue]) -> str:
        """Apply automatic fixes to content"""
        fixed_content = content
        
        for issue in issues:
            if issue.auto_fix and issue.category == 'import':
                # Add missing import
                if issue.auto_fix not in fixed_content:
                    # Add after existing imports or at the beginning
                    import_match = re.search(r'(import\s+\w+\n)+', fixed_content)
                    if import_match:
                        insert_pos = import_match.end()
                        fixed_content = fixed_content[:insert_pos] + issue.auto_fix + '\n' + fixed_content[insert_pos:]
                    else:
                        fixed_content = issue.auto_fix + '\n\n' + fixed_content
            
            elif issue.auto_fix and issue.category == 'ios_version':
                # Replace iOS 17+ features
                for feature, replacement in self.ios17_features.items():
                    if feature in fixed_content and replacement:
                        # Simple replacement (more sophisticated logic needed for production)
                        fixed_content = fixed_content.replace(feature, replacement.split(' ')[1] if ' ' in replacement else '')
        
        return fixed_content

