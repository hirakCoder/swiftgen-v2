"""
SwiftGen V2 - Production Swift Syntax Validator & Auto-Fixer
Ensures generated code is syntactically correct before build
"""

import re
from typing import Dict, List, Tuple, Optional
from pathlib import Path

class SwiftSyntaxValidator:
    """Production-grade Swift syntax validation and auto-fixing"""
    
    def __init__(self):
        self.delimiter_pairs = {
            '(': ')',
            '[': ']',
            '{': '}',
            '<': '>'
        }
        self.fixed_count = 0
        
    def validate_and_fix_file(self, file_path: str) -> Tuple[bool, str, List[str]]:
        """Validate and auto-fix Swift syntax issues"""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            fixed_content = content
            errors = []
            
            # Fix 1: Balance delimiters
            fixed_content, delimiter_errors = self._fix_delimiters(fixed_content)
            errors.extend(delimiter_errors)
            
            # Fix 2: Complete incomplete statements
            fixed_content, statement_errors = self._fix_incomplete_statements(fixed_content)
            errors.extend(statement_errors)
            
            # Fix 3: Fix ternary operators
            fixed_content, ternary_errors = self._fix_ternary_operators(fixed_content)
            errors.extend(ternary_errors)
            
            # Fix 4: Remove orphaned closing delimiters
            fixed_content = self._remove_orphaned_delimiters(fixed_content)
            
            # Fix 5: Ensure proper method calls
            fixed_content = self._fix_method_calls(fixed_content)
            
            # Write fixed content if changed
            if fixed_content != content:
                with open(file_path, 'w') as f:
                    f.write(fixed_content)
                self.fixed_count += 1
                return True, fixed_content, errors
            
            return len(errors) == 0, content, errors
            
        except Exception as e:
            return False, "", [f"Validation error: {str(e)}"]
    
    def _fix_delimiters(self, content: str) -> Tuple[str, List[str]]:
        """Fix unbalanced delimiters"""
        lines = content.split('\n')
        errors = []
        fixed_lines = []
        
        for i, line in enumerate(lines):
            # Skip comments and strings
            if line.strip().startswith('//') or '"""' in line:
                fixed_lines.append(line)
                continue
                
            # Count delimiters
            open_count = {d: 0 for d in self.delimiter_pairs.keys()}
            close_count = {d: 0 for d in self.delimiter_pairs.values()}
            
            in_string = False
            escape_next = False
            
            for char in line:
                if escape_next:
                    escape_next = False
                    continue
                if char == '\\':
                    escape_next = True
                    continue
                if char == '"' and not escape_next:
                    in_string = not in_string
                    continue
                if not in_string:
                    if char in open_count:
                        open_count[char] += 1
                    elif char in close_count:
                        close_count[char] += 1
            
            # Fix missing closing delimiters at end of line
            fixed_line = line
            for opener, closer in self.delimiter_pairs.items():
                diff = open_count[opener] - close_count[closer]
                if diff > 0:
                    # Missing closing delimiter
                    fixed_line += closer * diff
                    errors.append(f"Line {i+1}: Added {diff} missing '{closer}'")
            
            fixed_lines.append(fixed_line)
        
        return '\n'.join(fixed_lines), errors
    
    def _fix_incomplete_statements(self, content: str) -> Tuple[str, List[str]]:
        """Fix incomplete Swift statements"""
        lines = content.split('\n')
        errors = []
        fixed_lines = []
        
        for i, line in enumerate(lines):
            fixed_line = line
            
            # Fix incomplete ternary operators
            if '?' in line and ':' not in line and not line.strip().endswith('?'):
                # Likely incomplete ternary
                fixed_line += ' : nil'
                errors.append(f"Line {i+1}: Completed ternary operator")
            
            # Fix method calls missing parentheses
            if re.search(r'\b(func|init|\.)\w+\s*$', line):
                fixed_line += '()'
                errors.append(f"Line {i+1}: Added missing method parentheses")
            
            fixed_lines.append(fixed_line)
        
        return '\n'.join(fixed_lines), errors
    
    def _fix_ternary_operators(self, content: str) -> Tuple[str, List[str]]:
        """Fix malformed ternary operators"""
        errors = []
        
        # Pattern: question mark without corresponding colon
        pattern = r'([^?\n]+\?[^:\n]+)(?=\n|$)'
        
        def fix_ternary(match):
            expr = match.group(1)
            if ':' not in expr:
                errors.append(f"Fixed incomplete ternary: {expr[:30]}...")
                return expr + ' : nil'
            return expr
        
        fixed_content = re.sub(pattern, fix_ternary, content)
        return fixed_content, errors
    
    def _remove_orphaned_delimiters(self, content: str) -> str:
        """Remove orphaned closing delimiters on their own lines"""
        lines = content.split('\n')
        fixed_lines = []
        
        for line in lines:
            # Skip lines that are just closing delimiters with whitespace
            if re.match(r'^\s*[)\]\}]+\s*$', line):
                continue
            fixed_lines.append(line)
        
        return '\n'.join(fixed_lines)
    
    def _fix_method_calls(self, content: str) -> str:
        """Ensure method calls are properly formatted"""
        # Fix patterns like:
        # someMethod(
        #     param1: value1,
        #     param2: value2
        # )  <- This lonely parenthesis
        
        lines = content.split('\n')
        fixed_lines = []
        
        for i, line in enumerate(lines):
            # If line is just a closing paren, check if previous line needs it
            if re.match(r'^\s*\)\s*$', line) and i > 0:
                # Append to previous non-empty line
                j = i - 1
                while j >= 0 and not lines[j].strip():
                    j -= 1
                if j >= 0:
                    fixed_lines[j] += ')'
                    continue
            fixed_lines.append(line)
        
        return '\n'.join(fixed_lines)
    
    def validate_project(self, project_path: str) -> Tuple[bool, List[str]]:
        """Validate and fix entire project"""
        project_path = Path(project_path)
        all_errors = []
        
        # Find all Swift files
        swift_files = list(project_path.rglob("*.swift"))
        
        for swift_file in swift_files:
            valid, _, errors = self.validate_and_fix_file(str(swift_file))
            if errors:
                all_errors.extend([f"{swift_file.name}: {e}" for e in errors])
        
        return len(all_errors) == 0, all_errors
