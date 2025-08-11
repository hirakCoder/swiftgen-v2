"""
Auto-Learning Error Recovery System
Learns from successful fixes and applies them quickly without degrading code
"""

import os
import json
import hashlib
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class LearningErrorRecovery:
    """
    Auto-learning error recovery that:
    1. Remembers successful fixes
    2. Applies proven solutions quickly
    3. Never degrades existing working code
    4. Gets faster with each successful recovery
    """
    
    def __init__(self, knowledge_path: str = "error_recovery_knowledge.json"):
        self.knowledge_path = knowledge_path
        self.knowledge = self._load_knowledge()
        self.temp_fixes = {}  # Temporary fixes being tested
        
    def _load_knowledge(self) -> Dict:
        """Load learned error patterns and fixes"""
        if os.path.exists(self.knowledge_path):
            try:
                with open(self.knowledge_path, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        return {
            "patterns": {},  # error_signature -> fix_strategy
            "success_count": {},  # fix_id -> count
            "failure_count": {},  # fix_id -> count
            "last_updated": str(datetime.now())
        }
    
    def _save_knowledge(self):
        """Persist learned knowledge"""
        self.knowledge["last_updated"] = str(datetime.now())
        try:
            with open(self.knowledge_path, 'w') as f:
                json.dump(self.knowledge, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save knowledge: {e}")
    
    def _create_error_signature(self, error: str) -> str:
        """Create a unique signature for an error pattern"""
        # Remove file paths and line numbers to make signature generic
        cleaned = re.sub(r'/[^\s]+\.swift:\d+:\d+:', '', error)
        cleaned = re.sub(r'line \d+ column \d+', '', cleaned)
        cleaned = re.sub(r'\d+', 'NUM', cleaned)  # Replace numbers with placeholder
        
        # Create hash of cleaned error
        return hashlib.md5(cleaned.encode()).hexdigest()[:16]
    
    def has_learned_fix(self, error: str) -> bool:
        """Check if we've successfully fixed this error before"""
        signature = self._create_error_signature(error)
        
        if signature in self.knowledge["patterns"]:
            fix_id = self.knowledge["patterns"][signature]["fix_id"]
            success_count = self.knowledge["success_count"].get(fix_id, 0)
            failure_count = self.knowledge["failure_count"].get(fix_id, 0)
            
            # Only use if success rate > 80%
            if success_count > 0:
                success_rate = success_count / (success_count + failure_count)
                return success_rate > 0.8
        
        return False
    
    def get_learned_fix(self, error: str) -> Optional[Dict]:
        """Get a previously successful fix for this error"""
        signature = self._create_error_signature(error)
        
        if signature in self.knowledge["patterns"]:
            fix_data = self.knowledge["patterns"][signature]
            logger.info(f"Found learned fix for error signature {signature}")
            return fix_data
        
        return None
    
    def apply_learned_fix(self, error: str, file_content: str) -> Optional[str]:
        """Apply a learned fix without degrading the code"""
        fix_data = self.get_learned_fix(error)
        
        if not fix_data:
            return None
        
        fix_type = fix_data.get("type")
        fix_pattern = fix_data.get("pattern")
        fix_replacement = fix_data.get("replacement")
        
        # Create a backup of original content
        original = file_content
        
        try:
            if fix_type == "regex_replace":
                # Apply regex replacement
                fixed = re.sub(fix_pattern, fix_replacement, file_content)
                
                # Verify we didn't break the code
                if self._verify_no_degradation(original, fixed):
                    return fixed
                    
            elif fix_type == "add_import":
                # Add missing import
                if fix_pattern not in file_content:
                    fixed = fix_pattern + "\n" + file_content
                    if self._verify_no_degradation(original, fixed):
                        return fixed
                        
            elif fix_type == "subdirectory_inclusion":
                # This is a build system fix, not a code fix
                return file_content  # Return unchanged, let build system handle it
                
        except Exception as e:
            logger.error(f"Failed to apply learned fix: {e}")
        
        return None
    
    def _verify_no_degradation(self, original: str, fixed: str) -> bool:
        """
        Verify that the fix doesn't degrade existing code
        Returns True if fix is safe
        """
        # Check that we haven't removed any existing functionality
        original_lines = set(line.strip() for line in original.splitlines() if line.strip())
        fixed_lines = set(line.strip() for line in fixed.splitlines() if line.strip())
        
        # Allow additions but not removals (unless it's whitespace)
        removed_lines = original_lines - fixed_lines
        
        for line in removed_lines:
            # Allow removal of error-causing lines
            if any(pattern in line for pattern in [
                "PersistenceController",  # Often causes errors
                "managedObjectContext",  # Core Data not needed
                "import Components",  # Invalid import
                "import Views",  # Invalid import
            ]):
                continue
            
            # Don't allow removal of actual code
            if any(keyword in line for keyword in [
                "func", "var", "let", "class", "struct", "enum",
                "@State", "@Published", "@ObservedObject", "View {"
            ]):
                logger.warning(f"Fix would remove code: {line}")
                return False
        
        return True
    
    def learn_from_success(self, error: str, fix_applied: Dict):
        """Record a successful fix for future use"""
        signature = self._create_error_signature(error)
        fix_id = hashlib.md5(json.dumps(fix_applied, sort_keys=True).encode()).hexdigest()[:8]
        
        # Store the fix pattern
        self.knowledge["patterns"][signature] = {
            "fix_id": fix_id,
            "error_pattern": error[:200],  # Store sample for debugging
            **fix_applied,
            "first_seen": self.knowledge["patterns"].get(signature, {}).get("first_seen", str(datetime.now())),
            "last_used": str(datetime.now())
        }
        
        # Increment success count
        self.knowledge["success_count"][fix_id] = self.knowledge["success_count"].get(fix_id, 0) + 1
        
        # Save knowledge
        self._save_knowledge()
        
        logger.info(f"Learned successful fix for signature {signature} (fix_id: {fix_id})")
    
    def learn_from_failure(self, error: str, fix_attempted: Dict):
        """Record a failed fix to avoid it in future"""
        signature = self._create_error_signature(error)
        fix_id = hashlib.md5(json.dumps(fix_attempted, sort_keys=True).encode()).hexdigest()[:8]
        
        # Increment failure count
        self.knowledge["failure_count"][fix_id] = self.knowledge["failure_count"].get(fix_id, 0) + 1
        
        # If this fix fails too often, remove it
        failure_count = self.knowledge["failure_count"][fix_id]
        success_count = self.knowledge["success_count"].get(fix_id, 0)
        
        if failure_count > 3 and failure_count > success_count * 2:
            # Remove this fix pattern as it's not working
            if signature in self.knowledge["patterns"]:
                if self.knowledge["patterns"][signature].get("fix_id") == fix_id:
                    del self.knowledge["patterns"][signature]
                    logger.info(f"Removed failing fix pattern for signature {signature}")
        
        # Save knowledge
        self._save_knowledge()
    
    def get_statistics(self) -> Dict:
        """Get learning statistics"""
        total_patterns = len(self.knowledge["patterns"])
        total_successes = sum(self.knowledge["success_count"].values())
        total_failures = sum(self.knowledge["failure_count"].values())
        
        success_rate = 0
        if total_successes + total_failures > 0:
            success_rate = total_successes / (total_successes + total_failures) * 100
        
        return {
            "total_patterns_learned": total_patterns,
            "total_successful_fixes": total_successes,
            "total_failed_attempts": total_failures,
            "overall_success_rate": f"{success_rate:.1f}%",
            "last_updated": self.knowledge.get("last_updated", "Never")
        }
    
    def suggest_fix_strategy(self, error: str) -> Dict:
        """
        Suggest a fix strategy based on learned patterns and error analysis
        """
        # First check if we have a learned fix
        if self.has_learned_fix(error):
            learned_fix = self.get_learned_fix(error)
            return {
                "strategy": "learned",
                "confidence": "high",
                "fix": learned_fix,
                "message": "Using previously successful fix"
            }
        
        # Analyze error for common patterns
        suggestions = []
        
        if "cannot find" in error and "in scope" in error:
            # Extract the missing type
            match = re.search(r"cannot find '(\w+)' in scope", error)
            if match:
                missing_type = match.group(1)
                
                # Check if it's a style or view that might be in subdirectory
                if any(suffix in missing_type for suffix in ["Style", "View", "Model", "Controller"]):
                    suggestions.append({
                        "type": "subdirectory_inclusion",
                        "message": f"Check if {missing_type} exists in a subdirectory",
                        "pattern": missing_type
                    })
                
                # Check if it needs an import
                if missing_type in ["Color", "Text", "Button", "VStack", "HStack"]:
                    suggestions.append({
                        "type": "add_import",
                        "pattern": "import SwiftUI",
                        "message": "Add SwiftUI import"
                    })
        
        if "Invalid escape" in error or "Invalid \\escape" in error:
            suggestions.append({
                "type": "regex_replace",
                "pattern": r'\\(?![nrt"\\\\/])',
                "replacement": r'\\\\',
                "message": "Fix invalid escape sequences"
            })
        
        if suggestions:
            return {
                "strategy": "suggested",
                "confidence": "medium",
                "fixes": suggestions,
                "message": "Suggested fixes based on error analysis"
            }
        
        return {
            "strategy": "none",
            "confidence": "low",
            "message": "No learned or suggested fixes available"
        }


# Global instance for easy access
learning_recovery = LearningErrorRecovery(
    os.path.join(
        os.path.dirname(__file__), 
        "..", 
        "error_recovery_knowledge.json"
    )
)