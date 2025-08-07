# Multi-Provider LLM Handler

A Python system for building resilient AI applications by using configurable fallback strategies for multiple LLM providers. Supports AWS Bedrock, Anthropic, OpenAI, Cohere, and Google models with automatic failover.

## 🚀 Features

- **Multiple Providers**: Anthropic, OpenAI, AWS Bedrock, Cohere, Google
- **Configurable Fallbacks**: Define your own model priority order
- **Cost Tracking**: Monitor usage and costs across providers
- **Simple API**: Clean, straightforward interface
- **JSON Support**: Easy integration with APIs and services
- **Predefined Strategies**: Quality-first, speed-first, cost-conscious options

## 📁 Project Structure

```
├── available_models.py     # Model configurations and LiteLLM mappings
├── event_payload.py        # Event structure definitions
├── llm_handler.py         # Main handler with fallback logic
├── .env                   # API keys (create this file)
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## 🛠️ Setup

### 1. Install Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install packages
pip install -r requirements.txt
```

### 2. Configure API Keys

Create a `.env` file with your API keys:

```bash
# Multi-Provider LLM API Keys
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
OPENAI_API_KEY=sk-your-openai-key-here
COHERE_API_KEY=your-cohere-key-here
GOOGLE_API_KEY=your-google-key-here

# AWS Configuration (for Bedrock)
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_SESSION_TOKEN=your-session-token  # If using temporary credentials
# OR use AWS Profile
# AWS_PROFILE=default
```

**Note**: You only need the API keys for providers you want to use. The system will automatically skip unavailable providers.

## 🎯 Quick Start

### Command Line Usage

```bash
# List available models
python llm_handler.py models

# Show predefined strategies
python llm_handler.py strategies

# Run with default strategy
python llm_handler.py

# Use specific strategies
python llm_handler.py quality_first
python llm_handler.py speed_first
python llm_handler.py cost_first
```

### Python Code Usage

```python
from event_payload import EventPayload
from llm_handler import SimpleLLMHandler

# Create event with custom fallback order
payload = EventPayload(
    prompt="Explain machine learning in simple terms",
    models=[
        "claude-3-5-sonnet",        # 1st choice (primary)
        "gpt-4o",                   # 2nd choice
        "claude-3-5-sonnet-bedrock", # 3rd choice
        "gpt-4o-mini"               # 4th choice (last resort)
    ],
    max_tokens=2000,
    temperature=0.7
)

# Process with handler
handler = SimpleLLMHandler()
response = handler.process(payload)

if response.success:
    print(f"Response: {response.content}")
    print(f"Model used: {response.model_used}")
    print(f"Cost: ${response.cost:.4f}")
else:
    print(f"All models failed: {response.error}")
```

## 📋 Available Models

| Model Key | Provider | Description |
|-----------|----------|-------------|
| `claude-3-5-sonnet` | Anthropic | Claude 3.5 Sonnet (Direct API) |
| `claude-3-haiku` | Anthropic | Claude 3 Haiku (Direct API) |
| `gpt-4o` | OpenAI | GPT-4o |
| `gpt-4o-mini` | OpenAI | GPT-4o Mini (cheaper) |
| `gpt-4-turbo` | OpenAI | GPT-4 Turbo |
| `claude-3-5-sonnet-bedrock` | AWS Bedrock | Claude 3.5 Sonnet via Bedrock |
| `claude-3-haiku-bedrock` | AWS Bedrock | Claude 3 Haiku via Bedrock |
| `cohere-command-r-plus` | Cohere | Command R+ |
| `gemini-1-5-pro` | Google | Gemini 1.5 Pro |

## 🎯 Predefined Strategies

### Quality First
Best models first, cost secondary:
```python
models = ["claude-3-5-sonnet", "gpt-4o", "claude-3-5-sonnet-bedrock", "gpt-4o-mini"]
```

### Speed First
Fastest models first:
```python
models = ["claude-3-haiku", "gpt-4o-mini", "claude-3-haiku-bedrock", "claude-3-5-sonnet"]
```

### Cost First
Cheapest models first:
```python
models = ["gpt-4o-mini", "claude-3-haiku", "claude-3-haiku-bedrock", "gpt-4o"]
```

### Provider-Specific
Use only specific providers:
```python
# Anthropic only
models = ["claude-3-5-sonnet", "claude-3-haiku", "claude-3-5-sonnet-bedrock"]

# OpenAI only
models = ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"]
```

## 🔧 Advanced Usage

### JSON API Integration

```python
import json
from event_payload import EventPayload

# Create from JSON
json_input = '''
{
  "prompt": "What is quantum computing?",
  "models": ["claude-3-5-sonnet", "gpt-4o", "gpt-4o-mini"],
  "max_tokens": 1500,
  "temperature": 0.5,
  "request_id": "req-123"
}
'''

payload = EventPayload.from_json(json_input)
response = handler.process(payload)

# Convert response to JSON for APIs
response_json = {
    "success": response.success,
    "content": response.content,
    "model_used": response.model_used,
    "cost": response.cost,
    "attempts": len(response.attempts) if response.attempts else 0
}
```

### Custom Fallback Orders

```python
# High-stakes: Multiple high-quality options
payload = EventPayload(
    prompt="Write a critical business analysis",
    models=["claude-3-5-sonnet", "gpt-4o", "gpt-4-turbo", "claude-3-5-sonnet-bedrock"]
)

# Quick tasks: Fast and cheap
payload = EventPayload(
    prompt="Summarize this text",
    models=["gpt-4o-mini", "claude-3-haiku"]
)

# Diverse providers: Avoid single-provider dependency
payload = EventPayload(
    prompt="Creative writing task",
    models=["claude-3-5-sonnet", "gpt-4o", "cohere-command-r-plus", "gemini-1-5-pro"]
)
```

## 📊 Response Structure

```python
@dataclass
class SimpleResponse:
    success: bool                    # Whether any model succeeded
    content: Optional[str]           # The generated response
    model_used: Optional[str]        # Which model was used
    cost: Optional[float]            # Cost in USD
    usage: Optional[Dict]            # Token usage details
    error: Optional[str]             # Error message if all failed
    attempts: Optional[list]         # History of all attempts
```

## 🔍 Monitoring and Debugging

### View Attempt History

```python
response = handler.process(payload)

print("Attempt History:")
for i, attempt in enumerate(response.attempts, 1):
    status = "✅" if attempt['status'] == 'success' else "❌"
    print(f"  {i}. {attempt['name']}: {status}")
    if attempt['error']:
        print(f"     Error: {attempt['error']}")
```

### Cost Tracking

```python
total_cost = 0
responses = []

for prompt in prompts:
    payload = EventPayload(prompt=prompt, models=["claude-3-5-sonnet", "gpt-4o"])
    response = handler.process(payload)
    
    if response.success and response.cost:
        total_cost += response.cost
    
    responses.append(response)

print(f"Total cost: ${total_cost:.4f}")
```

## 🛠️ Extending the System

### Adding New Models

Edit `available_models.py`:

```python
AVAILABLE_MODELS = {
    # ... existing models ...
    'new-model-key': 'litellm-model-identifier',
}

MODEL_NAMES = {
    # ... existing names ...
    'new-model-key': 'Human Readable Name',
}
```

### Adding New Strategies

Edit `event_payload.py`:

```python
EXAMPLE_PAYLOADS = {
    # ... existing strategies ...
    "my_custom_strategy": EventPayload(
        prompt="Your prompt here",
        models=["model1", "model2", "model3"]
    ),
}
```

## 🚨 Troubleshooting

### Common Issues

**Import Errors**:
```bash
# Make sure you're in the right directory
ls -la  # Should see llm_handler.py, event_payload.py, available_models.py

# Activate virtual environment
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

**API Key Errors**:
```bash
# Check your .env file
cat .env

# Test with models you have keys for
python llm_handler.py openai_only  # if you have OpenAI
python llm_handler.py anthropic_only  # if you have Anthropic
```

**All Models Failing**:
- Check your internet connection
- Verify API keys are correct and not expired
- Check if you have sufficient credits/quota
- Try with a single, known-working model first

### Debug Mode

Set logging to DEBUG in `llm_handler.py`:

```python
logging.basicConfig(level=logging.DEBUG)
```

## 📝 License

This project is open source. Feel free to modify and distribute.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📞 Support

For issues and questions:
1. Check the troubleshooting section above
2. Review the example code
3. Test with individual providers to isolate issues
4. Check API provider status pages for outages

---

**Happy prompting! 🚀**