"""
SwiftUI Scope Analyzer - Understands and fixes scope issues in SwiftUI code
Properly handles nested ForEach, closures, and variable scope
"""

import re
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass

@dataclass
class Scope:
    """Represents a scope in Swift code"""
    scope_type: str  # 'ForEach', 'closure', 'function', 'struct', 'class'
    variables: Set[str]  # Variables defined in this scope
    line_start: int
    line_end: int
    indent_level: int
    parent: Optional['Scope'] = None
    children: List['Scope'] = None
    
    def __post_init__(self):
        if self.children is None:
            self.children = []
    
    def has_variable(self, var_name: str) -> bool:
        """Check if variable is accessible in this scope (including parent scopes)"""
        if var_name in self.variables:
            return True
        if self.parent:
            return self.parent.has_variable(var_name)
        return False
    
    def add_child(self, child: 'Scope'):
        """Add a child scope"""
        self.children.append(child)
        child.parent = self

class SwiftUIScopeAnalyzer:
    """
    Analyzes SwiftUI code to understand variable scopes and fix scope-related issues
    """
    
    def __init__(self):
        self.scope_tree = None
        self.lines = []
        
    def analyze(self, content: str) -> Dict:
        """
        Analyze Swift code and build scope tree
        Returns analysis with scope information and potential issues
        """
        self.lines = content.split('\n')
        self.scope_tree = self._build_scope_tree()
        
        issues = self._find_scope_issues()
        
        return {
            'scope_tree': self.scope_tree,
            'issues': issues,
            'fixes': self._suggest_fixes(issues)
        }
    
    def _build_scope_tree(self) -> Scope:
        """Build a tree of scopes from the code"""
        root = Scope('file', set(), 0, len(self.lines), 0)
        scope_stack = [root]
        
        for i, line in enumerate(self.lines):
            indent = self._get_indent_level(line)
            stripped = line.strip()
            
            # Pop scopes that have ended (based on indentation)
            while len(scope_stack) > 1 and indent <= scope_stack[-1].indent_level:
                if '}' in line:
                    scope_stack[-1].line_end = i
                scope_stack.pop()
            
            current_scope = scope_stack[-1]
            
            # Detect ForEach with variable binding
            foreach_match = re.search(r'ForEach\([^)]+\)\s*\{\s*(\w+)\s+in', stripped)
            if foreach_match:
                var_name = foreach_match.group(1)
                new_scope = Scope('ForEach', {var_name}, i, i, indent)
                current_scope.add_child(new_scope)
                scope_stack.append(new_scope)
                continue
            
            # Alternative ForEach syntax
            foreach_alt = re.search(r'ForEach\(([^,]+),\s*id:\s*[^)]+\)\s*\{\s*(\w+)\s+in', stripped)
            if foreach_alt:
                var_name = foreach_alt.group(2)
                new_scope = Scope('ForEach', {var_name}, i, i, indent)
                current_scope.add_child(new_scope)
                scope_stack.append(new_scope)
                continue
            
            # Detect closure with parameters
            closure_match = re.search(r'\{\s*(\w+(?:\s*,\s*\w+)*)\s+in', stripped)
            if closure_match and 'ForEach' not in line:
                params = [p.strip() for p in closure_match.group(1).split(',')]
                new_scope = Scope('closure', set(params), i, i, indent)
                current_scope.add_child(new_scope)
                scope_stack.append(new_scope)
                continue
            
            # Detect function definitions
            func_match = re.search(r'func\s+(\w+)\s*\(([^)]*)\)', stripped)
            if func_match:
                func_name = func_match.group(1)
                params_str = func_match.group(2)
                params = self._parse_function_params(params_str)
                new_scope = Scope('function', set(params), i, i, indent)
                current_scope.add_child(new_scope)
                scope_stack.append(new_scope)
                continue
            
            # Detect struct/class definitions
            struct_match = re.search(r'(struct|class)\s+(\w+)', stripped)
            if struct_match:
                type_kind = struct_match.group(1)
                type_name = struct_match.group(2)
                new_scope = Scope(type_kind, set(), i, i, indent)
                current_scope.add_child(new_scope)
                scope_stack.append(new_scope)
                continue
            
            # Detect variable declarations in current scope
            var_match = re.search(r'(@State\s+)?(private\s+)?(?:let|var)\s+(\w+)', stripped)
            if var_match:
                var_name = var_match.group(3)
                current_scope.variables.add(var_name)
        
        return root
    
    def _get_indent_level(self, line: str) -> int:
        """Get indentation level of a line"""
        return len(line) - len(line.lstrip())
    
    def _parse_function_params(self, params_str: str) -> List[str]:
        """Parse function parameters"""
        if not params_str.strip():
            return []
        
        params = []
        for param in params_str.split(','):
            # Extract parameter name (handle external/internal names)
            match = re.search(r'(\w+)\s*:', param)
            if match:
                params.append(match.group(1))
        
        return params
    
    def _find_scope_issues(self) -> List[Dict]:
        """Find scope-related issues in the code"""
        issues = []
        
        for i, line in enumerate(self.lines):
            # Check for variable usage
            var_uses = re.findall(r'\b(\w+)\.\w+', line)
            
            for var_name in var_uses:
                # Skip common types/modules
                if var_name in {'self', 'super', 'String', 'Int', 'Double', 'Float', 
                               'Bool', 'Array', 'Dictionary', 'Set', 'Date', 'UUID',
                               'Color', 'Text', 'Image', 'Button', 'VStack', 'HStack'}:
                    continue
                
                # Find which scope this line belongs to
                scope = self._find_scope_for_line(i)
                
                if scope and not scope.has_variable(var_name):
                    # Special check for swipeActions with item
                    if 'swipeActions' in line and var_name == 'item':
                        issues.append({
                            'type': 'swipeactions_scope',
                            'line': i,
                            'variable': var_name,
                            'message': f"Variable '{var_name}' not in scope for swipeActions",
                            'scope': scope
                        })
                    else:
                        issues.append({
                            'type': 'variable_not_in_scope',
                            'line': i,
                            'variable': var_name,
                            'message': f"Variable '{var_name}' not in scope",
                            'scope': scope
                        })
        
        return issues
    
    def _find_scope_for_line(self, line_num: int, scope: Scope = None) -> Optional[Scope]:
        """Find which scope a line belongs to"""
        if scope is None:
            scope = self.scope_tree
        
        # Check if line is in this scope
        if scope.line_start <= line_num <= scope.line_end:
            # Check children for more specific scope
            for child in scope.children:
                child_scope = self._find_scope_for_line(line_num, child)
                if child_scope:
                    return child_scope
            return scope
        
        return None
    
    def _suggest_fixes(self, issues: List[Dict]) -> List[Dict]:
        """Suggest fixes for scope issues"""
        fixes = []
        
        for issue in issues:
            if issue['type'] == 'swipeactions_scope':
                # SwipeActions needs to be moved to correct ForEach level
                fixes.append({
                    'issue': issue,
                    'fix_type': 'move_swipeactions',
                    'description': f"Move swipeActions to inner ForEach where '{issue['variable']}' is defined"
                })
            elif issue['type'] == 'variable_not_in_scope':
                # Suggest passing variable or restructuring
                fixes.append({
                    'issue': issue,
                    'fix_type': 'restructure_code',
                    'description': f"Restructure code to have access to '{issue['variable']}'"
                })
        
        return fixes
    
    def fix_scope_issues(self, content: str) -> Tuple[str, List[str]]:
        """
        Automatically fix scope issues in Swift code
        Returns: (fixed_content, list_of_fixes_applied)
        """
        analysis = self.analyze(content)
        fixes_applied = []
        
        if not analysis['issues']:
            return content, []
        
        lines = content.split('\n')
        
        for fix in analysis['fixes']:
            issue = fix['issue']
            
            if fix['fix_type'] == 'move_swipeactions':
                # Fix swipeActions scope issue
                lines, applied = self._fix_swipeactions_scope(lines, issue)
                if applied:
                    fixes_applied.append(applied)
            
            elif fix['fix_type'] == 'restructure_code':
                # More complex restructuring
                lines, applied = self._restructure_for_scope(lines, issue)
                if applied:
                    fixes_applied.append(applied)
        
        return '\n'.join(lines), fixes_applied
    
    def _fix_swipeactions_scope(self, lines: List[str], issue: Dict) -> Tuple[List[str], Optional[str]]:
        """Fix swipeActions attached to wrong scope"""
        swipe_line = issue['line']
        variable = issue['variable']
        
        # For swipeActions with 'item' not in scope, we need to move it to the correct ForEach
        # Find where swipeActions starts
        swipe_start = None
        swipe_end = None
        
        for i in range(max(0, swipe_line - 5), min(len(lines), swipe_line + 5)):
            if '.swipeActions' in lines[i]:
                swipe_start = i
                # Find the end of swipeActions block
                brace_count = 0
                in_block = False
                for j in range(i, len(lines)):
                    if '{' in lines[j]:
                        in_block = True
                        brace_count += lines[j].count('{')
                    if '}' in lines[j]:
                        brace_count -= lines[j].count('}')
                    if in_block and brace_count == 0:
                        swipe_end = j
                        break
                break
        
        if swipe_start is None or swipe_end is None:
            return lines, None
        
        # Find the inner ForEach that should have the swipeActions
        inner_foreach_line = None
        inner_foreach_item_line = None
        
        # Look backwards from swipeActions to find the ForEach with 'item'
        for i in range(swipe_start - 1, -1, -1):
            if 'ForEach' in lines[i] and '{ item in' in lines[i]:
                inner_foreach_line = i
                # Find the view inside this ForEach to attach swipeActions to
                for j in range(i + 1, swipe_start):
                    if 'Text' in lines[j] or 'Row' in lines[j] or 'HStack' in lines[j] or 'VStack' in lines[j]:
                        inner_foreach_item_line = j
                        break
                break
        
        if inner_foreach_line and inner_foreach_item_line:
            # Extract the swipeActions block
            swipe_block = lines[swipe_start:swipe_end + 1]
            
            # Remove from current location
            new_lines = []
            skip_until = -1
            
            for i, line in enumerate(lines):
                if i < swipe_start or i > swipe_end:
                    new_lines.append(line)
                elif i == swipe_start:
                    skip_until = swipe_end
            
            # Find where to insert (after the view inside ForEach)
            final_lines = []
            for i, line in enumerate(new_lines):
                final_lines.append(line)
                if i == inner_foreach_item_line:
                    # Add swipeActions with proper indentation
                    base_indent = len(line) - len(line.lstrip())
                    for swipe_line in swipe_block:
                        if swipe_line.strip():
                            final_lines.append(' ' * (base_indent + 4) + swipe_line.strip())
            
            return final_lines, f"Moved swipeActions to inner ForEach with access to '{variable}'"
        
        # If we can't move it properly, at least fix the reference
        return self._restructure_for_scope(lines, issue)
    
    def _restructure_for_scope(self, lines: List[str], issue: Dict) -> Tuple[List[str], Optional[str]]:
        """Restructure code for proper scope access"""
        # This is complex and depends on the specific pattern
        # For now, we'll handle common cases
        
        variable = issue['variable']
        line_num = issue['line']
        
        # If it's an 'item' reference in wrong scope, comment it out with TODO
        if variable == 'item' and 'removeAll' in lines[line_num]:
            lines[line_num] = lines[line_num].replace(
                f'{variable}.', 
                f'/* TODO: Fix scope for {variable} */ //{variable}.'
            )
            return lines, f"Commented out scope issue for '{variable}' - needs manual fix"
        
        return lines, None

# Convenience functions
def analyze_swift_scope(content: str) -> Dict:
    """Analyze Swift code scope"""
    analyzer = SwiftUIScopeAnalyzer()
    return analyzer.analyze(content)

def fix_swift_scope_issues(content: str) -> Tuple[str, List[str]]:
    """Fix Swift scope issues automatically"""
    analyzer = SwiftUIScopeAnalyzer()
    return analyzer.fix_scope_issues(content)