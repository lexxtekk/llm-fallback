#!/usr/bin/env python3
"""
Simple LLM Handler
Processes event payloads with fallback order using available models
"""

import os
import logging
import time
from typing import Dict, Any, Optional
from dataclasses import dataclass
from dotenv import load_dotenv
import litellm
from litellm import completion

# Import our simple configurations
from available_models import AVAILABLE_MODELS, MODEL_NAMES, get_model_id, get_model_name
from event_payload import EventPayload

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Suppress LiteLLM debug logs
litellm.set_verbose = False

@dataclass
class SimpleResponse:
    """Simple response structure"""
    success: bool
    content: Optional[str] = None
    model_used: Optional[str] = None
    cost: Optional[float] = None
    usage: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    attempts: Optional[list] = None

class SimpleLLMHandler:
    def __init__(self):
        """Initialize the handler"""
        self._setup_api_keys()
        logger.info(f"✅ Handler initialized with {len(AVAILABLE_MODELS)} available models")
    
    def _setup_api_keys(self):
        """Set up API keys for all providers"""
        api_keys = {
            'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),
            'ANTHROPIC_API_KEY': os.getenv('ANTHROPIC_API_KEY'),
            'COHERE_API_KEY': os.getenv('COHERE_API_KEY'),
            'GOOGLE_API_KEY': os.getenv('GOOGLE_API_KEY'),
            'AWS_ACCESS_KEY_ID': os.getenv('AWS_ACCESS_KEY_ID'),
            'AWS_SECRET_ACCESS_KEY': os.getenv('AWS_SECRET_ACCESS_KEY'),
            'AWS_SESSION_TOKEN': os.getenv('AWS_SESSION_TOKEN'),
        }
        
        # Set environment variables for LiteLLM
        for key, value in api_keys.items():
            if value:
                os.environ[key] = value
    
    def _call_model(self, model_key: str, prompt: str, max_tokens: int, temperature: float) -> Dict[str, Any]:
        """Call a specific model"""
        model_id = get_model_id(model_key)
        model_name = get_model_name(model_key)
        
        try:
            logger.info(f"🔄 Trying {model_name}...")
            
            # Make the API call
            response = completion(
                model=model_id,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            # Extract response data
            content = response.choices[0].message.content
            usage = response.usage._asdict() if hasattr(response.usage, '_asdict') else dict(response.usage)
            
            # Calculate cost if available
            cost = None
            try:
                cost = litellm.completion_cost(completion_response=response)
            except:
                pass
            
            logger.info(f"✅ {model_name} successful")
            
            return {
                'success': True,
                'content': content,
                'model_used': model_id,
                'usage': usage,
                'cost': cost
            }
            
        except Exception as e:
            error_msg = f"{model_name} failed: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return {
                'success': False,
                'error': error_msg
            }
    
    def process(self, payload: EventPayload) -> SimpleResponse:
        """
        Process an event payload with fallback order
        
        Args:
            payload: EventPayload with prompt and ordered list of models
            
        Returns:
            SimpleResponse with results
        """
        
        logger.info(f"🚀 Processing request (ID: {payload.request_id})")
        logger.info(f"📝 Prompt: {payload.prompt[:100]}{'...' if len(payload.prompt) > 100 else ''}")
        logger.info(f"🎯 Model order: {payload.models}")
        
        attempts = []
        
        # Try each model in order
        for i, model_key in enumerate(payload.models):
            is_primary = (i == 0)
            model_name = get_model_name(model_key)
            
            if is_primary:
                logger.info(f"🎯 Primary model: {model_name}")
            else:
                logger.info(f"🔄 Fallback #{i}: {model_name}")
            
            result = self._call_model(
                model_key,
                payload.prompt,
                payload.max_tokens,
                payload.temperature
            )
            
            attempts.append({
                'model': model_key,
                'name': model_name,
                'status': 'success' if result['success'] else 'failed',
                'error': result.get('error', '')
            })
            
            if result['success']:
                logger.info(f"✅ Success with {model_name}")
                return SimpleResponse(
                    success=True,
                    content=result['content'],
                    model_used=model_key,
                    cost=result.get('cost'),
                    usage=result.get('usage'),
                    attempts=attempts
                )
        
        # All models failed
        error_msg = f"All {len(payload.models)} models failed"
        logger.error(f"💀 {error_msg}")
        
        return SimpleResponse(
            success=False,
            error=error_msg,
            attempts=attempts
        )

def main():
    """Example usage"""
    import sys
    from event_payload import get_example_payload, EXAMPLE_PAYLOADS
    
    # Initialize handler
    handler = SimpleLLMHandler()
    
    # Check command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "models":
            # List available models
            print("📋 Available Models:")
            for key in AVAILABLE_MODELS.keys():
                name = get_model_name(key)
                print(f"  {key}: {name}")
            return
        
        elif sys.argv[1] == "strategies":
            # Show example strategies
            print("📋 Example Strategies:")
            for strategy in EXAMPLE_PAYLOADS.keys():
                example = EXAMPLE_PAYLOADS[strategy]
                print(f"  {strategy}: {example.models}")
            return
        
        elif sys.argv[1] in EXAMPLE_PAYLOADS:
            # Use specific strategy
            strategy = sys.argv[1]
            payload = get_example_payload(strategy, "Explain quantum computing in simple terms.")
            print(f"🎯 Using {strategy} strategy")
        else:
            print(f"Unknown option: {sys.argv[1]}")
            print("Available options: models, strategies, or strategy name")
            return
    else:
        # Default example
        payload = get_example_payload("quality_first", "Explain quantum computing in simple terms.")
    
    # Process the payload
    response = handler.process(payload)
    
    # Print results
    print(f"\n📊 Results:")
    print(f"Success: {'✅' if response.success else '❌'}")
    
    if response.success:
        print(f"Model Used: {get_model_name(response.model_used)}")
        if response.cost:
            print(f"Cost: ${response.cost:.4f}")
        if response.usage:
            print(f"Usage: {response.usage}")
        print(f"\n💬 Response:")
        print(response.content)
    else:
        print(f"Error: {response.error}")
    
    # Show attempt history
    if response.attempts:
        print(f"\n🔄 Attempt History:")
        for i, attempt in enumerate(response.attempts, 1):
            status_icon = "✅" if attempt['status'] == 'success' else "❌"
            print(f"  {i}. {attempt['name']}: {status_icon}")
            if attempt['error']:
                print(f"     Error: {attempt['error'][:80]}...")

if __name__ == "__main__":
    main()