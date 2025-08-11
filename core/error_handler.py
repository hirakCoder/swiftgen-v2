"""
Robust Error Handling and Auto-Fix System for SwiftGen V2
Automatically detects and fixes compilation errors, build failures, and syntax issues
"""

import re
import os
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

class ErrorType(Enum):
    """Types of errors we can handle"""
    MISSING_IMPORT = "missing_import"
    UNDEFINED_SYMBOL = "undefined_symbol"
    TYPE_MISMATCH = "type_mismatch"
    SYNTAX_ERROR = "syntax_error"
    MISSING_PROTOCOL = "missing_protocol"
    DUPLICATE_DECLARATION = "duplicate_declaration"
    INVALID_MODIFIER = "invalid_modifier"
    MISSING_FRAMEWORK = "missing_framework"
    INHERITANCE_ERROR = "inheritance_error"
    COMPILATION_ERROR = "compilation_error"

@dataclass
class ErrorPattern:
    """Pattern for detecting and fixing specific errors"""
    pattern: str
    error_type: ErrorType
    fix_strategy: str
    description: str

class SwiftErrorAutoFixer:
    """
    Comprehensive error detection and auto-fix system
    """
    
    def __init__(self):
        self.error_patterns = self._initialize_patterns()
        self.fix_history = []
        self.max_fix_attempts = 5
        
    def _initialize_patterns(self) -> List[ErrorPattern]:
        """Initialize error patterns with fix strategies"""
        return [
            # Missing imports - Updated patterns for actual Swift errors
            ErrorPattern(
                pattern=r"cannot find type '(UIImpactFeedbackGenerator|UIKit\w+|UIDevice|UIApplication)' in scope",
                error_type=ErrorType.MISSING_IMPORT,
                fix_strategy="add_uikit_import",
                description="Missing UIKit import"
            ),
            ErrorPattern(
                pattern=r"cannot find type '(App|Scene|View|WindowGroup|NavigationView|NavigationStack)' in scope",
                error_type=ErrorType.MISSING_IMPORT,
                fix_strategy="add_swiftui_import",
                description="Missing SwiftUI types"
            ),
            ErrorPattern(
                pattern=r"cannot find '(Timer|Date|URL|URLSession|Data|JSONEncoder|JSONDecoder)' in scope",
                error_type=ErrorType.MISSING_IMPORT,
                fix_strategy="add_foundation_import",
                description="Missing Foundation import"
            ),
            ErrorPattern(
                pattern=r"no such module '(\w+)'",
                error_type=ErrorType.MISSING_FRAMEWORK,
                fix_strategy="add_framework",
                description="Missing framework"
            ),
            
            # Type and protocol errors
            ErrorPattern(
                pattern=r"inheritance from non-protocol type '(App|Scene|View)'",
                error_type=ErrorType.INHERITANCE_ERROR,
                fix_strategy="fix_swiftui_inheritance",
                description="SwiftUI protocol inheritance error"
            ),
            ErrorPattern(
                pattern=r"type '(\w+)' does not conform to protocol '(\w+)'",
                error_type=ErrorType.MISSING_PROTOCOL,
                fix_strategy="add_protocol_conformance",
                description="Missing protocol conformance"
            ),
            
            # Duplicate declarations
            ErrorPattern(
                pattern=r"redeclaration of '(@MainActor|@main)'",
                error_type=ErrorType.DUPLICATE_DECLARATION,
                fix_strategy="remove_duplicate",
                description="Duplicate declaration"
            ),
            ErrorPattern(
                pattern=r"'@main' attribute cannot be applied to",
                error_type=ErrorType.INVALID_MODIFIER,
                fix_strategy="fix_main_attribute",
                description="Invalid @main attribute"
            ),
            
            # iOS 17+ Components
            ErrorPattern(
                pattern=r"'ContentUnavailableView' is only available in iOS 17.0 or newer",
                error_type=ErrorType.COMPILATION_ERROR,
                fix_strategy="replace_content_unavailable_view",
                description="ContentUnavailableView requires iOS 17+"
            ),
            
            # Syntax errors
            ErrorPattern(
                pattern=r"expected '(\{|\}|\)|\])' in",
                error_type=ErrorType.SYNTAX_ERROR,
                fix_strategy="fix_brackets",
                description="Missing or mismatched brackets"
            ),
            ErrorPattern(
                pattern=r"consecutive statements on a line must be separated by ';'",
                error_type=ErrorType.SYNTAX_ERROR,
                fix_strategy="fix_line_separation",
                description="Missing semicolon or newline"
            ),
            
            # Symbol errors
            ErrorPattern(
                pattern=r"use of unresolved identifier '(\w+)'",
                error_type=ErrorType.UNDEFINED_SYMBOL,
                fix_strategy="fix_undefined_symbol",
                description="Undefined symbol"
            ),
            ErrorPattern(
                pattern=r"value of type '(\w+)' has no member '(\w+)'",
                error_type=ErrorType.TYPE_MISMATCH,
                fix_strategy="fix_member_access",
                description="Invalid member access"
            ),
        ]
    
    def detect_errors(self, error_output: str) -> List[Tuple[ErrorPattern, str]]:
        """Detect errors in compiler output"""
        detected_errors = []
        
        for pattern in self.error_patterns:
            matches = re.finditer(pattern.pattern, error_output, re.MULTILINE | re.IGNORECASE)
            for match in matches:
                detected_errors.append((pattern, match.group(0)))
        
        return detected_errors
    
    def fix_file(self, file_path: str, error: ErrorPattern, error_text: str) -> bool:
        """Apply fix to a specific file"""
        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            return False
        
        with open(file_path, 'r') as f:
            content = f.read()
        
        original_content = content
        
        # Apply fix based on strategy
        if error.fix_strategy == "add_uikit_import":
            content = self._add_import(content, "UIKit")
        elif error.fix_strategy == "add_swiftui_import":
            content = self._add_import(content, "SwiftUI")
        elif error.fix_strategy == "add_foundation_import":
            content = self._add_import(content, "Foundation")
        elif error.fix_strategy == "add_import":
            # Legacy support
            content = self._add_import(content, "UIKit")
        elif error.fix_strategy == "fix_swiftui_inheritance":
            content = self._fix_swiftui_inheritance(content)
        elif error.fix_strategy == "remove_duplicate":
            content = self._remove_duplicate_declarations(content, error_text)
        elif error.fix_strategy == "fix_main_attribute":
            content = self._fix_main_attribute(content)
        elif error.fix_strategy == "fix_brackets":
            content = self._fix_brackets(content)
        elif error.fix_strategy == "fix_undefined_symbol":
            content = self._fix_undefined_symbol(content, error_text)
        elif error.fix_strategy == "add_framework":
            # Framework fixes are handled at compilation level
            return True
        elif error.fix_strategy == "replace_content_unavailable_view":
            content = self._replace_content_unavailable_view(content)
        
        if content != original_content:
            with open(file_path, 'w') as f:
                f.write(content)
            
            self.fix_history.append({
                "file": file_path,
                "error": error.description,
                "fix": error.fix_strategy
            })
            
            print(f"✅ Fixed: {error.description} in {os.path.basename(file_path)}")
            return True
        
        return False
    
    def _add_import(self, content: str, module: str) -> str:
        """Add missing import statement"""
        import_statement = f"import {module}"
        
        # Check if import already exists
        if import_statement in content:
            return content
        
        # Add import at the beginning, after any existing imports
        lines = content.split('\n')
        import_index = 0
        
        # Find the last import statement
        for i, line in enumerate(lines):
            if line.strip().startswith('import '):
                import_index = i + 1
            elif line.strip() and not line.strip().startswith('//'):
                # Stop at first non-import, non-comment line
                break
        
        # Insert the import
        lines.insert(import_index, import_statement)
        return '\n'.join(lines)
    
    def _fix_swiftui_inheritance(self, content: str) -> str:
        """Fix SwiftUI protocol inheritance issues"""
        # Ensure SwiftUI is imported
        content = self._add_import(content, "SwiftUI")
        
        # Fix App protocol
        content = re.sub(
            r'struct\s+(\w+)\s*:\s*App\s*\{',
            r'struct \1: App {',
            content
        )
        
        # Fix View protocol
        content = re.sub(
            r'struct\s+(\w+)\s*:\s*View\s*\{',
            r'struct \1: View {',
            content
        )
        
        return content
    
    def _remove_duplicate_declarations(self, content: str, duplicate: str) -> str:
        """Remove duplicate declarations like @MainActor or @main"""
        if '@MainActor' in duplicate:
            # Remove duplicate @MainActor
            lines = content.split('\n')
            seen_mainactor = False
            filtered_lines = []
            
            for line in lines:
                if '@MainActor' in line:
                    if not seen_mainactor:
                        filtered_lines.append(line)
                        seen_mainactor = True
                else:
                    filtered_lines.append(line)
            
            return '\n'.join(filtered_lines)
        
        elif '@main' in duplicate:
            # Ensure only one @main attribute
            content = re.sub(r'(@main\s*\n)+', '@main\n', content)
        
        return content
    
    def _fix_main_attribute(self, content: str) -> str:
        """Fix @main attribute application"""
        # Ensure @main is only applied to App conforming struct
        pattern = r'@main\s+struct\s+(\w+)(?!.*:\s*App)'
        replacement = r'@main\nstruct \1: App'
        return re.sub(pattern, replacement, content)
    
    def _replace_content_unavailable_view(self, content: str) -> str:
        """Replace iOS 17+ ContentUnavailableView with iOS 16 compatible version"""
        import re
        
        # Pattern 1: Simple ContentUnavailableView("Title", systemImage: "icon")
        content = re.sub(
            r'ContentUnavailableView\s*\(\s*"([^"]+)"\s*,\s*systemImage:\s*"([^"]+)"\s*\)',
            r'''VStack(spacing: 20) {
                Image(systemName: "\2")
                    .font(.system(size: 50))
                    .foregroundColor(.gray)
                Text("\1")
                    .font(.title2)
                    .foregroundColor(.gray)
            }''',
            content
        )
        
        # Pattern 2: ContentUnavailableView with description
        content = re.sub(
            r'ContentUnavailableView\s*\(\s*"([^"]+)"\s*,\s*systemImage:\s*"([^"]+)"\s*,\s*description:\s*Text\s*\(\s*"([^"]+)"\s*\)\s*\)',
            r'''VStack(spacing: 20) {
                Image(systemName: "\2")
                    .font(.system(size: 50))
                    .foregroundColor(.gray)
                Text("\1")
                    .font(.title2)
                    .foregroundColor(.gray)
                Text("\3")
                    .font(.body)
                    .foregroundColor(.gray.opacity(0.8))
                    .multilineTextAlignment(.center)
            }''',
            content
        )
        
        # Pattern 3: Generic ContentUnavailableView - replace with empty state
        content = re.sub(
            r'ContentUnavailableView[^)]*\)',
            r'''VStack(spacing: 20) {
                Image(systemName: "doc.text")
                    .font(.system(size: 50))
                    .foregroundColor(.gray)
                Text("No Content Available")
                    .font(.title2)
                    .foregroundColor(.gray)
            }''',
            content
        )
        
        return content
    
    def _fix_brackets(self, content: str) -> str:
        """Fix missing or mismatched brackets"""
        # Count brackets
        open_braces = content.count('{')
        close_braces = content.count('}')
        
        if open_braces > close_braces:
            # Add missing closing braces
            content += '\n' + ('}' * (open_braces - close_braces))
        elif close_braces > open_braces:
            # Remove extra closing braces (carefully)
            lines = content.split('\n')
            for i in range(len(lines) - 1, -1, -1):
                if lines[i].strip() == '}' and close_braces > open_braces:
                    lines.pop(i)
                    close_braces -= 1
            content = '\n'.join(lines)
        
        return content
    
    def _fix_undefined_symbol(self, content: str, error_text: str) -> str:
        """Fix undefined symbols"""
        # Extract symbol name from error
        match = re.search(r"'(\w+)'", error_text)
        if match:
            symbol = match.group(1)
            
            # Common fixes for undefined symbols
            fixes = {
                'Timer': 'Foundation',
                'URLSession': 'Foundation',
                'UserDefaults': 'Foundation',
                'NotificationCenter': 'Foundation',
                'Date': 'Foundation',
                'UUID': 'Foundation',
            }
            
            if symbol in fixes:
                content = self._add_import(content, fixes[symbol])
        
        return content
    
    def auto_fix_compilation_errors(self, error_output: str, project_path: str) -> Dict:
        """Main entry point for auto-fixing compilation errors"""
        print("🔧 Auto-fixing compilation errors...")
        
        detected_errors = self.detect_errors(error_output)
        
        if not detected_errors:
            return {
                "success": False,
                "message": "No recognizable errors detected",
                "fixed_count": 0
            }
        
        fixed_count = 0
        sources_dir = os.path.join(project_path, "Sources")
        
        # Try to fix each detected error
        for error_pattern, error_text in detected_errors:
            print(f"🔍 Detected: {error_pattern.description}")
            
            # Apply fix to all Swift files
            if os.path.exists(sources_dir):
                for file_name in os.listdir(sources_dir):
                    if file_name.endswith('.swift'):
                        file_path = os.path.join(sources_dir, file_name)
                        if self.fix_file(file_path, error_pattern, error_text):
                            fixed_count += 1
        
        return {
            "success": fixed_count > 0,
            "message": f"Fixed {fixed_count} errors",
            "fixed_count": fixed_count,
            "history": self.fix_history
        }
    
    def validate_swift_syntax(self, file_path: str) -> bool:
        """Validate Swift syntax before compilation"""
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Basic syntax validation
        checks = [
            ('{', '}', "braces"),
            ('(', ')', "parentheses"),
            ('[', ']', "brackets"),
        ]
        
        for open_char, close_char, name in checks:
            if content.count(open_char) != content.count(close_char):
                print(f"⚠️ Mismatched {name} in {os.path.basename(file_path)}")
                return False
        
        # Check for basic Swift requirements
        if '@main' in content and 'struct' not in content:
            print(f"⚠️ @main without struct in {os.path.basename(file_path)}")
            return False
        
        return True
    
    def generate_fix_report(self) -> str:
        """Generate a report of all fixes applied"""
        if not self.fix_history:
            return "No fixes applied"
        
        report = "📋 Auto-Fix Report\n"
        report += "=" * 40 + "\n"
        
        for fix in self.fix_history:
            report += f"✓ {fix['error']}\n"
            report += f"  File: {os.path.basename(fix['file'])}\n"
            report += f"  Strategy: {fix['fix']}\n\n"
        
        report += f"Total fixes applied: {len(self.fix_history)}"
        return report

# Global instance
error_fixer = SwiftErrorAutoFixer()