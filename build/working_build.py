"""
Working Build System - From July 15 stable branch
This actually worked and launched apps successfully
"""

import os
import asyncio
import subprocess
import json
import time
import sys
from typing import Dict, Optional
from pathlib import Path

# Add backend path for all the working services
sys.path.insert(0, '/Users/hirakbanerjee/Desktop/SwiftGen_Clean/stable_reference/backend')

class WorkingBuildService:
    """
    The build service that was actually working on July 15
    Uses all the proven components from the stable branch
    """
    
    def __init__(self):
        # Import the actual working build service
        from build_service import BuildService
        self.build_service = BuildService()
        
        # Import simulator service
        try:
            from simulator_service import SimulatorService
            self.simulator_service = SimulatorService()
            print("[WorkingBuild] Initialized SimulatorService")
        except:
            self.simulator_service = None
        
        # Import production build system
        try:
            from production_build_system import production_build_system
            self.production_build = production_build_system
            print("[WorkingBuild] Initialized ProductionBuildSystem")
        except:
            self.production_build = None
    
    async def build_and_launch(self, project_path: str, project_id: str) -> Dict:
        """
        Build and launch using the exact working method from July 15
        WITH EMERGENCY FIX for xcodebuild hanging
        """
        print(f"[WorkingBuild] Building {project_id} using proven July 15 method")
        
        # Determine complexity
        complexity = self._get_complexity(project_path)
        
        # Get bundle ID from project
        bundle_id = self._get_bundle_id(project_path)
        
        # DIRECT BUILD: Use direct compilation bypassing xcodegen/xcodebuild completely
        # This is the most reliable method for Intel Macs
        try:
            from .direct_build import direct_build_system
            print("[WorkingBuild] Using DIRECT BUILD SYSTEM")
            return await direct_build_system.build_and_launch(project_path, project_id)
        except Exception as e:
            print(f"[WorkingBuild] Direct build failed: {e}")
            # Try emergency fix as fallback
            try:
                from .emergency_fix_build import emergency_build_fix
                print("[WorkingBuild] Falling back to EMERGENCY FIX")
                return await emergency_build_fix.build_and_launch(project_path, project_id)
            except Exception as e2:
                print(f"[WorkingBuild] Emergency fix also failed: {e2}")
        
        try:
            # Fallback to the original working build service
            result = await self.build_service.build_project(
                project_path=project_path,
                project_id=project_id,
                bundle_id=bundle_id,
                app_complexity=complexity
            )
            
            if result.success:
                print(f"[WorkingBuild] Build successful!")
                
                # Now launch in simulator
                if result.app_path and self.simulator_service:
                    launch_success = await self._launch_app(result.app_path, bundle_id)
                    
                    if launch_success:
                        return {
                            'success': True,
                            'app_path': result.app_path,
                            'bundle_id': bundle_id,
                            'message': 'App launched in simulator successfully!'
                        }
                
                return {
                    'success': True,
                    'app_path': result.app_path,
                    'bundle_id': bundle_id,
                    'message': 'App built successfully'
                }
            else:
                return {
                    'success': False,
                    'error': result.errors[0] if result.errors else 'Build failed'
                }
                
        except Exception as e:
            print(f"[WorkingBuild] Error: {e}")
            
            # Fallback to direct production build
            if self.production_build:
                try:
                    result = await self.production_build.build_project(
                        project_path=project_path,
                        project_id=project_id,
                        complexity=complexity
                    )
                    
                    if result['success']:
                        return {
                            'success': True,
                            'app_path': result.get('app_path', project_path),
                            'message': result.get('message', 'Build completed')
                        }
                    else:
                        return {
                            'success': False,
                            'error': result.get('error', 'Build failed')
                        }
                except Exception as e2:
                    print(f"[WorkingBuild] Production build also failed: {e2}")
            
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _launch_app(self, app_path: str, bundle_id: str) -> bool:
        """Launch app in simulator"""
        try:
            if self.simulator_service:
                success, message = await self.simulator_service.install_and_launch_app(
                    app_path=app_path,
                    bundle_id=bundle_id
                )
                return success
        except Exception as e:
            print(f"[WorkingBuild] Launch failed: {e}")
        
        # Fallback to direct simctl
        try:
            # Get booted device
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
                            device_id = device['udid']
                            
                            # Install and launch
                            subprocess.run(
                                ['xcrun', 'simctl', 'install', device_id, app_path],
                                capture_output=True,
                                timeout=30
                            )
                            
                            subprocess.run(
                                ['xcrun', 'simctl', 'launch', device_id, bundle_id],
                                capture_output=True,
                                timeout=10
                            )
                            
                            # Open Simulator
                            subprocess.run(['open', '-a', 'Simulator'])
                            
                            return True
        except:
            pass
        
        return False
    
    def _get_complexity(self, project_path: str) -> str:
        """Determine app complexity"""
        try:
            swift_files = 0
            for root, dirs, files in os.walk(project_path):
                swift_files += len([f for f in files if f.endswith('.swift')])
            
            if swift_files <= 3:
                return 'simple'
            elif swift_files <= 10:
                return 'medium'
            else:
                return 'complex'
        except:
            return 'simple'
    
    def _get_bundle_id(self, project_path: str) -> str:
        """Get bundle ID from project"""
        try:
            # Try to get from project.json
            project_json = os.path.join(project_path, 'project.json')
            if os.path.exists(project_json):
                with open(project_json, 'r') as f:
                    data = json.load(f)
                    return data.get('bundle_id', 'com.swiftgen.app')
            
            # Try to get from project.yml
            project_yml = os.path.join(project_path, 'project.yml')
            if os.path.exists(project_yml):
                with open(project_yml, 'r') as f:
                    content = f.read()
                    # Extract bundle ID from PRODUCT_BUNDLE_IDENTIFIER
                    import re
                    match = re.search(r'PRODUCT_BUNDLE_IDENTIFIER:\s*([^\s\n]+)', content)
                    if match:
                        return match.group(1)
            
            # Default based on project name
            for item in os.listdir(project_path):
                if item.endswith('.xcodeproj'):
                    app_name = item.replace('.xcodeproj', '')
                    return f"com.swiftgen.{app_name.lower()}"
            
        except Exception as e:
            print(f"[WorkingBuild] Could not get bundle ID: {e}")
        
        return "com.swiftgen.app"