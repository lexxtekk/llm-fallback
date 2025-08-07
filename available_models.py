#!/usr/bin/env python3
"""
Available Models Configuration
Simple model definitions with their LiteLLM identifiers
"""

# Available models with their LiteLLM model identifiers
AVAILABLE_MODELS = {
    # Anthropic Direct
    'claude-3-5-sonnet': 'claude-3-5-sonnet-20241022',
    'claude-3-haiku': 'claude-3-haiku-20240307',
    
    # OpenAI
    'gpt-4o': 'gpt-4o',
    'gpt-4o-mini': 'gpt-4o-mini',
    'gpt-4-turbo': 'gpt-4-turbo',
    
    # Bedrock
    'claude-3-5-sonnet-bedrock': 'bedrock/us.anthropic.claude-3-5-sonnet-20241022-v2:0',
    'claude-3-haiku-bedrock': 'bedrock/anthropic.claude-3-haiku-20240307-v1:0',
    
    # Other Providers
    'cohere-command-r-plus': 'cohere/command-r-plus',
    'gemini-1-5-pro': 'gemini/gemini-1.5-pro',
}

# Model display names for logging
MODEL_NAMES = {
    'claude-3-5-sonnet': 'Claude 3.5 Sonnet (Direct)',
    'claude-3-haiku': 'Claude 3 Haiku (Direct)',
    'gpt-4o': 'GPT-4o',
    'gpt-4o-mini': 'GPT-4o Mini',
    'gpt-4-turbo': 'GPT-4 Turbo',
    'claude-3-5-sonnet-bedrock': 'Claude 3.5 Sonnet (Bedrock)',
    'claude-3-haiku-bedrock': 'Claude 3 Haiku (Bedrock)',
    'cohere-command-r-plus': 'Cohere Command R+',
    'gemini-1-5-pro': 'Gemini 1.5 Pro',
}

def get_model_id(model_key: str) -> str:
    """Get the LiteLLM model ID for a model key"""
    if model_key not in AVAILABLE_MODELS:
        raise ValueError(f"Unknown model: {model_key}. Available: {list(AVAILABLE_MODELS.keys())}")
    return AVAILABLE_MODELS[model_key]

def get_model_name(model_key: str) -> str:
    """Get the display name for a model key"""
    return MODEL_NAMES.get(model_key, model_key)

def list_available_models():
    """Print all available models"""
    print("Available Models:")
    for key, model_id in AVAILABLE_MODELS.items():
        name = get_model_name(key)
        print(f"  {key}: {name}")

if __name__ == "__main__":
    list_available_models()