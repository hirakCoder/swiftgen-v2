"""
MainActor Isolation Fixer
Fixes actor isolation errors in Swift code
"""

import re
import os

def fix_mainactor_issues(error_output: str, project_path: str) -> dict:
    """
    Fix @MainActor isolation issues in Swift code
    
    Common patterns:
    1. Timer callbacks updating UI state
    2. Async methods calling UI updates
    3. ObservableObject methods modifying @Published properties
    """
    
    fixes_applied = []
    
    # Pattern 1: updateTimer() and similar UI update methods
    timer_pattern = r"instance method '(\w+)\(\)' .* outside of its actor context"
    matches = re.findall(timer_pattern, error_output)
    
    for method_name in matches:
        # Find and fix the method
        sources_dir = os.path.join(project_path, "Sources")
        for root, dirs, files in os.walk(sources_dir):
            for file in files:
                if file.endswith('.swift'):
                    filepath = os.path.join(root, file)
                    with open(filepath, 'r') as f:
                        content = f.read()
                    
                    # Check if this file has the method
                    if f"func {method_name}()" in content or f"private func {method_name}()" in content:
                        original = content
                        
                        # Add @MainActor to the method
                        # Pattern: private func methodName() {
                        content = re.sub(
                            f"(private )?func {method_name}\\(\\)",
                            f"@MainActor \\1func {method_name}()",
                            content
                        )
                        
                        # Also check if class needs @MainActor
                        if "class " in content and "@MainActor" not in content:
                            # Add @MainActor to the class if it's an ObservableObject
                            if "ObservableObject" in content:
                                content = re.sub(
                                    r"(class \w+.*ObservableObject)",
                                    r"@MainActor \1",
                                    content
                                )
                        
                        if content != original:
                            with open(filepath, 'w') as f:
                                f.write(content)
                            fixes_applied.append(f"Added @MainActor to {method_name} in {os.path.basename(filepath)}")
    
    # Pattern 2: Timer.scheduledTimer callbacks
    if "Timer.scheduledTimer" in error_output and "actor" in error_output:
        sources_dir = os.path.join(project_path, "Sources")
        for root, dirs, files in os.walk(sources_dir):
            for file in files:
                if file.endswith('.swift'):
                    filepath = os.path.join(root, file)
                    with open(filepath, 'r') as f:
                        content = f.read()
                    
                    if "Timer.scheduledTimer" in content:
                        original = content
                        
                        # Wrap timer callback in MainActor.run
                        content = re.sub(
                            r'Timer\.scheduledTimer\(withTimeInterval: ([^,]+), repeats: ([^)]+)\) \{ \[weak self\] _ in\s+self\?\.(\w+)\(\)',
                            r'Timer.scheduledTimer(withTimeInterval: \1, repeats: \2) { [weak self] _ in\n            Task { @MainActor in\n                self?.\3()\n            }',
                            content
                        )
                        
                        if content != original:
                            with open(filepath, 'w') as f:
                                f.write(content)
                            fixes_applied.append(f"Wrapped Timer callback in @MainActor in {os.path.basename(filepath)}")
    
    return {
        "success": len(fixes_applied) > 0,
        "fixes_applied": fixes_applied
    }

def fix_missing_parenthesis(error_output: str, project_path: str) -> dict:
    """
    Fix missing closing parenthesis errors
    """
    fixes_applied = []
    
    # Pattern: expected ')' in expression list
    if "expected ')'" in error_output:
        # Extract file and line from error
        pattern = r"([\w/]+\.swift):(\d+).*expected '\)'"
        matches = re.findall(pattern, error_output)
        
        for filepath, line_num in matches:
            # Handle both absolute and relative paths
            if not os.path.isabs(filepath):
                filepath = os.path.join(project_path, filepath)
            
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    lines = f.readlines()
                
                line_idx = int(line_num) - 1
                if line_idx > 0 and line_idx < len(lines):
                    # Check the previous line for missing )
                    prev_line = lines[line_idx - 1]
                    
                    # Count parentheses
                    open_count = prev_line.count('(')
                    close_count = prev_line.count(')')
                    
                    if open_count > close_count:
                        # Add missing ) to the previous line
                        lines[line_idx - 1] = prev_line.rstrip() + ')\n'
                        
                        with open(filepath, 'w') as f:
                            f.writelines(lines)
                        
                        fixes_applied.append(f"Added missing ) at line {line_num - 1} in {os.path.basename(filepath)}")
    
    return {
        "success": len(fixes_applied) > 0,
        "fixes_applied": fixes_applied
    }