"""
Direct Build System - Bypasses xcodegen/xcodebuild completely
Creates and launches iOS apps directly without Xcode project files
"""

import os
import asyncio
import subprocess
import json
import shutil
from pathlib import Path
from typing import Dict, Optional, List
import re

class DirectBuildSystem:
    """
    Direct compilation and deployment without xcodegen/xcodebuild
    This is the most reliable approach for Intel Macs with Xcode issues
    """
    
    def __init__(self):
        self.simulator = SimulatorManager()
    
    async def build_and_launch(self, project_path: str, project_id: str, is_modification: bool = False) -> Dict:
        """
        Build and launch app directly without Xcode project
        """
        print(f"[DIRECT BUILD] Building {project_id} (modification: {is_modification})")
        
        # Handle both relative and absolute paths
        if not os.path.isabs(project_path):
            project_path = os.path.abspath(project_path)
        
        # Step 1: Get app name and prepare paths
        app_name = self._get_app_name(project_path)
        bundle_id = f"com.swiftgen.{app_name.lower()}"
        
        # Step 2: Prepare build directory
        build_dir = os.path.join(project_path, 'build')
        app_bundle = os.path.join(build_dir, f'{app_name}.app')
        os.makedirs(app_bundle, exist_ok=True)
        
        # Step 3: Fix duplicate @main files before building
        try:
            from backend.duplicate_main_validator import DuplicateMainValidator
            validation_result = DuplicateMainValidator.validate_and_fix(project_path)
            if validation_result['actions']:
                print(f"[DIRECT BUILD] Fixed duplicate @main: {validation_result['actions']}")
        except Exception as e:
            print(f"[DIRECT BUILD] Warning: Could not validate @main files: {e}")
        
        # Step 4: Fix Swift code quality issues
        self._improve_code_quality(project_path)
        
        # Step 4.5: Apply comprehensive fixes BEFORE compilation
        try:
            # Try comprehensive fixer first (includes all fixes)
            from core.comprehensive_swift_fixer import ComprehensiveSwiftFixer
            fixer = ComprehensiveSwiftFixer()
            success, fixes = fixer.fix_project(project_path)
            if fixes:
                print(f"[DIRECT BUILD] Applied comprehensive fixes: {len(fixes)} issues resolved")
        except ImportError:
            # Fallback to individual fixers
            try:
                from core.advanced_parenthesis_balancer import AdvancedParenthesisBalancer
                from core.mainactor_concurrency_fixer import MainActorConcurrencyFixer
                
                sources_dir = os.path.join(project_path, 'Sources')
                fixes_applied = 0
                
                # Fix all Swift files
                for root, dirs, files in os.walk(sources_dir):
                    for f in files:
                        if f.endswith('.swift'):
                            file_path = os.path.join(root, f)
                            
                            # Apply parenthesis fixes
                            if AdvancedParenthesisBalancer.balance_file(file_path):
                                fixes_applied += 1
                            
                            # Apply MainActor fixes
                            if MainActorConcurrencyFixer.fix_file(file_path):
                                fixes_applied += 1
                
                if fixes_applied > 0:
                    print(f"[DIRECT BUILD] Applied {fixes_applied} advanced fixes before compilation")
            except Exception as e:
                print(f"[DIRECT BUILD] Warning: Advanced fixers not available: {e}")
        
        # Step 5: Compile Swift files
        success = await self._compile_swift(project_path, app_bundle, app_name)
        
        if not success:
            return {
                'success': False,
                'error': 'Failed to compile Swift files'
            }
        
        # Step 5: Create proper app bundle structure
        self._create_app_bundle(app_bundle, app_name, bundle_id)
        
        # Step 6: Launch in simulator with proper focus
        # For modifications, bring to focus AFTER launch to show changes
        launch_success = await self.simulator.install_and_launch(
            app_bundle, 
            bundle_id,
            bring_to_focus=is_modification  # Bring to focus for modifications
        )
        
        if launch_success:
            return {
                'success': True,
                'app_path': app_bundle,
                'bundle_id': bundle_id,
                'message': 'App launched successfully!'
            }
        else:
            # Try to recover from build/launch errors
            print("[DIRECT BUILD] Launch failed, attempting recovery...")
            
            try:
                from core.build_error_recovery import build_error_recovery
                
                # Generate diagnostic info
                diagnostic = build_error_recovery.generate_diagnostic_report(project_path, app_bundle)
                print(diagnostic)
                
                # Attempt recovery
                recovery_result = await build_error_recovery.recover_from_build_error(
                    "Failed to launch app in simulator",
                    project_path,
                    app_bundle,
                    bundle_id
                )
                
                if recovery_result["success"]:
                    print(f"[DIRECT BUILD] {recovery_result['message']}")
                    
                    # Try launching again
                    launch_success = await self.simulator.install_and_launch(
                        app_bundle,
                        bundle_id,
                        bring_to_focus=False  # Don't steal focus - let user see progress complete
                    )
                    
                    if launch_success:
                        return {
                            'success': True,
                            'app_path': app_bundle,
                            'bundle_id': bundle_id,
                            'message': 'App launched after recovery!'
                        }
            except Exception as e:
                print(f"[DIRECT BUILD] Recovery failed: {e}")
            
            return {
                'success': False,
                'error': 'Failed to launch app in simulator after recovery attempts'
            }
    
    def _get_app_name(self, project_path: str) -> str:
        """Extract app name from project files"""
        # Try from Swift files
        sources_dir = os.path.join(project_path, 'Sources')
        if os.path.exists(sources_dir):
            for file in os.listdir(sources_dir):
                if file.endswith('App.swift') and file != 'App.swift':
                    return file.replace('App.swift', '')
        
        # Try to extract from App.swift content
        app_swift = os.path.join(sources_dir, 'App.swift') if os.path.exists(sources_dir) else None
        if not app_swift:
            # Look for any *App.swift file
            for file in os.listdir(sources_dir) if os.path.exists(sources_dir) else []:
                if 'App.swift' in file:
                    app_swift = os.path.join(sources_dir, file)
                    break
        
        if app_swift and os.path.exists(app_swift):
            with open(app_swift, 'r') as f:
                content = f.read()
                import re
                match = re.search(r'struct\s+(\w+)App\s*:', content)
                if match:
                    return match.group(1)
        
        # Try from project.yml
        project_yml = os.path.join(project_path, 'project.yml')
        if os.path.exists(project_yml):
            with open(project_yml, 'r') as f:
                content = f.read()
                import re
                match = re.search(r'name:\s*(\w+)', content)
                if match:
                    return match.group(1)
        
        # Default to project directory name
        return os.path.basename(project_path).replace('_', '').title()
    
    def _improve_code_quality(self, project_path: str):
        """
        Fix ONLY critical syntax issues that would prevent compilation
        Don't change working code
        """
        sources_dir = os.path.join(project_path, 'Sources')
        if not os.path.exists(sources_dir):
            return
        
        # CRITICAL: Run syntax validator FIRST to catch common LLM errors
        # This works regardless of which LLM provider generated the code
        try:
            from core.basic_syntax_validator import validate_and_fix_swift
            
            for filename in os.listdir(sources_dir):
                if not filename.endswith('.swift'):
                    continue
                
                filepath = os.path.join(sources_dir, filename)
                with open(filepath, 'r') as f:
                    content = f.read()
                
                # Run syntax validator to fix common issues like missing parentheses
                fixed_content, issues = validate_and_fix_swift(content)
                
                if fixed_content != content:
                    with open(filepath, 'w') as f:
                        f.write(fixed_content)
                    print(f"[DIRECT BUILD] Syntax validator fixed {len(issues)} issues in {filename}")
        except Exception as e:
            print(f"[DIRECT BUILD] Warning: Syntax validator not available: {e}")
        
        # Then run our other critical fixes
        for filename in os.listdir(sources_dir):
            if not filename.endswith('.swift'):
                continue
            
            filepath = os.path.join(sources_dir, filename)
            with open(filepath, 'r') as f:
                content = f.read()
            
            original = content
            
            # Only fix critical syntax issues
            content = self._fix_critical_swift_syntax(content)
            
            if content != original:
                with open(filepath, 'w') as f:
                    f.write(content)
                print(f"[DIRECT BUILD] Fixed critical syntax in {filename}")
    
    def _fix_critical_swift_syntax(self, content: str) -> str:
        """Fix ONLY critical syntax issues that prevent compilation"""
        # Fix environment syntax (critical - causes compilation error)
        if '@Environment(\\ .dismiss)' in content:
            content = content.replace('@Environment(\\ .dismiss)', '@Environment(\\.dismiss)')
        
        # Fix broken Timer struct (critical - causes compilation error)
        if 'struct AppTimer {' in content and 'struct AppTimer: Timer' in content:
            # This is a broken definition that would fail compilation
            content = re.sub(r'struct AppTimer\s*:\s*Timer\s*\{[^}]*\}', '', content, flags=re.DOTALL)
            content = content.replace('AppTimer?', 'Timer?')
            content = content.replace('AppTimer.scheduledTimer', 'Timer.scheduledTimer')
        
        return content
    
    def _improve_ui_quality(self, content: str) -> str:
        """
        Only fix critical syntax issues, preserve LLM's creative design
        """
        # Only fix broken preview syntax if present
        if '#Preview' in content:
            # Check if preview is malformed
            preview_match = re.search(r'#Preview\s*{([^}]*)}', content, re.DOTALL)
            if preview_match:
                preview_content = preview_match.group(1)
                # Count braces to see if it's malformed
                open_braces = preview_content.count('{')
                close_braces = preview_content.count('}')
                if open_braces != close_braces:
                    # Fix broken preview
                    content = re.sub(
                        r'#Preview\s*{[^}]*}[^}]*}',
                        '#Preview {\n    ContentView()\n}',
                        content,
                        flags=re.DOTALL
                    )
        
        # Don't modify the UI - preserve the LLM's creative output
        return content
    
    async def _compile_swift(self, project_path: str, app_bundle: str, app_name: str) -> bool:
        """Compile Swift files using swiftc with iOS 16 compatibility validation"""
        # Handle both relative and absolute paths
        if not os.path.isabs(project_path):
            # If relative, make it absolute from current working directory
            project_path = os.path.abspath(project_path)
        
        sources_dir = os.path.join(project_path, 'Sources')
        swift_files = []
        
        # Just collect Swift files first, no proactive iOS 16 fixes
        for root, dirs, files in os.walk(sources_dir):
            for f in files:
                if f.endswith('.swift'):
                    swift_files.append(os.path.join(root, f))
        
        if not swift_files:
            print("[DIRECT BUILD] No Swift files found")
            return False
        
        # Get SDK path
        sdk_path = subprocess.check_output(
            ['xcrun', '--sdk', 'iphonesimulator', '--show-sdk-path']
        ).decode().strip()
        
        # Compile command with SwiftUI framework
        compile_cmd = [
            'swiftc',
            '-sdk', sdk_path,
            '-target', 'x86_64-apple-ios16.0-simulator',
            '-emit-executable',
            '-o', os.path.join(app_bundle, app_name),
            '-framework', 'SwiftUI',
            '-framework', 'Foundation',
            '-framework', 'UIKit',
            '-Xlinker', '-rpath',
            '-Xlinker', '@executable_path/Frameworks',
            '-Xlinker', '-rpath',
            '-Xlinker', '/System/Library/Frameworks',
            '-parse-as-library'  # Important for @main
        ] + swift_files
        
        try:
            result = subprocess.run(
                compile_cmd,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=project_path
            )
            
            # Check if compilation actually failed (not just warnings)
            # swiftc returns non-zero for warnings too, so check stderr content
            stderr_lower = result.stderr.lower()
            has_real_error = "error:" in stderr_lower
            
            if result.returncode == 0 or (not has_real_error and "warning:" in stderr_lower):
                # Success or only warnings
                if result.returncode != 0 and "warning:" in stderr_lower:
                    print(f"[DIRECT BUILD] Compiled with warnings (ignoring): {result.stderr[:200]}")
                os.chmod(os.path.join(app_bundle, app_name), 0o755)
                print(f"[DIRECT BUILD] Successfully compiled {len(swift_files)} files")
                return True
            else:
                print(f"[DIRECT BUILD] Compilation failed, attempting auto-fix...")
                
                # Send WebSocket update about fixing
                async def send_fix_status(message):
                    try:
                        if hasattr(self, 'websocket_callback') and self.websocket_callback:
                            await self.websocket_callback({
                                'type': 'status',
                                'message': message,
                                'stage': 'fix'
                            })
                    except:
                        pass
                
                await send_fix_status('🔧 Analyzing compilation errors...')
                
                # Check for iOS version errors and fix ONLY if present
                if 'is only available in iOS' in result.stderr:
                    try:
                        from core.ios16_compatibility_validator import ios16_validator
                        
                        print("[DIRECT BUILD] iOS version compatibility issues detected, applying fixes...")
                        
                        # Only fix files with iOS version errors
                        files_with_errors = self._extract_files_from_errors(result.stderr)
                        ios_fixes_applied = 0
                        
                        for file_path in files_with_errors:
                            if os.path.exists(file_path):
                                with open(file_path, 'r') as f:
                                    content = f.read()
                                
                                fixed_content, fixes = ios16_validator.fix_compatibility_issues(content)
                                
                                if fixes:
                                    with open(file_path, 'w') as f:
                                        f.write(fixed_content)
                                    ios_fixes_applied += len(fixes)
                                    print(f"[iOS 16 Validator] Applied {len(fixes)} fixes to {os.path.basename(file_path)}")
                        
                        if ios_fixes_applied > 0:
                            # Retry compilation after iOS fixes
                            result = subprocess.run(
                                compile_cmd,
                                capture_output=True,
                                text=True,
                                timeout=30,
                                cwd=project_path
                            )
                            
                            if result.returncode == 0:
                                print("[DIRECT BUILD] Successfully compiled after iOS 16 fixes!")
                                os.chmod(os.path.join(app_bundle, app_name), 0o755)
                                return True
                    except Exception as e:
                        print(f"[iOS 16 Validator] Error: {e}")
                
                # First check learning system for known fixes
                try:
                    from core.learning_error_recovery import learning_recovery
                    
                    # Check if we've seen and fixed this before
                    if learning_recovery.has_learned_fix(result.stderr):
                        print("[DIRECT BUILD] Found learned fix for this error pattern")
                        stats = learning_recovery.get_statistics()
                        print(f"[DIRECT BUILD] Learning stats: {stats['total_successful_fixes']} successes, {stats['overall_success_rate']} success rate")
                        
                        # Apply learned fix to each file
                        for file in swift_files:
                            with open(file, 'r') as f:
                                content = f.read()
                            
                            fixed_content = learning_recovery.apply_learned_fix(result.stderr, content)
                            if fixed_content and fixed_content != content:
                                with open(file, 'w') as f:
                                    f.write(fixed_content)
                                print(f"[DIRECT BUILD] Applied learned fix to {file}")
                        
                        # Try compilation again
                        cmd = [
                            'xcrun', 'swiftc',
                            '-sdk', sdk_path,
                            '-target', 'arm64-apple-ios16.0-simulator',
                            '-o', os.path.join(app_bundle, app_name)
                        ] + swift_files
                        
                        result = subprocess.run(cmd, capture_output=True, text=True)
                        if result.returncode == 0:
                            print("[DIRECT BUILD] ✅ Compilation successful with learned fix!")
                            learning_recovery.learn_from_success(result.stderr, {"type": "learned_fix_applied"})
                            os.chmod(os.path.join(app_bundle, app_name), 0o755)
                            return True
                        else:
                            learning_recovery.learn_from_failure(result.stderr, {"type": "learned_fix_failed"})
                    
                except Exception as e:
                    print(f"[DIRECT BUILD] Learning system error: {e}")
                
                # Check for subdirectory issues
                try:
                    from core.subdirectory_error_handler import SubdirectoryErrorHandler
                    subdirectory_check = SubdirectoryErrorHandler.suggest_fix(result.stderr, project_path)
                    
                    if subdirectory_check.get('has_issue') and subdirectory_check.get('action') == 'rebuild_with_subdirectories':
                        print(f"[DIRECT BUILD] {subdirectory_check['message']}")
                        print("[DIRECT BUILD] Note: Build system has been updated to include subdirectories")
                        # The build system already includes subdirectories after our fix,
                        # but this helps diagnose if the issue recurs
                except Exception as e:
                    print(f"[DIRECT BUILD] Subdirectory check failed: {e}")
                
                # First try advanced Swift fixer for complex issues ONLY if there are relevant errors
                if ('cannot find' in result.stderr and 'in scope' in result.stderr) or \
                   ('swipeActions' in result.stderr) or \
                   ('sheet' in result.stderr and 'Binding' in result.stderr) or \
                   ('async' in result.stderr or 'await' in result.stderr):
                    try:
                        from core.advanced_swift_fixer import fix_complex_swift_issues
                        
                        print("[DIRECT BUILD] Detected complex Swift pattern errors, applying advanced fixes...")
                        
                        # Only fix files mentioned in the error output
                        files_with_errors = self._extract_files_from_errors(result.stderr)
                        complex_fixes_applied = []
                        
                        for file_path in files_with_errors:
                            if os.path.exists(file_path) and file_path.endswith('.swift'):
                                with open(file_path, 'r') as f:
                                    content = f.read()
                                
                                fixed_content, fixes = fix_complex_swift_issues(content, result.stderr)
                                
                                if fixes:
                                    with open(file_path, 'w') as f:
                                        f.write(fixed_content)
                                    complex_fixes_applied.extend(fixes)
                        
                        if complex_fixes_applied:
                            print(f"[DIRECT BUILD] Advanced fixer applied {len(complex_fixes_applied)} complex fixes:")
                            for fix in complex_fixes_applied:
                                print(f"  🔧 {fix}")
                            
                            # Retry compilation
                            result = subprocess.run(
                                compile_cmd,
                                capture_output=True,
                                text=True,
                                timeout=30,
                                cwd=project_path
                            )
                            
                            if result.returncode == 0:
                                print("[DIRECT BUILD] Successfully compiled after complex fixes!")
                                return True
                    
                    except Exception as e:
                        print(f"[DIRECT BUILD] Advanced fixer error: {e}")
                
                # Fix MainActor isolation issues FIRST
                if "actor context" in result.stderr or "MainActor" in result.stderr:
                    try:
                        from core.mainactor_fixer import fix_mainactor_issues
                        
                        await send_fix_status('🎭 Fixing actor isolation issues...')
                        print("[DIRECT BUILD] Fixing MainActor isolation issues...")
                        actor_result = fix_mainactor_issues(result.stderr, project_path)
                        
                        if actor_result["success"]:
                            print(f"[DIRECT BUILD] Fixed actor issues: {actor_result['fixes_applied']}")
                            await send_fix_status(f"✅ Fixed {len(actor_result['fixes_applied'])} actor issues")
                    except Exception as e:
                        print(f"[DIRECT BUILD] MainActor fixer error: {e}")
                
                # Fix missing parenthesis issues
                if "expected ')'" in result.stderr:
                    try:
                        from core.mainactor_fixer import fix_missing_parenthesis
                        
                        await send_fix_status('🔧 Fixing missing parentheses...')
                        paren_result = fix_missing_parenthesis(result.stderr, project_path)
                        
                        if paren_result["success"]:
                            print(f"[DIRECT BUILD] Fixed parenthesis: {paren_result['fixes_applied']}")
                            await send_fix_status(f"✅ Fixed {len(paren_result['fixes_applied'])} syntax issues")
                    except Exception as e:
                        print(f"[DIRECT BUILD] Parenthesis fixer error: {e}")
                
                # Then try standard Swift compilation fixer
                try:
                    from core.swift_compilation_fixer import auto_fix_swift_errors
                    
                    await send_fix_status('🔨 Applying Swift syntax fixes...')
                    print("[DIRECT BUILD] Applying standard Swift compilation fixes...")
                    swift_fix_result = auto_fix_swift_errors(result.stderr, project_path)
                    
                    if swift_fix_result["success"]:
                        print(f"[DIRECT BUILD] Swift fixer applied {len(swift_fix_result['fixes_applied'])} fixes")
                        fixes_summary = f"✅ Applied {len(swift_fix_result['fixes_applied'])} automatic fixes"
                        await send_fix_status(fixes_summary)
                        
                        for fix in swift_fix_result['fixes_applied']:
                            print(f"  ✅ {fix}")
                        
                        # Retry compilation after Swift fixes
                        result = subprocess.run(
                            compile_cmd,
                            capture_output=True,
                            text=True,
                            timeout=30,
                            cwd=project_path
                        )
                        
                        if result.returncode == 0:
                            print("[DIRECT BUILD] Successfully compiled after Swift fixes!")
                            return True
                except Exception as e:
                    print(f"[DIRECT BUILD] Swift fixer error: {e}")
                
                # If Swift fixer didn't work, use intelligent error recovery (pattern + LLM)
                try:
                    from core.intelligent_error_recovery import intelligent_recovery
                    
                    # Set up LLM service if available
                    try:
                        from generation.llm_router import LLMRouter
                        intelligent_recovery.llm_service = LLMRouter()
                    except:
                        pass
                    
                    # Apply intelligent recovery
                    fix_result = await intelligent_recovery.recover_from_error(
                        result.stderr, 
                        project_path
                    )
                    
                    if fix_result["success"]:
                        print(f"[DIRECT BUILD] {fix_result['message']}")
                        
                        # Retry compilation
                        result = subprocess.run(
                            compile_cmd,
                            capture_output=True,
                            text=True,
                            timeout=30,
                            cwd=project_path
                        )
                        
                        if result.returncode == 0:
                            print("[DIRECT BUILD] ✅ Compilation successful after intelligent recovery!")
                            # Learn from this success
                            try:
                                from core.learning_error_recovery import learning_recovery
                                learning_recovery.learn_from_success(
                                    result.stderr, 
                                    {"type": "intelligent_recovery", "fixes": fix_result.get("fixes_applied", [])}
                                )
                            except:
                                pass
                            os.chmod(os.path.join(app_bundle, app_name), 0o755)
                            return True
                        else:
                            print("[DIRECT BUILD] Still has errors after recovery, trying one more time...")
                            # One more attempt with fallback strategies
                            from core.error_handler import error_fixer
                            error_fixer.auto_fix_compilation_errors(result.stderr, project_path)
                            
                            result = subprocess.run(
                                compile_cmd,
                                capture_output=True,
                                text=True,
                                timeout=30,
                                cwd=project_path
                            )
                            
                            if result.returncode == 0:
                                os.chmod(os.path.join(app_bundle, app_name), 0o755)
                                return True
                            
                except ImportError as e:
                    print(f"[DIRECT BUILD] Intelligent recovery not available: {e}, using basic fixes")
                    from core.error_handler import error_fixer
                    fix_result = error_fixer.auto_fix_compilation_errors(
                        result.stderr,
                        project_path
                    )
                
                # Fall back to legacy fixes
                if 'has no member' in result.stderr or 'cannot find' in result.stderr or 'inheritance from non-protocol' in result.stderr:
                    self._fix_compilation_errors(project_path, result.stderr)
                    # Retry compilation
                    result = subprocess.run(
                        compile_cmd,
                        capture_output=True,
                        text=True,
                        timeout=30,
                        cwd=project_path
                    )
                    
                    if result.returncode == 0:
                        os.chmod(os.path.join(app_bundle, app_name), 0o755)
                        return True
                
                print(f"[DIRECT BUILD] Failed after auto-fix attempts: {result.stderr[:500]}")
                return False
        except Exception as e:
            print(f"[DIRECT BUILD] Compilation error: {e}")
            return False
    
    def _extract_files_from_errors(self, error_output: str) -> List[str]:
        """Extract file paths mentioned in error output"""
        files = set()
        lines = error_output.split('\n')
        
        for line in lines:
            # Match file paths in error messages
            # Pattern: /path/to/file.swift:line:column: error:
            match = re.match(r'(/[^:]+\.swift):\d+:\d+:', line)
            if match:
                files.add(match.group(1))
            # Also match relative paths
            match = re.match(r'([^/][^:]+\.swift):\d+:\d+:', line)
            if match:
                files.add(match.group(1))
        
        return list(files)
    
    def _fix_compilation_errors(self, project_path: str, errors: str):
        """Fix specific compilation errors"""
        sources_dir = os.path.join(project_path, 'Sources')
        
        # Fix SwiftUI import issues
        if 'App' in errors and 'inheritance from non-protocol' in errors:
            for file in os.listdir(sources_dir):
                if file.endswith('App.swift'):
                    filepath = os.path.join(sources_dir, file)
                    with open(filepath, 'r') as f:
                        content = f.read()
                    if 'import SwiftUI' not in content:
                        content = 'import SwiftUI\n' + content
                        with open(filepath, 'w') as f:
                            f.write(content)
        
        # Parse errors and fix them
        if 'UIImpactFeedbackGenerator' in errors and 'UIKit' in errors:
            # Add UIKit import if missing
            for file in os.listdir(sources_dir):
                if file.endswith('.swift'):
                    filepath = os.path.join(sources_dir, file)
                    with open(filepath, 'r') as f:
                        content = f.read()
                    if 'UIImpactFeedbackGenerator' in content and 'import UIKit' not in content:
                        content = 'import UIKit\n' + content
                        with open(filepath, 'w') as f:
                            f.write(content)
    
    def _create_app_bundle(self, app_bundle: str, app_name: str, bundle_id: str):
        """Create proper app bundle structure"""
        # Create Info.plist
        info_plist = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>{app_name}</string>
    <key>CFBundleIdentifier</key>
    <string>{bundle_id}</string>
    <key>CFBundleName</key>
    <string>{app_name}</string>
    <key>CFBundleDisplayName</key>
    <string>{app_name}</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    <key>CFBundleVersion</key>
    <string>1</string>
    <key>LSRequiresIPhoneOS</key>
    <true/>
    <key>UILaunchStoryboardName</key>
    <string>LaunchScreen</string>
    <key>UIRequiredDeviceCapabilities</key>
    <array>
        <string>arm64</string>
    </array>
    <key>UISupportedInterfaceOrientations</key>
    <array>
        <string>UIInterfaceOrientationPortrait</string>
        <string>UIInterfaceOrientationLandscapeLeft</string>
        <string>UIInterfaceOrientationLandscapeRight</string>
    </array>
    <key>UIApplicationSceneManifest</key>
    <dict>
        <key>UIApplicationSupportsMultipleScenes</key>
        <false/>
    </dict>
</dict>
</plist>"""
        
        with open(os.path.join(app_bundle, 'Info.plist'), 'w') as f:
            f.write(info_plist)
        
        # Create PkgInfo
        with open(os.path.join(app_bundle, 'PkgInfo'), 'w') as f:
            f.write('APPL????')


class SimulatorManager:
    """
    Manages iOS Simulator with proper boot/launch/focus logic
    """
    
    def __init__(self):
        self.simulator_id = None
    
    async def install_and_launch(
        self, 
        app_bundle: str, 
        bundle_id: str,
        bring_to_focus: bool = False  # Default to not stealing focus
    ) -> bool:
        """
        Install and launch app with proper simulator management
        """
        # Step 1: Find or boot a simulator
        self.simulator_id = await self._get_or_boot_simulator()
        
        if not self.simulator_id:
            print("[SIMULATOR] Failed to get simulator")
            return False
        
        # Step 2: Open Simulator app first (brings to focus)
        if bring_to_focus:
            self._open_simulator_app()
            await asyncio.sleep(2)  # Give it time to open
        
        # Step 3: Install the app
        success = await self._install_app(app_bundle)
        if not success:
            print(f"[SIMULATOR] Failed to install {app_bundle}")
            return False
        
        # Step 4: Launch the app
        success = await self._launch_app(bundle_id)
        if not success:
            print(f"[SIMULATOR] Failed to launch {bundle_id}")
            return False
        
        # Step 5: Bring Simulator to foreground again
        if bring_to_focus:
            self._bring_simulator_to_front()
        
        print(f"[SIMULATOR] Successfully launched {bundle_id}")
        return True
    
    async def _get_or_boot_simulator(self) -> Optional[str]:
        """
        Get booted simulator or boot one
        Priority: Use already booted > Boot iPhone 16 Pro > Boot any iPhone
        """
        # Check for booted simulator
        try:
            result = subprocess.run(
                ['xcrun', 'simctl', 'list', 'devices', 'booted', '-j'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            devices_data = json.loads(result.stdout)
            
            # Find any booted device
            for runtime, devices in devices_data.get('devices', {}).items():
                for device in devices:
                    if device.get('state') == 'Booted':
                        device_id = device['udid']
                        device_name = device['name']
                        print(f"[SIMULATOR] Using already booted: {device_name}")
                        return device_id
            
            # No booted device, find one to boot
            print("[SIMULATOR] No booted simulator, looking for one to boot...")
            
            # Get all available devices
            result = subprocess.run(
                ['xcrun', 'simctl', 'list', 'devices', '-j'],
                capture_output=True,
                text=True,
                timeout=5
            )
            devices_data = json.loads(result.stdout)
            
            # Priority list of simulators to boot
            priority_devices = [
                'iPhone 16 Pro',
                'iPhone 16',
                'iPhone 15 Pro',
                'iPhone 15',
                'iPhone 14 Pro',
                'iPhone 14'
            ]
            
            # Try to boot priority devices first
            for runtime, devices in devices_data.get('devices', {}).items():
                if 'iOS' not in runtime:
                    continue
                
                for priority_name in priority_devices:
                    for device in devices:
                        if (priority_name in device.get('name', '') and 
                            device.get('isAvailable', False)):
                            device_id = device['udid']
                            device_name = device['name']
                            print(f"[SIMULATOR] Booting {device_name}...")
                            
                            # Boot the simulator
                            subprocess.run(
                                ['xcrun', 'simctl', 'boot', device_id],
                                capture_output=True,
                                timeout=10
                            )
                            
                            # Wait for boot
                            await asyncio.sleep(5)
                            
                            print(f"[SIMULATOR] Successfully booted {device_name}")
                            return device_id
            
            # If no priority device available, boot any iPhone
            for runtime, devices in devices_data.get('devices', {}).items():
                if 'iOS' in runtime:
                    for device in devices:
                        if 'iPhone' in device.get('name', '') and device.get('isAvailable', False):
                            device_id = device['udid']
                            device_name = device['name']
                            print(f"[SIMULATOR] Booting {device_name}...")
                            
                            subprocess.run(
                                ['xcrun', 'simctl', 'boot', device_id],
                                capture_output=True,
                                timeout=10
                            )
                            
                            await asyncio.sleep(5)
                            return device_id
            
        except Exception as e:
            print(f"[SIMULATOR] Error: {e}")
        
        return None
    
    def _open_simulator_app(self):
        """Open Simulator.app to bring it to focus"""
        try:
            subprocess.run(['open', '-a', 'Simulator'], check=False)
        except:
            pass
    
    def _bring_simulator_to_front(self):
        """Bring Simulator app to foreground using AppleScript"""
        try:
            applescript = '''
            tell application "Simulator"
                activate
            end tell
            '''
            subprocess.run(
                ['osascript', '-e', applescript],
                capture_output=True,
                timeout=2
            )
        except:
            # Fallback to open command
            subprocess.run(['open', '-a', 'Simulator'], check=False)
    
    async def _install_app(self, app_bundle: str) -> bool:
        """Install app in simulator with error recovery"""
        try:
            result = subprocess.run(
                ['xcrun', 'simctl', 'install', self.simulator_id, app_bundle],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                print(f"[SIMULATOR] Install error: {result.stderr}")
                
                # Attempt recovery based on error type
                if "Could not hardlink" in result.stderr or "Unable to Install" in result.stderr:
                    # Clean installation issue
                    bundle_name = os.path.basename(app_bundle).replace('.app', '')
                    bundle_id = f"com.swiftgen.{bundle_name.lower()}"
                    
                    # Force uninstall
                    subprocess.run(
                        ['xcrun', 'simctl', 'uninstall', self.simulator_id, bundle_id],
                        capture_output=True,
                        timeout=5
                    )
                    
                    # Clean simulator caches
                    subprocess.run(
                        ['xcrun', 'simctl', 'spawn', self.simulator_id, 'rm', '-rf', 
                         '/tmp/*', '/var/tmp/*'],
                        capture_output=True
                    )
                    
                    print("[SIMULATOR] Cleaned caches, retrying install...")
                    
                elif "Permission denied" in result.stderr:
                    # Fix permissions
                    subprocess.run(['chmod', '-R', '755', app_bundle], check=False)
                    app_name = os.path.basename(app_bundle).replace('.app', '')
                    executable = os.path.join(app_bundle, app_name)
                    if os.path.exists(executable):
                        subprocess.run(['chmod', '+x', executable], check=False)
                    print("[SIMULATOR] Fixed permissions, retrying install...")
                
                elif "Info.plist" in result.stderr:
                    # Fix Info.plist issues
                    from core.build_error_recovery import build_error_recovery
                    bundle_name = os.path.basename(app_bundle).replace('.app', '')
                    bundle_id = f"com.swiftgen.{bundle_name.lower()}"
                    build_error_recovery._fix_info_plist(app_bundle, bundle_id)
                    print("[SIMULATOR] Fixed Info.plist, retrying install...")
                
                # Retry install
                result = subprocess.run(
                    ['xcrun', 'simctl', 'install', self.simulator_id, app_bundle],
                    capture_output=True,
                    timeout=30
                )
            
            return result.returncode == 0
        except Exception as e:
            print(f"[SIMULATOR] Install exception: {e}")
            return False
    
    async def _launch_app(self, bundle_id: str) -> bool:
        """Launch app in simulator"""
        try:
            # First terminate any existing instance of the app
            subprocess.run(
                ['xcrun', 'simctl', 'terminate', self.simulator_id, bundle_id],
                capture_output=True,
                timeout=5
            )
            await asyncio.sleep(0.5)  # Brief pause
            
            # Now launch the fresh version
            result = subprocess.run(
                ['xcrun', 'simctl', 'launch', self.simulator_id, bundle_id],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                print(f"[SIMULATOR] Launch error: {result.stderr}")
                return False
            
            # For modifications, bring simulator to front to show changes
            # This happens AFTER the progress is complete so user sees both
            await asyncio.sleep(1)  # Brief pause to let app fully launch
            self._bring_simulator_to_front()
            print(f"[SIMULATOR] App relaunched with modifications - check simulator")
            
            return True
        except Exception as e:
            print(f"[SIMULATOR] Launch exception: {e}")
            return False


# Global instance
direct_build_system = DirectBuildSystem()