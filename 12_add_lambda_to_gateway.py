#!/usr/bin/env python3
"""
Script to add Lambda target to AgentCore Gateway.

Prerequisites:
- gateway_config.json (from gateway creation)
- lambda_config.json (from Lambda creation)
"""

import json
import boto3

# Load gateway configuration
with open('gateway_config.json') as f:
    gateway_config = json.load(f)

# Load Lambda configuration
with open('lambda_config.json') as f:
    lambda_config = json.load(f)

# Initialize AgentCore control plane client
gateway_client = boto3.client("bedrock-agentcore-control", region_name='us-west-2')

# Extract Lambda ARN and tool schema from config
lambda_arn = lambda_config["function_arn"]
tool_schema = [lambda_config["tool_schema"]]

# Build Lambda target configuration with MCP protocol
lambda_target_config = {
    "mcp": {
        "lambda": {
            "lambdaArn": lambda_arn,
            "toolSchema": {
                "inlinePayload": tool_schema
            }
        }
    }
}

# Use gateway's IAM role for Lambda invocation
credential_config = [{"credentialProviderType": "GATEWAY_IAM_ROLE"}]

# Create target
print("Adding Lambda target to gateway...")
print(f"  Gateway ID: {gateway_config['gateway_id']}")
print(f"  Target Name: OrderLookup")
print(f"  Lambda ARN: {lambda_arn}")

create_response = gateway_client.create_gateway_target(
    gatewayIdentifier=gateway_config["gateway_id"],
    name="OrderLookup",
    description="Lambda function to look up order details by order ID",
    targetConfiguration=lambda_target_config,
    credentialProviderConfigurations=credential_config
)

target_id = create_response["targetId"]

print(f"\n✓ Lambda target added successfully!")
print(f"  Target ID: {target_id}")
print(f"  Target Name: OrderLookup")
print(f"  Tool: lookup_order")
