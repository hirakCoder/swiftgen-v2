"""
Grok JSON Response Fixer
Fixes common JSON issues in Grok's responses
"""

import re
import json
import logging

logger = logging.getLogger(__name__)

class GrokJSONFixer:
    """Fix Grok-specific JSON issues"""
    
    @staticmethod
    def fix_grok_json(raw_response: str) -> str:
        """Fix common Grok JSON issues"""
        
        # Original response for fallback
        original = raw_response
        
        try:
            # Step 1: Remove markdown code blocks if present
            if "```json" in raw_response:
                raw_response = raw_response.split("```json")[1].split("```")[0]
            elif "```" in raw_response:
                raw_response = raw_response.split("```")[1].split("```")[0]
            
            # Step 2: Fix invalid escape sequences
            # Replace single backslashes that aren't valid escapes
            raw_response = raw_response.replace('\\n', '\\\\n')
            raw_response = raw_response.replace('\\t', '\\\\t')
            raw_response = raw_response.replace('\\"', '\\\\"')
            
            # Fix Windows-style paths if any
            raw_response = re.sub(r'\\([^"\\ntr/])', r'\\\\\1', raw_response)
            
            # Step 3: Fix unescaped quotes in strings
            # This is tricky - we need to find quotes inside string values
            lines = raw_response.split('\n')
            fixed_lines = []
            
            for line in lines:
                # If line contains ": " it might be a JSON key-value pair
                if '": "' in line:
                    # Split by the first ": " to separate key from value
                    parts = line.split('": "', 1)
                    if len(parts) == 2:
                        key_part = parts[0]
                        value_part = parts[1]
                        
                        # Check if value part ends properly
                        if value_part.rstrip().endswith('",') or value_part.rstrip().endswith('"'):
                            # Find the last quote that should be the closing quote
                            # Everything between first and last quote should be escaped
                            if value_part.count('"') > 1:
                                # There are internal quotes that need escaping
                                # Find content between quotes
                                last_quote_idx = value_part.rfind('"')
                                content = value_part[:last_quote_idx]
                                ending = value_part[last_quote_idx:]
                                
                                # Escape internal quotes
                                content = content.replace('"', '\\"')
                                value_part = content + ending
                        
                        line = key_part + '": "' + value_part
                
                fixed_lines.append(line)
            
            raw_response = '\n'.join(fixed_lines)
            
            # Step 4: Fix nested JSON strings (double-encoded JSON)
            # Look for patterns like "{\\"key\\": \\"value\\"}"
            raw_response = re.sub(r'"{(\\"[^"]*\\":\s*\\"[^"]*\\"[^}]*)}"', r'{\1}', raw_response)
            
            # Step 5: Fix trailing commas
            raw_response = re.sub(r',(\s*[}\]])', r'\1', raw_response)
            
            # Step 6: Ensure proper JSON structure
            # If response doesn't start with { or [, try to find JSON object
            raw_response = raw_response.strip()
            if not (raw_response.startswith('{') or raw_response.startswith('[')):
                # Try to find JSON object in response
                json_match = re.search(r'(\{[\s\S]*\})', raw_response)
                if json_match:
                    raw_response = json_match.group(1)
            
            # Step 7: Validate by parsing
            try:
                json.loads(raw_response)
                logger.info("[GROK FIX] Successfully fixed Grok JSON")
                return raw_response
            except json.JSONDecodeError as e:
                logger.warning(f"[GROK FIX] Still invalid after fixes: {e}")
                
                # Last resort: try to extract files array directly
                files_match = re.search(r'"files"\s*:\s*\[([\s\S]*?)\]', raw_response)
                if files_match:
                    try:
                        files_content = "[" + files_match.group(1) + "]"
                        files = json.loads(files_content)
                        
                        # Reconstruct minimal valid JSON
                        result = {
                            "files": files,
                            "app_name": "App",
                            "bundle_id": "com.swiftgen.app"
                        }
                        return json.dumps(result)
                    except:
                        pass
                
                # If all else fails, return original
                return original
                
        except Exception as e:
            logger.error(f"[GROK FIX] Unexpected error: {e}")
            return original
    
    @staticmethod
    def validate_swift_content(content: str) -> tuple[bool, list[str]]:
        """Validate Swift content for common Grok issues"""
        issues = []
        
        # Check for unbalanced delimiters
        if content.count('(') != content.count(')'):
            issues.append(f"Unbalanced parentheses: {content.count('(')} open, {content.count(')')} close")
        
        if content.count('{') != content.count('}'):
            issues.append(f"Unbalanced braces: {content.count('{')} open, {content.count('}')} close")
        
        if content.count('[') != content.count(']'):
            issues.append(f"Unbalanced brackets: {content.count('[')} open, {content.count(']')} close")
        
        # Check for orphaned delimiters on their own lines
        lines = content.split('\n')
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped in [')', '}', ']']:
                issues.append(f"Line {i+1}: Orphaned closing delimiter '{stripped}'")
            elif stripped == '()' or stripped == '{}' or stripped == '[]':
                issues.append(f"Line {i+1}: Empty delimiter pair '{stripped}'")
        
        # Check for incomplete method calls
        if '.rotation3DEffect()' in content:
            # Check if it has proper parameters
            pattern = r'\.rotation3DEffect\(\s*\)'
            if re.search(pattern, content):
                issues.append("Empty rotation3DEffect() call - needs parameters")
        
        return len(issues) == 0, issues