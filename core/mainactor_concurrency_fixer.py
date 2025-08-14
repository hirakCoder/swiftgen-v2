"""
MainActor Concurrency Fixer - Fixes Swift 6 concurrency issues
Specifically handles Timer and async closure issues with MainActor isolation
"""

import re
from typing import Tuple, List

class MainActorConcurrencyFixer:
    """
    Fixes MainActor isolation issues in Swift code
    Common with Timer.scheduledTimer and other async operations
    """
    
    @staticmethod
    def fix_timer_mainactor_issues(content: str) -> Tuple[str, int]:
        """
        Fix Timer closures that violate MainActor isolation
        """
        fixes_applied = 0
        lines = content.split('\n')
        fixed_lines = []
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Pattern 1: Timer.scheduledTimer with property mutations
            if 'Timer.scheduledTimer' in line:
                # Look ahead to find the closure
                timer_block = [line]
                j = i + 1
                brace_count = line.count('{') - line.count('}')
                
                # Collect the entire timer block
                while j < len(lines) and brace_count > 0:
                    next_line = lines[j]
                    timer_block.append(next_line)
                    brace_count += next_line.count('{') - next_line.count('}')
                    j += 1
                
                # Check if there are property mutations in the closure
                timer_content = '\n'.join(timer_block)
                if re.search(r'self\?\.\w+\s*[+\-*/]?=', timer_content) or \
                   re.search(r'self\.\w+\s*[+\-*/]?=', timer_content):
                    # Wrap mutations in Task { @MainActor in }
                    fixed_timer_block = MainActorConcurrencyFixer._wrap_timer_mutations(timer_block)
                    fixed_lines.extend(fixed_timer_block)
                    fixes_applied += 1
                    print(f"[MainActor Fixer] Fixed Timer MainActor issue at line {i+1}")
                    i = j
                    continue
            
            # Pattern 2: Direct Timer() usage with closures
            if 'Timer(' in line and 'TimeInterval' in line:
                # Similar fix as above
                timer_block = [line]
                j = i + 1
                brace_count = line.count('{') - line.count('}')
                
                while j < len(lines) and brace_count > 0:
                    next_line = lines[j]
                    timer_block.append(next_line)
                    brace_count += next_line.count('{') - next_line.count('}')
                    j += 1
                
                timer_content = '\n'.join(timer_block)
                if 'self.' in timer_content or 'self?' in timer_content:
                    fixed_timer_block = MainActorConcurrencyFixer._wrap_timer_mutations(timer_block)
                    fixed_lines.extend(fixed_timer_block)
                    fixes_applied += 1
                    print(f"[MainActor Fixer] Fixed Timer constructor at line {i+1}")
                    i = j
                    continue
            
            fixed_lines.append(line)
            i += 1
        
        return '\n'.join(fixed_lines), fixes_applied
    
    @staticmethod
    def _wrap_timer_mutations(timer_block: List[str]) -> List[str]:
        """
        Wrap property mutations in Task { @MainActor in }
        """
        fixed_block = []
        
        for i, line in enumerate(timer_block):
            # Check if this line has a property mutation
            if re.search(r'self\?\.\w+\s*[+\-*/]?=', line) or \
               re.search(r'self\.\w+\s*[+\-*/]?=', line):
                # Get indentation
                indent = len(line) - len(line.lstrip())
                spaces = ' ' * indent
                
                # Check if already wrapped in Task
                if i > 0 and 'Task' in timer_block[i-1]:
                    fixed_block.append(line)
                else:
                    # Wrap in Task { @MainActor in }
                    fixed_block.append(f"{spaces}Task {{ @MainActor in")
                    fixed_block.append(f"    {line}")
                    fixed_block.append(f"{spaces}}}")
            else:
                fixed_block.append(line)
        
        return fixed_block
    
    @staticmethod
    def fix_observable_object_issues(content: str) -> Tuple[str, int]:
        """
        Fix ObservableObject class issues with MainActor
        """
        fixes_applied = 0
        
        # Pattern: class ViewModel: ObservableObject without @MainActor
        pattern = r'^(class\s+\w+\s*:\s*ObservableObject)'
        
        lines = content.split('\n')
        fixed_lines = []
        
        for i, line in enumerate(lines):
            if re.match(pattern, line):
                # Check if @MainActor already exists in previous lines
                has_mainactor = False
                for j in range(max(0, i-3), i):
                    if '@MainActor' in lines[j]:
                        has_mainactor = True
                        break
                
                if not has_mainactor:
                    # Add @MainActor before the class
                    fixed_lines.append('@MainActor')
                    fixed_lines.append(line)
                    fixes_applied += 1
                    print(f"[MainActor Fixer] Added @MainActor to ObservableObject at line {i+1}")
                else:
                    fixed_lines.append(line)
            else:
                fixed_lines.append(line)
        
        return '\n'.join(fixed_lines), fixes_applied
    
    @staticmethod
    def fix_file(file_path: str) -> bool:
        """
        Apply all MainActor fixes to a file
        """
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Apply timer fixes
            content, timer_fixes = MainActorConcurrencyFixer.fix_timer_mainactor_issues(content)
            
            # Apply ObservableObject fixes
            content, observable_fixes = MainActorConcurrencyFixer.fix_observable_object_issues(content)
            
            total_fixes = timer_fixes + observable_fixes
            
            if total_fixes > 0:
                with open(file_path, 'w') as f:
                    f.write(content)
                print(f"[MainActor Fixer] Applied {total_fixes} concurrency fixes to {file_path}")
                return True
            
            return False
            
        except Exception as e:
            print(f"[MainActor Fixer] Error processing {file_path}: {e}")
            return False
    
    @staticmethod
    def detect_issues(content: str) -> List[str]:
        """
        Detect potential MainActor isolation issues
        """
        issues = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            # Timer with self mutations
            if 'Timer.scheduledTimer' in line:
                # Look for self mutations in next few lines
                for j in range(i, min(i+10, len(lines))):
                    if 'self.' in lines[j] and '=' in lines[j]:
                        issues.append(f"Line {j}: Potential MainActor violation in Timer closure")
                        break
            
            # ObservableObject without MainActor
            if re.match(r'^class\s+\w+\s*:\s*ObservableObject', line):
                if i > 0 and '@MainActor' not in lines[i-2:i]:
                    issues.append(f"Line {i}: ObservableObject class should have @MainActor")
        
        return issues