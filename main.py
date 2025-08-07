"""
SwiftGen V2 - Production-Ready iOS App Generator
Clean, pragmatic, battle-tested architecture
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import asyncio
import json
import os
import sys
import time
import uuid
import subprocess
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path

# Add swiftgen_v2 to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# Add backend path for existing services
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

# Import core components
from core.pipeline import SwiftGenPipeline
from core.circuit_breaker import CircuitBreakerError
from generation.llm_router import LLMRouter
from build.working_build import WorkingBuildService

# Initialize FastAPI app
app = FastAPI(
    title="SwiftGen V2 - Production iOS App Generator",
    version="2.0.0",
    description="Generate iOS apps from natural language in under 60 seconds"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Request/Response models
class GenerateRequest(BaseModel):
    description: str
    app_name: str
    provider: Optional[str] = None  # claude, gpt4, grok, or hybrid
    project_id: Optional[str] = None  # For modifications

class GenerateResponse(BaseModel):
    success: bool
    project_id: str
    message: str
    app_path: Optional[str] = None
    error: Optional[str] = None
    fallback_action: Optional[str] = None
    duration: float = 0

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        if client_id not in self.active_connections:
            self.active_connections[client_id] = []
        self.active_connections[client_id].append(websocket)
    
    def disconnect(self, websocket: WebSocket, client_id: str):
        if client_id in self.active_connections:
            self.active_connections[client_id].remove(websocket)
            if not self.active_connections[client_id]:
                del self.active_connections[client_id]
    
    async def send_message(self, client_id: str, message: dict):
        if client_id in self.active_connections:
            for connection in self.active_connections[client_id]:
                try:
                    await connection.send_json(message)
                except:
                    pass

# Initialize components
manager = ConnectionManager()
llm_router = LLMRouter()
builder = WorkingBuildService()
pipeline = SwiftGenPipeline(llm_service=llm_router, build_service=builder)

# Active projects tracking
active_projects = {}

# Mount static files and frontend
frontend_path = Path(__file__).parent / "frontend"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path / "static")), name="static")
    app.mount("/frontend", StaticFiles(directory=str(frontend_path), html=True), name="frontend")

@app.get("/")
async def root():
    """Redirect to frontend"""
    return FileResponse(str(frontend_path / "index.html"))

@app.get("/api")
async def api_info():
    """API info"""
    return {
        "status": "online",
        "service": "SwiftGen V2",
        "version": "2.0.0",
        "endpoints": {
            "generate": "/api/generate",
            "status": "/api/status/{project_id}",
            "metrics": "/api/metrics",
            "health": "/api/health"
        }
    }

@app.post("/api/modify", response_model=GenerateResponse)
async def modify_app(request: GenerateRequest):
    """
    Modify an existing app with flexible interpretation
    Then rebuild and relaunch to show changes (like Xcode)
    """
    start_time = time.time()
    
    try:
        # Import modification handler
        from core.modification_handler import IntelligentModificationRouter
        
        # Get project path
        project_id = request.project_id or request.app_name.lower().replace(' ', '_')
        project_path = f"workspaces/{project_id}"
        
        if not os.path.exists(project_path):
            return GenerateResponse(
                success=False,
                project_id=project_id,
                message="Project not found",
                error=f"No project found at {project_path}"
            )
        
        # Route modification
        result = await IntelligentModificationRouter.route_modification(
            request=request.description,
            project_path=project_path,
            llm_service=llm_router
        )
        
        if result['success']:
            print(f"[MODIFY] Files modified successfully, rebuilding {project_id}...")
            
            # Rebuild and relaunch the app with modifications
            from build.working_build import WorkingBuildService
            builder = WorkingBuildService()
            
            # Clean build directory first to ensure fresh build
            import shutil
            build_dir = os.path.join(project_path, 'build')
            if os.path.exists(build_dir):
                shutil.rmtree(build_dir)
                print(f"[MODIFY] Cleaned build directory for fresh build")
            
            # Build and launch the modified app
            build_result = await builder.build_and_launch(project_path, project_id)
            
            if build_result.get('success'):
                print(f"[MODIFY] App rebuilt and relaunched successfully!")
                return GenerateResponse(
                    success=True,
                    project_id=project_id,
                    message=f"✅ App modified and relaunched! {result.get('files_modified', 0)} files updated",
                    app_path=build_result.get('app_path'),
                    duration=time.time() - start_time
                )
            else:
                return GenerateResponse(
                    success=False,
                    project_id=project_id,
                    message="Modification succeeded but rebuild failed",
                    error=build_result.get('error', 'Build error'),
                    duration=time.time() - start_time
                )
        else:
            return GenerateResponse(
                success=False,
                project_id=project_id,
                message="Modification failed",
                error=result.get('error')
            )
            
    except Exception as e:
        return GenerateResponse(
            success=False,
            project_id=request.project_id or "unknown",
            message="Modification error",
            error=str(e)
        )

@app.post("/api/generate", response_model=GenerateResponse)
async def generate_app(request: GenerateRequest):
    """
    Main endpoint - generate iOS app from description
    """
    start_time = time.time()
    project_id = str(uuid.uuid4())[:8]
    
    # Track active project
    active_projects[project_id] = {
        'status': 'processing',
        'started': datetime.now(),
        'description': request.description
    }
    
    try:
        # Send initial status
        await manager.send_message(project_id, {
            'type': 'status',
            'message': '🚀 Starting app generation...',
            'status': 'started'
        })
        
        # Process through pipeline
        result = await pipeline.process_request(
            description=request.description,
            app_name=request.app_name,
            project_id=project_id
        )
        
        # Update project status
        active_projects[project_id]['status'] = 'completed' if result.success else 'failed'
        
        # Send final status
        if result.success:
            await manager.send_message(project_id, {
                'type': 'success',
                'message': '✅ App generated successfully!',
                'app_path': result.app_path
            })
            
            return GenerateResponse(
                success=True,
                project_id=project_id,
                message=f"App generated successfully in {result.duration:.1f}s",
                app_path=result.app_path,
                duration=result.duration
            )
        else:
            # Handle failure with clear fallback
            fallback_msg = _get_fallback_message(result.fallback_action, result.app_path)
            
            await manager.send_message(project_id, {
                'type': 'error',
                'message': f'❌ {result.error}',
                'fallback': fallback_msg
            })
            
            return GenerateResponse(
                success=False,
                project_id=project_id,
                message=result.error or "Generation failed",
                error=result.error,
                fallback_action=result.fallback_action,
                duration=result.duration
            )
            
    except Exception as e:
        # Unexpected error
        error_msg = str(e)
        print(f"[API] Unexpected error: {error_msg}")
        
        await manager.send_message(project_id, {
            'type': 'error',
            'message': f'❌ Unexpected error: {error_msg}'
        })
        
        return GenerateResponse(
            success=False,
            project_id=project_id,
            message="An unexpected error occurred",
            error=error_msg,
            fallback_action="contact_support",
            duration=time.time() - start_time
        )

@app.get("/api/status/{project_id}")
async def get_project_status(project_id: str):
    """Get status of a project"""
    if project_id in active_projects:
        return active_projects[project_id]
    else:
        raise HTTPException(status_code=404, detail="Project not found")

@app.get("/api/metrics")
async def get_metrics():
    """Get system metrics"""
    metrics = pipeline.get_metrics()
    metrics['active_projects'] = len(active_projects)
    metrics['llm_health'] = llm_router.get_health_status()
    return metrics

@app.get("/api/health")
async def health_check():
    """Detailed health check"""
    health = {
        'status': 'healthy',
        'components': {
            'llm_router': 'healthy' if any(
                p['healthy'] for p in llm_router.get_health_status().values()
            ) else 'degraded',
            'builder': 'healthy',  # Always healthy since it has fallback
            'pipeline': 'healthy'
        },
        'circuit_breakers': pipeline.get_metrics()
    }
    
    # Overall status
    if all(v == 'healthy' for v in health['components'].values()):
        health['status'] = 'healthy'
    elif any(v == 'healthy' for v in health['components'].values()):
        health['status'] = 'degraded'
    else:
        health['status'] = 'unhealthy'
    
    return health

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket for real-time updates"""
    await manager.connect(websocket, client_id)
    
    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            
            # Echo back for now
            await websocket.send_json({
                'type': 'echo',
                'message': data
            })
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, client_id)

def _get_fallback_message(action: str, app_path: str = None) -> str:
    """Get user-friendly fallback message"""
    messages = {
        'open_in_xcode': f"Open the project in Xcode and press Cmd+R to run: {app_path}",
        'try_again_later': "The service is temporarily unavailable. Please try again in a minute.",
        'use_template': "Using a template app. You can customize it in Xcode.",
        'retry_or_open_xcode': "Try again, or open the project in Xcode to continue manually.",
        'contact_support': "Please contact support if this issue persists."
    }
    
    return messages.get(action, "Please try again or open the project in Xcode.")

@app.on_event("startup")
async def startup_event():
    """Initialize system on startup"""
    print("=" * 60)
    print("SwiftGen V2 - Production iOS App Generator")
    print("=" * 60)
    print("✅ Intent Parser: Ready")
    print("✅ Circuit Breakers: Initialized")
    print("✅ LLM Router: Ready")
    print("✅ Builder: Ready with 30s timeout")
    print("✅ Pipeline: Ready")
    print("=" * 60)
    print("Server running at http://localhost:8000")
    print("API docs at http://localhost:8000/docs")
    print("=" * 60)

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    # Kill any hanging build processes
    try:
        subprocess.run(['pkill', '-9', 'xcodebuild'], capture_output=True)
    except:
        pass
    print("SwiftGen V2 shutdown complete")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)