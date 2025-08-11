"""
Subdirectory Error Handler - Handles build errors related to files in subdirectories
"""

import os
import re
from typing import Dict, List, Optional

class SubdirectoryErrorHandler:
    """
    Handles build errors caused by files in subdirectories not being found
    """
    
    @staticmethod
    def detect_subdirectory_error(error_output: str) -> bool:
        """
        Check if error is related to missing types that might be in subdirectories
        """
        patterns = [
            r"cannot find '(\w+Style)' in scope",
            r"cannot find '(\w+View)' in scope",
            r"cannot find '(\w+Model)' in scope",
            r"cannot find '(\w+Controller)' in scope",
            r"cannot find '(\w+Service)' in scope",
            r"cannot find '(\w+Manager)' in scope",
            r"use of undeclared type '(\w+Style)'",
            r"use of undeclared type '(\w+View)'",
        ]
        
        for pattern in patterns:
            if re.search(pattern, error_output):
                return True
        return False
    
    @staticmethod
    def find_missing_files(error_output: str, project_path: str) -> Dict[str, str]:
        """
        Find files that exist in subdirectories but weren't included in build
        """
        missing_files = {}
        
        # Extract missing type names from errors
        missing_types = set()
        patterns = [
            r"cannot find '(\w+)' in scope",
            r"use of undeclared type '(\w+)'"
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, error_output)
            missing_types.update(matches)
        
        # Search for these types in subdirectories
        sources_dir = os.path.join(project_path, 'Sources')
        if os.path.exists(sources_dir):
            for root, dirs, files in os.walk(sources_dir):
                for file in files:
                    if file.endswith('.swift'):
                        # Check if filename matches any missing type
                        file_base = file.replace('.swift', '')
                        if file_base in missing_types:
                            full_path = os.path.join(root, file)
                            relative_path = os.path.relpath(full_path, project_path)
                            missing_files[file_base] = relative_path
        
        return missing_files
    
    @staticmethod
    def suggest_fix(error_output: str, project_path: str) -> Dict:
        """
        Suggest fix for subdirectory-related errors
        """
        if not SubdirectoryErrorHandler.detect_subdirectory_error(error_output):
            return {
                'has_issue': False,
                'message': 'No subdirectory-related errors detected'
            }
        
        missing_files = SubdirectoryErrorHandler.find_missing_files(error_output, project_path)
        
        if missing_files:
            fix_message = "Found files in subdirectories that weren't included in build:\n"
            for type_name, path in missing_files.items():
                fix_message += f"  - {type_name}: {path}\n"
            fix_message += "\nFix: Ensure build system recursively includes all Swift files in subdirectories"
            
            return {
                'has_issue': True,
                'missing_files': missing_files,
                'message': fix_message,
                'action': 'rebuild_with_subdirectories'
            }
        else:
            # Files don't exist, need to create them
            missing_types = set()
            patterns = [
                r"cannot find '(\w+)' in scope",
                r"use of undeclared type '(\w+)'"
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, error_output)
                missing_types.update(matches)
            
            return {
                'has_issue': True,
                'missing_types': list(missing_types),
                'message': f"Missing types need to be created: {', '.join(missing_types)}",
                'action': 'create_missing_types'
            }
    
    @staticmethod
    def verify_build_includes_subdirectories(build_command: str) -> bool:
        """
        Check if build command includes subdirectories
        """
        # Check if using wildcard or recursive pattern
        if '**/*.swift' in build_command or 'find' in build_command or 'os.walk' in build_command:
            return True
        
        # Check if only looking at top level
        if 'Sources/*.swift' in build_command and 'Sources/**' not in build_command:
            return False
        
        return True  # Assume it's okay if we can't determine