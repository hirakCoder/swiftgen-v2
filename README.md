# SwiftGen V2 - Production iOS App Generator

Generate production-ready iOS apps from natural language descriptions in under 60 seconds.

## Features

✅ **Working Features:**
- Generate iOS apps from natural language descriptions
- Direct Swift compilation (bypassing xcodebuild issues)
- Automatic simulator launch
- App modification with rebuild and relaunch
- Multi-LLM support (Claude 3.5, GPT-4, xAI Grok)
- Intent-based parsing
- Circuit breakers for error prevention
- Flexible prompts for creative freedom

🚧 **Pending Implementation:**
- Robust error handling and auto-fix mechanism
- Automatic compilation error recovery
- Build failure auto-resolution
- Syntax error correction

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/swiftgen-v2.git
cd swiftgen-v2
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
export CLAUDE_API_KEY="your-claude-api-key"
export OPENAI_API_KEY="your-openai-api-key"
export XAI_API_KEY="your-xai-api-key"
```

## Usage

1. Start the server:
```bash
python run.py
```

2. Open browser:
```
http://localhost:8000
```

3. Generate an app:
```bash
curl -X POST http://localhost:8000/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Create a timer app with start, stop, and reset buttons",
    "app_name": "MyTimer"
  }'
```

4. Modify an app:
```bash
curl -X POST http://localhost:8000/api/modify \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Add dark mode support",
    "app_name": "MyTimer",
    "project_id": "project-id-here"
  }'
```

## Architecture

### Core Components

- **Intent Parser** (`core/intent.py`): Understands what users want
- **Circuit Breakers** (`core/circuit_breaker.py`): Prevents cascading failures
- **LLM Router** (`generation/llm_router.py`): Routes to best LLM for task
- **Direct Build** (`build/direct_build.py`): Compiles Swift directly
- **Pipeline** (`core/pipeline.py`): Orchestrates the entire flow

### Build System

The system uses direct Swift compilation with `swiftc` to bypass xcodebuild issues:
- Compiles Swift files directly to executable
- Creates proper app bundle structure
- Installs and launches in simulator

### Multi-LLM Strategy

- **Claude 3.5 Sonnet**: Best for architecture and complex apps
- **GPT-4 Turbo**: Good for algorithms and bug fixes
- **xAI Grok**: Excellent for UI design and simple tasks

## API Endpoints

### Generate App
```
POST /api/generate
Body: {
  "description": "string",
  "app_name": "string"
}
```

### Modify App
```
POST /api/modify
Body: {
  "description": "string",
  "app_name": "string",
  "project_id": "string"
}
```

### Get Status
```
GET /api/status/{project_id}
```

### Health Check
```
GET /api/health
```

## Requirements

- macOS with Xcode installed
- Python 3.8+
- iOS Simulator
- API keys for Claude, OpenAI, and xAI

## License

MIT

## Contributing

Pull requests are welcome. For major changes, please open an issue first.