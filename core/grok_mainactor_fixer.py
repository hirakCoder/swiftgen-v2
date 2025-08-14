"""
Grok @MainActor Fixer
Fixes common async/await and @MainActor issues in Grok-generated Swift code
"""

import re
from typing import Tuple, List
from pathlib import Path

class GrokMainActorFixer:
    """Fixes @MainActor and async/await issues specific to Grok's code generation"""
    
    def __init__(self):
        self.fixes_applied = 0
        
    def fix_file(self, file_path: str) -> Tuple[bool, str, List[str]]:
        """Fix @MainActor issues in a Swift file"""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            original = content
            errors_fixed = []
            
            # Fix 1: Timer.scheduledTimer callbacks need @MainActor
            content, count = self._fix_timer_callbacks(content)
            if count > 0:
                errors_fixed.append(f"Fixed {count} timer callback @MainActor issues")
            
            # Fix 2: Methods calling @MainActor methods need to be async or @MainActor
            content, count = self._fix_mainactor_calls(content)
            if count > 0:
                errors_fixed.append(f"Fixed {count} @MainActor method call issues")
            
            # Fix 3: @Published updates must be on main thread
            content, count = self._fix_published_updates(content)
            if count > 0:
                errors_fixed.append(f"Fixed {count} @Published update issues")
            
            # Fix 4: View model methods should be @MainActor
            content, count = self._fix_viewmodel_methods(content)
            if count > 0:
                errors_fixed.append(f"Fixed {count} ViewModel method issues")
            
            # Write back if changed
            if content != original:
                with open(file_path, 'w') as f:
                    f.write(content)
                self.fixes_applied += len(errors_fixed)
                return True, content, errors_fixed
                
            return True, content, []
            
        except Exception as e:
            return False, "", [f"Error processing file: {str(e)}"]
    
    def _fix_timer_callbacks(self, content: str) -> Tuple[str, int]:
        """Fix Timer.scheduledTimer callbacks to handle @MainActor properly"""
        fixes = 0
        
        # Pattern 1: Timer with closure that calls @MainActor methods
        pattern = r'(Timer\.scheduledTimer\(.*?\)\s*\{[^}]*\})'
        
        def fix_timer(match):
            nonlocal fixes
            timer_code = match.group(1)
            
            # If it contains method calls that might be @MainActor
            if 'self?' in timer_code or 'self.' in timer_code:
                # Wrap the closure content with Task { @MainActor in
                if 'Task {' not in timer_code:
                    # Extract the closure body
                    closure_pattern = r'(\{)([^}]+)(\})'
                    def wrap_closure(m):
                        return f"{{ _ in\n            Task {{ @MainActor in\n{m.group(2)}\n            }}\n        }}"
                    
                    new_timer = re.sub(closure_pattern, wrap_closure, timer_code, count=1)
                    if new_timer != timer_code:
                        fixes += 1
                        return new_timer
            
            return timer_code
        
        content = re.sub(pattern, fix_timer, content, flags=re.DOTALL)
        return content, fixes
    
    def _fix_mainactor_calls(self, content: str) -> Tuple[str, int]:
        """Fix methods that call @MainActor methods"""
        fixes = 0
        lines = content.split('\n')
        fixed_lines = []
        
        in_class = False
        class_is_mainactor = False
        
        for i, line in enumerate(lines):
            # Check if we're entering a class
            if '@MainActor' in line:
                class_is_mainactor = True
            elif 'class ' in line and 'ViewModel' in line:
                in_class = True
                if not class_is_mainactor and '@MainActor' not in lines[max(0, i-1)]:
                    # Add @MainActor to ViewModels
                    fixed_lines.append('@MainActor')
                    fixes += 1
            
            # Fix methods that should be async
            if in_class and 'func ' in line and 'private func' in line:
                # Check if this method calls other methods (likely @MainActor)
                if i + 5 < len(lines):
                    next_few_lines = '\n'.join(lines[i:i+5])
                    if ('stopTimer()' in next_few_lines or 
                        'startTimer()' in next_few_lines or
                        'reset' in next_few_lines):
                        if 'async' not in line and '@MainActor' not in line:
                            # Make it async
                            line = line.replace('func ', 'func ', 1)
                            if 'private func' in line:
                                line = line.replace('private func', '@MainActor private func')
                                fixes += 1
            
            fixed_lines.append(line)
            
            # Reset when leaving class
            if in_class and line.strip() == '}' and not any('{' in l for l in lines[i+1:i+3] if i+3 < len(lines)):
                in_class = False
                class_is_mainactor = False
        
        return '\n'.join(fixed_lines), fixes
    
    def _fix_published_updates(self, content: str) -> Tuple[str, int]:
        """Ensure @Published properties are updated on main thread"""
        fixes = 0
        
        # Find @Published property updates not wrapped in MainActor
        pattern = r'(\s+)(self\.)?(\w+)\s*=\s*([^;\n]+)(?=\n)'
        
        def check_published_update(match):
            nonlocal fixes
            indent = match.group(1)
            self_ref = match.group(2) or ''
            property_name = match.group(3)
            value = match.group(4)
            
            # Check if this property is likely @Published
            if property_name in ['timeRemaining', 'isRunning', 'progress', 'count', 'selectedDuration']:
                # Check if we're already in a MainActor context
                line_start = content.rfind('\n', 0, match.start()) + 1
                line = content[line_start:match.start()]
                
                # If not in Task { @MainActor or DispatchQueue.main
                if 'Task { @MainActor' not in content[max(0, match.start()-200):match.start()]:
                    if 'Timer.scheduledTimer' in content[max(0, match.start()-500):match.start()]:
                        # We're in a timer callback, need MainActor
                        fixes += 1
                        return f'{indent}Task {{ @MainActor in\n{indent}    {self_ref}{property_name} = {value}\n{indent}}}'
            
            return match.group(0)
        
        # Only apply in specific contexts
        if 'Timer.scheduledTimer' in content:
            content = re.sub(pattern, check_published_update, content)
        
        return content, fixes
    
    def _fix_viewmodel_methods(self, content: str) -> Tuple[str, int]:
        """Ensure ViewModel methods are properly marked with @MainActor"""
        fixes = 0
        
        # If it's a ViewModel file
        if 'ViewModel' in content and 'ObservableObject' in content:
            # Check if class is marked with @MainActor
            if '@MainActor\nclass' not in content and '@MainActor class' not in content:
                # Add @MainActor to the class
                content = re.sub(
                    r'(class\s+\w+ViewModel\s*:\s*ObservableObject)',
                    r'@MainActor\n\1',
                    content,
                    count=1
                )
                fixes += 1
        
        return content, fixes
    
    def fix_project(self, project_path: str) -> Tuple[bool, List[str]]:
        """Fix all Swift files in a project"""
        project_path = Path(project_path)
        all_errors = []
        
        # Find all Swift files
        swift_files = list(project_path.rglob("*.swift"))
        
        for swift_file in swift_files:
            # Focus on ViewModel files for Grok issues
            if 'ViewModel' in swift_file.name or 'Model' in swift_file.name:
                success, _, errors = self.fix_file(str(swift_file))
                if errors:
                    all_errors.extend([f"{swift_file.name}: {e}" for e in errors])
        
        return len(all_errors) == 0, all_errors

# Integration function for the pipeline
def fix_grok_mainactor_issues(project_path: str) -> bool:
    """Quick function to fix Grok @MainActor issues"""
    fixer = GrokMainActorFixer()
    success, errors = fixer.fix_project(project_path)
    
    if fixer.fixes_applied > 0:
        print(f"[Grok Fixer] Applied {fixer.fixes_applied} @MainActor fixes")
    
    return success