# Complete AgentCore Tutorial: Building a Production Returns & Refunds Agent

This tutorial walks through building a complete production-ready customer service agent using AWS Bedrock AgentCore, from initial setup to production deployment.

## Table of Contents

1. [Introduction](#introduction)
2. [What is AgentCore?](#what-is-agentcore)
3. [Architecture Overview](#architecture-overview)
4. [Step-by-Step Implementation](#step-by-step-implementation)
5. [Testing & Validation](#testing--validation)
6. [Production Deployment](#production-deployment)
7. [Monitoring & Observability](#monitoring--observability)
8. [Key Learnings](#key-learnings)

---

## Introduction

This tutorial demonstrates building a sophisticated customer service agent that:
- **Remembers** customer preferences and history (AgentCore Memory)
- **Looks up** order details via external APIs (AgentCore Gateway)
- **Retrieves** policy documents (Knowledge Base)
- **Processes** returns with custom business logic
- **Deploys** to production with auto-scaling (AgentCore Runtime)

**What You'll Build:**
A production-ready returns and refunds agent that can:
- Check return eligibility based on purchase date and category
- Calculate refunds considering item condition and return reason
- Look up order details from a database
- Remember customer communication preferences
- Access policy documents for accurate information

---

## What is AgentCore?

AgentCore is AWS's managed platform for building and deploying production AI agents. It provides three core services:

### 1. AgentCore Memory
**What it does:** Persistent, intelligent memory for agents

**Key Features:**
- **Three memory strategies:**
  - **Semantic**: Stores factual details (e.g., "returned defective laptop")
  - **Preferences**: Captures user preferences (e.g., "prefers email notifications")
  - **Summary**: Maintains conversation context and summaries
- **Two-tier system:**
  - Short-term memory (STM): Immediate conversation storage
  - Long-term memory (LTM): Async processing and extraction (20-30 seconds)
- **Event-based pricing:** $0.25 per 1,000 events (not time-based!)

**Why use it?**
- No manual state management
- Automatic preference extraction
- Semantic search across conversations
- Persistent across sessions

### 2. AgentCore Gateway
**What it does:** Centralized hub for connecting agents to external services

**Key Features:**
- **Four target types:**
  - Lambda functions
  - OpenAPI endpoints
  - MCP servers
  - Smithy models
- **Built-in security:** OAuth2, API keys, IAM
- **Semantic search:** Agents discover tools automatically
- **Protocol translation:** Unified interface for different backends

**Pricing:** $25/M search calls, $5/M invoke calls

**Why use it?**
- Centralized tool management
- OAuth security built-in
- No custom integration code
- Semantic tool discovery

### 3. AgentCore Runtime
**What it does:** Serverless deployment platform for production agents

**Key Features:**
- **Zero infrastructure:** No servers to manage
- **Auto-scaling:** From zero to any load
- **Built-in observability:** CloudWatch + X-Ray
- **OAuth-protected endpoints:** Secure by default

**Deployment Process:**
```
Your Code → CodeBuild → Docker Container → ECR → Runtime → HTTPS Endpoint
```

**Why use it?**
- No infrastructure management
- Pay only for invocation time
- Production-ready out of the box
- Automatic health monitoring

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Customer Request                         │
└────────────────────────────┬────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                   AgentCore Runtime Agent                       │
│                  (Production Deployment)                        │
└────────────────────────────┬────────────────────────────────────┘
                             ↓
        ┌────────────────────┼────────────────────┐
        ↓                    ↓                    ↓
┌───────────────┐   ┌────────────────┐   ┌──────────────┐
│ AgentCore     │   │ AgentCore      │   │ Knowledge    │
│ Memory        │   │ Gateway        │   │ Base         │
│               │   │                │   │              │
│ • Semantic    │   │ ↓              │   │ • Policy     │
│ • Preferences │   │ Lambda         │   │   Documents  │
│ • Summary     │   │ (Order Lookup) │   │ • FAQs       │
└───────────────┘   └────────────────┘   └──────────────┘
                             ↓
                    ┌────────────────┐
                    │ Custom Tools   │
                    │                │
                    │ • Eligibility  │
                    │ • Refund Calc  │
                    │ • Formatting   │
                    └────────────────┘
```

---

## Step-by-Step Implementation

### Phase 1: Basic Agent with Custom Tools

**Goal:** Create an agent with custom business logic

**Script:** `01_returns_refunds_agent.py`

**Custom Tools Created:**
1. **check_return_eligibility**: Validates return windows
   - Electronics: 30 days
   - Clothing: 60 days
   - Books: 30 days

2. **calculate_refund_amount**: Computes refunds
   - Considers item condition (new, like-new, used)
   - Applies restocking fees based on reason
   - Defects: No restocking fee
   - Changed mind: 15% restocking fee

3. **format_policy_response**: Customer-friendly formatting

**Built-in Tools:**
- `current_time`: Get current date/time
- `retrieve`: Access Knowledge Base documents

**Test:** `02_test_agent.py`
```bash
python3 02_test_agent.py
```

**Result:** Agent successfully uses custom tools and Knowledge Base

---

### Phase 2: Add Memory for Personalization

**Goal:** Enable the agent to remember customer preferences and history

**What is AgentCore Memory?**

Memory provides persistent, intelligent storage across conversations:

**Infrastructure:**
- S3 for vector embeddings
- DynamoDB for metadata
- OpenSearch for semantic search
- Lambda for async processing

**Memory Strategies:**
```python
[
  {"summaryMemoryStrategy": {
    "name": "summary",
    "namespaces": ["app/{actorId}/{sessionId}/summary"]
  }},
  {"userPreferenceMemoryStrategy": {
    "name": "preferences", 
    "namespaces": ["app/{actorId}/preferences"]
  }},
  {"semanticMemoryStrategy": {
    "name": "semantic",
    "namespaces": ["app/{actorId}/semantic"]
  }}
]
```

**Setup Steps:**

1. **Create Memory Resource** (`03_create_memory.py`)
```bash
python3 03_create_memory.py
```
Creates: `returns_refunds_memory-4otpYM6Aks`

2. **Seed with Sample Data** (`04_seed_memory.py`)
```bash
python3 04_seed_memory.py
```
Adds conversations for user_001:
- "I prefer email notifications"
- "Previously returned defective laptop"

**Wait 30 seconds** for async processing to extract preferences!

3. **Verify Memory** (`05_verify_memory.py`)
```bash
python3 05_verify_memory.py
```
Confirms extraction:
- Preferences: "prefers email over SMS"
- Semantic: "returned defective laptop with dead pixels"

4. **Create Memory-Enabled Agent** (`06_memory_enabled_agent.py`)
```bash
python3 06_memory_enabled_agent.py
```

**Test:** `07_test_memory_agent.py`
```bash
python3 07_test_memory_agent.py
```

**Result:** Agent recalls user_001's email preference and laptop return history!

**Cost Example:**
- May-June conversation: ~$0.01 total
- Not time-based, only event-based

---

### Phase 3: Add Gateway for External Services

**Goal:** Enable the agent to call external APIs (Lambda functions)

**What is AgentCore Gateway?**

Gateway is a centralized MCP hub that:
- Exposes Lambda functions as tools
- Handles OAuth authentication
- Provides semantic tool discovery
- Translates protocols automatically

**Setup Steps:**

1. **Create Cognito for OAuth** (`08_create_cognito.py`)
```bash
python3 08_create_cognito.py
```
Creates:
- User Pool: `us-west-2_hnM3way3f`
- Domain: `agentcore-gateway-51a78834`
- App Client with client credentials flow
- OAuth scopes: read, write, invoke

**Important:** Uses IDP-based discovery URL:
```
https://cognito-idp.us-west-2.amazonaws.com/{pool_id}/.well-known/openid-configuration
```

2. **Create Gateway IAM Role** (`09_create_gateway_role.py`)
```bash
python3 09_create_gateway_role.py
```
Grants:
- `lambda:InvokeFunction`
- CloudWatch Logs permissions

3. **Create Lambda Function** (`10_create_lambda.py`)
```bash
python3 10_create_lambda.py
```
Creates `OrderLookupFunction` with mock data:
- ORD-001: Dell XPS 15 Laptop (recent, eligible)
- ORD-002: iPhone 12 (old, not eligible)
- ORD-003: Samsung Galaxy Tab S7 (defective, eligible)

4. **Create Gateway** (`11_create_gateway.py`)
```bash
python3 11_create_gateway.py
```
Creates: `ReturnsRefundsGateway`
- OAuth authentication via Cognito
- MCP protocol
- Gateway URL for agent access

5. **Add Lambda to Gateway** (`12_add_lambda_to_gateway.py`)
```bash
python3 12_add_lambda_to_gateway.py
```
Registers Lambda as target named "OrderLookup"

6. **Verify Gateway** (`13_list_gateway_targets.py`)
```bash
python3 13_list_gateway_targets.py
```
Shows: 1 target (OrderLookup) with status READY

7. **Create Full Agent** (`14_full_agent.py`)
```bash
python3 14_full_agent.py
```
Integrates:
- All custom tools
- Memory (all three namespaces)
- Gateway (order lookup)
- Knowledge Base (policy documents)

**Test:** `15_test_full_agent.py`
```bash
python3 15_test_full_agent.py
```

**Result:** Agent successfully:
- Recalled email preference (Memory)
- Looked up order ORD-001 (Gateway → Lambda)
- Checked return eligibility (Custom tool)
- Provided personalized response

---

### Phase 4: Deploy to Production

**Goal:** Deploy the agent to AgentCore Runtime for production use

**What is AgentCore Runtime?**

Runtime is AWS's serverless platform for production agents:

**Key Differences from Local:**
| Local Agent | Runtime Agent |
|-------------|---------------|
| `from strands import Agent` | `from bedrock_agentcore_starter_toolkit import BedrockAgentCoreApp` |
| `agent = Agent(...)` | `@app.entrypoint` decorator |
| Run with `python agent.py` | Invoke via HTTPS API |
| Manual scaling | Auto-scales automatically |
| No built-in auth | OAuth required |

**Deployment Process:**
```
Configure → Launch → CodeBuild → Docker → ECR → Runtime → HTTPS Endpoint
```

**Setup Steps:**

1. **Create Runtime Execution Role** (`16_create_runtime_role.py`)
```bash
python3 16_create_runtime_role.py
```
Grants permissions for:
- Bedrock model invocation
- Memory access
- Gateway invocation
- Knowledge Base retrieval
- CloudWatch Logs
- X-Ray tracing
- ECR container access

2. **Create Runtime-Ready Agent** (`17_runtime_agent.py`)

Key changes from local agent:
```python
# Import Runtime app
from bedrock_agentcore.runtime import BedrockAgentCoreApp

# Initialize app
app = BedrockAgentCoreApp()

# Use entrypoint decorator
@app.entrypoint
def invoke(payload, context=None):
    # Agent logic here
    pass
```

3. **Create requirements.txt**
```
strands-agents>=0.1.0
strands-agents-tools>=0.1.0
bedrock-agentcore>=0.1.0
bedrock-agentcore-starter-toolkit>=0.1.0
boto3>=1.34.0
mcp>=1.0.0
requests>=2.31.0
```

4. **Deploy to Runtime** (`19_deploy_agent.py`)
```bash
python3 19_deploy_agent.py
```

**What happens:**
- Loads all config files (memory, gateway, cognito, kb, role)
- Configures runtime deployment settings
- Sets environment variables:
  - MEMORY_ID
  - KNOWLEDGE_BASE_ID
  - GATEWAY_URL
  - COGNITO_CLIENT_ID
  - COGNITO_CLIENT_SECRET
  - COGNITO_DISCOVERY_URL
- Creates CodeBuild project
- Builds ARM64 Docker container
- Pushes to ECR
- Deploys to Runtime
- Configures CloudWatch Logs + X-Ray

**Deployment time:** 5-10 minutes

**Result:**
```
Agent ARN: arn:aws:bedrock-agentcore:us-west-2:680079228867:runtime/returns_refunds_agent-rVRyTe40Z7
Status: READY
```

5. **Check Status** (`20_check_status.py`)
```bash
python3 20_check_status.py
```

Possible statuses:
- CREATING: Deployment in progress
- READY: Agent operational
- CREATE_FAILED: Deployment failed

6. **Invoke Production Agent** (`21_invoke_agent.py`)
```bash
python3 21_invoke_agent.py
```

**What happens:**
- Gets OAuth token from Cognito
- Invokes agent via HTTPS endpoint
- Agent processes request with all integrations
- Returns personalized response

**Test Result:**
```
Agent successfully:
✓ Authenticated with OAuth token
✓ Retrieved memory for user_001 (email preference)
✓ Called Lambda via Gateway (order ORD-001 details)
✓ Checked return eligibility (15 days remaining)
✓ Provided personalized response
```

---

## Testing & Validation

### Local Testing

**Test Basic Agent:**
```bash
python3 02_test_agent.py
```
Validates: Custom tools, Knowledge Base

**Test Memory:**
```bash
python3 05_verify_memory.py
```
Validates: Memory extraction and retrieval

**Test Memory-Enabled Agent:**
```bash
python3 07_test_memory_agent.py
```
Validates: Agent recalls preferences

**Test Full Agent:**
```bash
python3 15_test_full_agent.py
```
Validates: All integrations working together

### Production Testing

**Check Deployment Status:**
```bash
python3 20_check_status.py
```

**Invoke Production Agent:**
```bash
python3 21_invoke_agent.py
```

**View Logs:**
```bash
python3 22_view_logs.py
```

---

## Monitoring & Observability

### 1. GenAI Observability Dashboard

**URL:** https://console.aws.amazon.com/cloudwatch/home?region=us-west-2#gen-ai-observability/agent-core

**What you see:**
- Request traces with full conversation flow
- Tool invocations (Memory, Gateway, KB)
- Response times and latency
- Success/error rates
- Token usage and costs

### 2. CloudWatch Logs

**Log Group:** `/aws/bedrock-agentcore/runtimes/returns_refunds_agent-*/DEFAULT`

**View logs:**
```bash
# Programmatically
python3 22_view_logs.py

# AWS CLI - tail in real-time
aws logs tail /aws/bedrock-agentcore/runtimes/returns_refunds_agent-*/DEFAULT --follow

# View last hour
aws logs tail /aws/bedrock-agentcore/runtimes/returns_refunds_agent-*/DEFAULT --since 1h
```

**What gets logged:**
- Every invocation request/response
- Tool calls (Memory, Gateway, KB)
- Custom tool executions
- Errors with stack traces
- Performance metrics

### 3. X-Ray Traces

**URL:** https://console.aws.amazon.com/xray/home?region=us-west-2#/traces

**What you see:**
- End-to-end request flow
- Time spent in each component
- Bottlenecks and performance issues
- Error traces with details

### 4. Key Metrics to Monitor

- **Invocation Count**: Total requests
- **Success Rate**: % successful responses
- **Latency**: Response time (p50, p99)
- **Error Rate**: Failed invocations
- **Token Usage**: Cost tracking
- **Tool Usage**: Which tools called most

---

## Key Learnings

### 1. Memory Best Practices

**Event-Based Pricing:**
- NOT time-based (no monthly charges)
- Only pay per conversation event
- Example: May-June conversation = ~$0.01 total

**Cost Optimization:**
- Tune event retention periods
- Use selective memory strategies
- Smart retrieval with relevance scores
- Ephemeral vs persistent memory

**Memory Strategies:**
- Use tagged union format:
```python
{"semanticMemoryStrategy": {"name": "semantic", "namespaces": [...]}}
```
- NOT: `{"name": "semantic", "namespaces": [...]}`

**Message Format:**
- Use tuple format:
```python
[("Hello", "USER"), ("Hi", "ASSISTANT")]
```
- NOT: `[{"role": "USER", "content": [{"text": "Hello"}]}]`

**Processing Time:**
- Wait 20-30 seconds after storing for LTM extraction
- Short-term memory is immediate
- Long-term memory is async

### 2. Gateway Best Practices

**Authentication:**
- Use IDP-based discovery URL:
```
https://cognito-idp.{region}.amazonaws.com/{pool_id}/.well-known/openid-configuration
```
- NOT hosted UI domain format

**Tool Schema:**
- Provide clear descriptions
- Use proper JSON Schema for inputs
- Include examples in descriptions

**IAM Permissions:**
- Gateway role needs `lambda:InvokeFunction`
- Use least privilege principle
- Wait 10 seconds for IAM propagation

### 3. Runtime Best Practices

**Agent Code:**
- Use `@app.entrypoint` decorator
- Initialize model inside invoke function (not at module level)
- Handle errors gracefully
- Add comprehensive logging

**Environment Variables:**
- Set all required vars during deployment
- Don't hardcode credentials
- Use descriptive names

**Deployment:**
- Takes 5-10 minutes
- Monitor CodeBuild logs
- Check status before invoking
- Use auto_update_on_conflict=True for updates

**Observability:**
- Enable CloudWatch Logs
- Enable X-Ray tracing
- Use GenAI dashboard for insights
- Set up billing alarms

### 4. Development Workflow

**Recommended Order:**
1. Build basic agent locally
2. Add custom tools and test
3. Add Memory and test
4. Add Gateway and test
5. Test complete agent locally
6. Deploy to Runtime
7. Test production agent
8. Monitor and optimize

**Testing Strategy:**
- Test each integration separately
- Test combined integrations locally
- Test production deployment
- Monitor production usage

### 5. Common Mistakes to Avoid

**Memory:**
- ❌ Using wrong strategy format (missing wrapper)
- ❌ Using wrong message format (dict instead of tuple)
- ❌ Not waiting for async processing
- ✓ Use tagged union format
- ✓ Use tuple format for messages
- ✓ Wait 30 seconds after storing

**Gateway:**
- ❌ Using hosted UI domain for OIDC
- ❌ Forgetting IAM propagation wait
- ❌ Wrong OAuth scopes
- ✓ Use IDP domain format
- ✓ Wait 10 seconds after IAM changes
- ✓ Use correct scope format

**Runtime:**
- ❌ Using `Agent` instead of `BedrockAgentCoreApp`
- ❌ Initializing model at module level
- ❌ Not handling errors
- ✓ Use `@app.entrypoint` decorator
- ✓ Initialize model in invoke function
- ✓ Add comprehensive error handling

### 6. Cost Optimization

**Memory:**
- $0.25 per 1,000 events
- Optimize by reducing unnecessary events
- Use selective strategies

**Gateway:**
- $25/M search calls
- $5/M invoke calls
- Cache tool discovery results

**Runtime:**
- Pay only for invocation time
- Scales to zero when idle
- No infrastructure costs

**Bedrock:**
- Token-based pricing
- Optimize prompts for efficiency
- Use appropriate model sizes

---

## Next Steps

### Enhance the Agent

1. **Add More Tools:**
   - Shipping label generation
   - Refund status tracking
   - Customer notification system

2. **Expand Memory:**
   - Add more conversation history
   - Track return patterns
   - Personalize recommendations

3. **Enhance Gateway:**
   - Add inventory check Lambda
   - Add shipping cost calculator
   - Add fraud detection service

4. **Improve Knowledge Base:**
   - Upload more policy documents
   - Add FAQs
   - Add troubleshooting guides

### Production Readiness

1. **Security:**
   - Implement rate limiting
   - Add input validation
   - Enable AWS WAF
   - Rotate credentials regularly

2. **Monitoring:**
   - Set up CloudWatch alarms
   - Create custom dashboards
   - Configure SNS notifications
   - Track SLAs

3. **Cost Management:**
   - Set up billing alarms
   - Monitor token usage
   - Optimize tool calls
   - Review memory retention

4. **Scaling:**
   - Test under load
   - Optimize response times
   - Configure auto-scaling limits
   - Plan for peak traffic

### Learning Resources

- [AgentCore Documentation](https://docs.aws.amazon.com/bedrock-agentcore/)
- [Strands Agents Framework](https://github.com/awslabs/strands-agents)
- [MCP Protocol](https://modelcontextprotocol.io/)
- [AWS Bedrock](https://aws.amazon.com/bedrock/)

---

## Conclusion

You've built a complete production-ready AI agent with:
- ✓ Custom business logic
- ✓ Persistent memory
- ✓ External API integration
- ✓ Knowledge base access
- ✓ Production deployment
- ✓ Full observability

**Key Achievements:**
- Zero infrastructure management
- Auto-scaling production agent
- Personalized customer experiences
- Secure OAuth authentication
- Comprehensive monitoring

**What Makes This Production-Ready:**
- Error handling and logging
- OAuth security
- Auto-scaling
- Built-in observability
- Cost optimization

This architecture can be adapted for:
- Customer support agents
- Sales assistants
- Technical support bots
- Order management systems
- Any domain requiring memory, external data, and custom logic

Happy building! 🚀
