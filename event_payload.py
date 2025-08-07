#!/usr/bin/env python3
"""
Event Payload Structure
Simple event payload for LLM requests with fallback order
"""

import json
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

@dataclass
class EventPayload:
    """Simple event payload with fallback order"""
    prompt: str
    models: List[str]  # First model is primary, rest are fallbacks in order
    max_tokens: int = 4000
    temperature: float = 0.7
    request_id: Optional[str] = None
    
    @property
    def primary_model(self) -> str:
        """Get the primary model (first in the list)"""
        return self.models[0]
    
    @property
    def fallback_models(self) -> List[str]:
        """Get the fallback models (rest of the list)"""
        return self.models[1:] if len(self.models) > 1 else []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'prompt': self.prompt,
            'models': self.models,
            'max_tokens': self.max_tokens,
            'temperature': self.temperature,
            'request_id': self.request_id
        }
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EventPayload':
        """Create from dictionary"""
        return cls(**data)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'EventPayload':
        """Create from JSON string"""
        data = json.loads(json_str)
        return cls.from_dict(data)

# Example payloads for common scenarios
EXAMPLE_PAYLOADS = {

    "1p_to_3p": EventPayload(
        prompt="What is cloud computing",
        models=[
            "claude-3-haiku-bedrock",
            "claude-3-5-sonnet"
            ]
    ),

    "quality_first": EventPayload(
        prompt="Your prompt here",
        models=[
            "claude-3-5-sonnet",
            "gpt-4o", 
            "claude-3-5-sonnet-bedrock",
            "gpt-4o-mini"
        ]
    ),
    
    "speed_first": EventPayload(
        prompt="Your prompt here",
        models=[
            "claude-3-haiku",
            "gpt-4o-mini",
            "claude-3-haiku-bedrock",
            "claude-3-5-sonnet"
        ]
    ),
    
    "cost_first": EventPayload(
        prompt="Your prompt here", 
        models=[
            "gpt-4o-mini",
            "claude-3-haiku",
            "claude-3-haiku-bedrock",
            "gpt-4o"
        ]
    ),
    
    "anthropic_only": EventPayload(
        prompt="Your prompt here",
        models=[
            "claude-3-5-sonnet",
            "claude-3-haiku",
            "claude-3-5-sonnet-bedrock",
            "claude-3-haiku-bedrock"
        ]
    ),
    
    "openai_only": EventPayload(
        prompt="Your prompt here",
        models=[
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4-turbo"
        ]
    )
}

def create_payload(prompt: str, models: List[str], **kwargs) -> EventPayload:
    """Helper to create event payload"""
    return EventPayload(prompt=prompt, models=models, **kwargs)

def get_example_payload(strategy: str, prompt: str) -> EventPayload:
    """Get an example payload with custom prompt"""
    if strategy not in EXAMPLE_PAYLOADS:
        raise ValueError(f"Unknown strategy: {strategy}. Available: {list(EXAMPLE_PAYLOADS.keys())}")
    
    example = EXAMPLE_PAYLOADS[strategy]
    return EventPayload(
        prompt=prompt,
        models=example.models,
        max_tokens=example.max_tokens,
        temperature=example.temperature
    )

if __name__ == "__main__":
    # Show example payloads
    print("Example Event Payloads:\n")
    
    for strategy, payload in EXAMPLE_PAYLOADS.items():
        print(f"{strategy.upper()}:")
        print(f"  Primary: {payload.primary_model}")
        print(f"  Fallbacks: {payload.fallback_models}")
        print()
    
    # Show JSON example
    example = get_example_payload("quality_first", "Explain machine learning")
    print("JSON Example:")
    print(example.to_json())