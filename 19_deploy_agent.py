#!/usr/bin/env python3
"""
Complete deployment script for AgentCore Runtime.

This script:
1. Loads all configuration files
2. Configures runtime deployment settings
3. Sets environment variables
4. Deploys agent to AgentCore Runtime
5. Saves agent ARN to runtime_config.json
"""

import json
import os
from bedrock_agentcore_starter_toolkit import Runtime

print("=" * 80)
print("AGENTCORE RUNTIME DEPLOYMENT")
print("=" * 80)

# Step 1: Load all configuration files
print("\n1. Loading configuration files...")

with open('memory_config.json') as f:
    memory_config = json.load(f)
    print(f"   ✓ Memory ID: {memory_config['memory_id']}")

with open('gateway_config.json') as f:
    gateway_config = json.load(f)
    print(f"   ✓ Gateway URL: {gateway_config['gateway_url']}")

with open('cognito_config.json') as f:
    cognito_config = json.load(f)
    print(f"   ✓ Cognito Client ID: {cognito_config['client_id']}")

with open('runtime_execution_role_config.json') as f:
    role_config = json.load(f)
    print(f"   ✓ Execution Role ARN: {role_config['role_arn']}")

with open('kb_config.json') as f:
    kb_config = json.load(f)
    print(f"   ✓ Knowledge Base ID: {kb_config['knowledge_base_id']}")

# Step 2: Initialize Runtime
print("\n2. Initializing AgentCore Runtime...")
runtime = Runtime()
print("   ✓ Runtime initialized")

# Step 3: Configure runtime deployment
print("\n3. Configuring runtime deployment settings...")

# Build authorizer configuration for Cognito JWT
auth_config = {
    "customJWTAuthorizer": {
        "allowedClients": [cognito_config["client_id"]],
        "discoveryUrl": cognito_config["discovery_url"]
    }
}

runtime.configure(
    entrypoint="17_runtime_agent.py",
    agent_name="returns_refunds_agent",
    execution_role=role_config["role_arn"],
    auto_create_ecr=True,
    memory_mode="NO_MEMORY",
    requirements_file="requirements.txt",
    region="us-west-2",
    authorizer_configuration=auth_config
)
print("   ✓ Runtime configured")
print("   ✓ Configuration saved to .bedrock_agentcore.yaml")

# Step 4: Build environment variables
print("\n4. Setting environment variables...")

env_vars = {
    "MEMORY_ID": memory_config["memory_id"],
    "KNOWLEDGE_BASE_ID": kb_config["knowledge_base_id"],
    "GATEWAY_URL": gateway_config["gateway_url"],
    "COGNITO_CLIENT_ID": cognito_config["client_id"],
    "COGNITO_CLIENT_SECRET": cognito_config["client_secret"],
    "COGNITO_DISCOVERY_URL": cognito_config["discovery_url"],
    "OAUTH_SCOPES": "agentcore-gateway-api/read agentcore-gateway-api/write agentcore-gateway-api/invoke"
}

print("\n   Environment variables:")
for key, value in env_vars.items():
    if "SECRET" in key:
        print(f"     {key}: ***")
    else:
        print(f"     {key}: {value}")

# Step 5: Launch agent to runtime
print("\n" + "=" * 80)
print("LAUNCHING AGENT TO AGENTCORE RUNTIME")
print("=" * 80)
print("\nThis process will:")
print("  1. Create CodeBuild project")
print("  2. Build Docker container from your agent code")
print("  3. Push container to Amazon ECR")
print("  4. Deploy to AgentCore Runtime")
print("\n⏱️  Expected time: 5-10 minutes")
print("\n☕ Grab a coffee while the deployment runs...")
print("=" * 80)

try:
    launch_result = runtime.launch(
        env_vars=env_vars,
        auto_update_on_conflict=True
    )
    
    agent_arn = launch_result.agent_arn
    
    # Step 6: Save agent ARN to config
    print("\n6. Saving deployment configuration...")
    
    runtime_output_config = {
        "agent_arn": agent_arn,
        "agent_name": "returns_refunds_agent",
        "region": "us-west-2",
        "memory_id": memory_config["memory_id"],
        "gateway_url": gateway_config["gateway_url"],
        "knowledge_base_id": kb_config["knowledge_base_id"]
    }
    
    with open('runtime_config.json', 'w') as f:
        json.dump(runtime_output_config, f, indent=2)
    
    print("   ✓ Configuration saved to runtime_config.json")
    
    print("\n" + "=" * 80)
    print("✓ DEPLOYMENT INITIATED SUCCESSFULLY!")
    print("=" * 80)
    print(f"\nAgent ARN: {agent_arn}")
    print(f"Agent Name: returns_refunds_agent")
    print(f"Region: us-west-2")
    
    print("\n" + "=" * 80)
    print("NEXT STEPS")
    print("=" * 80)
    print("\n1. Monitor deployment status:")
    print("   The build process is running in CodeBuild")
    print("   Check status with: python 20_check_status.py")
    print("\n2. Wait for status to show 'READY' (5-10 minutes)")
    print("\n3. Once READY, test your agent:")
    print("   Run: python 21_test_runtime_agent.py")
    print("\n" + "=" * 80)

except Exception as e:
    print("\n" + "=" * 80)
    print("✗ DEPLOYMENT FAILED")
    print("=" * 80)
    print(f"\nError: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
