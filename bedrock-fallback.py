#!/usr/bin/env python3
"""
Claude 4.0 with Bedrock Fallback Script
Calls Anthropic API directly first, falls back to Amazon Bedrock on throttling/failure
"""

import boto3
import json
import time
import logging
import os
from typing import Optional, Dict, Any
from dataclasses import dataclass
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ClaudeResponse:
    content: str
    model_used: str
    source: str  # 'anthropic' or 'bedrock'
    usage: Optional[Dict[str, Any]] = None

class ClaudeFallbackClient:
    def __init__(self, anthropic_api_key: str = None, aws_region: str = 'us-east-1'):
        self.anthropic_api_key = anthropic_api_key
        self.aws_region = aws_region
        
        # Initialize Bedrock client with better error handling
        try:
            self.bedrock_client = boto3.client('bedrock-runtime', region_name=aws_region)
            # Test AWS credentials
            sts_client = boto3.client('sts', region_name=aws_region)
            identity = sts_client.get_caller_identity()
            logger.info(f"✅ AWS credentials valid for account: {identity.get('Account', 'Unknown')}")
        except Exception as e:
            logger.warning(f"⚠️ AWS credentials issue: {str(e)}")
            logger.warning("🔧 Bedrock fallback may not work. Please configure AWS credentials.")
        
        # Setup requests session with retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Anthropic API endpoint
        self.anthropic_url = "https://api.anthropic.com/v1/messages"
        
    def call_anthropic_direct(self, prompt: str, max_tokens: int = 4000) -> ClaudeResponse:
        """Call Anthropic API directly"""
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.anthropic_api_key,
            "anthropic-version": "2023-06-01"
        }
        
        payload = {
            "model": "claude-3-5-sonnet-20241022",  # Latest Claude model
            "max_tokens": max_tokens,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        
        try:
            logger.info("Attempting Anthropic API call...")
            response = self.session.post(
                self.anthropic_url,
                headers=headers,
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                content = data['content'][0]['text']
                usage = data.get('usage', {})
                
                logger.info("✅ Anthropic API call successful")
                return ClaudeResponse(
                    content=content,
                    model_used="claude-3-5-sonnet-20241022",
                    source="anthropic",
                    usage=usage
                )
            
            elif response.status_code == 429:
                logger.warning("⚠️ Anthropic API throttled (429)")
                raise Exception(f"Throttled: {response.text}")
            
            else:
                logger.error(f"❌ Anthropic API error: {response.status_code}")
                raise Exception(f"API Error {response.status_code}: {response.text}")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Request failed: {str(e)}")
            raise Exception(f"Request failed: {str(e)}")  

    def call_bedrock_fallback(self, prompt: str, max_tokens: int = 4000) -> ClaudeResponse:   
        """Call Amazon Bedrock as fallback"""
        try:
            logger.info("🔄 Calling Amazon Bedrock...")
            
            # Use Claude inference profile instead of direct model ID
            model_id = "us.anthropic.claude-3-5-sonnet-20241022-v2:0"
            
            # Prepare the request body for Bedrock
            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }
            
            response = self.bedrock_client.invoke_model(
                modelId=model_id,
                body=json.dumps(body),
                contentType="application/json"
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            content = response_body['content'][0]['text']
            usage = response_body.get('usage', {})
            
            logger.info("✅ Bedrock fallback successful")
            return ClaudeResponse(
                content=content,
                model_used=model_id,
                source="bedrock",
                usage=usage
            )
            
        except Exception as e:
            logger.error(f"❌ Bedrock fallback failed: {str(e)}")
            raise Exception(f"Bedrock fallback failed: {str(e)}")
    
    def generate_response(self, prompt: str, max_tokens: int = 4000) -> ClaudeResponse:
        """
        Main method: Try Anthropic first, fallback to Bedrock on failure
        """
        try:
            # First attempt: Anthropic API
            return self.call_anthropic_direct(prompt, max_tokens)
            
        except Exception as anthropic_error:
            logger.warning(f"Anthropic failed: {str(anthropic_error)}")
            
            # Check if it's a throttling error or other failure
            if "429" in str(anthropic_error) or "throttl" in str(anthropic_error).lower():
                logger.info("🚦 Detected throttling, switching to Bedrock...")
            else:
                logger.info("💥 Detected failure, switching to Bedrock...")
            
            # Fallback attempt: Amazon Bedrock
            try:
                return self.call_bedrock_fallback(prompt, max_tokens)
            except Exception as bedrock_error:
                # Both failed
                error_msg = f"Both services failed. Anthropic: {anthropic_error}. Bedrock: {bedrock_error}"
                logger.error(f"💀 {error_msg}")
                raise Exception(error_msg)

def main():
    """Example usage"""
    # Get configuration from environment variables
    anthropic_key = os.getenv('ANTHROPIC_API_KEY')
    aws_region = os.getenv('AWS_REGION', 'us-east-1')
    max_tokens = int(os.getenv('MAX_TOKENS', '4000'))
    log_level = os.getenv('LOG_LEVEL', 'INFO')
    
    # Configure logging level from environment
    logging.getLogger().setLevel(getattr(logging, log_level.upper()))
    
    if not anthropic_key:
        print("❌ Please set ANTHROPIC_API_KEY in your .env file")
        print("📝 Edit the .env file and add your API key")
        return
    
    # Initialize client with configuration from .env file
    client = ClaudeFallbackClient(
        anthropic_api_key=anthropic_key,
        aws_region=aws_region
    )
    
    # Example prompt
    prompt = "Explain quantum computing in simple terms."
    
    try:
        print("🚀 Generating response...")
        print(f"📍 Using region: {aws_region}")
        print(f"🎯 Max tokens: {max_tokens}")
        
        response = client.generate_response(prompt, max_tokens=max_tokens)
        
        print(f"\n📊 Response Details:")
        print(f"Source: {response.source}")
        print(f"Model: {response.model_used}")
        if response.usage:
            print(f"Usage: {response.usage}")
        
        print(f"\n💬 Response:")
        print(response.content)
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    main()