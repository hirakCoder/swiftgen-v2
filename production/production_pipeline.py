"""
SwiftGen V2 - Production Pipeline
Complete production-ready pipeline with structured generation and validation
"""

import asyncio
import json
import logging
import time
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

# Import our production components
from structured_generator import StructuredGenerator
from direct_spm_builder import DirectSPMBuilder

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PipelineResult:
    """Result from pipeline execution"""
    success: bool
    app_name: str
    duration: float
    app_path: Optional[str] = None
    error: Optional[str] = None
    validation_score: float = 0.0
    files_generated: int = 0
    method: str = "structured"

class ValidationPipeline:
    """Validation pipeline with multiple gates"""
    
    def validate_structure(self, files: List[Dict[str, str]]) -> Dict[str, Any]:
        """Validate file structure before writing"""
        
        issues = []
        score = 100.0
        
        for file_info in files:
            content = file_info["content"]
            path = file_info["path"]
            
            # Check for basic Swift syntax
            if path.endswith(".swift"):
                # Check balanced delimiters
                open_braces = content.count("{")
                close_braces = content.count("}")
                if open_braces != close_braces:
                    issues.append(f"{path}: Unbalanced braces ({open_braces} open, {close_braces} close)")
                    score -= 10
                
                open_parens = content.count("(")
                close_parens = content.count(")")
                if open_parens != close_parens:
                    issues.append(f"{path}: Unbalanced parentheses ({open_parens} open, {close_parens} close)")
                    score -= 10
                
                # Check for required imports
                if "ContentView" in path and "import SwiftUI" not in content:
                    issues.append(f"{path}: Missing import SwiftUI")
                    score -= 5
                
                # Check for @main in App file
                if "App.swift" in path and "@main" not in content:
                    issues.append(f"{path}: Missing @main attribute")
                    score -= 15
        
        return {
            "valid": len(issues) == 0,
            "score": max(0, score),
            "issues": issues
        }
    
    def validate_swift_syntax(self, file_content: str) -> bool:
        """Quick Swift syntax validation"""
        
        # Basic checks that catch 90% of issues
        checks = [
            (file_content.count("{") == file_content.count("}"), "Braces"),
            (file_content.count("(") == file_content.count(")"), "Parentheses"),
            (file_content.count("[") == file_content.count("]"), "Brackets"),
            ("struct" in file_content or "class" in file_content or "@main" in file_content, "Type definition"),
            (not file_content.strip().endswith(","), "Trailing comma")
        ]
        
        for check, name in checks:
            if not check:
                logger.warning(f"Syntax check failed: {name}")
                return False
        
        return True

class ProductionPipeline:
    """Main production pipeline"""
    
    def __init__(self):
        self.generator = StructuredGenerator()
        self.builder = DirectSPMBuilder()
        self.validator = ValidationPipeline()
        self.workspace_dir = Path("production_workspace")
        
    async def generate_app(self, description: str, app_name: str, provider: str = "structured") -> PipelineResult:
        """Generate app through production pipeline"""
        
        start_time = time.time()
        logger.info(f"\n{'='*60}")
        logger.info(f"PRODUCTION PIPELINE: {app_name}")
        logger.info(f"Description: {description}")
        logger.info(f"Provider: {provider}")
        logger.info(f"{'='*60}")
        
        try:
            # Stage 1: Generate with structured templates
            logger.info("📝 Stage 1: Structured Generation")
            generation_result = await self.generator.generate_app(description, app_name, provider)
            
            if not generation_result["success"]:
                return PipelineResult(
                    success=False,
                    app_name=app_name,
                    duration=time.time() - start_time,
                    error="Generation failed"
                )
            
            files = generation_result["files"]
            logger.info(f"   ✅ Generated {len(files)} files")
            
            # Stage 2: Validate before writing
            logger.info("🔍 Stage 2: Validation")
            validation = self.validator.validate_structure(files)
            
            if not validation["valid"]:
                logger.warning(f"   ⚠️ Validation issues: {validation['issues']}")
                # Continue anyway with structured generation
            else:
                logger.info(f"   ✅ Validation passed (score: {validation['score']})")
            
            # Stage 3: Write to disk
            logger.info("💾 Stage 3: Writing Files")
            project_path = self.workspace_dir / app_name
            if project_path.exists():
                shutil.rmtree(project_path)
            
            for file_info in files:
                file_path = project_path / file_info["path"]
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(file_info["content"])
            
            logger.info(f"   ✅ Written to {project_path}")
            
            # Stage 4: Build and deploy
            logger.info("🔨 Stage 4: Build & Deploy")
            build_result = await self.builder.build_and_deploy(str(project_path), app_name)
            
            if build_result["success"]:
                logger.info(f"   ✅ Build successful")
                
                duration = time.time() - start_time
                logger.info(f"\n{'='*60}")
                logger.info(f"✅ SUCCESS: {app_name} ready in {duration:.1f}s")
                logger.info(f"{'='*60}\n")
                
                return PipelineResult(
                    success=True,
                    app_name=app_name,
                    duration=duration,
                    app_path=build_result.get("app_path"),
                    validation_score=validation["score"],
                    files_generated=len(files),
                    method=build_result.get("method", "structured")
                )
            else:
                return PipelineResult(
                    success=False,
                    app_name=app_name,
                    duration=time.time() - start_time,
                    error=f"Build failed: {build_result.get('error', 'Unknown')}"
                )
                
        except Exception as e:
            logger.error(f"Pipeline error: {e}")
            return PipelineResult(
                success=False,
                app_name=app_name,
                duration=time.time() - start_time,
                error=str(e)
            )
    
    async def test_comprehensive(self) -> Dict[str, Any]:
        """Run comprehensive tests"""
        
        logger.info("\n" + "="*60)
        logger.info("COMPREHENSIVE PRODUCTION TESTING")
        logger.info("="*60)
        
        test_cases = [
            # Simple apps
            ("Create a counter app", "Counter", "simple"),
            ("Create a timer app", "Timer", "simple"),
            ("Create a dice roller", "DiceRoller", "simple"),
            
            # Themed apps
            ("Create a timer with galaxy theme", "GalaxyTimer", "themed"),
            ("Create a calculator with neon theme", "NeonCalc", "themed"),
            ("Create a counter with martian theme", "MartianCounter", "themed"),
            
            # Complex apps
            ("Create a todo list app", "TodoList", "complex"),
            ("Create a weather app", "Weather", "complex"),
            ("Create a notes app", "Notes", "complex"),
            ("Create a calculator", "Calculator", "complex")
        ]
        
        results = []
        
        for description, app_name, complexity in test_cases:
            logger.info(f"\n🧪 Test {len(results) + 1}/10: {app_name} ({complexity})")
            
            result = await self.generate_app(description, app_name)
            results.append({
                "app": app_name,
                "complexity": complexity,
                "success": result.success,
                "duration": result.duration,
                "validation_score": result.validation_score,
                "files": result.files_generated,
                "error": result.error
            })
            
            # Brief pause between tests
            await asyncio.sleep(1)
        
        # Generate report
        successful = sum(1 for r in results if r["success"])
        total = len(results)
        success_rate = (successful / total * 100) if total > 0 else 0
        
        avg_duration = sum(r["duration"] for r in results) / total if total > 0 else 0
        avg_validation = sum(r["validation_score"] for r in results) / total if total > 0 else 0
        
        # Check syntax validity
        syntax_valid = sum(1 for r in results if r["validation_score"] >= 95)
        syntax_rate = (syntax_valid / total * 100) if total > 0 else 0
        
        report = {
            "total_tests": total,
            "successful": successful,
            "failed": total - successful,
            "success_rate": success_rate,
            "syntax_validity_rate": syntax_rate,
            "average_duration": avg_duration,
            "average_validation_score": avg_validation,
            "results": results
        }
        
        # Print report
        logger.info("\n" + "="*60)
        logger.info("📊 TEST RESULTS SUMMARY")
        logger.info("="*60)
        logger.info(f"Total Tests: {total}")
        logger.info(f"Successful: {successful} ✅")
        logger.info(f"Failed: {total - successful} ❌")
        logger.info(f"Success Rate: {success_rate:.1f}%")
        logger.info(f"Syntax Validity: {syntax_rate:.1f}%")
        logger.info(f"Avg Duration: {avg_duration:.1f}s")
        logger.info(f"Avg Validation: {avg_validation:.1f}")
        
        # Performance check
        simple_apps = [r for r in results if r["complexity"] == "simple"]
        if simple_apps:
            simple_avg = sum(r["duration"] for r in simple_apps) / len(simple_apps)
            logger.info(f"Simple Apps Avg: {simple_avg:.1f}s {'✅' if simple_avg < 30 else '⚠️'}")
        
        logger.info("\n📋 Detailed Results:")
        logger.info("-" * 60)
        logger.info(f"{'App':<15} {'Type':<10} {'Status':<10} {'Time':<8} {'Valid':<8}")
        logger.info("-" * 60)
        
        for r in results:
            status = "✅ Pass" if r["success"] else "❌ Fail"
            logger.info(f"{r['app']:<15} {r['complexity']:<10} {status:<10} {r['duration']:<6.1f}s {r['validation_score']:<6.0f}%")
        
        # Save report
        report_path = Path("production_test_report.json")
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"\n💾 Report saved to {report_path}")
        
        # Check success criteria
        logger.info("\n🎯 Production Criteria:")
        logger.info(f"{'✅' if success_rate >= 90 else '❌'} 90%+ success rate (actual: {success_rate:.1f}%)")
        logger.info(f"{'✅' if syntax_rate >= 95 else '❌'} 95%+ syntax validity (actual: {syntax_rate:.1f}%)")
        logger.info(f"{'✅' if simple_avg < 30 else '❌'} <30s for simple apps (actual: {simple_avg:.1f}s)")
        
        return report

# Main test function
async def main():
    """Run production pipeline tests"""
    pipeline = ProductionPipeline()
    
    # Run comprehensive tests
    report = await pipeline.test_comprehensive()
    
    # Print final verdict
    success_rate = report["success_rate"]
    syntax_rate = report["syntax_validity_rate"]
    
    print("\n" + "="*60)
    if success_rate >= 90 and syntax_rate >= 95:
        print("🎉 PRODUCTION READY!")
        print("The system meets all production criteria.")
    else:
        print("⚠️ NOT YET PRODUCTION READY")
        print("The system needs more work to meet criteria.")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())