"""
SwiftGen V2 - Correct Model Configurations
Uses actual working model IDs from each provider
"""

from dataclasses import dataclass
from typing import Optional

@dataclass
class ModelConfig:
    """Verified working model configurations"""
    provider: str
    model_id: str
    max_tokens: int
    temperature: float
    timeout: int
    api_endpoint: Optional[str] = None

# VERIFIED WORKING MODELS (as of August 2025)
PRODUCTION_MODELS = {
    "claude": ModelConfig(
        provider="anthropic",
        model_id="claude-3-5-sonnet-latest",  # Latest Sonnet model
        max_tokens=8192,
        temperature=0.7,
        timeout=60
    ),
    "gpt4": ModelConfig(
        provider="openai",
        model_id="gpt-4-0125-preview",  # Working GPT-4 model
        max_tokens=4096,
        temperature=0.7,
        timeout=60
    ),
    "grok": ModelConfig(
        provider="xai",
        model_id="grok-3",  # Grok 3 (aliases: grok-3-latest, grok-3-beta)
        max_tokens=8192,
        temperature=0.7,
        timeout=60,
        api_endpoint="https://api.x.ai/v1/chat/completions"
    )
}

def get_model_config(provider: str) -> ModelConfig:
    """Get verified model configuration"""
    return PRODUCTION_MODELS.get(provider.lower())

def validate_api_keys() -> dict:
    """Check which API keys are available"""
    import os
    
    available = {}
    required_keys = {
        "claude": "CLAUDE_API_KEY",
        "gpt4": "OPENAI_API_KEY",
        "grok": "XAI_API_KEY"
    }
    
    for provider, env_var in required_keys.items():
        api_key = os.getenv(env_var, "").strip()
        available[provider] = bool(api_key)
    
    return available
