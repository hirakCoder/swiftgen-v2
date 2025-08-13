"""
Basic Swift Syntax Validator
Catches simple syntax errors before compilation
"""

import re
from typing import List, Dict, Tuple

class BasicSyntaxValidator:
    """
    Validates basic Swift syntax to catch simple errors early
    """
    
    @staticmethod
    def validate_swift_file(content: str) -> List[Dict]:
        """
        Check for basic syntax errors in Swift code
        Returns list of issues found
        """
        issues = []
        lines = content.split('\n')
        
        # Check for balanced parentheses, brackets, and braces
        paren_count = 0
        bracket_count = 0
        brace_count = 0
        
        for i, line in enumerate(lines, 1):
            # Skip comments
            if line.strip().startswith('//'):
                continue
            
            # Count parentheses
            for char in line:
                if char == '(':
                    paren_count += 1
                elif char == ')':
                    paren_count -= 1
                    if paren_count < 0:
                        issues.append({
                            'line': i,
                            'issue': 'Extra closing parenthesis',
                            'severity': 'error'
                        })
                        paren_count = 0  # Reset to avoid cascading errors
                
                elif char == '[':
                    bracket_count += 1
                elif char == ']':
                    bracket_count -= 1
                    if bracket_count < 0:
                        issues.append({
                            'line': i,
                            'issue': 'Extra closing bracket',
                            'severity': 'error'
                        })
                        bracket_count = 0
                
                elif char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
            
            # Check for orphaned parentheses at the start of a line
            stripped = line.strip()
            if stripped == ')' or (stripped.startswith(')') and not any(c in stripped for c in ['.', ',', ';', '}', ']'])):
                issues.append({
                    'line': i,
                    'issue': 'Orphaned closing parenthesis',
                    'severity': 'error'
                })
            
            # Check for malformed ternary operators (e.g., "condition ?)" without true/false values)
            if '?)' in line and ':' not in line:
                issues.append({
                    'line': i,
                    'issue': 'Malformed ternary operator - missing true/false values',
                    'severity': 'error'
                })
            
            # Check for incomplete ternary on current and next line
            if '?' in line and ':' not in line:
                # Check if colon is on the next line
                if i + 1 < len(lines) and ':' not in lines[i + 1]:
                    issues.append({
                        'line': i,
                        'issue': 'Incomplete ternary operator',
                        'severity': 'error'
                    })
        
        # Check for missing imports
        if 'UINotificationFeedbackGenerator' in content or 'UIImpactFeedbackGenerator' in content:
            if 'import UIKit' not in content:
                issues.append({
                    'line': 0,
                    'issue': 'Missing import UIKit for haptic feedback',
                    'severity': 'error'
                })
        
        if 'Timer' in content and 'AppTimer' not in content:  # Using Timer but not custom AppTimer
            if 'import Foundation' not in content:
                issues.append({
                    'line': 0,
                    'issue': 'Missing import Foundation for Timer',
                    'severity': 'warning'
                })
        
        # Check for common typos
        if '@Enviroment' in content:
            issues.append({
                'line': 0,
                'issue': '@Enviroment should be @Environment',
                'severity': 'error'
            })
        
        if '.forgroundColor' in content or '.forgroundStyle' in content:
            issues.append({
                'line': 0,
                'issue': 'forground should be foreground',
                'severity': 'error'
            })
        
        return issues
    
    @staticmethod
    def fix_basic_issues(content: str, issues: List[Dict]) -> str:
        """
        Attempt to fix basic syntax issues automatically
        """
        lines = content.split('\n')
        
        # First, fix specific LinearGradient/GeometryReader/VStack/HStack/ZStack pattern issue
        # This is a common LLM generation error where closing parenthesis is on wrong line
        view_initializers = ['LinearGradient(', 'GeometryReader', 'VStack', 'HStack', 'ZStack', 
                             'NavigationView', 'ScrollView', 'List(', 'ForEach(', 'Group(']
        
        # Also check for modifier patterns that often have missing closing parentheses
        modifier_patterns = ['.gesture(', '.onTapGesture(', '.sheet(', '.alert(', 
                           '.overlay(', '.background(', '.onChange(', '.onAppear(',
                           '.onDisappear(', '.task(', '.onReceive(']
        
        # First handle modifier patterns with closures (like .gesture)
        # This is CRITICAL for fixing common LLM generation errors
        for i in range(len(lines)):
            # Check for modifiers that start a closure
            for mod in modifier_patterns:
                if mod in lines[i]:
                    # Found a modifier with potential closure
                    # Count all parentheses from this point until we balance or hit another structure
                    open_count = 0
                    close_count = 0
                    closure_end = -1
                    
                    # Start counting from this line
                    for j in range(i, min(i + 50, len(lines))):
                        open_count += lines[j].count('(')
                        close_count += lines[j].count(')')
                        
                        # Look for the end of the closure (usually a line with just whitespace after })
                        # Or when we see another major structure starting
                        if j > i and (
                            ('}' in lines[j] and (j + 1 >= len(lines) or not lines[j + 1].strip() or lines[j + 1].strip().startswith('.'))) or
                            (j > i + 2 and any(struct in lines[j] for struct in ['struct ', 'class ', 'func ', 'var body:']))
                        ):
                            closure_end = j
                            break
                    
                    # If we found unbalanced parentheses
                    if closure_end > 0 and open_count > close_count:
                        # Add the missing closing parenthesis on the line with the closing brace
                        missing = ')' * (open_count - close_count)
                        # If the line ends with }, add the ) after it
                        if lines[closure_end].rstrip().endswith('}'):
                            # Find the indentation of the closing brace
                            indent = len(lines[closure_end]) - len(lines[closure_end].lstrip())
                            lines[closure_end] = lines[closure_end].rstrip() + missing
                        else:
                            # Otherwise add it at the end of the line
                            lines[closure_end] = lines[closure_end].rstrip() + missing
                        break  # Fixed this one, move to next line
        
        for i in range(len(lines)):
            # Check for view initializers that might have misplaced closing parenthesis
            if any(init in lines[i] for init in view_initializers):
                # Look ahead for a line that starts with a dot (SwiftUI modifier)
                # but appears before the closing parenthesis
                for j in range(i + 1, min(i + 15, len(lines))):
                    curr_line = lines[j].strip()
                    
                    # If we find a modifier line (starts with .)
                    if curr_line.startswith('.'):
                        # Count parentheses from start to this point
                        open_count = 0
                        close_count = 0
                        
                        for k in range(i, j):
                            open_count += lines[k].count('(')
                            close_count += lines[k].count(')')
                        
                        # If parentheses are unbalanced, we need to add closing parenthesis
                        if open_count > close_count:
                            # Find the last non-empty, non-blank line before the modifier
                            # This could be either j-1 or earlier if there are blank lines
                            prev_line_idx = j - 1
                            while prev_line_idx > i:
                                # Skip empty lines
                                if not lines[prev_line_idx].strip():
                                    prev_line_idx -= 1
                                    continue
                                    
                                # Found a non-empty line
                                # Check if this line already ends with a closing parenthesis
                                if not lines[prev_line_idx].rstrip().endswith(')'):
                                    # Add the missing closing parenthesis
                                    lines[prev_line_idx] = lines[prev_line_idx].rstrip() + ')'
                                    print(f"[Syntax Validator] Added missing ) after line {prev_line_idx + 1}")
                                break
                            break
        
        for issue in issues:
            if issue['issue'] == 'Orphaned closing parenthesis':
                # Remove the orphaned parenthesis
                line_num = issue['line'] - 1
                if line_num < len(lines):
                    lines[line_num] = lines[line_num].replace(')', '', 1)
            
            elif issue['issue'] == 'Malformed ternary operator - missing true/false values':
                # Fix malformed ternary by completing it
                line_num = issue['line'] - 1
                if line_num < len(lines):
                    line = lines[line_num]
                    # Replace "condition ?)" with complete ternary
                    if '?)' in line:
                        # Extract the condition part
                        parts = line.split('?)')
                        if len(parts) == 2:
                            # Guess reasonable values based on context
                            if 'Color' in line or 'background' in line:
                                lines[line_num] = parts[0] + '? .blue : .gray)' + parts[1]
                            elif 'opacity' in line:
                                lines[line_num] = parts[0] + '? 1.0 : 0.5)' + parts[1]
                            else:
                                lines[line_num] = parts[0] + '? true : false)' + parts[1]
            
            elif issue['issue'] == 'Missing import UIKit for haptic feedback':
                # Add UIKit import after SwiftUI import
                for i, line in enumerate(lines):
                    if 'import SwiftUI' in line:
                        lines.insert(i + 1, 'import UIKit')
                        break
            
            elif issue['issue'] == '@Enviroment should be @Environment':
                content = '\n'.join(lines)
                content = content.replace('@Enviroment', '@Environment')
                lines = content.split('\n')
            
            elif 'forground should be foreground' in issue['issue']:
                content = '\n'.join(lines)
                content = content.replace('.forgroundColor', '.foregroundColor')
                content = content.replace('.forgroundStyle', '.foregroundStyle')
                lines = content.split('\n')
        
        return '\n'.join(lines)

def validate_and_fix_swift(content: str) -> Tuple[str, List[Dict]]:
    """
    Validate and fix basic Swift syntax issues
    Returns: (fixed_content, issues_found)
    """
    import time
    start = time.time()
    
    validator = BasicSyntaxValidator()
    issues = validator.validate_swift_file(content)
    
    elapsed = time.time() - start
    
    # ALWAYS run fix_basic_issues to catch LinearGradient and other structural issues
    # that may not be detected by validate_swift_file
    fixed_content = validator.fix_basic_issues(content, issues)
    
    if issues:
        print(f"[Syntax Validator] Found {len(issues)} syntax issues in {elapsed*1000:.1f}ms")
        for issue in issues:
            print(f"  Line {issue['line']}: {issue['issue']} ({issue['severity']})")
    
    # Check if content changed even without detected issues
    if fixed_content != content:
        if not issues:
            print(f"[Syntax Validator] Applied structural fixes in {elapsed*1000:.1f}ms")
        
        # Validate again to see if fixes worked
        remaining_issues = validator.validate_swift_file(fixed_content)
        
        if issues and len(remaining_issues) < len(issues):
            print(f"[Syntax Validator] Fixed {len(issues) - len(remaining_issues)} issues")
        
        return fixed_content, remaining_issues
        
    return content, issues