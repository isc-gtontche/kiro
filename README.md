# AgentCore Returns & Refunds Agent

Complete implementation of a production-ready returns and refunds agent using AWS Bedrock AgentCore with Memory, Gateway, and Knowledge Base integrations.

## Overview

This project demonstrates a full-featured customer service agent that:
- Remembers customer preferences and history (AgentCore Memory)
- Looks up order details via Lambda functions (AgentCore Gateway)
- Accesses policy documents (Knowledge Base)
- Processes returns with custom business logic
- Deploys to production on AgentCore Runtime

## Architecture

```
Customer Request
    ↓
AgentCore Runtime (Production Agent)
    ↓
├── Memory (Customer preferences & history)
├── Gateway → Lambda (Order lookup)
├── Knowledge Base (Policy documents)
└── Custom Tools (Return eligibility, refund calculation)
```

## Project Structure

### Agent Files
- `01_returns_refunds_agent.py` - Initial agent with custom tools
- `06_memory_enabled_agent.py` - Agent with memory integration
- `14_full_agent.py` - Complete agent with memory + gateway (local testing)
- `17_runtime_agent.py` - Production-ready agent for Runtime deployment

### Setup Scripts
- `00_retrieve_kb_id.py` - Get Knowledge Base ID from CloudFormation
- `03_create_memory.py` - Create AgentCore Memory resource
- `04_seed_memory.py` - Add sample conversations to memory
- `08_create_cognito.py` - Set up OAuth authentication
- `09_create_gateway_role.py` - Create IAM role for gateway
- `10_create_lambda.py` - Deploy order lookup Lambda function
- `11_create_gateway.py` - Create AgentCore Gateway
- `12_add_lambda_to_gateway.py` - Register Lambda as gateway target
- `16_create_runtime_role.py` - Create IAM execution role for Runtime

### Deployment Scripts
- `19_deploy_agent.py` - Deploy agent to AgentCore Runtime
- `20_check_status.py` - Monitor deployment status
- `21_invoke_agent.py` - Test the deployed agent

### Testing Scripts
- `02_test_agent.py` - Test basic agent functionality
- `05_test_memory.py` - Verify memory retrieval
- `07_test_memory_agent.py` - Test memory-enabled agent
- `15_test_full_agent.py` - Test complete agent with all integrations
- `22_view_logs.py` - View CloudWatch logs

### Utility Scripts
- `13_list_gateway_targets.py` - List registered gateway targets

### Configuration Files
- `requirements.txt` - Python dependencies
- `kb_config.json` - Knowledge Base configuration
- `memory_config.json` - Memory resource configuration
- `cognito_config.json` - OAuth credentials
- `gateway_config.json` - Gateway configuration
- `lambda_config.json` - Lambda function details
- `runtime_config.json` - Deployed agent details

## Prerequisites

- AWS Account with access to:
  - Amazon Bedrock (Claude models)
  - AgentCore (Memory, Gateway, Runtime)
  - Lambda, IAM, Cognito, CloudWatch
- Python 3.9+
- AWS CLI configured

## Quick Start

### 1. Set Up Infrastructure

```bash
# Create Knowledge Base (if not exists)
python3 00_retrieve_kb_id.py

# Create Memory
python3 03_create_memory.py
python3 04_seed_memory.py

# Set up Authentication
python3 08_create_cognito.py

# Create Gateway
python3 09_create_gateway_role.py
python3 10_create_lambda.py
python3 11_create_gateway.py
python3 12_add_lambda_to_gateway.py
```

### 2. Test Locally

```bash
# Test basic agent
python3 02_test_agent.py

# Test with memory
python3 07_test_memory_agent.py

# Test complete agent
python3 15_test_full_agent.py
```

### 3. Deploy to Production

```bash
# Create execution role
python3 16_create_runtime_role.py

# Deploy to Runtime
python3 19_deploy_agent.py

# Check status
python3 20_check_status.py

# Test production agent
python3 21_invoke_agent.py
```

## Features

### Custom Tools
- **check_return_eligibility**: Validates return windows by category
- **calculate_refund_amount**: Computes refunds based on condition and reason
- **format_policy_response**: Formats policy text for customers

### AgentCore Memory
- **Semantic Memory**: Stores factual details (e.g., "returned defective laptop")
- **Preference Memory**: Captures preferences (e.g., "prefers email notifications")
- **Summary Memory**: Maintains conversation context

### AgentCore Gateway
- **Order Lookup**: Lambda function with mock order data
- **OAuth Authentication**: Cognito-based security
- **MCP Protocol**: Standardized tool interface

### Knowledge Base
- Retrieves Amazon return policy documents
- Provides accurate, up-to-date information

## Monitoring

### GenAI Observability Dashboard
```
https://console.aws.amazon.com/cloudwatch/home?region=us-west-2#gen-ai-observability/agent-core
```

### View Logs
```bash
# Programmatically
python3 22_view_logs.py

# AWS CLI
aws logs tail /aws/bedrock-agentcore/runtimes/returns_refunds_agent-*/DEFAULT --follow
```

### X-Ray Traces
```
https://console.aws.amazon.com/xray/home?region=us-west-2#/traces
```

## Cost Optimization

- **Memory**: ~$0.25 per 1,000 events
- **Gateway**: $5 per 1M invocations
- **Runtime**: Pay only for invocation time (scales to zero)
- **Bedrock**: Token-based pricing

## Architecture Decisions

### Why AgentCore Memory?
- Persistent across sessions
- Automatic preference extraction
- Semantic search capabilities
- No manual state management

### Why AgentCore Gateway?
- Centralized tool management
- OAuth security built-in
- Semantic tool discovery
- Protocol translation (Lambda, OpenAPI, MCP)

### Why AgentCore Runtime?
- Zero infrastructure management
- Auto-scaling
- Built-in observability
- Production-ready deployment

## Troubleshooting

### Agent not responding
```bash
python3 20_check_status.py
```

### View error logs
```bash
python3 22_view_logs.py
```

### Test individual components
```bash
# Test memory
python3 05_test_memory.py

# Test gateway
python3 13_list_gateway_targets.py
```

## Next Steps

1. **Add more tools**: Extend gateway with additional Lambda functions
2. **Enhance memory**: Add more conversation history
3. **Expand KB**: Upload more policy documents
4. **Monitor costs**: Set up CloudWatch billing alarms
5. **Scale**: Runtime auto-scales based on demand

## Resources

- [AgentCore Documentation](https://docs.aws.amazon.com/bedrock-agentcore/)
- [Strands Agents Framework](https://github.com/awslabs/strands-agents)
- [MCP Protocol](https://modelcontextprotocol.io/)

## License

MIT License - See LICENSE file for details

## Author

Built with AWS Bedrock AgentCore and Strands Agents framework.
