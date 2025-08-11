#!/usr/bin/env python3
"""
Robust Multi-Model Error Recovery System for SwiftGen
World-class implementation that combines Claude, OpenAI, and xAI for intelligent error recovery
"""

import os
import re
import json
import asyncio
import logging
import time
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime

# Import AI services
try:
    import openai
    from openai import AsyncOpenAI
except ImportError:
    openai = None
    AsyncOpenAI = None

try:
    import httpx
except ImportError:
    httpx = None


class RobustErrorRecoverySystem:
    """Multi-model error recovery system for Swift build errors"""

    def __init__(self, claude_service=None, openai_key=None, xai_key=None, rag_kb=None):
        """Initialize with multiple AI services and RAG knowledge base"""
        self.claude_service = claude_service
        self.openai_key = openai_key
        self.xai_key = xai_key
        self.rag_kb = rag_kb  # RAG Knowledge Base

        # Set up logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        # Track recovery attempts
        self.attempt_count = 0
        self.max_attempts = 3
        
        # Track what we've tried to avoid infinite loops
        self.attempted_fixes = {}  # error_fingerprint -> attempt_count
        self.ios_target_version = "16.0"

        # Load error patterns
        self.error_patterns = self._load_error_patterns()

        # Define recovery strategies based on available services
        self.recovery_strategies = self._get_dynamic_recovery_strategies()

        self.logger.info("Robust error recovery system initialized")
    
    def reset_attempted_fixes(self):
        """Reset attempted fixes counter for new generations"""
        self.attempted_fixes.clear()
        self.logger.info("Reset attempted fixes counter for new generation")

    def _load_error_patterns(self):
        """Load error patterns from file or use defaults"""
        patterns_file = os.path.join(os.path.dirname(__file__), 'error_patterns.json')

        if os.path.exists(patterns_file):
            try:
                with open(patterns_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.warning(f"Failed to load error patterns: {e}")

        # Return default patterns - comprehensive list
        return {
            "ios_version": {
                "patterns": [
                    "is only available in iOS 17",
                    "is only available in macOS",
                    "symbolEffect.*is only available",
                    "bounce.*is only available",
                    "@Observable.*is only available",
                    "scrollBounceBehavior.*is only available",
                    "contentTransition.*is only available",
                    "ContentUnavailableView.*is only available",
                    "'ContentUnavailableView' is only available"
                ],
                "fixes": [
                    "Replace .symbolEffect() with .scaleEffect or .opacity animations",
                    "Replace .bounce with .animation(.spring())",
                    "Replace @Observable with ObservableObject + @Published",
                    "Remove iOS 17+ modifiers or use iOS 16 alternatives",
                    "Use NavigationView instead of NavigationStack for simple cases"
                ]
            },
            "immutable_variable": {
                "patterns": [
                    "cannot assign to value.*is immutable",
                    "cannot assign to value: 'error' is immutable",
                    "immutable value 'error'"
                ],
                "fixes": [
                    "In catch blocks, rename the caught error: catch let caughtError",
                    "Use self.error instead of error when assigning to properties",
                    "Rename local variables that conflict with property names"
                ]
            },
            "string_literal": {
                "patterns": [
                    "unterminated string literal",
                    "cannot find '\"' in scope",
                    "consecutive statements on a line must be separated"
                ],
                "fixes": [
                    "Use double quotes \" for strings, not single quotes '",
                    "Ensure all string literals are properly terminated",
                    "Check for unescaped quotes within strings"
                ]
            },
            "persistence_controller": {
                "patterns": [
                    "cannot find 'PersistenceController' in scope",
                    "cannot find type 'PersistenceController'",
                    "use of unresolved identifier 'PersistenceController'",
                    "cannot find 'managedObjectContext' in scope"
                ],
                "fixes": [
                    "Remove Core Data references if not needed",
                    "Remove PersistenceController property from App",
                    "Remove .environment(\\.managedObjectContext) modifier"
                ]
            },
            "immutable_variable": {
                "patterns": [
                    "cannot assign to value.*is immutable",
                    "cannot assign to value: 'error' is immutable",
                    "immutable value 'error'"
                ],
                "fixes": [
                    "In catch blocks, rename the caught error: catch let caughtError",
                    "Use self.error instead of error when assigning to properties",
                    "Rename local variables that conflict with property names"
                ]
            },
            "missing_import": {
                "patterns": [
                    "cannot find type .* in scope",
                    "use of unresolved identifier",
                    "no such module"
                ],
                "fixes": [
                    "Add missing import statements",
                    "import SwiftUI for SwiftUI types",
                    "import Foundation for basic types",
                    "Remove incorrect module imports",
                    "Fix relative imports to use file names directly"
                ]
            },
            "syntax_error": {
                "patterns": [
                    "expected",
                    "invalid redeclaration",
                    "consecutive declarations"
                ],
                "fixes": [
                    "Check for missing braces or parentheses",
                    "Ensure proper Swift syntax",
                    "Remove duplicate declarations"
                ]
            },
            "exhaustive_switch": {
                "patterns": [
                    "switch must be exhaustive",
                    "does not have a member"
                ],
                "fixes": [
                    "Add all missing enum cases to switch",
                    "Add default case to handle remaining cases",
                    "Verify enum definition matches usage"
                ]
            },
            "type_not_found": {
                "patterns": [
                    "cannot find .* in scope",
                    "use of undeclared type"
                ],
                "fixes": [
                    "Define missing types or remove references",
                    "Ensure all custom Views are implemented",
                    "Check file names match type names",
                    "Check if types are defined in subdirectories (e.g., Views/, Models/)",
                    "Ensure build system includes all subdirectories in Sources/"
                ]
            },
            "protocol_conformance": {
                "patterns": [
                    "conform to 'Decodable'",
                    "conform to 'Encodable'",
                    "conform to 'Codable'",
                    "does not conform to protocol",
                    "conform to 'Hashable'"
                ],
                "fixes": [
                    "Add protocol conformance to types",
                    "For JSON encoding/decoding, add : Codable",
                    "For Hashable conformance, add : Hashable",
                    "Ensure all required protocol methods are implemented"
                ]
            },
            "hashable_conformance": {
                "patterns": [
                    "must conform to 'Hashable'",
                    "requires that .* conform to 'Hashable'",
                    "Type .* does not conform to protocol 'Hashable'",
                    "does not conform to protocol 'Hashable'",
                    "'init.*' requires that '.*' conform to 'Hashable'",
                    "instance method '.*' requires that '.*' conform to 'Hashable'",
                    "error: type '.*' does not conform to protocol 'Hashable'",
                    "error: type '.*' does not conform to protocol 'Equatable'"
                ],
                "fixes": [
                    "Add : Hashable to the type declaration",
                    "For structs with all Hashable properties, Swift synthesizes conformance automatically",
                    "For custom types, implement hash(into:) and == methods",
                    "Ensure all properties are Hashable for automatic synthesis"
                ]
            },
            "toolbar_ambiguous": {
                "patterns": [
                    "ambiguous use of 'toolbar'",
                    "ambiguous use of 'toolbar\(content:'"
                ],
                "fixes": [
                    "Use .toolbar { } instead of .toolbar(content: { })",
                    "Place toolbar modifier after navigationTitle",
                    "Ensure toolbar is attached to correct view hierarchy"
                ]
            },
            "duplicate_declaration": {
                "patterns": [
                    "invalid redeclaration",
                    "redundant conformance",
                    "duplicate modifier",
                    "final @MainActor",
                    "redundant '@MainActor'",
                    "duplicate '@MainActor'",
                    "multiple global actor attributes",
                    "declaration can not have multiple global actor"
                ],
                "fixes": [
                    "Remove duplicate @MainActor declarations",
                    "Remove duplicate modifiers like 'final' when used with @MainActor",
                    "Ensure each declaration appears only once"
                ]
            }
        }

    def _get_dynamic_recovery_strategies(self):
        """Get recovery strategies based on available services"""
        strategies = [
            self._pattern_based_recovery,
            self._swift_syntax_recovery,
            self._dependency_recovery,
            self._rag_based_recovery,  # Add RAG recovery before LLM
            self._llm_based_recovery
        ]

        return strategies

    async def recover_from_errors(self, errors: List[str], swift_files: List[Dict],
                                  bundle_id: str = None) -> Tuple[bool, List[Dict], List[str]]:
        """Main recovery method that tries multiple strategies"""

        self.logger.info(f"Starting error recovery with {len(errors)} errors")
        
        # Create error fingerprint to track what we've tried
        error_fingerprint = self._create_error_fingerprint(errors)
        
        # CRITICAL: Allow more recovery attempts and reset counters for new generations
        # Check if we've tried fixing this exact error pattern before
        if error_fingerprint in self.attempted_fixes:
            if self.attempted_fixes[error_fingerprint] >= 5:  # Increased from 2 to 5
                self.logger.warning(f"Already attempted to fix this error pattern {self.attempted_fixes[error_fingerprint]} times. Stopping to avoid infinite loop.")
                return False, swift_files, ["Automated recovery exhausted for this error pattern"]
        else:
            self.attempted_fixes[error_fingerprint] = 0
        
        # Increment attempt count for this fingerprint
        self.attempted_fixes[error_fingerprint] += 1
        self.logger.info(f"Recovery attempt {self.attempted_fixes[error_fingerprint]} for error pattern: {error_fingerprint[:100]}")

        # Analyze errors
        error_analysis = self._analyze_errors(errors)
        fixes_applied = []

        # Try each recovery strategy
        modified_files = swift_files
        cumulative_fixes = []
        
        for strategy in self.recovery_strategies:
            try:
                self.logger.info(f"Attempting recovery strategy: {strategy.__name__}")
                success, modified_files = await strategy(errors, modified_files, error_analysis)

                if success:
                    self.logger.info(f"Recovery strategy {strategy.__name__} made changes")

                    # Track what was fixed
                    if strategy.__name__ == "_pattern_based_recovery":
                        cumulative_fixes.append("Applied pattern-based syntax fixes")
                        
                        # CRITICAL: Don't return yet! Let other strategies run too
                        # Pattern-based fixes might be partial, so we need AI recovery as well
                        if strategy.__name__ != "_llm_based_recovery":
                            continue
                    
                    elif strategy.__name__ == "_rag_based_recovery":
                        cumulative_fixes.append("Applied RAG knowledge-based fixes")
                        # Continue to try other strategies too
                        continue
                            
                    elif strategy.__name__ == "_llm_based_recovery":
                        cumulative_fixes.append("Applied AI-powered fixes")

                    # Only return after trying all strategies or after LLM recovery
                    if cumulative_fixes and strategy.__name__ == "_llm_based_recovery":
                        return True, modified_files, cumulative_fixes

            except Exception as e:
                self.logger.error(f"Strategy {strategy.__name__} failed: {e}")
                continue
        
        # If we made any fixes at all, return them
        if cumulative_fixes:
            return True, modified_files, cumulative_fixes

        # If all strategies fail, try last resort
        return await self._last_resort_recovery(errors, swift_files, error_analysis)

    def _create_error_fingerprint(self, errors: List[str]) -> str:
        """Create a fingerprint of the error pattern to track attempts"""
        # Extract error types and sort them to create consistent fingerprint
        error_types = []
        for error in errors[:5]:  # Use first 5 errors for fingerprint
            # Extract the core error message
            if "is only available in iOS" in error:
                error_types.append("ios_version_error")
            elif "unterminated string literal" in error:
                error_types.append("string_literal_error")
            elif "cannot find" in error and "in scope" in error:
                error_types.append("missing_type_error")
            elif "switch must be exhaustive" in error:
                error_types.append("exhaustive_switch_error")
            elif "cannot assign to value" in error and "is immutable" in error:
                error_types.append("immutable_variable_error")
            else:
                # Use first 20 chars of error as type
                error_types.append(error[:20].replace(" ", "_"))
        
        # Sort and join to create consistent fingerprint
        return "|".join(sorted(set(error_types)))
    
    def _analyze_errors(self, errors: List[str]) -> Dict[str, List[str]]:
        """Analyze errors to categorize them"""
        analysis = {
            "ios_version_errors": [],
            "string_literal_errors": [],
            "missing_imports": [],
            "syntax_errors": [],
            "exhaustive_switch_errors": [],
            "type_not_found_errors": [],
            "protocol_conformance_errors": [],
            "persistence_controller_errors": [],
            "immutable_variable_errors": [],
            "hashable_conformance_errors": [],
            "toolbar_ambiguous_errors": [],
            "duplicate_declaration_errors": [],
            "other_errors": []
        }

        for error in errors:
            categorized = False

            # Check each error pattern
            for error_type, pattern_info in self.error_patterns.items():
                for pattern in pattern_info["patterns"]:
                    if re.search(pattern, error, re.IGNORECASE):
                        if error_type == "ios_version":
                            analysis["ios_version_errors"].append(error)
                        elif error_type == "string_literal":
                            analysis["string_literal_errors"].append(error)
                        elif error_type == "missing_import":
                            analysis["missing_imports"].append(error)
                        elif error_type == "syntax_error":
                            analysis["syntax_errors"].append(error)
                        elif error_type == "exhaustive_switch":
                            analysis["exhaustive_switch_errors"].append(error)
                        elif error_type == "type_not_found":
                            analysis["type_not_found_errors"].append(error)
                        elif error_type == "protocol_conformance":
                            analysis["protocol_conformance_errors"].append(error)
                        elif error_type == "persistence_controller":
                            analysis["persistence_controller_errors"].append(error)
                        elif error_type == "immutable_variable":
                            analysis["immutable_variable_errors"].append(error)
                        elif error_type == "hashable_conformance":
                            analysis["hashable_conformance_errors"].append(error)
                        elif error_type == "toolbar_ambiguous":
                            analysis["toolbar_ambiguous_errors"].append(error)
                        elif error_type == "duplicate_declaration":
                            analysis["duplicate_declaration_errors"].append(error)
                        categorized = True
                        break
                if categorized:
                    break

            if not categorized:
                analysis["other_errors"].append(error)

        return analysis

    async def _pattern_based_recovery(self, errors: List[str], swift_files: List[Dict],
                                      error_analysis: Dict) -> Tuple[bool, List[Dict]]:
        """Pattern-based recovery for common errors"""
        self.logger.info(f"Pattern-based recovery processing {len(errors)} errors: {[e[:80] for e in errors[:3]]}")

        # Check for iOS version errors
        has_ios_version_error = bool(error_analysis.get("ios_version_errors"))
        
        # Check for PersistenceController errors
        has_persistence_error = bool(error_analysis.get("persistence_controller_errors")) or \
                              any("PersistenceController" in error or "managedObjectContext" in error for error in errors)
        
        # Check for protocol conformance errors
        has_codable_error = bool(error_analysis.get("protocol_conformance_errors"))
        
        # Check for module import errors
        has_module_error = any("no such module" in error for error in errors)
        
        # Check for immutable variable errors
        has_immutable_error = any("cannot assign to value" in error and "is immutable" in error for error in errors)
        
        # Check for hashable conformance errors
        has_hashable_error = bool(error_analysis.get("hashable_conformance_errors")) or \
                            any("conform to 'Hashable'" in error or "conform to 'Hashable'" in error for error in errors)
        
        # Check for toolbar ambiguity errors
        has_toolbar_error = bool(error_analysis.get("toolbar_ambiguous_errors")) or \
                           any("ambiguous use of 'toolbar'" in error for error in errors)
        
        # Check for duplicate declaration errors
        has_duplicate_error = bool(error_analysis.get("duplicate_declaration_errors")) or \
                             any("invalid redeclaration" in error or "final @MainActor" in error or "redundant" in error or 
                                 "multiple global actor attributes" in error or "declaration can not have multiple global actor" in error 
                                 for error in errors)
        
        if not (error_analysis.get("string_literal_errors") or 
                error_analysis.get("syntax_errors") or 
                has_persistence_error or 
                has_codable_error or
                has_immutable_error or
                has_ios_version_error or
                has_module_error or
                has_hashable_error or
                has_toolbar_error or
                has_duplicate_error):
            return False, swift_files

        modified_files = []
        changes_made = False

        for file in swift_files:
            content = file["content"]
            original_content = content

            # Fix iOS version errors by replacing iOS 17+ features
            if has_ios_version_error:
                # Replace ContentUnavailableView with custom implementation
                if 'ContentUnavailableView' in content:
                    # More comprehensive regex patterns for different ContentUnavailableView usages
                    # Add logging
                    self.logger.info(f"Found ContentUnavailableView in {file['path']}, applying iOS 16 compatible replacement")
                    
                    # Pattern 0: Simple ContentUnavailableView("Title", systemImage: "icon") without description
                    content = re.sub(
                        r'ContentUnavailableView\s*\(\s*"([^"]+)"\s*,\s*systemImage:\s*"([^"]+)"\s*\)',
                        r'''VStack(spacing: 20) {
                        Image(systemName: "\2")
                            .font(.system(size: 50))
                            .foregroundColor(.gray)
                        Text("\1")
                            .font(.title2)
                            .foregroundColor(.gray)
                    }
                    .padding()''',
                        content
                    )
                    
                    # Pattern 1: ContentUnavailableView("Title", systemImage: "icon", description: Text("desc"))
                    content = re.sub(
                        r'ContentUnavailableView\s*\(\s*"([^"]+)"\s*,\s*systemImage:\s*"([^"]+)"\s*,\s*description:\s*Text\s*\(\s*"([^"]+)"\s*\)\s*\)',
                        r'''VStack(spacing: 20) {
                        Image(systemName: "\2")
                            .font(.system(size: 50))
                            .foregroundColor(.gray)
                        Text("\1")
                            .font(.title2)
                            .foregroundColor(.gray)
                        Text("\3")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                    .padding()''',
                        content
                    )
                    
                    # Pattern 2: Generic ContentUnavailableView with any content
                    content = re.sub(
                        r'ContentUnavailableView\s*\{[^}]+\}',
                        '''VStack(spacing: 20) {
                        Image(systemName: "exclamationmark.triangle")
                            .font(.system(size: 50))
                            .foregroundColor(.gray)
                        Text("Content Unavailable")
                            .font(.title2)
                            .foregroundColor(.gray)
                    }
                    .padding()''',
                        content,
                        flags=re.DOTALL
                    )
                    
                    # Pattern 3: Any remaining ContentUnavailableView - GENERIC replacement
                    content = re.sub(
                        r'ContentUnavailableView[^)]*\)',
                        '''VStack(spacing: 20) {
                        Image(systemName: "exclamationmark.triangle")
                            .font(.system(size: 50))
                            .foregroundColor(.gray)
                        Text("Content Unavailable")
                            .font(.title2)
                            .foregroundColor(.gray)
                        Text("Please check back later")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                    .padding()''',
                        content
                    )
                    changes_made = True
                
                # Replace symbolEffect with spring animation
                content = re.sub(
                    r'\.symbolEffect\([^)]*\)',
                    '.scaleEffect(1.1).animation(.spring(), value: true)',
                    content
                )
                
                # Replace bounce effects
                content = re.sub(
                    r'\.bounce',
                    '.spring()',
                    content
                )
                
                # Replace @Observable with ObservableObject
                content = re.sub(
                    r'@Observable\s+class\s+',
                    'class ',
                    content
                )
                
                # Ensure ObservableObject conformance
                content = re.sub(
                    r'(class\s+\w+)(?!.*:.*ObservableObject)',
                    r'\1: ObservableObject',
                    content
                )
                
                # Modern pattern: Convert NavigationView to NavigationStack (opposite of before!)
                # NavigationView is deprecated, we should use NavigationStack
                if 'NavigationView' in content:
                    content = re.sub(r'NavigationView\s*{', 'NavigationStack {', content)
                    self.logger.info(f"Migrated NavigationView to NavigationStack in {file['path']}")
                
                # Remove iOS 17+ only modifiers
                ios17_modifiers = [
                    r'\.scrollBounceBehavior\([^)]*\)',
                    r'\.contentTransition\([^)]*\)',
                    r'\.presentationBackground\([^)]*\)',
                    r'\.presentationCornerRadius\([^)]*\)'
                ]
                
                for modifier in ios17_modifiers:
                    if re.search(modifier, content):
                        content = re.sub(modifier, '', content)
                        self.logger.info(f"Removed iOS 17+ modifier: {modifier}")
                
                # Fix deprecated modifiers
                deprecated_replacements = {
                    r'\.foregroundColor\(': '.foregroundStyle(',
                    r'\.accentColor\(': '.tint(',
                }
                
                for old_pattern, new_pattern in deprecated_replacements.items():
                    if re.search(old_pattern, content):
                        content = re.sub(old_pattern, new_pattern, content)
                        self.logger.info(f"Replaced deprecated {old_pattern} with {new_pattern}")
                
                if content != original_content:
                    changes_made = True
                    self.logger.info(f"Fixed iOS version compatibility issues in {file['path']}")
                else:
                    self.logger.info(f"No iOS version fixes needed in {file['path']}")

            # Fix module import errors
            if has_module_error:
                # Check for "no such module 'Components'" or similar
                modules_removed = []
                for error in errors:
                    if "no such module" in error:
                        match = re.search(r"no such module '([^']+)'", error)
                        if match:
                            bad_module = match.group(1)
                            # Remove the bad import
                            content = re.sub(rf'import\s+{bad_module}\s*\n', '', content)
                            modules_removed.append(bad_module)
                            changes_made = True
                            self.logger.info(f"Removed incorrect module import '{bad_module}' from {file['path']}")
                
                # Also check for incorrect relative imports in SwiftUI
                # In SwiftUI, we don't use module imports for local files
                local_modules = ['Views', 'Models', 'ViewModels', 'Components', 'Services', 'Utilities', 'Helpers', 'Extensions']
                for module in local_modules:
                    if re.search(rf'import\s+{module}\s*\n', content):
                        content = re.sub(rf'import\s+{module}\s*\n', '', content)
                        modules_removed.append(module)
                        changes_made = True
                
                # CRITICAL: Also remove module prefixes from type references
                # e.g., Components.MyView -> MyView
                for module in modules_removed:
                    # Remove module prefix from type references
                    content = re.sub(rf'{module}\.(\w+)', r'\1', content)
                    self.logger.info(f"Removed module prefix '{module}.' from type references")
                
                if content != original_content:
                    changes_made = True

            # Fix PersistenceController errors by removing Core Data references
            if has_persistence_error:
                # Remove from any file that has these references
                if "PersistenceController" in content or "managedObjectContext" in content or "CoreData" in content:
                    # Remove Core Data import
                    content = re.sub(r'import CoreData\s*\n', '', content)
                    
                    # Remove PersistenceController property declarations
                    content = re.sub(r'(private\s+)?let\s+persistenceController\s*=\s*PersistenceController[^\n]*\n', '', content)
                    
                    # Remove .environment modifiers with managedObjectContext
                    content = re.sub(r'\.environment\(\\\.managedObjectContext[^)]*\)\s*', '', content)
                    
                    # Remove @Environment property wrappers for managedObjectContext
                    content = re.sub(r'@Environment\(\\\.managedObjectContext\)\s*(?:private\s+)?var\s+\w+\s*:\s*NSManagedObjectContext\s*\n', '', content)
                    
                    # Remove @FetchRequest property wrappers
                    content = re.sub(r'@FetchRequest\([^}]*\}\s*(?:private\s+)?var\s+\w+\s*:[^\n]*\n', '', content)
                    
                    # Remove PersistenceController references in preview providers
                    content = re.sub(r'\.environment\(\\\.managedObjectContext[^)]*PersistenceController[^)]*\)', '', content)
                    
                    changes_made = True

            # Fix immutable variable errors
            if has_immutable_error:
                # Fix catch block error assignment conflicts
                # Pattern: } catch { error = ... }
                # This happens when there's a property named 'error' and catch block also has 'error'
                
                # Fix 1: Rename the catch parameter
                content = re.sub(
                    r'(\s+)catch\s*\{\s*\n(\s+)error\s*=',
                    r'\1catch let caughtError {\n\2self.error =',
                    content
                )
                
                # Fix 2: If error assignment uses the catch error
                content = re.sub(
                    r'catch\s*\{\s*\n(\s+)error\s*=\s*error',
                    r'catch let caughtError {\n\1self.error = caughtError',
                    content
                )
                
                # Fix 3: Generic pattern for any catch block with error assignment
                content = re.sub(
                    r'catch\s*\{\s*\n([\s\S]*?)error\s*=\s*error',
                    r'catch let caughtError {\n\1self.error = caughtError',
                    content,
                    flags=re.MULTILINE
                )
                
                if content != original_content:
                    changes_made = True
                    self.logger.info(f"Fixed immutable error assignment in {file['path']}")
            
            # Fix string literal errors
            if error_analysis.get("string_literal_errors"):
                # Fix line by line for better control
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    original_line = line
                    
                    # Replace single quotes with double quotes for string literals
                    # But be careful not to replace character literals or within strings
                    # Look for patterns like = 'text' or ('text' or Text('text')
                    line = re.sub(r"(=\s*)'([^']*)'(?!\w)", r'\1"\2"', line)
                    line = re.sub(r"\('([^']*)'\)", r'("\1")', line)
                    line = re.sub(r"Text\('([^']*)'\)", r'Text("\1")', line)
                    line = re.sub(r"Button\('([^']*)'\)", r'Button("\1")', line)
                    line = re.sub(r"\b'([^']+)'\b", r'"\1"', line)
                    
                    # Fix fancy quotes
                    line = line.replace('"', '"').replace('"', '"').replace(''', "'").replace(''', "'")
                    
                    # Count quotes to check for unterminated strings
                    # Skip escaped quotes when counting
                    temp_line = line.replace('\\"', '')
                    quote_count = temp_line.count('"')
                    
                    # If odd number of quotes, likely unterminated
                    if quote_count % 2 != 0:
                        # Look for common patterns of unterminated strings
                        if re.search(r'=\s*"[^"]*$', line):  # Assignment ending with open quote
                            line = line.rstrip() + '"'
                        elif re.search(r'\("[^"]*$', line):  # Function call with open quote
                            line = line.rstrip() + '"'
                        elif re.search(r'Text\("[^"]*$', line):  # Text view with open quote
                            line = line.rstrip() + '")'
                        elif re.search(r'print\("[^"]*$', line):  # Print with open quote
                            line = line.rstrip() + '"'
                        else:
                            # Generic fix - add closing quote
                            line = line.rstrip() + '"'
                    
                    lines[i] = line
                    if line != original_line:
                        changes_made = True
                
                content = '\n'.join(lines)

            # Fix Codable conformance errors
            if has_codable_error:
                for error in error_analysis.get("protocol_conformance_errors", []):
                    # Extract type name that needs Codable
                    match = re.search(r"type '(\w+)' does not conform to protocol '(Codable|Decodable|Encodable)'", error)
                    if match:
                        type_name = match.group(1)
                        protocol_name = match.group(2)
                        
                        # Find the type definition
                        # Look for struct or class definition
                        struct_pattern = rf'(struct\s+{type_name}(?:\s*:\s*([^{{]+))?\s*{{)'
                        class_pattern = rf'(class\s+{type_name}(?:\s*:\s*([^{{]+))?\s*{{)'
                        
                        for pattern in [struct_pattern, class_pattern]:
                            match = re.search(pattern, content)
                            if match:
                                full_match = match.group(0)
                                existing_conformances = match.group(2) if match.group(2) else ""
                                
                                if "Codable" not in existing_conformances and protocol_name not in existing_conformances:
                                    if existing_conformances:
                                        # Add to existing conformances
                                        new_conformances = existing_conformances.strip() + ", Codable"
                                        new_declaration = full_match.replace(existing_conformances, new_conformances)
                                    else:
                                        # Add conformance
                                        type_keyword = "struct" if "struct" in full_match else "class"
                                        new_declaration = full_match.replace(
                                            f"{type_keyword} {type_name}",
                                            f"{type_keyword} {type_name}: Codable"
                                        )
                                    
                                    content = content.replace(full_match, new_declaration)
                                    changes_made = True
                                    break
            
            # Fix Hashable conformance errors
            if has_hashable_error:
                hashable_errors = error_analysis.get("hashable_conformance_errors", []) + \
                                 [e for e in errors if "Hashable" in e]
                
                for error in hashable_errors:
                    # Multiple patterns to catch all Hashable error variants
                    type_name = None
                    
                    # Pattern 1: 'TypeName' must conform to 'Hashable'
                    match = re.search(r"'(\w+)' must conform to 'Hashable'", error)
                    if match:
                        type_name = match.group(1)
                    
                    # Pattern 2: requires that 'TypeName' conform to 'Hashable'
                    if not type_name:
                        match = re.search(r"requires that '(\w+)' conform to 'Hashable'", error)
                        if match:
                            type_name = match.group(1)
                    
                    # Pattern 3: Type 'TypeName' does not conform to protocol 'Hashable'
                    if not type_name:
                        match = re.search(r"Type '(\w+)' does not conform to protocol 'Hashable'", error)
                        if match:
                            type_name = match.group(1)
                    
                    # Pattern 4: type 'TypeName' does not conform to protocol 'Hashable'
                    if not type_name:
                        match = re.search(r"type '(\w+)' does not conform to protocol 'Hashable'", error)
                        if match:
                            type_name = match.group(1)
                    
                    # Pattern 5: 'TypeName' does not conform to protocol 'Hashable'
                    if not type_name:
                        match = re.search(r"'(\w+)' does not conform to protocol 'Hashable'", error)
                        if match:
                            type_name = match.group(1)
                    
                    # Pattern 6: Same patterns for Equatable (which is part of Hashable)
                    if not type_name:
                        match = re.search(r"'(\w+)' does not conform to protocol 'Equatable'", error)
                        if match:
                            type_name = match.group(1)
                    
                    if type_name:
                        self.logger.info(f"Found type {type_name} needs Hashable conformance")
                        
                        # Find the type definition
                        struct_pattern = rf'(struct\s+{type_name}(?:\s*:\s*([^{{]+))?\s*{{)'
                        class_pattern = rf'(class\s+{type_name}(?:\s*:\s*([^{{]+))?\s*{{)'
                        enum_pattern = rf'(enum\s+{type_name}(?:\s*:\s*([^{{]+))?\s*{{)'
                        
                        for pattern in [struct_pattern, class_pattern, enum_pattern]:
                            match = re.search(pattern, content)
                            if match:
                                full_match = match.group(0)
                                existing_conformances = match.group(2) if match.group(2) else ""
                                
                                if "Hashable" not in existing_conformances:
                                    if existing_conformances:
                                        # Add to existing conformances
                                        new_conformances = existing_conformances.strip() + ", Hashable"
                                        new_declaration = full_match.replace(existing_conformances, new_conformances)
                                    else:
                                        # Add conformance
                                        type_keyword = "struct" if "struct" in full_match else ("class" if "class" in full_match else "enum")
                                        new_declaration = full_match.replace(
                                            f"{type_keyword} {type_name}",
                                            f"{type_keyword} {type_name}: Hashable"
                                        )
                                    
                                    content = content.replace(full_match, new_declaration)
                                    
                                    # For types with complex properties that might need custom implementation
                                    # Check if we need to add hash(into:) and == methods
                                    if not re.search(rf'func hash\(into hasher: inout Hasher\)', content) and \
                                       not re.search(rf'static func == \(lhs: {type_name}, rhs: {type_name}\) -> Bool', content):
                                        
                                        # Find closing brace of the type
                                        type_start = content.find(new_declaration) + len(new_declaration)
                                        brace_count = 1
                                        i = type_start
                                        
                                        while i < len(content) and brace_count > 0:
                                            if content[i] == '{':
                                                brace_count += 1
                                            elif content[i] == '}':
                                                brace_count -= 1
                                            i += 1
                                        
                                        if brace_count == 0:
                                            # Insert hash and equality methods before the closing brace
                                            insertion_point = i - 1  # Before the closing brace
                                            hash_methods = f"""
    
    func hash(into hasher: inout Hasher) {{
        hasher.combine(id)
    }}
    
    static func == (lhs: {type_name}, rhs: {type_name}) -> Bool {{
        lhs.id == rhs.id
    }}
"""
                                            content = content[:insertion_point] + hash_methods + content[insertion_point:]
                                            self.logger.info(f"Added hash(into:) and == methods to {type_name}")
                                    
                                    changes_made = True
                                    self.logger.info(f"Added Hashable conformance to {type_name} in {file['path']}")
                                    break
            
            # Fix toolbar ambiguity errors
            if has_toolbar_error:
                # Replace .toolbar(content: { }) with .toolbar { }
                content = re.sub(r'\.toolbar\s*\(\s*content\s*:\s*\{', '.toolbar {', content)
                
                # Find and fix duplicate toolbar modifiers
                lines = content.split('\n')
                toolbar_lines = []
                for i, line in enumerate(lines):
                    if '.toolbar' in line:
                        toolbar_lines.append(i)
                
                # If multiple toolbars found, keep only the first one
                if len(toolbar_lines) > 1:
                    # Find the complete toolbar blocks
                    for idx in reversed(toolbar_lines[1:]):
                        # Simple approach: remove the line with .toolbar
                        if idx < len(lines):
                            lines[idx] = '// ' + lines[idx]  # Comment out duplicate toolbars
                    content = '\n'.join(lines)
                    changes_made = True
                    self.logger.info("Fixed toolbar ambiguity by commenting duplicate toolbars")
            
            # Fix duplicate declaration errors
            if has_duplicate_error:
                # Fix duplicate @MainActor declarations
                # Pattern 1: "final @MainActor" on a line by itself after @MainActor
                content = re.sub(
                    r'(@MainActor\s*\n\s*)final\s+@MainActor\s*\n',
                    r'\1final\n',
                    content,
                    flags=re.MULTILINE
                )
                
                # Pattern 2: "final @MainActor" on the same line as class/struct declaration
                content = re.sub(
                    r'final\s+@MainActor\s+(class|struct)',
                    r'@MainActor final \1',
                    content
                )
                
                # Pattern 3: Multiple @MainActor on same line
                content = re.sub(
                    r'@MainActor\s+@MainActor',
                    r'@MainActor',
                    content
                )
                
                # Pattern 4: @MainActor followed by final @MainActor
                content = re.sub(
                    r'@MainActor\s*\n\s*final\s+@MainActor',
                    r'@MainActor\nfinal',
                    content
                )
                
                # Pattern 5: Clean up any remaining "final @MainActor" patterns
                content = re.sub(
                    r'final\s+@MainActor',
                    r'@MainActor final',
                    content
                )
                
                # Pattern 6: Remove duplicate consecutive @MainActor declarations
                lines = content.split('\n')
                fixed_lines = []
                prev_line_had_mainactor = False
                
                for line in lines:
                    # Check if current line has @MainActor
                    if '@MainActor' in line and not line.strip().startswith('//'):
                        if prev_line_had_mainactor and line.strip() == 'final @MainActor':
                            # Skip this line - it's a duplicate
                            continue
                        elif 'final @MainActor' in line and '@MainActor' in content[:content.find(line)]:
                            # Replace "final @MainActor" with just "final"
                            line = line.replace('final @MainActor', 'final')
                        prev_line_had_mainactor = True
                    else:
                        prev_line_had_mainactor = False
                    
                    fixed_lines.append(line)
                
                content = '\n'.join(fixed_lines)
                
                if content != original_content:
                    changes_made = True
                    self.logger.info(f"Fixed duplicate @MainActor declarations in {file['path']}")
            
            # Fix common syntax errors
            content = re.sub(r'\.presentationMode', '.dismiss', content)
            content = re.sub(r'@Environment\(\\\.presentationMode\)', '@Environment(\\.dismiss)', content)

            if content != original_content:
                changes_made = True

            modified_files.append({
                "path": file["path"],
                "content": content
            })

        return changes_made, modified_files

    async def _swift_syntax_recovery(self, errors: List[str], swift_files: List[Dict],
                                     error_analysis: Dict) -> Tuple[bool, List[Dict]]:
        """Swift-specific syntax recovery"""

        modified_files = []
        changes_made = False

        for file in swift_files:
            content = file["content"]
            original_content = content

            # Ensure proper imports
            if "@main" in content and "import SwiftUI" not in content:
                content = "import SwiftUI\n" + content
                changes_made = True

            if "Date()" in content and "import Foundation" not in content:
                content = "import Foundation\n" + content
                changes_made = True

            modified_files.append({
                "path": file["path"],
                "content": content
            })

        return changes_made, modified_files

    async def _dependency_recovery(self, errors: List[str], swift_files: List[Dict],
                                   error_analysis: Dict) -> Tuple[bool, List[Dict]]:
        """Fix missing dependencies"""

        if not error_analysis["missing_imports"]:
            return False, swift_files

        modified_files = []
        changes_made = False

        # Extract missing types from errors
        missing_types = set()
        for error in error_analysis["missing_imports"]:
            match = re.search(r"cannot find type '([^']+)' in scope", error)
            if match:
                missing_types.add(match.group(1))

        # Map types to imports
        type_to_import = {
            "Color": "SwiftUI",
            "View": "SwiftUI",
            "Text": "SwiftUI",
            "Button": "SwiftUI",
            "VStack": "SwiftUI",
            "HStack": "SwiftUI",
            "List": "SwiftUI",
            "NavigationView": "SwiftUI",
            "NavigationStack": "SwiftUI",
            "Date": "Foundation",
            "DateFormatter": "Foundation",
            "UUID": "Foundation",
            "URL": "Foundation"
        }

        for file in swift_files:
            content = file["content"]
            imports_to_add = set()

            # Check which imports are needed
            for missing_type in missing_types:
                if missing_type in type_to_import and missing_type in content:
                    import_module = type_to_import[missing_type]
                    if f"import {import_module}" not in content:
                        imports_to_add.add(import_module)

            # Add missing imports
            if imports_to_add:
                import_statements = "\n".join(f"import {module}" for module in sorted(imports_to_add))
                content = import_statements + "\n" + content
                changes_made = True

            modified_files.append({
                "path": file["path"],
                "content": content
            })

        return changes_made, modified_files

    async def _rag_based_recovery(self, errors: List[str], swift_files: List[Dict],
                                  error_analysis: Dict) -> Tuple[bool, List[Dict]]:
        """Use RAG knowledge base to fix errors before resorting to LLMs"""
        
        if not self.rag_kb:
            self.logger.info("RAG knowledge base not available, skipping")
            return False, swift_files
            
        self.logger.info("Attempting RAG-based recovery")
        changes_made = False
        modified_files = []
        
        # Process each file
        for file in swift_files:
            content = file["content"]
            file_path = file["path"]
            original_content = content
            
            # Query RAG for each error type
            error_contexts = []
            
            # Get solutions for specific errors
            for error in errors[:10]:  # Limit to first 10 errors
                # Query RAG for this specific error
                solutions = self.rag_kb.search(error, k=3)
                
                for solution in solutions:
                    if solution.get('severity') in ['critical', 'important']:
                        error_contexts.append({
                            'error': error,
                            'solution': solution,
                            'quick_fixes': solution.get('quick_fixes', {})
                        })
            
            # Apply quick fixes from RAG
            for context in error_contexts:
                quick_fixes = context['solution'].get('quick_fixes', {})
                
                # Apply quick string replacements
                for old_pattern, new_pattern in quick_fixes.items():
                    if old_pattern in content:
                        content = content.replace(old_pattern, new_pattern)
                        self.logger.info(f"RAG: Applied quick fix: {old_pattern} -> {new_pattern}")
                        changes_made = True
            
            # Apply pattern-based fixes from RAG solutions
            for error_type, error_list in error_analysis.items():
                if error_list:
                    # Query RAG for this error type
                    pattern_solutions = self.rag_kb.search(error_type.replace('_', ' '), k=2)
                    
                    for solution in pattern_solutions:
                        # Apply solutions based on RAG recommendations
                        if error_type == "ios_version_errors":
                            # Apply iOS version fixes from RAG
                            content = self._apply_rag_ios_fixes(content, solution)
                        elif error_type == "string_literal_errors":
                            # Apply string literal fixes from RAG
                            content = self._apply_rag_string_fixes(content, solution)
                        elif error_type == "missing_imports":
                            # Apply import fixes from RAG
                            content = self._apply_rag_import_fixes(content, solution)
            
            # Check for reserved type conflicts using RAG
            reserved_types = ['Task', 'State', 'Action', 'Result', 'Error']
            for reserved_type in reserved_types:
                if f"struct {reserved_type}" in content or f"class {reserved_type}" in content:
                    # Get alternatives from RAG
                    alternatives = self.rag_kb.get_naming_alternatives(reserved_type)
                    if alternatives:
                        replacement = alternatives[0]  # Use first alternative
                        content = content.replace(f"struct {reserved_type}", f"struct {replacement}")
                        content = content.replace(f"class {reserved_type}", f"class {replacement}")
                        # Also replace usage
                        content = re.sub(f'\\b{reserved_type}\\b(?!<)', replacement, content)
                        self.logger.info(f"RAG: Replaced reserved type {reserved_type} with {replacement}")
                        changes_made = True
            
            if content != original_content:
                modified_files.append({
                    "path": file_path,
                    "content": content
                })
            else:
                modified_files.append(file)
        
        # Store successful fixes back to RAG
        if changes_made:
            # Create a summary of what was fixed
            fix_summary = f"Fixed {len(errors)} errors using RAG patterns"
            self.rag_kb.add_learned_solution(
                error="; ".join(errors[:3]),
                solution=fix_summary,
                success=True
            )
        
        return changes_made, modified_files
    
    def _apply_rag_ios_fixes(self, content: str, solution: Dict) -> str:
        """Apply iOS version fixes based on RAG solution"""
        # Remove iOS 17+ features based on RAG recommendations
        ios17_patterns = {
            r'\.symbolEffect\([^)]*\)': '',
            r'\.contentTransition\([^)]*\)': '',
            r'\.scrollBounceBehavior\([^)]*\)': '',
            r'@Observable\s+': '',
            r'\.bounce\b': '.animation(.spring())'
        }
        
        for pattern, replacement in ios17_patterns.items():
            content = re.sub(pattern, replacement, content)
        
        return content
    
    def _apply_rag_string_fixes(self, content: str, solution: Dict) -> str:
        """Apply string literal fixes based on RAG solution"""
        # Fix single quotes to double quotes
        lines = content.split('\n')
        fixed_lines = []
        
        for line in lines:
            # Skip comments
            if not line.strip().startswith('//'):
                # Replace single quotes with double quotes for string literals
                line = re.sub(r"'([^']*)'", r'"\1"', line)
            fixed_lines.append(line)
        
        return '\n'.join(fixed_lines)
    
    def _apply_rag_import_fixes(self, content: str, solution: Dict) -> str:
        """Apply import fixes based on RAG solution"""
        # Check what imports are needed
        needs_swiftui = any(keyword in content for keyword in [
            'View', 'Text', 'Button', '@State', '@Binding', 'VStack', 'HStack'
        ])
        needs_foundation = any(keyword in content for keyword in [
            'UUID', 'Date', 'URL', 'Data'
        ])
        
        # Add missing imports at the beginning
        imports_to_add = []
        if needs_swiftui and 'import SwiftUI' not in content:
            imports_to_add.append('import SwiftUI')
        if needs_foundation and 'import Foundation' not in content:
            imports_to_add.append('import Foundation')
        
        if imports_to_add:
            content = '\n'.join(imports_to_add) + '\n\n' + content
        
        return content

    async def _llm_based_recovery(self, errors: List[str], swift_files: List[Dict],
                                  error_analysis: Dict) -> Tuple[bool, List[Dict]]:
        """Use LLMs to fix errors"""

        # Try Claude first if available - FIXED METHOD CALL
        if self.claude_service:
            try:
                # Check which methods are available
                if hasattr(self.claude_service, 'generate_ios_app'):
                    # Use the modification approach
                    fix_prompt = self._create_error_fix_prompt(errors, swift_files, error_analysis)

                    # Create a modification request that fixes the errors
                    # Check if we need to create missing files
                    missing_views = []
                    for error in errors:
                        if "cannot find" in error and "View" in error and "in scope" in error:
                            # Extract the missing view name
                            import re
                            match = re.search(r"cannot find '(\w+View)' in scope", error)
                            if match:
                                missing_views.append(match.group(1))
                    
                    if missing_views:
                        modification_request = f"Fix these build errors by creating the missing SwiftUI views:\n"
                        for view in missing_views:
                            # Specify proper path structure
                            view_path = f"Sources/Views/{view}.swift"
                            modification_request += f"- Create {view_path} with a proper SwiftUI View implementation for {view}\n"
                        modification_request += f"\nMake sure to:\n"
                        modification_request += f"1. Create files in the correct directory structure (Sources/Views/ for views)\n"
                        modification_request += f"2. Include all necessary imports (import SwiftUI)\n"
                        modification_request += f"3. Make the views match their usage in the app\n"
                        modification_request += f"\nErrors:\n{chr(10).join(errors[:5])}"
                    else:
                        modification_request = f"Fix these build errors:\n{chr(10).join(errors[:5])}"

                    # Use modify_ios_app if available
                    if hasattr(self.claude_service, 'modify_ios_app'):
                        result = await self.claude_service.modify_ios_app(
                            app_name="App",
                            description="Fix build errors",
                            modification=modification_request,
                            files=swift_files
                        )

                        if result and "files" in result and len(result["files"]) > 0:
                            # Validate that files have content
                            valid_files = []
                            for f in result["files"]:
                                if isinstance(f, dict) and "content" in f and f["content"]:
                                    # Apply string literal fixes
                                    fixed_content = self._fix_string_literals(f["content"])
                                    valid_files.append({
                                        "path": f["path"],
                                        "content": fixed_content
                                    })
                                else:
                                    # Use original file if recovery failed
                                    for orig in swift_files:
                                        if orig.get("path") == f.get("path"):
                                            valid_files.append(orig)
                                            break
                            
                            if valid_files:
                                return True, valid_files

                    # Fall back to generate_text
                    elif hasattr(self.claude_service, 'generate_text'):
                        result = self.claude_service.generate_text(fix_prompt)
                        if result["success"]:
                            fixed_files = self._parse_ai_response(result["text"], swift_files)
                            if fixed_files:
                                return True, fixed_files

            except Exception as e:
                self.logger.error(f"Claude recovery failed: {e}")

        # Try OpenAI if available
        if self.openai_key:
            success, files = await self._openai_recovery(errors, swift_files, error_analysis)
            if success:
                return success, files

        # Try xAI if available
        if self.xai_key:
            success, files = await self._xai_recovery(errors, swift_files, error_analysis)
            if success:
                return success, files

        return False, swift_files

    async def _openai_recovery(self, errors: List[str], swift_files: List[Dict],
                               error_analysis: Dict) -> Tuple[bool, List[Dict]]:
        """Use OpenAI for recovery"""

        if not openai or not AsyncOpenAI:
            self.logger.warning("OpenAI not available")
            return False, swift_files

        try:
            client = AsyncOpenAI(api_key=self.openai_key)

            # Create context
            error_text = "\n".join(errors[:10])  # Limit to first 10 errors
            code_context = "\n---\n".join([
                f"File: {f['path']}\n{f['content'][:500]}..."
                for f in swift_files[:3]
            ])

            messages = [
                {
                    "role": "system",
                    "content": """You are an expert Swift developer. Fix compilation errors in iOS apps.
                    
Key rules:
1. Use double quotes " for strings, never single quotes '
2. Use @Environment(\\.dismiss) instead of @Environment(\\.presentationMode)
3. Ensure all Swift syntax is correct
4. Return complete fixed code, not snippets"""
                },
                {
                    "role": "user",
                    "content": f"""Fix these Swift build errors:

ERRORS:
{error_text}

CURRENT CODE:
{code_context}

Return a JSON object with this structure:
{{
    "files": [
        {{
            "path": "Sources/FileName.swift",
            "content": "// COMPLETE fixed Swift code here"
        }}
    ],
    "fixes_applied": ["List of fixes made"]
}}"""
                }
            ]

            response = await client.chat.completions.create(
                model="gpt-4-turbo-preview",  # or "gpt-4" or "gpt-3.5-turbo"
                messages=messages,
                temperature=0.3,
                max_tokens=4000,
                response_format={"type": "json_object"}  # Force JSON response
            )

            content = response.choices[0].message.content
            self.logger.info("GPT-4 response received")

            # Parse JSON response
            try:
                result = json.loads(content)
                if "files" in result:
                    self.logger.info(f"GPT-4 fixes: {result.get('fixes_applied', [])}")
                    return True, result["files"]
            except json.JSONDecodeError:
                # Try to parse as code blocks
                fixed_files = self._parse_ai_response(content, swift_files)
                if fixed_files:
                    return True, fixed_files

        except Exception as e:
            self.logger.error(f"OpenAI recovery failed: {e}")
            import traceback
            traceback.print_exc()

        return False, swift_files

    async def _xai_recovery(self, errors: List[str], swift_files: List[Dict],
                            error_analysis: Dict) -> Tuple[bool, List[Dict]]:
        """Use xAI (Grok) for recovery - placeholder for now"""
        # xAI implementation would go here when API is available
        return False, swift_files

    def _create_error_fix_prompt(self, errors: List[str], swift_files: List[Dict],
                                 error_analysis: Dict) -> str:
        """Create a prompt for LLMs to fix errors"""

        # Get relevant files with errors
        error_files = set()
        for error in errors:
            # Extract file path from error
            match = re.search(r'(Sources/[^:]+\.swift)', error)
            if match:
                error_files.add(match.group(1))

        # Get the files that have errors
        relevant_files = [f for f in swift_files if f["path"] in error_files]

        # Use newline character instead of chr(10) in f-string
        newline = '\n'
        errors_text = newline.join(errors[:10])
        files_text = newline.join([f"File: {f['path']}\n```swift\n{f['content']}\n```" for f in relevant_files])

        prompt = f"""Fix these Swift compilation errors. Be VERY careful with string literals and quotes.

ERRORS:
{errors_text}

ERROR TYPES DETECTED:
{json.dumps(error_analysis, indent=2)}

FILES WITH ERRORS:
{files_text}

CRITICAL INSTRUCTIONS:
1. For iOS version compatibility errors (HIGHEST PRIORITY):
   - Target iOS: 16.0 - DO NOT use iOS 17+ features
   - Replace .symbolEffect() with .scaleEffect or .opacity animations
   - Replace .bounce with .animation(.spring())
   - Replace @Observable with ObservableObject + @Published
   - Use NavigationView instead of NavigationStack for simple navigation
   - Remove any iOS 17+ specific modifiers

2. For "cannot find type in scope" errors:
   - If it's 'PersistenceController', 'DataController', or similar:
     * These are Core Data controllers - either implement them or remove Core Data references
     * For simple apps, you can remove these and use @State/@StateObject instead
   - If it's a custom View or Model:
     * Add the missing type definition
     * Or remove references if not needed
   - Ensure all referenced types have complete implementations

3. For "no such module" errors:
   - In SwiftUI, you DON'T import local folders like 'Components', 'Views', etc.
   - Only import system frameworks: SwiftUI, Foundation, Combine, etc.
   - Remove any import statements for local folders
   - Access types directly without module prefix

4. For "switch must be exhaustive" errors:
   - Add ALL missing cases to the switch statement
   - Or add a default case: default: break
   - Check the enum definition for all cases

5. For string literal errors:
   - Use regular double quotes " not fancy quotes " " or ' '
   - Fix: Text("Hello") not Text("Hello") or Text('Hello')
   - Ensure all strings are properly terminated

6. For import errors:
   - Add missing imports at the top of files
   - SwiftUI apps need: import SwiftUI
   - Core Data apps need: import CoreData
   - DO NOT import local folders like Views, Models, Components

6. For Codable/Encodable/Decodable errors:
   - Add ": Codable" to struct/class declarations that need JSON encoding
   - Import Foundation if not already imported
   - Example: struct TodoItem: Identifiable, Codable { ... }

7. For '@StateObject' requires property wrapper errors:
   - Ensure the class conforms to ObservableObject
   - Use @Published for properties that should trigger UI updates

8. For missing initializer errors:
   - Add required init methods
   - Or provide default values for all properties

9. IMPORTANT: 
   - Target iOS 16.0 - avoid ALL iOS 17+ features
   - Fix the ROOT CAUSE, not just symptoms
   - If Core Data is causing issues and not essential, remove it
   - Keep the app functional even if simplified
   - Return COMPLETE, WORKING code for ALL files

Return JSON with the fixed files:
{{
    "files": [
        {{
            "path": "Sources/FileName.swift",
            "content": "// Complete FIXED code here"
        }}
    ],
    "fixes_applied": ["List of fixes"]
}}"""

        return prompt

    async def _last_resort_recovery(self, errors: List[str], swift_files: List[Dict],
                                    error_analysis: Dict) -> Tuple[bool, List[Dict], List[str]]:
        """Last resort - create minimal working version"""

        self.logger.info("Applying last resort recovery")

        # Find the main app file
        app_file = None
        other_files = []

        for file in swift_files:
            if "@main" in file["content"]:
                app_file = file
            else:
                other_files.append(file)

        if not app_file:
            return False, swift_files, []

        # Create minimal working versions
        modified_files = []

        # Fix app file
        app_name = "MyApp"
        match = re.search(r'struct\s+(\w+):\s*App', app_file["content"])
        if match:
            app_name = match.group(1)

        minimal_app = f"""import SwiftUI

@main
struct {app_name}: App {{
    var body: some Scene {{
        WindowGroup {{
            ContentView()
        }}
    }}
}}"""

        modified_files.append({
            "path": app_file["path"],
            "content": minimal_app
        })

        # Create minimal ContentView
        content_view = """import SwiftUI

struct ContentView: View {
    var body: some View {
        VStack {
            Image(systemName: "globe")
                .imageScale(.large)
                .foregroundStyle(.tint)
            Text("Hello, world!")
        }
        .padding()
    }
}

#Preview {
    ContentView()
}"""

        # Find ContentView file or create one
        content_view_file = None
        for file in other_files:
            if "ContentView" in file["path"]:
                content_view_file = file
                break

        if content_view_file:
            modified_files.append({
                "path": content_view_file["path"],
                "content": content_view
            })
        else:
            modified_files.append({
                "path": "Sources/ContentView.swift",
                "content": content_view
            })

        return True, modified_files, ["Applied minimal working template"]

    def _parse_ai_response(self, response: str, original_files: List[Dict]) -> List[Dict]:
        """Parse AI response to extract fixed files"""

        # Try to parse as JSON first
        try:
            result = json.loads(response)
            if "files" in result:
                # Post-process files to fix common string literal issues
                fixed_files = []
                for file in result["files"]:
                    content = file["content"]
                    # Fix smart quotes and ensure proper string formatting
                    content = self._fix_string_literals(content)
                    fixed_files.append({
                        "path": file["path"],
                        "content": content
                    })
                return fixed_files
        except json.JSONDecodeError:
            pass

        # Try to extract Swift code blocks
        swift_blocks = re.findall(r'```swift(.*?)```', response, re.DOTALL)

        if swift_blocks:
            # Match blocks to original files
            fixed_files = []
            for file in original_files:
                # Try to find corresponding code block
                for block in swift_blocks:
                    # Simple heuristic: check if file contains key identifiers
                    if "@main" in file["content"] and "@main" in block:
                        fixed_files.append({
                            "path": file["path"],
                            "content": self._fix_string_literals(block.strip())
                        })
                        break
                    elif "ContentView" in file["path"] and "ContentView" in block:
                        fixed_files.append({
                            "path": file["path"],
                            "content": self._fix_string_literals(block.strip())
                        })
                        break

            if fixed_files:
                return fixed_files

        return None
    
    def _fix_string_literals(self, content: str) -> str:
        """Fix common string literal issues in Swift code"""
        # Replace smart quotes with regular quotes
        content = content.replace('"', '"').replace('"', '"')
        content = content.replace(''', "'").replace(''', "'")
        
        # CRITICAL: Fix malformed String(format:) patterns first
        
        # Pattern 1: Text with text before String(format:)
        # Fix: Text("Minimum order: String(format: "%.2f", value)")
        # To: Text("Minimum order: \(String(format: "%.2f", value))")
        content = re.sub(
            r'Text\("([^"]*?)String\(format:\s*"([^"]+)",\s*([^)]+)\)"\)',
            r'Text("\1\\(String(format: "\2", \3))")',
            content
        )
        
        # Pattern 2: Text("String(format: "%.2f", value)")  
        content = re.sub(
            r'Text\("String\(format:\s*"([^"]+)",\s*([^)]+)\)"\)',
            r'Text(String(format: "\1", \2))',
            content
        )
        
        # Pattern 3: "String(format: "%.2f", value)"
        content = re.sub(
            r'"String\(format:\s*"([^"]+)",\s*([^)]+)\)"',
            r'String(format: "\1", \2)',
            content
        )
        
        # Fix string interpolation issues
        content = re.sub(
            r'\$\\\(([^,]+),\s*specifier:\s*"([^"]+)"\)',
            r'String(format: "\2", \1)',
            content
        )
        
        # Fix Text() with malformed string interpolation
        content = re.sub(
            r'Text\("([^"]*)\$\\\(([^)]+)\)([^"]*)"\.font',
            r'Text("\1\\(\2)\3").font',
            content
        )
        
        # Fix specific patterns we're seeing in the logs
        lines = content.split('\n')
        fixed_lines = []
        fixes_made = 0
        for i, line in enumerate(lines):
            original_line = line
            # Fix any remaining String(format: issues
            if '"String(format:' in line and 'Text(' in line:
                # Pattern: Text("String(format: "%.2f", value)")
                line = re.sub(
                    r'Text\("String\(format:\s*"([^"]+)",\s*([^)]+)\)"\)',
                    r'Text(String(format: "\1", \2))',
                    line
                )
                if line != original_line:
                    fixes_made += 1
                    self.logger.info(f"Fixed string literal on line {i+1}: {original_line.strip()[:50]} -> {line.strip()[:50]}")
            elif 'String(format:' in line and not line.strip().startswith('Text(String(format:'):
                # Standalone malformed String(format:
                line = re.sub(
                    r'"String\(format:\s*"([^"]+)",\s*([^)]+)\)"',
                    r'String(format: "\1", \2)',
                    line
                )
                if line != original_line:
                    fixes_made += 1
                    self.logger.info(f"Fixed standalone string format on line {i+1}: {original_line.strip()[:50]} -> {line.strip()[:50]}")
            
            fixed_lines.append(line)
        
        if fixes_made > 0:
            self.logger.info(f"Applied {fixes_made} string literal fixes to content")
        
        return '\n'.join(fixed_lines)


def create_intelligent_recovery_system(claude_service=None, openai_key=None, xai_key=None):
    """Factory function to create recovery system"""
    return RobustErrorRecoverySystem(
        claude_service=claude_service,
        openai_key=openai_key,
        xai_key=xai_key
    )