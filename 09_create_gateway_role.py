#!/usr/bin/env python3
"""
Script to create IAM role for AgentCore Gateway.

This script creates:
- IAM role with trust policy for AgentCore Gateway
- IAM policy with Lambda invoke permissions
- Attaches policy to role
- Saves role ARN to configuration file
"""

import boto3
import json
import time
import uuid
from botocore.exceptions import ClientError

# Configuration
REGION = 'us-west-2'
ROLE_NAME = f'AgentCoreGatewayRole-{uuid.uuid4().hex[:8]}'
POLICY_NAME = f'AgentCoreGatewayPolicy-{uuid.uuid4().hex[:8]}'

print("=" * 80)
print("IAM ROLE SETUP FOR AGENTCORE GATEWAY")
print("=" * 80)
print()
print(f"Region: {REGION}")
print(f"Role Name: {ROLE_NAME}")
print(f"Policy Name: {POLICY_NAME}")
print()

# Create IAM client
iam_client = boto3.client('iam')
sts_client = boto3.client('sts')

# Get AWS account ID
try:
    account_id = sts_client.get_caller_identity()['Account']
    print(f"AWS Account ID: {account_id}")
    print()
except ClientError as e:
    print(f"❌ Error getting account ID: {e}")
    exit(1)

# ============================================================================
# STEP 1: CREATE IAM ROLE
# ============================================================================
print("=" * 80)
print("STEP 1: Creating IAM Role")
print("=" * 80)
print()

# Trust policy for AgentCore Gateway service
trust_policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "bedrock-agentcore.amazonaws.com"
            },
            "Action": "sts:AssumeRole",
            "Condition": {
                "StringEquals": {
                    "aws:SourceAccount": account_id
                },
                "ArnLike": {
                    "aws:SourceArn": f"arn:aws:bedrock-agentcore:{REGION}:{account_id}:gateway/*"
                }
            }
        }
    ]
}

try:
    role_response = iam_client.create_role(
        RoleName=ROLE_NAME,
        AssumeRolePolicyDocument=json.dumps(trust_policy),
        Description='IAM role for AgentCore Gateway to invoke Lambda functions'
    )
    
    role_arn = role_response['Role']['Arn']
    print(f"✓ IAM Role created successfully")
    print(f"  Role Name: {ROLE_NAME}")
    print(f"  Role ARN: {role_arn}")
    print()
    
except ClientError as e:
    if e.response['Error']['Code'] == 'EntityAlreadyExists':
        print(f"⚠️  Role {ROLE_NAME} already exists, retrieving...")
        role_response = iam_client.get_role(RoleName=ROLE_NAME)
        role_arn = role_response['Role']['Arn']
        print(f"  Role ARN: {role_arn}")
        print()
    else:
        print(f"❌ Error creating role: {e}")
        exit(1)

# ============================================================================
# STEP 2: CREATE IAM POLICY
# ============================================================================
print("=" * 80)
print("STEP 2: Creating IAM Policy")
print("=" * 80)
print()

# Policy document with Lambda invoke permissions
policy_document = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "InvokeLambdaFunctions",
            "Effect": "Allow",
            "Action": [
                "lambda:InvokeFunction"
            ],
            "Resource": [
                f"arn:aws:lambda:{REGION}:{account_id}:function:*"
            ]
        },
        {
            "Sid": "CloudWatchLogs",
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": [
                f"arn:aws:logs:{REGION}:{account_id}:log-group:/aws/bedrock-agentcore/gateway/*"
            ]
        }
    ]
}

try:
    policy_response = iam_client.create_policy(
        PolicyName=POLICY_NAME,
        PolicyDocument=json.dumps(policy_document),
        Description='Policy for AgentCore Gateway to invoke Lambda functions and write logs'
    )
    
    policy_arn = policy_response['Policy']['Arn']
    print(f"✓ IAM Policy created successfully")
    print(f"  Policy Name: {POLICY_NAME}")
    print(f"  Policy ARN: {policy_arn}")
    print()
    
except ClientError as e:
    if e.response['Error']['Code'] == 'EntityAlreadyExists':
        print(f"⚠️  Policy {POLICY_NAME} already exists")
        policy_arn = f"arn:aws:iam::{account_id}:policy/{POLICY_NAME}"
        print(f"  Policy ARN: {policy_arn}")
        print()
    else:
        print(f"❌ Error creating policy: {e}")
        # Clean up role
        iam_client.delete_role(RoleName=ROLE_NAME)
        exit(1)

# ============================================================================
# STEP 3: ATTACH POLICY TO ROLE
# ============================================================================
print("=" * 80)
print("STEP 3: Attaching Policy to Role")
print("=" * 80)
print()

try:
    iam_client.attach_role_policy(
        RoleName=ROLE_NAME,
        PolicyArn=policy_arn
    )
    
    print(f"✓ Policy attached to role successfully")
    print()
    
except ClientError as e:
    print(f"❌ Error attaching policy: {e}")
    # Clean up
    iam_client.delete_policy(PolicyArn=policy_arn)
    iam_client.delete_role(RoleName=ROLE_NAME)
    exit(1)

# Wait for IAM propagation
print("Waiting for IAM propagation (10 seconds)...")
time.sleep(10)
print("✓ IAM propagation complete")
print()

# ============================================================================
# STEP 4: SAVE CONFIGURATION
# ============================================================================
print("=" * 80)
print("STEP 4: Saving Configuration")
print("=" * 80)
print()

config = {
    "role_arn": role_arn,
    "role_name": ROLE_NAME,
    "policy_arn": policy_arn,
    "policy_name": POLICY_NAME,
    "region": REGION,
    "account_id": account_id
}

with open('gateway_role_config.json', 'w') as f:
    json.dump(config, f, indent=2)

print("✓ Configuration saved to gateway_role_config.json")
print()

# ============================================================================
# STEP 5: VERIFY ROLE
# ============================================================================
print("=" * 80)
print("STEP 5: Verifying Role")
print("=" * 80)
print()

try:
    role_info = iam_client.get_role(RoleName=ROLE_NAME)
    
    print("✓ Role verified successfully")
    print(f"  Role ARN: {role_info['Role']['Arn']}")
    print(f"  Created: {role_info['Role']['CreateDate']}")
    print()
    
    # List attached policies
    attached_policies = iam_client.list_attached_role_policies(RoleName=ROLE_NAME)
    print("Attached Policies:")
    for policy in attached_policies['AttachedPolicies']:
        print(f"  - {policy['PolicyName']} ({policy['PolicyArn']})")
    print()
    
except ClientError as e:
    print(f"⚠️  Error verifying role: {e}")
    print()

# ============================================================================
# SUMMARY
# ============================================================================
print("=" * 80)
print("SETUP COMPLETE")
print("=" * 80)
print()
print("IAM Resources Created:")
print(f"  ✓ Role: {ROLE_NAME}")
print(f"  ✓ Policy: {POLICY_NAME}")
print()
print("Role ARN:")
print(f"  {role_arn}")
print()
print("Permissions Granted:")
print("  ✓ Invoke Lambda functions in this account")
print("  ✓ Write CloudWatch logs")
print()
print("Configuration File:")
print("  ✓ gateway_role_config.json")
print()
print("Trust Policy:")
print("  ✓ AgentCore Gateway service can assume this role")
print("  ✓ Restricted to this AWS account")
print("  ✓ Restricted to gateway resources")
print()
print("Next Steps:")
print("  1. Use this role ARN when creating AgentCore Gateway")
print("  2. Create Lambda functions for gateway targets")
print("  3. Test gateway with Lambda invocations")
print()
print("=" * 80)
