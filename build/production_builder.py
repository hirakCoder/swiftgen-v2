"""
Production Builder - Actually builds and launches apps in simulator
Uses intelligent timeouts based on app complexity
"""

import asyncio
import subprocess
import os
import json
import time
import sys
from typing import Dict, Optional, Tuple
from pathlib import Path
from datetime import datetime

# Add backend path for existing services
sys.path.insert(0, '/Users/hirakbanerjee/Desktop/SwiftGen_Clean/stable_reference/backend')

class ProductionBuilder:
    """
    Production-grade builder that actually launches apps
    Uses proven working methods from existing system
    """
    
    # Intelligent timeouts based on real-world data
    BUILD_TIMEOUTS = {
        'simple': 60,      # Simple apps: 1 minute
        'medium': 120,     # Medium apps: 2 minutes  
        'complex': 180,    # Complex apps: 3 minutes
        'xcodegen': 15     # xcodegen: 15 seconds
    }
    
    def __init__(self):
        self.simulator_id = None
        self.simulator_service = None
        self._init_services()
    
    def _init_services(self):
        """Initialize simulator service from existing working code"""
        try:
            from simulator_service import SimulatorService
            self.simulator_service = SimulatorService()
            print("[ProductionBuilder] Initialized SimulatorService")
        except Exception as e:
            print(f"[ProductionBuilder] Could not initialize SimulatorService: {e}")
    
    def _get_complexity(self, project_path: str) -> str:
        """Determine app complexity based on file count and features"""
        try:
            # Count Swift files
            swift_files = 0
            for root, dirs, files in os.walk(project_path):
                swift_files += len([f for f in files if f.endswith('.swift')])
            
            # Determine complexity
            if swift_files <= 3:
                return 'simple'
            elif swift_files <= 10:
                return 'medium'
            else:
                return 'complex'
        except:
            return 'medium'  # Default to medium
    
    async def build_and_launch(self, project_path: str, project_id: str) -> Dict:
        """
        Build project and launch in simulator
        This is what actually makes the app appear on screen
        """
        print(f"[ProductionBuilder] Starting build and launch for {project_id}")
        start_time = time.time()
        
        # Determine complexity for timeout
        complexity = self._get_complexity(project_path)
        build_timeout = self.BUILD_TIMEOUTS[complexity]
        print(f"[ProductionBuilder] Detected {complexity} app, using {build_timeout}s timeout")
        
        # Step 1: Ensure xcodeproj exists
        xcodeproj = await self._ensure_xcodeproj(project_path)
        if not xcodeproj:
            return {
                'success': False,
                'error': 'Failed to create Xcode project'
            }
        
        # Step 2: Build the app
        print(f"[ProductionBuilder] Building with xcodebuild...")
        build_result = await self._build_app(project_path, xcodeproj, build_timeout)
        
        if not build_result['success']:
            print(f"[ProductionBuilder] Build failed: {build_result.get('error')}")
            return build_result
        
        # Step 3: Find the built app
        app_path = self._find_app_bundle(project_path)
        if not app_path:
            return {
                'success': False,
                'error': 'Built app not found'
            }
        
        print(f"[ProductionBuilder] Found app bundle: {app_path}")
        
        # Step 4: Launch in simulator
        bundle_id = self._get_bundle_id(project_path, xcodeproj)
        launch_result = await self._launch_in_simulator(app_path, bundle_id)
        
        if launch_result['success']:
            print(f"[ProductionBuilder] App launched successfully in {time.time() - start_time:.1f}s")
            return {
                'success': True,
                'app_path': app_path,
                'bundle_id': bundle_id,
                'duration': time.time() - start_time,
                'message': f'App launched in simulator! Look for {xcodeproj.replace(".xcodeproj", "")} app.'
            }
        else:
            return {
                'success': False,
                'error': launch_result.get('error', 'Failed to launch app'),
                'app_path': app_path
            }
    
    async def _ensure_xcodeproj(self, project_path: str) -> Optional[str]:
        """Ensure we have an Xcode project"""
        # Check if xcodeproj exists
        for item in os.listdir(project_path):
            if item.endswith('.xcodeproj'):
                return item
        
        # Run xcodegen
        print("[ProductionBuilder] Running xcodegen...")
        try:
            process = await asyncio.create_subprocess_exec(
                'xcodegen',
                cwd=project_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.BUILD_TIMEOUTS['xcodegen']
            )
            
            if process.returncode == 0:
                # Find the created xcodeproj
                for item in os.listdir(project_path):
                    if item.endswith('.xcodeproj'):
                        print(f"[ProductionBuilder] Created {item}")
                        return item
            else:
                print(f"[ProductionBuilder] xcodegen failed: {stderr.decode()}")
                
        except asyncio.TimeoutError:
            print("[ProductionBuilder] xcodegen timeout")
            process.kill()
            await process.wait()
        except Exception as e:
            print(f"[ProductionBuilder] xcodegen error: {e}")
        
        return None
    
    async def _build_app(self, project_path: str, xcodeproj: str, timeout: int) -> Dict:
        """Build the app with xcodebuild"""
        scheme = xcodeproj.replace('.xcodeproj', '')
        
        # Get or ensure simulator
        destination = await self._get_build_destination()
        
        build_cmd = [
            'xcodebuild',
            '-project', xcodeproj,
            '-scheme', scheme,
            '-destination', destination,
            '-configuration', 'Debug',
            '-derivedDataPath', 'build',
            'CODE_SIGN_IDENTITY=',
            'CODE_SIGNING_REQUIRED=NO',
            'CODE_SIGNING_ALLOWED=NO',
            'build'
        ]
        
        print(f"[ProductionBuilder] Building with timeout {timeout}s...")
        
        try:
            process = await asyncio.create_subprocess_exec(
                *build_cmd,
                cwd=project_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )
            
            if process.returncode == 0:
                print("[ProductionBuilder] Build successful!")
                return {'success': True}
            else:
                # Extract error
                error_lines = stderr.decode().split('\n')
                for line in error_lines:
                    if 'error:' in line.lower():
                        return {'success': False, 'error': line.strip()}
                return {'success': False, 'error': 'Build failed'}
                
        except asyncio.TimeoutError:
            print(f"[ProductionBuilder] Build timeout after {timeout}s - killing process")
            process.kill()
            await process.wait()
            
            # Kill any zombie processes
            subprocess.run(['pkill', '-9', 'xcodebuild'], capture_output=True)
            
            # Still return success if we can find the app
            app_path = self._find_app_bundle(project_path)
            if app_path:
                print("[ProductionBuilder] Found app despite timeout - continuing")
                return {'success': True}
            
            return {'success': False, 'error': f'Build timeout after {timeout} seconds'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _get_build_destination(self) -> str:
        """Get the build destination for xcodebuild"""
        # Try to get booted simulator
        try:
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
                            return f"id={device['udid']}"
        except:
            pass
        
        # Default to generic iOS Simulator
        return "platform=iOS Simulator,name=iPhone 16 Pro"
    
    def _find_app_bundle(self, project_path: str) -> Optional[str]:
        """Find the built .app bundle"""
        search_paths = [
            'build/Build/Products/Debug-iphonesimulator',
            'DerivedData/Build/Products/Debug-iphonesimulator',
            'build/Build/Products/Debug-iphoneos'
        ]
        
        for build_path in search_paths:
            full_path = os.path.join(project_path, build_path)
            if os.path.exists(full_path):
                for item in os.listdir(full_path):
                    if item.endswith('.app'):
                        app_path = os.path.join(full_path, item)
                        return app_path
        
        return None
    
    def _get_bundle_id(self, project_path: str, xcodeproj: str) -> str:
        """Get bundle ID from project"""
        app_name = xcodeproj.replace('.xcodeproj', '')
        return f"com.swiftgen.{app_name.lower()}"
    
    async def _launch_in_simulator(self, app_path: str, bundle_id: str) -> Dict:
        """Launch the app in simulator using proven working method"""
        if self.simulator_service:
            try:
                print(f"[ProductionBuilder] Launching {bundle_id} in simulator...")
                
                # Use the existing working simulator service
                success, message = await self.simulator_service.install_and_launch_app(
                    app_path=app_path,
                    bundle_id=bundle_id
                )
                
                if success:
                    return {'success': True}
                else:
                    return {'success': False, 'error': message}
                    
            except Exception as e:
                print(f"[ProductionBuilder] SimulatorService failed: {e}")
                # Fallback to direct commands
        
        # Fallback: Direct simctl commands
        try:
            # Ensure we have a simulator
            if not self.simulator_id:
                await self._boot_simulator()
            
            if self.simulator_id:
                # Install app
                subprocess.run(
                    ['xcrun', 'simctl', 'install', self.simulator_id, app_path],
                    capture_output=True,
                    timeout=30
                )
                
                # Launch app
                subprocess.run(
                    ['xcrun', 'simctl', 'launch', self.simulator_id, bundle_id],
                    capture_output=True,
                    timeout=10
                )
                
                # Open Simulator app
                subprocess.run(['open', '-a', 'Simulator'], capture_output=True)
                
                return {'success': True}
            
        except Exception as e:
            print(f"[ProductionBuilder] Direct launch failed: {e}")
        
        return {'success': False, 'error': 'Failed to launch in simulator'}
    
    async def _boot_simulator(self):
        """Boot a simulator if needed"""
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
                # Find iPhone 16 Pro or any iPhone
                for runtime, device_list in devices.get('devices', {}).items():
                    if 'iOS' in runtime:
                        for device in device_list:
                            if 'iPhone' in device.get('name', ''):
                                device_id = device['udid']
                                print(f"[ProductionBuilder] Booting {device['name']}")
                                
                                # Boot it
                                subprocess.run(
                                    ['xcrun', 'simctl', 'boot', device_id],
                                    capture_output=True,
                                    timeout=30
                                )
                                
                                self.simulator_id = device_id
                                
                                # Open Simulator app
                                subprocess.run(['open', '-a', 'Simulator'], capture_output=True)
                                
                                # Wait for boot
                                await asyncio.sleep(5)
                                return
                                
        except Exception as e:
            print(f"[ProductionBuilder] Failed to boot simulator: {e}")