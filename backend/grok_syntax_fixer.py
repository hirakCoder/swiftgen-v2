"""
Grok Swift Syntax Fixer
Fixes common Swift syntax issues in Grok-generated code
"""

import re
import logging

logger = logging.getLogger(__name__)

class GrokSyntaxFixer:
    """Fix Grok-specific Swift syntax issues"""
    
    @staticmethod
    def fix_swift_syntax(content: str) -> tuple[str, int]:
        """Fix common Swift syntax issues from Grok"""
        
        fixes_applied = 0
        original = content
        
        # Fix 1: Unclosed .overlay() calls
        # Pattern: .overlay(\n    RoundedRectangle...\n) without closing paren
        lines = content.split('\n')
        fixed_lines = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # Check for .overlay( pattern
            if '.overlay(' in line:
                # Count parentheses in this line
                open_count = line.count('(')
                close_count = line.count(')')
                
                if open_count > close_count:
                    # Look ahead to find where to close
                    j = i + 1
                    indent_level = len(line) - len(line.lstrip())
                    found_content = False
                    
                    while j < len(lines):
                        next_line = lines[j]
                        next_indent = len(next_line) - len(next_line.lstrip())
                        
                        # Track parentheses
                        open_count += next_line.count('(')
                        close_count += next_line.count(')')
                        
                        # Check if this line has content
                        if next_line.strip() and not next_line.strip().startswith(')'):
                            found_content = True
                        
                        # If we're back at same or lower indent and have content
                        if found_content and next_indent <= indent_level:
                            # Check if we need to add closing paren
                            if open_count > close_count:
                                # Add closing paren to previous line
                                if j > i + 1:
                                    lines[j-1] = lines[j-1] + ')'
                                    fixes_applied += 1
                                    logger.info(f"[GROK FIX] Added closing paren after line {j-1}")
                                break
                        
                        # If we hit a closing brace or another method, close here
                        if next_line.strip() in ['}', '})'] or next_line.strip().startswith('.'):
                            if open_count > close_count:
                                lines[j-1] = lines[j-1] + ')'
                                fixes_applied += 1
                                logger.info(f"[GROK FIX] Added closing paren before line {j}")
                            break
                        
                        j += 1
                    
                    # If we reached end and still unclosed
                    if j >= len(lines) and open_count > close_count:
                        lines[-1] = lines[-1] + ')'
                        fixes_applied += 1
            
            fixed_lines.append(lines[i])
            i += 1
        
        content = '\n'.join(fixed_lines)
        
        # Fix 2: Empty .rotation3DEffect() calls
        # Pattern: .rotation3DEffect() without parameters
        pattern = r'\.rotation3DEffect\(\s*\)'
        if re.search(pattern, content):
            # Add default parameters
            content = re.sub(
                pattern,
                '.rotation3DEffect(.degrees(0), axis: (x: 0, y: 0, z: 1))',
                content
            )
            fixes_applied += 1
            logger.info("[GROK FIX] Fixed empty rotation3DEffect call")
        
        # Fix 3: Broken multiline method calls
        # Pattern: method call split incorrectly
        pattern = r'\.rotation3DEffect\(\)\s*\n\s*\.(degrees|angle)'
        if re.search(pattern, content):
            # This is a broken call, fix it
            content = re.sub(
                r'\.rotation3DEffect\(\)\s*\n\s*\.degrees\(([^)]+)\),\s*\n\s*axis:([^)]+)\)',
                r'.rotation3DEffect(.degrees(\1), axis:\2)',
                content
            )
            fixes_applied += 1
            logger.info("[GROK FIX] Fixed broken rotation3DEffect syntax")
        
        # Fix 4: Missing closing parentheses at end of closures
        # Pattern: }) at end but missing )
        lines = content.split('\n')
        fixed_lines = []
        
        for i, line in enumerate(lines):
            if line.strip() == '})' or line.strip().endswith('})'):
                # Check if we need more closing parens
                # Count all delimiters up to this point
                all_prev = '\n'.join(lines[:i+1])
                open_parens = all_prev.count('(')
                close_parens = all_prev.count(')')
                
                if open_parens > close_parens:
                    # Add missing parens
                    missing = open_parens - close_parens
                    line = line.replace('})', '})' + ')' * missing)
                    fixes_applied += missing
                    logger.info(f"[GROK FIX] Added {missing} closing parens at line {i+1}")
            
            fixed_lines.append(line)
        
        content = '\n'.join(fixed_lines)
        
        # Fix 5: Check overall delimiter balance
        final_check = {
            '(': content.count('('),
            ')': content.count(')'),
            '{': content.count('{'),
            '}': content.count('}'),
            '[': content.count('['),
            ']': content.count(']')
        }
        
        # Add missing closing delimiters at the end if needed
        if final_check['('] > final_check[')']:
            missing = final_check['('] - final_check[')']
            content += ')' * missing
            fixes_applied += missing
            logger.info(f"[GROK FIX] Added {missing} closing parens at end")
        
        if final_check['{'] > final_check['}']:
            missing = final_check['{'] - final_check['}']
            content += '}' * missing
            fixes_applied += missing
            logger.info(f"[GROK FIX] Added {missing} closing braces at end")
        
        if final_check['['] > final_check[']']:
            missing = final_check['['] - final_check[']']
            content += ']' * missing
            fixes_applied += missing
            logger.info(f"[GROK FIX] Added {missing} closing brackets at end")
        
        if fixes_applied > 0:
            logger.info(f"[GROK FIX] Applied {fixes_applied} fixes to Swift code")
        
        return content, fixes_applied
    
    @staticmethod
    def validate_and_fix_files(files: list) -> list:
        """Validate and fix all Swift files from Grok"""
        
        fixed_files = []
        total_fixes = 0
        
        for file_info in files:
            if file_info['path'].endswith('.swift'):
                content = file_info['content']
                fixed_content, fixes = GrokSyntaxFixer.fix_swift_syntax(content)
                total_fixes += fixes
                
                fixed_files.append({
                    'path': file_info['path'],
                    'content': fixed_content
                })
            else:
                fixed_files.append(file_info)
        
        if total_fixes > 0:
            logger.info(f"[GROK FIX] Total fixes applied across all files: {total_fixes}")
        
        return fixed_files