"""
Duplicate @main Validator
Detects and removes duplicate @main entry points in Swift projects
Prevents compilation errors from multiple @main declarations
"""

import os
import re
import logging

logger = logging.getLogger(__name__)

class DuplicateMainValidator:
    """
    Validates and fixes duplicate @main declarations in Swift projects
    """
    
    @staticmethod
    def validate_and_fix(project_path: str) -> dict:
        """
        Check for duplicate @main files and remove the generic App.swift if needed
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            dict with success status and any actions taken
        """
        sources_dir = os.path.join(project_path, "Sources")
        
        if not os.path.exists(sources_dir):
            return {
                "success": True,
                "message": "No Sources directory found",
                "actions": []
            }
        
        # Find all files with @main
        main_files = []
        
        try:
            for filename in os.listdir(sources_dir):
                if filename.endswith('.swift'):
                    file_path = os.path.join(sources_dir, filename)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            # Look for @main declaration
                            if re.search(r'@main\s+struct', content):
                                main_files.append(filename)
                    except Exception as e:
                        logger.warning(f"Could not read {filename}: {e}")
            
            # Check if we have duplicates
            if len(main_files) <= 1:
                return {
                    "success": True,
                    "message": f"Valid: Found {len(main_files)} @main file(s)",
                    "actions": [],
                    "main_files": main_files
                }
            
            # We have duplicates - need to fix
            logger.warning(f"Found duplicate @main files: {main_files}")
            
            actions = []
            
            # Strategy: Keep the app-specific file (e.g., TestTodoApp.swift)
            # Remove the generic App.swift
            if "App.swift" in main_files:
                # Find the non-generic app file
                app_specific_files = [f for f in main_files if f != "App.swift"]
                
                if app_specific_files:
                    # Remove the generic App.swift
                    try:
                        app_swift_path = os.path.join(sources_dir, "App.swift")
                        os.remove(app_swift_path)
                        actions.append(f"Removed duplicate App.swift (keeping {app_specific_files[0]})")
                        main_files.remove("App.swift")
                        logger.info(f"Removed duplicate App.swift, keeping {app_specific_files[0]}")
                    except Exception as e:
                        logger.error(f"Failed to remove App.swift: {e}")
                        return {
                            "success": False,
                            "message": f"Failed to remove duplicate: {e}",
                            "actions": actions,
                            "main_files": main_files
                        }
            else:
                # Multiple app-specific files - keep the first one alphabetically
                main_files.sort()
                files_to_remove = main_files[1:]  # Keep first, remove rest
                
                for file_to_remove in files_to_remove:
                    try:
                        file_path = os.path.join(sources_dir, file_to_remove)
                        os.remove(file_path)
                        actions.append(f"Removed duplicate {file_to_remove} (keeping {main_files[0]})")
                        logger.info(f"Removed duplicate {file_to_remove}")
                    except Exception as e:
                        logger.error(f"Failed to remove {file_to_remove}: {e}")
                
                main_files = [main_files[0]]  # Only the kept file remains
            
            return {
                "success": True,
                "message": "Fixed duplicate @main files",
                "actions": actions,
                "main_files": main_files
            }
            
        except Exception as e:
            logger.error(f"Error during validation: {e}")
            return {
                "success": False,
                "message": f"Validation error: {e}",
                "actions": [],
                "main_files": []
            }
    
    @staticmethod
    def get_main_app_name(project_path: str) -> str:
        """
        Get the name of the main app file
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            Name of the main app file without extension, or None if not found
        """
        sources_dir = os.path.join(project_path, "Sources")
        
        if not os.path.exists(sources_dir):
            return None
        
        try:
            for filename in os.listdir(sources_dir):
                if filename.endswith('App.swift') and filename != 'App.swift':
                    # Return the app name without 'App.swift'
                    return filename.replace('App.swift', '')
            
            # If only App.swift exists
            if os.path.exists(os.path.join(sources_dir, 'App.swift')):
                return "App"
                
        except Exception as e:
            logger.error(f"Error finding app name: {e}")
        
        return None