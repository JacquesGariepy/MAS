# Mock Mode Configuration Guide

## Overview

The MAS system now supports a **Mock Mode** that allows running and testing the system without requiring external LLM API keys. This is ideal for:

- Local development and testing
- CI/CD pipelines
- Demonstrations
- Environments without internet access
- Cost-effective testing

## How Mock Mode Works

When enabled, the LLM service generates intelligent mock responses instead of calling external APIs. The mock responses are context-aware and suitable for testing all agent types.

## Enabling Mock Mode

Mock mode is automatically enabled when:

1. **No API key is configured** (or using default test keys)
2. **LLM_PROVIDER is set to "mock"**
3. **ENABLE_MOCK_LLM is set to "true"**
4. **Running in test environment** (TESTING=true)

### Method 1: Using Test Configuration (Recommended)

```bash
# Use the provided test startup script
./start_test_mode.sh

# Or manually with test config
docker-compose -f docker-compose.dev.yml --env-file config/test.env up
```

### Method 2: Environment Variables

```bash
export ENABLE_MOCK_LLM=true
export LLM_PROVIDER=mock
docker-compose -f docker-compose.dev.yml up
```

### Method 3: Docker Compose Override

The `docker-compose.dev.yml` now defaults to mock mode:

```yaml
environment:
  - LLM_PROVIDER=${LLM_PROVIDER:-mock}
  - LLM_API_KEY=${LLM_API_KEY:-mock_key_for_testing}
  - ENABLE_MOCK_LLM=${ENABLE_MOCK_LLM:-true}
```

## Mock Response Examples

The mock LLM provides context-aware responses:

### Analysis Requests
```json
{
  "analysis": "Mock analysis indicates optimal conditions",
  "findings": [
    "Pattern A detected with 85% confidence",
    "Optimization opportunity identified",
    "Resource allocation is balanced"
  ],
  "recommendations": [
    "Continue current approach",
    "Monitor key metrics",
    "Consider scaling if needed"
  ],
  "confidence": 0.85,
  "status": "completed",
  "mock_mode": true
}
```

### Planning Requests
```json
{
  "plan": {
    "phase1": "Initial setup and configuration",
    "phase2": "Implementation and testing",
    "phase3": "Deployment and monitoring"
  },
  "timeline": "2-3 weeks estimated",
  "resources_needed": ["Developer", "Tester", "Reviewer"],
  "risks": ["Timeline constraints", "Resource availability"],
  "status": "ready",
  "mock_mode": true
}
```

### Agent BDI State
```json
{
  "beliefs": {
    "environment": "Testing environment detected",
    "capabilities": "All systems operational",
    "constraints": "Mock mode active"
  },
  "desires": [
    "Complete assigned tasks",
    "Collaborate with other agents",
    "Optimize performance"
  ],
  "intentions": [
    "Process incoming messages",
    "Update internal state",
    "Report status"
  ],
  "mock_mode": true
}
```

## Testing with Mock Mode

### Running Tests

```bash
# Start system in mock mode
./start_test_mode.sh

# Run the test suite
python examples/test_all_agent_types_fixed.py
```

### Expected Behavior

- ✅ All agent types (cognitive, reflexive, hybrid) work normally
- ✅ Inter-agent communication functions correctly
- ✅ No external API calls are made
- ✅ Responses are generated instantly
- ✅ System logs indicate "Mock Mode" is active

### Identifying Mock Mode

You can verify mock mode is active by:

1. **Check logs**: Look for "LLM Service initialized in MOCK MODE"
2. **Check responses**: Mock responses include `"mock_mode": true`
3. **Check API info**: The `/health` endpoint shows LLM configuration

## Configuration Reference

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ENABLE_MOCK_LLM` | `false` | Force mock mode regardless of other settings |
| `LLM_PROVIDER` | `openai` | Set to `mock` to enable mock mode |
| `LLM_API_KEY` | None | Mock mode auto-enables if missing |
| `OPENAI_API_KEY` | None | Fallback API key check |
| `TESTING` | `false` | Mock mode auto-enables when true |

### Configuration File (config/test.env)

```env
# Enable mock mode for testing
ENABLE_MOCK_LLM=true
LLM_PROVIDER=mock
LLM_API_KEY=mock_key_for_testing

# Other test settings
ENVIRONMENT=testing
DEBUG=true
RATE_LIMIT_ENABLED=false
```

## Production vs Mock Mode

### Production Mode
- Requires valid API keys
- Makes real API calls
- Full LLM capabilities
- Costs per API call
- Network latency

### Mock Mode
- No API keys needed
- No external calls
- Simulated responses
- Free to use
- Instant responses

## Troubleshooting

### Mock Mode Not Working

1. **Check environment variables**:
   ```bash
   docker-compose -f docker-compose.dev.yml exec core env | grep LLM
   ```

2. **Check service logs**:
   ```bash
   docker-compose -f docker-compose.dev.yml logs core | grep -i mock
   ```

3. **Verify configuration**:
   ```bash
   curl http://localhost:8088/health
   ```

### Switching to Production Mode

To use real LLM providers:

1. Set valid API keys:
   ```bash
   export OPENAI_API_KEY=your-real-api-key
   export LLM_PROVIDER=openai
   export ENABLE_MOCK_LLM=false
   ```

2. Restart services:
   ```bash
   docker-compose -f docker-compose.dev.yml down
   docker-compose -f docker-compose.dev.yml up
   ```

## Best Practices

1. **Use mock mode for**:
   - Unit tests
   - Integration tests
   - Local development
   - CI/CD pipelines
   - Demos and tutorials

2. **Use production mode for**:
   - Performance testing
   - Real workload testing
   - Production deployment
   - Advanced AI features

3. **Configuration management**:
   - Keep separate env files (test.env, prod.env)
   - Use environment-specific docker-compose files
   - Document API key requirements clearly

## Summary

Mock mode makes MAS accessible for testing and development without external dependencies. It provides realistic responses suitable for verifying system functionality while keeping costs at zero.