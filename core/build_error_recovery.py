"""
Build Error Recovery System
Handles build-time errors that occur after successful compilation
"""

import os
import re
import subprocess
import plistlib
import json
import shutil
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

class BuildErrorType(Enum):
    """Types of build errors"""
    MISSING_INFO_PLIST = "missing_info_plist"
    INVALID_BUNDLE_ID = "invalid_bundle_id"
    MISSING_EXECUTABLE = "missing_executable"
    CODE_SIGNING = "code_signing"
    PROVISIONING = "provisioning"
    SIMULATOR_ERROR = "simulator_error"
    ARCHITECTURE_MISMATCH = "architecture_mismatch"
    FRAMEWORK_MISSING = "framework_missing"
    RESOURCE_MISSING = "resource_missing"
    PERMISSION_DENIED = "permission_denied"
    DISK_SPACE = "disk_space"
    APP_INSTALL_FAILED = "app_install_failed"

@dataclass
class BuildError:
    """Represents a build error"""
    error_type: BuildErrorType
    message: str
    file_path: Optional[str] = None
    suggestion: Optional[str] = None

class BuildErrorRecovery:
    """
    Comprehensive build error recovery system
    Handles errors that occur during:
    - App bundle creation
    - Code signing
    - Simulator installation
    - App launch
    """
    
    def __init__(self):
        self.recovery_attempts = 0
        self.max_attempts = 3
        
    async def recover_from_build_error(
        self, 
        error_output: str, 
        project_path: str,
        app_bundle: str = None,
        bundle_id: str = None
    ) -> Dict:
        """
        Main entry point for build error recovery
        """
        print("🔨 Build Error Recovery Started...")
        
        # Detect the type of build error
        errors = self._detect_build_errors(error_output)
        
        if not errors:
            # Try to infer from symptoms
            errors = self._infer_errors_from_symptoms(project_path, app_bundle)
        
        fixed_count = 0
        for error in errors:
            print(f"🔍 Detected: {error.error_type.value} - {error.message}")
            
            # Apply appropriate fix
            if self._fix_build_error(error, project_path, app_bundle, bundle_id):
                fixed_count += 1
                print(f"✅ Fixed: {error.error_type.value}")
            else:
                print(f"❌ Could not fix: {error.error_type.value}")
        
        return {
            "success": fixed_count > 0,
            "fixed_count": fixed_count,
            "errors_detected": len(errors),
            "message": f"Fixed {fixed_count}/{len(errors)} build errors"
        }
    
    def _detect_build_errors(self, error_output: str) -> List[BuildError]:
        """Detect build errors from output"""
        errors = []
        
        # Info.plist errors
        if "Info.plist" in error_output or "CFBundleExecutable" in error_output:
            errors.append(BuildError(
                BuildErrorType.MISSING_INFO_PLIST,
                "Info.plist is missing or invalid",
                suggestion="Create proper Info.plist"
            ))
        
        # Bundle ID errors
        if "bundle identifier" in error_output.lower() or "CFBundleIdentifier" in error_output:
            errors.append(BuildError(
                BuildErrorType.INVALID_BUNDLE_ID,
                "Invalid or missing bundle identifier",
                suggestion="Fix bundle identifier format"
            ))
        
        # Executable errors
        if "executable" in error_output.lower() or "Mach-O" in error_output:
            errors.append(BuildError(
                BuildErrorType.MISSING_EXECUTABLE,
                "App executable is missing or invalid",
                suggestion="Rebuild executable"
            ))
        
        # Code signing errors
        if "code sign" in error_output.lower() or "codesign" in error_output:
            errors.append(BuildError(
                BuildErrorType.CODE_SIGNING,
                "Code signing failed",
                suggestion="Disable code signing for simulator"
            ))
        
        # Simulator errors
        if "simulator" in error_output.lower() or "simctl" in error_output:
            errors.append(BuildError(
                BuildErrorType.SIMULATOR_ERROR,
                "Simulator error",
                suggestion="Reset simulator or use different device"
            ))
        
        # Installation errors
        if "install" in error_output.lower() and "failed" in error_output.lower():
            errors.append(BuildError(
                BuildErrorType.APP_INSTALL_FAILED,
                "App installation failed",
                suggestion="Clean and reinstall"
            ))
        
        # Architecture errors
        if "architecture" in error_output.lower() or "arm64" in error_output or "x86_64" in error_output:
            errors.append(BuildError(
                BuildErrorType.ARCHITECTURE_MISMATCH,
                "Architecture mismatch",
                suggestion="Build for correct architecture"
            ))
        
        # Permission errors
        if "permission denied" in error_output.lower():
            errors.append(BuildError(
                BuildErrorType.PERMISSION_DENIED,
                "Permission denied",
                suggestion="Fix file permissions"
            ))
        
        return errors
    
    def _infer_errors_from_symptoms(self, project_path: str, app_bundle: str) -> List[BuildError]:
        """Infer errors by checking the build artifacts"""
        errors = []
        
        if app_bundle and os.path.exists(app_bundle):
            # Check Info.plist
            info_plist_path = os.path.join(app_bundle, "Info.plist")
            if not os.path.exists(info_plist_path):
                errors.append(BuildError(
                    BuildErrorType.MISSING_INFO_PLIST,
                    "Info.plist not found in app bundle"
                ))
            
            # Check executable
            app_name = os.path.basename(app_bundle).replace('.app', '')
            executable_path = os.path.join(app_bundle, app_name)
            if not os.path.exists(executable_path):
                errors.append(BuildError(
                    BuildErrorType.MISSING_EXECUTABLE,
                    f"Executable {app_name} not found in app bundle"
                ))
            elif not os.access(executable_path, os.X_OK):
                errors.append(BuildError(
                    BuildErrorType.PERMISSION_DENIED,
                    f"Executable {app_name} is not executable"
                ))
        
        return errors
    
    def _fix_build_error(
        self, 
        error: BuildError, 
        project_path: str,
        app_bundle: str,
        bundle_id: str
    ) -> bool:
        """Apply fix for specific build error"""
        
        if error.error_type == BuildErrorType.MISSING_INFO_PLIST:
            return self._fix_info_plist(app_bundle, bundle_id)
        
        elif error.error_type == BuildErrorType.INVALID_BUNDLE_ID:
            return self._fix_bundle_id(app_bundle, bundle_id)
        
        elif error.error_type == BuildErrorType.MISSING_EXECUTABLE:
            return self._fix_missing_executable(project_path, app_bundle)
        
        elif error.error_type == BuildErrorType.CODE_SIGNING:
            return self._fix_code_signing(app_bundle)
        
        elif error.error_type == BuildErrorType.SIMULATOR_ERROR:
            return self._fix_simulator_error()
        
        elif error.error_type == BuildErrorType.APP_INSTALL_FAILED:
            return self._fix_installation_error(app_bundle, bundle_id)
        
        elif error.error_type == BuildErrorType.ARCHITECTURE_MISMATCH:
            return self._fix_architecture_mismatch(project_path, app_bundle)
        
        elif error.error_type == BuildErrorType.PERMISSION_DENIED:
            return self._fix_permissions(app_bundle)
        
        return False
    
    def _fix_info_plist(self, app_bundle: str, bundle_id: str) -> bool:
        """Create or fix Info.plist"""
        if not app_bundle:
            return False
        
        app_name = os.path.basename(app_bundle).replace('.app', '')
        info_plist_path = os.path.join(app_bundle, "Info.plist")
        
        # Create comprehensive Info.plist
        info_dict = {
            'CFBundleExecutable': app_name,
            'CFBundleIdentifier': bundle_id or f'com.swiftgen.{app_name.lower()}',
            'CFBundleName': app_name,
            'CFBundleDisplayName': app_name,
            'CFBundlePackageType': 'APPL',
            'CFBundleShortVersionString': '1.0',
            'CFBundleVersion': '1',
            'CFBundleInfoDictionaryVersion': '6.0',
            'LSRequiresIPhoneOS': True,
            'UILaunchStoryboardName': 'LaunchScreen',
            'UIRequiredDeviceCapabilities': ['arm64'],
            'UISupportedInterfaceOrientations': [
                'UIInterfaceOrientationPortrait',
                'UIInterfaceOrientationLandscapeLeft',
                'UIInterfaceOrientationLandscapeRight'
            ],
            'UIApplicationSceneManifest': {
                'UIApplicationSupportsMultipleScenes': False,
                'UISceneConfigurations': {}
            },
            'DTCompiler': 'com.apple.compilers.llvm.clang.1_0',
            'DTPlatformBuild': '',
            'DTPlatformName': 'iphonesimulator',
            'DTPlatformVersion': '16.0',
            'DTSDKBuild': '20A360',
            'DTSDKName': 'iphonesimulator16.0',
            'MinimumOSVersion': '16.0',
            'UIDeviceFamily': [1, 2]  # iPhone and iPad
        }
        
        try:
            with open(info_plist_path, 'wb') as f:
                plistlib.dump(info_dict, f)
            print(f"✅ Created Info.plist for {app_name}")
            return True
        except Exception as e:
            print(f"❌ Failed to create Info.plist: {e}")
            return False
    
    def _fix_bundle_id(self, app_bundle: str, bundle_id: str) -> bool:
        """Fix bundle identifier issues"""
        if not app_bundle:
            return False
        
        info_plist_path = os.path.join(app_bundle, "Info.plist")
        
        try:
            # Read existing or create new
            if os.path.exists(info_plist_path):
                with open(info_plist_path, 'rb') as f:
                    info_dict = plistlib.load(f)
            else:
                info_dict = {}
            
            # Ensure valid bundle ID
            app_name = os.path.basename(app_bundle).replace('.app', '')
            if not bundle_id:
                bundle_id = f"com.swiftgen.{app_name.lower()}"
            
            # Clean bundle ID (remove spaces, special chars)
            bundle_id = re.sub(r'[^a-zA-Z0-9.-]', '', bundle_id)
            
            info_dict['CFBundleIdentifier'] = bundle_id
            
            with open(info_plist_path, 'wb') as f:
                plistlib.dump(info_dict, f)
            
            print(f"✅ Fixed bundle ID: {bundle_id}")
            return True
        except Exception as e:
            print(f"❌ Failed to fix bundle ID: {e}")
            return False
    
    def _fix_missing_executable(self, project_path: str, app_bundle: str) -> bool:
        """Rebuild missing executable"""
        if not app_bundle:
            return False
        
        app_name = os.path.basename(app_bundle).replace('.app', '')
        executable_path = os.path.join(app_bundle, app_name)
        
        # Check if executable exists but wrong name
        for file in os.listdir(app_bundle):
            file_path = os.path.join(app_bundle, file)
            if os.path.isfile(file_path) and os.access(file_path, os.X_OK):
                if file != app_name:
                    # Rename to correct name
                    try:
                        shutil.move(file_path, executable_path)
                        print(f"✅ Renamed executable to {app_name}")
                        return True
                    except:
                        pass
        
        # Try to recompile
        sources_dir = os.path.join(project_path, "Sources")
        if os.path.exists(sources_dir):
            print("🔨 Attempting to rebuild executable...")
            
            # Get SDK path
            try:
                sdk_path = subprocess.check_output(
                    ['xcrun', '--sdk', 'iphonesimulator', '--show-sdk-path']
                ).decode().strip()
                
                swift_files = [
                    os.path.join(sources_dir, f)
                    for f in os.listdir(sources_dir)
                    if f.endswith('.swift')
                ]
                
                # Compile
                compile_cmd = [
                    'swiftc',
                    '-sdk', sdk_path,
                    '-target', 'x86_64-apple-ios16.0-simulator',
                    '-framework', 'SwiftUI',
                    '-framework', 'UIKit',
                    '-framework', 'Foundation',
                    '-emit-executable',
                    '-o', executable_path,
                    '-parse-as-library'
                ] + swift_files
                
                result = subprocess.run(
                    compile_cmd,
                    capture_output=True,
                    timeout=30,
                    cwd=project_path
                )
                
                if result.returncode == 0:
                    os.chmod(executable_path, 0o755)
                    print(f"✅ Rebuilt executable: {app_name}")
                    return True
            except Exception as e:
                print(f"❌ Failed to rebuild: {e}")
        
        return False
    
    def _fix_code_signing(self, app_bundle: str) -> bool:
        """Fix code signing issues for simulator"""
        if not app_bundle:
            return False
        
        try:
            # For simulator, we can disable code signing
            # Create embedded provisioning profile placeholder
            embedded_path = os.path.join(app_bundle, "_CodeSignature")
            if os.path.exists(embedded_path):
                shutil.rmtree(embedded_path)
            
            # Remove code signing requirements from Info.plist
            info_plist_path = os.path.join(app_bundle, "Info.plist")
            if os.path.exists(info_plist_path):
                with open(info_plist_path, 'rb') as f:
                    info_dict = plistlib.load(f)
                
                # Remove signing-related keys
                keys_to_remove = [
                    'CFBundleSignature',
                    'DTXcodeBuild',
                    'DTXcode'
                ]
                for key in keys_to_remove:
                    info_dict.pop(key, None)
                
                with open(info_plist_path, 'wb') as f:
                    plistlib.dump(info_dict, f)
            
            print("✅ Removed code signing requirements")
            return True
        except Exception as e:
            print(f"❌ Failed to fix code signing: {e}")
            return False
    
    def _fix_simulator_error(self) -> bool:
        """Fix simulator-related errors"""
        try:
            # Kill and restart simulator
            subprocess.run(['killall', 'Simulator'], capture_output=True)
            
            # Boot a fresh simulator
            result = subprocess.run(
                ['xcrun', 'simctl', 'list', 'devices', '-j'],
                capture_output=True,
                text=True
            )
            
            devices = json.loads(result.stdout)
            
            # Find an iPhone simulator
            for runtime, device_list in devices.get('devices', {}).items():
                if 'iOS' in runtime:
                    for device in device_list:
                        if 'iPhone' in device.get('name', '') and device.get('isAvailable', False):
                            device_id = device['udid']
                            
                            # Shutdown if booted
                            subprocess.run(
                                ['xcrun', 'simctl', 'shutdown', device_id],
                                capture_output=True
                            )
                            
                            # Boot fresh
                            subprocess.run(
                                ['xcrun', 'simctl', 'boot', device_id],
                                capture_output=True
                            )
                            
                            print(f"✅ Rebooted simulator: {device['name']}")
                            return True
            
        except Exception as e:
            print(f"❌ Failed to fix simulator: {e}")
        
        return False
    
    def _fix_installation_error(self, app_bundle: str, bundle_id: str) -> bool:
        """Fix app installation errors"""
        if not bundle_id:
            app_name = os.path.basename(app_bundle).replace('.app', '')
            bundle_id = f"com.swiftgen.{app_name.lower()}"
        
        try:
            # Get booted simulator
            result = subprocess.run(
                ['xcrun', 'simctl', 'list', 'devices', 'booted', '-j'],
                capture_output=True,
                text=True
            )
            
            devices = json.loads(result.stdout)
            
            for runtime, device_list in devices.get('devices', {}).items():
                for device in device_list:
                    if device.get('state') == 'Booted':
                        device_id = device['udid']
                        
                        # Uninstall existing
                        subprocess.run(
                            ['xcrun', 'simctl', 'uninstall', device_id, bundle_id],
                            capture_output=True
                        )
                        
                        # Clean simulator caches
                        subprocess.run(
                            ['xcrun', 'simctl', 'spawn', device_id, 'launchctl', 'kickstart', '-k', 'system/com.apple.CoreSimulator.CoreSimulatorService'],
                            capture_output=True
                        )
                        
                        print(f"✅ Cleaned simulator for fresh install")
                        return True
            
        except Exception as e:
            print(f"❌ Failed to fix installation: {e}")
        
        return False
    
    def _fix_architecture_mismatch(self, project_path: str, app_bundle: str) -> bool:
        """Fix architecture mismatch issues"""
        if not app_bundle:
            return False
        
        app_name = os.path.basename(app_bundle).replace('.app', '')
        executable_path = os.path.join(app_bundle, app_name)
        
        try:
            # Check current architecture
            result = subprocess.run(
                ['file', executable_path],
                capture_output=True,
                text=True
            )
            
            # Determine correct architecture
            if 'arm64' in result.stdout and 'x86_64' not in result.stdout:
                # Need to rebuild for x86_64 (Intel simulator)
                target_arch = 'x86_64-apple-ios16.0-simulator'
            else:
                # Need to rebuild for arm64 (Apple Silicon)
                target_arch = 'arm64-apple-ios16.0-simulator'
            
            print(f"🔨 Rebuilding for {target_arch}...")
            
            # This would trigger a rebuild with correct architecture
            # (Implementation depends on build system)
            
            return False  # Would need to trigger full rebuild
            
        except Exception as e:
            print(f"❌ Failed to fix architecture: {e}")
            return False
    
    def _fix_permissions(self, app_bundle: str) -> bool:
        """Fix file permission issues"""
        if not app_bundle:
            return False
        
        try:
            # Fix app bundle permissions
            subprocess.run(['chmod', '-R', '755', app_bundle], check=True)
            
            # Fix executable specifically
            app_name = os.path.basename(app_bundle).replace('.app', '')
            executable_path = os.path.join(app_bundle, app_name)
            
            if os.path.exists(executable_path):
                subprocess.run(['chmod', '+x', executable_path], check=True)
            
            print("✅ Fixed file permissions")
            return True
            
        except Exception as e:
            print(f"❌ Failed to fix permissions: {e}")
            return False
    
    def generate_diagnostic_report(self, project_path: str, app_bundle: str) -> str:
        """Generate detailed diagnostic report for debugging"""
        report = "📋 Build Diagnostic Report\n"
        report += "=" * 40 + "\n\n"
        
        # Check project structure
        report += "Project Structure:\n"
        if os.path.exists(project_path):
            sources_dir = os.path.join(project_path, "Sources")
            if os.path.exists(sources_dir):
                files = os.listdir(sources_dir)
                report += f"  Sources: {', '.join(files)}\n"
            else:
                report += "  ❌ No Sources directory\n"
        
        # Check app bundle
        if app_bundle and os.path.exists(app_bundle):
            report += f"\nApp Bundle ({os.path.basename(app_bundle)}):\n"
            
            # Check Info.plist
            info_plist = os.path.join(app_bundle, "Info.plist")
            if os.path.exists(info_plist):
                report += "  ✅ Info.plist exists\n"
                try:
                    with open(info_plist, 'rb') as f:
                        info = plistlib.load(f)
                    report += f"    Bundle ID: {info.get('CFBundleIdentifier', 'Missing')}\n"
                    report += f"    Executable: {info.get('CFBundleExecutable', 'Missing')}\n"
                except:
                    report += "    ❌ Could not parse Info.plist\n"
            else:
                report += "  ❌ No Info.plist\n"
            
            # Check executable
            app_name = os.path.basename(app_bundle).replace('.app', '')
            executable = os.path.join(app_bundle, app_name)
            if os.path.exists(executable):
                report += f"  ✅ Executable exists: {app_name}\n"
                if os.access(executable, os.X_OK):
                    report += "    ✅ Is executable\n"
                else:
                    report += "    ❌ Not executable\n"
            else:
                report += f"  ❌ No executable: {app_name}\n"
        else:
            report += "\n❌ No app bundle found\n"
        
        # Check simulator status
        report += "\nSimulator Status:\n"
        try:
            result = subprocess.run(
                ['xcrun', 'simctl', 'list', 'devices', 'booted'],
                capture_output=True,
                text=True
            )
            if 'Booted' in result.stdout:
                report += "  ✅ Simulator is booted\n"
            else:
                report += "  ❌ No booted simulator\n"
        except:
            report += "  ❌ Could not check simulator\n"
        
        return report

# Global instance
build_error_recovery = BuildErrorRecovery()