"""
Simple Builder - Just build with xcodebuild, no fancy strategies
If it fails or hangs, open in Xcode. That's it.
"""

import asyncio
import subprocess
import os
import json
import signal
import time
from typing import Dict, Optional, Tuple
from pathlib import Path
from datetime import datetime

class BuildResult:
    def __init__(self, success: bool, app_path: Optional[str] = None, 
                 error: Optional[str] = None, fallback: Optional[str] = None):
        self.success = success
        self.app_path = app_path
        self.error = error
        self.fallback = fallback

class SimpleBuilder:
    """
    Dead simple builder - tries xcodebuild once with hard timeout
    No retries, no complex strategies. Just build or bail.
    """
    
    # CRITICAL: Hard timeout to prevent hanging
    BUILD_TIMEOUT = 30  # 30 seconds max
    XCODEGEN_TIMEOUT = 10  # 10 seconds for xcodegen
    
    def __init__(self):
        self.simulator_id = None
        self._ensure_simulator()
        
        # Try to use existing working build system if available
        try:
            import sys
            sys.path.insert(0, '/Users/hirakbanerjee/Desktop/SwiftGen_Clean/stable_reference/backend')
            from WORKING_BUILD_FIX import working_build_system
            self.working_build = working_build_system
            print("[Builder] Using existing WorkingBuildSystem as fallback")
        except:
            self.working_build = None
    
    def _ensure_simulator(self):
        """Make sure we have a simulator ready"""
        try:
            # Get booted simulator
            result = subprocess.run(
                ['xcrun', 'simctl', 'list', 'devices', 'booted', '-j'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                devices = json.loads(result.stdout)
                for runtime, device_list in devices.get('devices', {}).items():
                    for device in device_list:
                        if device.get('state') == 'Booted':
                            self.simulator_id = device['udid']
                            print(f"[Builder] Using booted simulator: {device['name']}")
                            return
            
            # No booted simulator, try to boot one
            self._boot_simulator()
            
        except Exception as e:
            print(f"[Builder] Simulator check failed: {e}")
    
    def _boot_simulator(self):
        """Boot a simulator if none are running"""
        try:
            # Get available simulators
            result = subprocess.run(
                ['xcrun', 'simctl', 'list', 'devices', '-j'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                devices = json.loads(result.stdout)
                # Find first available iPhone simulator
                for runtime, device_list in devices.get('devices', {}).items():
                    if 'iOS' in runtime:
                        for device in device_list:
                            if 'iPhone' in device.get('name', '') and device.get('isAvailable'):
                                device_id = device['udid']
                                print(f"[Builder] Booting simulator: {device['name']}")
                                
                                # Boot it
                                subprocess.run(
                                    ['xcrun', 'simctl', 'boot', device_id],
                                    capture_output=True,
                                    timeout=10
                                )
                                
                                self.simulator_id = device_id
                                time.sleep(3)  # Give it time to boot
                                return
                                
        except Exception as e:
            print(f"[Builder] Failed to boot simulator: {e}")
    
    async def build(self, project_path: str, project_id: str) -> Dict:
        """
        Build the project with xcodebuild
        Hard timeout, no retries
        """
        print(f"[Builder] Starting build for {project_id}")
        start_time = time.time()
        
        # Step 1: Ensure we have an xcodeproj
        xcodeproj = await self._ensure_xcodeproj(project_path)
        if not xcodeproj:
            return {
                'success': False,
                'error': 'Failed to create Xcode project',
                'fallback': 'manual_xcodegen'
            }
        
        # Step 2: Try to build with xcodebuild
        build_result = await self._run_xcodebuild(project_path, xcodeproj)
        
        # Step 3: Return result with clear fallback
        if build_result['success']:
            print(f"[Builder] Build successful in {time.time() - start_time:.1f}s")
            # Find the built app
            app_path = self._find_app_bundle(project_path)
            return {
                'success': True,
                'app_path': app_path,
                'duration': time.time() - start_time
            }
        else:
            print(f"[Builder] Build failed: {build_result['error']}")
            return {
                'success': False,
                'error': build_result['error'],
                'fallback': 'open_in_xcode',
                'xcodeproj_path': os.path.join(project_path, xcodeproj),
                'duration': time.time() - start_time
            }
    
    async def _ensure_xcodeproj(self, project_path: str) -> Optional[str]:
        """Ensure we have an Xcode project file"""
        # Check if xcodeproj already exists
        for item in os.listdir(project_path):
            if item.endswith('.xcodeproj'):
                print(f"[Builder] Found existing xcodeproj: {item}")
                return item
        
        # No xcodeproj, try xcodegen
        print("[Builder] Running xcodegen...")
        try:
            process = await asyncio.create_subprocess_exec(
                'xcodegen',
                cwd=project_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.XCODEGEN_TIMEOUT
                )
                
                if process.returncode == 0:
                    # Check if xcodeproj was created
                    for item in os.listdir(project_path):
                        if item.endswith('.xcodeproj'):
                            print(f"[Builder] xcodegen created: {item}")
                            return item
                else:
                    print(f"[Builder] xcodegen failed: {stderr.decode()}")
                    
            except asyncio.TimeoutError:
                print(f"[Builder] xcodegen timeout after {self.XCODEGEN_TIMEOUT}s")
                process.kill()
                await process.wait()
                
        except Exception as e:
            print(f"[Builder] xcodegen error: {e}")
        
        return None
    
    async def _run_xcodebuild(self, project_path: str, xcodeproj: str) -> Dict:
        """
        Run xcodebuild with HARD timeout
        Kill it if it hangs
        """
        scheme = xcodeproj.replace('.xcodeproj', '')
        
        # Build command - simple and direct
        build_cmd = [
            'xcodebuild',
            '-project', xcodeproj,
            '-scheme', scheme,
            '-configuration', 'Debug',
            'CODE_SIGN_IDENTITY=',
            'CODE_SIGNING_REQUIRED=NO',
            'CODE_SIGNING_ALLOWED=NO',
            'build'
        ]
        
        # Add simulator destination if we have one
        if self.simulator_id:
            build_cmd.extend(['-destination', f'id={self.simulator_id}'])
        else:
            build_cmd.extend(['-destination', 'generic/platform=iOS Simulator'])
        
        print(f"[Builder] Running xcodebuild (timeout: {self.BUILD_TIMEOUT}s)...")
        
        try:
            process = await asyncio.create_subprocess_exec(
                *build_cmd,
                cwd=project_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            try:
                # CRITICAL: Hard timeout on build
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.BUILD_TIMEOUT
                )
                
                if process.returncode == 0:
                    print("[Builder] xcodebuild succeeded")
                    return {'success': True}
                else:
                    # Extract meaningful error
                    error_msg = self._extract_build_error(stderr.decode())
                    return {
                        'success': False,
                        'error': error_msg
                    }
                    
            except asyncio.TimeoutError:
                # CRITICAL: Kill hanging xcodebuild
                print(f"[Builder] xcodebuild timeout - killing process")
                process.kill()
                await process.wait()
                
                # Also kill any zombie xcodebuild processes
                subprocess.run(['pkill', '-9', 'xcodebuild'], capture_output=True)
                
                return {
                    'success': False,
                    'error': f'Build timeout after {self.BUILD_TIMEOUT} seconds'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Build failed: {str(e)}'
            }
    
    def _extract_build_error(self, stderr: str) -> str:
        """Extract meaningful error from xcodebuild output"""
        # Look for actual error messages
        lines = stderr.split('\n')
        for line in lines:
            if 'error:' in line.lower():
                return line.strip()
        
        # If no specific error, return last few lines
        relevant_lines = [l for l in lines if l.strip() and not l.startswith('Command')]
        if relevant_lines:
            return ' '.join(relevant_lines[-3:])
        
        return "Build failed (no specific error message)"
    
    def _find_app_bundle(self, project_path: str) -> Optional[str]:
        """Find the built .app bundle"""
        # Look in standard build directories
        possible_paths = [
            'build/Build/Products/Debug-iphonesimulator',
            'build/Build/Products/Debug-iphoneos',
            'DerivedData/Build/Products/Debug-iphonesimulator'
        ]
        
        for build_path in possible_paths:
            full_path = os.path.join(project_path, build_path)
            if os.path.exists(full_path):
                for item in os.listdir(full_path):
                    if item.endswith('.app'):
                        app_path = os.path.join(full_path, item)
                        print(f"[Builder] Found app bundle: {app_path}")
                        return app_path
        
        return None
    
    async def open_in_xcode(self, project_path: str) -> Dict:
        """
        Fallback: Just open the project in Xcode
        Let the user press Cmd+R
        """
        xcodeproj = None
        for item in os.listdir(project_path):
            if item.endswith('.xcodeproj'):
                xcodeproj = item
                break
        
        if xcodeproj:
            xcodeproj_path = os.path.join(project_path, xcodeproj)
            subprocess.run(['open', xcodeproj_path])
            
            return {
                'success': True,
                'message': 'Project opened in Xcode. Press Cmd+R to run.',
                'xcodeproj_path': xcodeproj_path
            }
        else:
            return {
                'success': False,
                'error': 'No Xcode project found to open'
            }
    
    def cleanup_zombies(self):
        """Clean up any hanging xcodebuild processes"""
        try:
            subprocess.run(['pkill', '-9', 'xcodebuild'], capture_output=True)
            subprocess.run(['pkill', '-9', 'ibtoold'], capture_output=True)
            subprocess.run(['pkill', '-9', 'ibtool'], capture_output=True)
            print("[Builder] Cleaned up zombie processes")
        except:
            pass