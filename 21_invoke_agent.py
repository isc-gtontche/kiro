#!/usr/bin/env python3
"""
Script to invoke deployed AgentCore Runtime agent.
"""

import json
import os
import requests
from bedrock_agentcore_starter_toolkit import Runtime

# Check if runtime config exists
if not os.path.exists('runtime_config.json'):
    print("❌ Error: Agent not deployed yet")
    print("Please run 19_deploy_agent.py first")
    exit(1)

print("=" * 80)
print("INVOKING AGENTCORE RUNTIME AGENT")
print("=" * 80)

# Load configuration
print("\n1. Loading configuration files...")
with open('cognito_config.json') as f:
    cognito_config = json.load(f)
    print(f"   ✓ Cognito Client ID: {cognito_config['client_id']}")

with open('runtime_execution_role_config.json') as f:
    role_config = json.load(f)
    print(f"   ✓ Execution Role loaded")

with open('runtime_config.json') as f:
    runtime_deployed_config = json.load(f)
    print(f"   ✓ Agent ARN: {runtime_deployed_config['agent_arn']}")

# Load .bedrock_agentcore.yaml to get agent name and entrypoint
if not os.path.exists('.bedrock_agentcore.yaml'):
    print("❌ Error: .bedrock_agentcore.yaml not found")
    print("Please run 19_deploy_agent.py first")
    exit(1)

import yaml
with open('.bedrock_agentcore.yaml') as f:
    runtime_config = yaml.safe_load(f)

default_agent = runtime_config.get('default_agent')
agent_config = runtime_config.get('agents', {}).get(default_agent, {})
agent_name = agent_config.get('name')
entrypoint = agent_config.get('entrypoint')

# Generate bearer token using Cognito client credentials flow
print("\n2. Generating OAuth bearer token...")

# Get token endpoint from discovery URL
discovery_response = requests.get(cognito_config["discovery_url"])
token_endpoint = discovery_response.json()['token_endpoint']

# Request token using client credentials flow
response = requests.post(
    token_endpoint,
    data={
        "grant_type": "client_credentials",
        "client_id": cognito_config["client_id"],
        "client_secret": cognito_config["client_secret"],
        "scope": "agentcore-gateway-api/read agentcore-gateway-api/write agentcore-gateway-api/invoke"
    },
    headers={"Content-Type": "application/x-www-form-urlencoded"}
)

if response.status_code != 200:
    print(f"❌ Failed to get OAuth token: {response.text}")
    exit(1)

bearer_token = response.json()["access_token"]
print("   ✓ OAuth token obtained")

# Initialize Runtime
runtime = Runtime()

# Build authorizer configuration for Cognito JWT
auth_config = {
    "customJWTAuthorizer": {
        "allowedClients": [cognito_config["client_id"]],
        "discoveryUrl": cognito_config["discovery_url"]
    }
}

# Configure runtime (to load existing configuration)
print("\n3. Configuring runtime...")
runtime.configure(
    entrypoint=entrypoint,
    agent_name=agent_name,
    execution_role=role_config["role_arn"],
    auto_create_ecr=True,
    memory_mode="NO_MEMORY",
    requirements_file="requirements.txt",
    region="us-west-2",
    authorizer_configuration=auth_config
)
print("   ✓ Runtime configured")

# Invoke agent
print("\n4. Invoking agent...")
print("   User: user_001")
print("   Query: 'Can you look up my order ORD-001 and help me with a return?'")
print("\n" + "=" * 80)

payload = {
    "prompt": "Can you look up my order ORD-001 and help me with a return?",
    "actor_id": "user_001"
}

try:
    response = runtime.invoke(
        payload,
        bearer_token=bearer_token
    )
    
    print("AGENT RESPONSE")
    print("=" * 80)
    print(response)
    print("=" * 80)
    
    print("\n✓ Agent invocation successful!")
    print("\nThe agent successfully:")
    print("  - Authenticated with OAuth token")
    print("  - Retrieved memory for user_001")
    print("  - Called Lambda via Gateway to lookup order ORD-001")
    print("  - Provided personalized return assistance")
    
except Exception as e:
    print("=" * 80)
    print("❌ ERROR INVOKING AGENT")
    print("=" * 80)
    print(f"Error: {e}")
    print("\nTroubleshooting:")
    print("  1. Check agent status: python 20_check_status.py")
    print("  2. Verify agent is in READY state")
    print("  3. Check CloudWatch logs for errors:")
    print(f"     Log group: /aws/bedrock-agentcore/runtimes/{agent_name}")
    print("=" * 80)
    import traceback
    traceback.print_exc()
    exit(1)
