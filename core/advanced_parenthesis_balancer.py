"""
Advanced Parenthesis Balancer - Intelligently fixes missing parentheses in Swift code
Uses context-aware parsing to fix function calls with missing closing parentheses
"""

import re
from typing import List, Tuple, Optional

class AdvancedParenthesisBalancer:
    """
    Fixes missing parentheses in function calls by understanding Swift syntax
    Unlike simple bracket counting, this understands the structure of Swift code
    """
    
    @staticmethod
    def fix_code(content: str) -> Tuple[str, int]:
        """
        Fix missing parentheses in Swift code
        Returns: (fixed_content, number_of_fixes)
        """
        lines = content.split('\n')
        fixes_applied = 0
        fixed_lines = []
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Pattern 1: Function call with parameters ending with a closure
            # Example: TimerButton(title: "x", color: .red { // Missing )
            if '(' in line and '{' in line and ')' not in line[line.index('('):line.index('{')]:
                # Check if this looks like a function call
                func_pattern = r'(\w+)\s*\([^)]*\s*\{'
                if re.search(func_pattern, line):
                    # Find where to insert the closing paren
                    brace_pos = line.index('{')
                    # Insert ) before {
                    fixed_line = line[:brace_pos].rstrip() + ')' + line[brace_pos:]
                    fixed_lines.append(fixed_line)
                    fixes_applied += 1
                    print(f"[Parenthesis Balancer] Fixed missing ) before {{ on line {i+1}")
                    i += 1
                    continue
            
            # Pattern 1b: Malformed Button(action:){ pattern
            # Should be Button(action: {
            malformed_button = r'Button\(action:\)\s*\{'
            if re.search(malformed_button, line):
                fixed_line = re.sub(r'Button\(action:\)\s*\{', 'Button(action: {', line)
                fixed_lines.append(fixed_line)
                fixes_applied += 1
                print(f"[Parenthesis Balancer] Fixed malformed Button(action:) on line {i+1}")
                i += 1
                continue
            
            # Pattern 1c: Extra }) that should just be }
            # Common when LLMs generate malformed button closures
            if line.strip() == '})' and i > 0:
                # Check if previous lines indicate this is a closure ending
                prev_lines = '\n'.join(lines[max(0, i-5):i])
                if 'Button(action:' in prev_lines or 'Button {' in prev_lines:
                    # This is likely an extra paren
                    fixed_lines.append(line.replace('})', '}'))
                    fixes_applied += 1
                    print(f"[Parenthesis Balancer] Removed extra ) from }} on line {i+1}")
                    i += 1
                    continue
            
            # Pattern 2: Multi-line function call with missing closing paren
            # Detect function calls that span multiple lines
            if re.match(r'\s*\w+\s*\($', line.strip()):
                # This is a function call opening
                func_name = re.match(r'\s*(\w+)\s*\($', line.strip()).group(1)
                open_parens = 1
                close_parens = 0
                func_lines = [line]
                j = i + 1
                
                # Scan ahead to find the matching structure
                while j < len(lines) and open_parens > close_parens:
                    next_line = lines[j]
                    func_lines.append(next_line)
                    
                    # Count parentheses
                    open_parens += next_line.count('(')
                    close_parens += next_line.count(')')
                    
                    # Check if we hit a closure opening without closing the function
                    if '{' in next_line and open_parens > close_parens:
                        # Check if the previous line might be missing a )
                        if j > i + 1:
                            prev_line = func_lines[-2]
                            # If previous line ends with a parameter, add )
                            if re.search(r':\s*\.\w+\s*$', prev_line) or \
                               re.search(r':\s*\w+\s*$', prev_line) or \
                               re.search(r':\s*"[^"]+"\s*$', prev_line):
                                # Add closing paren to previous line
                                func_lines[-2] = prev_line.rstrip() + ')'
                                fixes_applied += 1
                                close_parens += 1
                                print(f"[Parenthesis Balancer] Added missing ) on line {i+j}")
                        # Or if current line starts with {
                        elif next_line.strip().startswith('{'):
                            # Insert ) at the end of previous line
                            func_lines[-2] = func_lines[-2].rstrip() + ')'
                            fixes_applied += 1
                            close_parens += 1
                            print(f"[Parenthesis Balancer] Added ) before {{ on line {i+j}")
                    j += 1
                
                # Add all the processed lines
                fixed_lines.extend(func_lines)
                i = j
                continue
            
            # Pattern 3: Ternary operator followed by closure without closing paren
            # Example: color: isRunning ? .red : .green {
            ternary_pattern = r'(\w+:\s*\w+\s*\?\s*\.\w+\s*:\s*\.\w+)\s*\{'
            match = re.search(ternary_pattern, line)
            if match:
                # Insert ) before {
                fixed_line = re.sub(ternary_pattern, r'\1) {', line)
                fixed_lines.append(fixed_line)
                fixes_applied += 1
                print(f"[Parenthesis Balancer] Fixed ternary+closure on line {i+1}")
                i += 1
                continue
            
            # No fixes needed for this line
            fixed_lines.append(line)
            i += 1
        
        return '\n'.join(fixed_lines), fixes_applied
    
    @staticmethod
    def balance_file(file_path: str) -> bool:
        """
        Balance parentheses in a Swift file
        Returns True if fixes were applied
        """
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            fixed_content, fixes = AdvancedParenthesisBalancer.fix_code(content)
            
            if fixes > 0:
                with open(file_path, 'w') as f:
                    f.write(fixed_content)
                print(f"[Parenthesis Balancer] Applied {fixes} fixes to {file_path}")
                return True
            
            return False
        except Exception as e:
            print(f"[Parenthesis Balancer] Error processing {file_path}: {e}")
            return False
    
    @staticmethod
    def validate_balance(content: str) -> List[str]:
        """
        Validate if parentheses are balanced and return issues
        """
        issues = []
        lines = content.split('\n')
        
        # Track overall balance
        paren_stack = []
        brace_stack = []
        bracket_stack = []
        
        for i, line in enumerate(lines, 1):
            for char in line:
                if char == '(':
                    paren_stack.append(i)
                elif char == ')':
                    if not paren_stack:
                        issues.append(f"Line {i}: Unmatched closing parenthesis")
                    else:
                        paren_stack.pop()
                elif char == '{':
                    brace_stack.append(i)
                elif char == '}':
                    if not brace_stack:
                        issues.append(f"Line {i}: Unmatched closing brace")
                    else:
                        brace_stack.pop()
                elif char == '[':
                    bracket_stack.append(i)
                elif char == ']':
                    if not bracket_stack:
                        issues.append(f"Line {i}: Unmatched closing bracket")
                    else:
                        bracket_stack.pop()
        
        # Report unclosed delimiters
        if paren_stack:
            issues.append(f"Unclosed parentheses starting at lines: {paren_stack[:5]}")
        if brace_stack:
            issues.append(f"Unclosed braces starting at lines: {brace_stack[:5]}")
        if bracket_stack:
            issues.append(f"Unclosed brackets starting at lines: {bracket_stack[:5]}")
        
        return issues