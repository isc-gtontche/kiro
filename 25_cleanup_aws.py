#!/usr/bin/env python3
"""
Comprehensive AWS Resource Cleanup Script

This script safely deletes all AWS resources created during the tutorial:
- AgentCore Runtime (deployed agent)
- AgentCore Gateway (and targets)
- AgentCore Memory (customer data)
- Lambda function and IAM roles
- Cognito User Pool (domain first, then pool)
- IAM roles and policies
- ECR repository

FEATURES:
- 5-second warning before deletion
- Proper deletion order (dependencies first)
- Graceful handling of missing resources
- Rerunnable (safe to run multiple times)
"""

import json
import os
import boto3
import time

def load_config(filename):
    """Load configuration file if it exists"""
    if os.path.exists(filename):
        try:
            with open(filename) as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️  Failed to load {filename}: {e}")
    return None

def safe_delete(operation_name, delete_func, *args, **kwargs):
    """Execute delete operation with error handling"""
    try:
        delete_func(*args, **kwargs)
        print(f"✓ {operation_name} deleted successfully")
        return True
    except Exception as e:
        error_msg = str(e).lower()
        if any(x in error_msg for x in ["not found", "notfound", "does not exist", "resourcenotfound"]):
            print(f"⚠️  {operation_name} already deleted or not found")
            return True
        else:
            print(f"✗ Error deleting {operation_name}: {e}")
            return False

print("=" * 80)
print("AWS RESOURCE CLEANUP SCRIPT")
print("=" * 80)
print("\nThis script will delete ALL AWS resources created during the tutorial:")
print("  - AgentCore Runtime agent")
print("  - AgentCore Gateway and targets")
print("  - AgentCore Memory")
print("  - Lambda function and IAM roles")
print("  - Cognito User Pool and domain")
print("  - IAM roles and policies")
print("  - ECR repository")
print("\n⚠️  WARNING: This action cannot be undone!")
print("=" * 80)

# 5-second warning
print("\nStarting deletion in 5 seconds... (Press Ctrl+C to cancel)")
for i in range(5, 0, -1):
    print(f"  {i}...")
    time.sleep(1)

print("\n" + "=" * 80)
print("STARTING CLEANUP")
print("=" * 80)

# Load all configurations
runtime_config = load_config('runtime_config.json')
gateway_config = load_config('gateway_config.json')
memory_config = load_config('memory_config.json')
lambda_config = load_config('lambda_config.json')
cognito_config = load_config('cognito_config.json')
gateway_role_config = load_config('gateway_role_config.json')
runtime_role_config = load_config('runtime_execution_role_config.json')

# Initialize AWS clients
agentcore_client = boto3.client('bedrock-agentcore-control', region_name='us-west-2')
lambda_client = boto3.client('lambda', region_name='us-west-2')
cognito_client = boto3.client('cognito-idp', region_name='us-west-2')
iam_client = boto3.client('iam', region_name='us-west-2')
ecr_client = boto3.client('ecr', region_name='us-west-2')

# ============================================================================
# STEP 1: Delete AgentCore Runtime
# ============================================================================
print("\n" + "=" * 80)
print("STEP 1: Deleting AgentCore Runtime")
print("=" * 80)

if runtime_config and runtime_config.get('agent_arn'):
    agent_arn = runtime_config['agent_arn']
    agent_id = agent_arn.split('/')[-1]
    print(f"Agent ID: {agent_id}")
    
    safe_delete(
        "Runtime agent",
        agentcore_client.delete_agent_runtime,
        agentRuntimeId=agent_id
    )
else:
    print("⚠️  No runtime config found - skipping")

# ============================================================================
# STEP 2: Delete Gateway Targets, then Gateway
# ============================================================================
print("\n" + "=" * 80)
print("STEP 2: Deleting AgentCore Gateway")
print("=" * 80)

if gateway_config and gateway_config.get('gateway_id'):
    gateway_id = gateway_config['gateway_id']
    print(f"Gateway ID: {gateway_id}")
    
    # Step 2a: Delete all targets first
    print("\nStep 2a: Deleting gateway targets...")
    try:
        response = agentcore_client.list_gateway_targets(gatewayIdentifier=gateway_id)
        targets = response.get('items', [])
        
        if targets:
            for target in targets:
                target_name = target.get('name', target['targetId'])
                safe_delete(
                    f"Target '{target_name}'",
                    agentcore_client.delete_gateway_target,
                    gatewayIdentifier=gateway_id,
                    targetId=target['targetId']
                )
            
            # Wait for targets to be fully deleted
            print("\nWaiting 5 seconds for targets to be fully deleted...")
            time.sleep(5)
        else:
            print("⚠️  No targets found")
    except Exception as e:
        if "not found" not in str(e).lower():
            print(f"⚠️  Could not list targets: {e}")
    
    # Step 2b: Delete gateway
    print("\nStep 2b: Deleting gateway...")
    safe_delete(
        "Gateway",
        agentcore_client.delete_gateway,
        gatewayIdentifier=gateway_id
    )
else:
    print("⚠️  No gateway config found - skipping")

# ============================================================================
# STEP 3: Delete AgentCore Memory
# ============================================================================
print("\n" + "=" * 80)
print("STEP 3: Deleting AgentCore Memory")
print("=" * 80)

if memory_config and memory_config.get('memory_id'):
    memory_id = memory_config['memory_id']
    print(f"Memory ID: {memory_id}")
    
    try:
        from bedrock_agentcore_starter_toolkit.operations.memory.manager import MemoryManager
        memory_manager = MemoryManager(region_name='us-west-2')
        safe_delete(
            "Memory resource",
            memory_manager.delete_memory,
            memory_id=memory_id
        )
    except Exception as e:
        print(f"⚠️  Could not delete memory: {e}")
else:
    print("⚠️  No memory config found - skipping")

# ============================================================================
# STEP 4: Delete Lambda Function and Role
# ============================================================================
print("\n" + "=" * 80)
print("STEP 4: Deleting Lambda Function")
print("=" * 80)

if lambda_config and lambda_config.get('function_name'):
    function_name = lambda_config['function_name']
    role_arn = lambda_config.get('role_arn')
    
    print(f"Function Name: {function_name}")
    
    # Delete Lambda function
    safe_delete(
        f"Lambda function '{function_name}'",
        lambda_client.delete_function,
        FunctionName=function_name
    )
    
    # Delete Lambda execution role
    if role_arn:
        role_name = role_arn.split('/')[-1]
        print(f"\nDeleting Lambda role: {role_name}")
        
        # Detach managed policy
        try:
            iam_client.detach_role_policy(
                RoleName=role_name,
                PolicyArn='arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole'
            )
            print(f"✓ Detached AWSLambdaBasicExecutionRole from {role_name}")
        except Exception as e:
            if "not found" not in str(e).lower():
                print(f"⚠️  Could not detach policy: {e}")
        
        # Delete role
        safe_delete(
            f"Lambda role '{role_name}'",
            iam_client.delete_role,
            RoleName=role_name
        )
else:
    print("⚠️  No Lambda config found - skipping")

# ============================================================================
# STEP 5: Delete Cognito (Domain first, then User Pool)
# ============================================================================
print("\n" + "=" * 80)
print("STEP 5: Deleting Cognito User Pool")
print("=" * 80)

if cognito_config and cognito_config.get('user_pool_id'):
    user_pool_id = cognito_config['user_pool_id']
    domain_prefix = cognito_config.get('domain_prefix')
    
    print(f"User Pool ID: {user_pool_id}")
    
    # Step 5a: Delete domain first
    if domain_prefix:
        print(f"\nStep 5a: Deleting domain '{domain_prefix}'...")
        safe_delete(
            f"Cognito domain '{domain_prefix}'",
            cognito_client.delete_user_pool_domain,
            Domain=domain_prefix,
            UserPoolId=user_pool_id
        )
        
        # Wait for domain deletion
        print("Waiting 5 seconds for domain deletion...")
        time.sleep(5)
    
    # Step 5b: Delete user pool
    print("\nStep 5b: Deleting user pool...")
    safe_delete(
        "Cognito User Pool",
        cognito_client.delete_user_pool,
        UserPoolId=user_pool_id
    )
else:
    print("⚠️  No Cognito config found - skipping")

# ============================================================================
# STEP 6: Delete Gateway IAM Role
# ============================================================================
print("\n" + "=" * 80)
print("STEP 6: Deleting Gateway IAM Role")
print("=" * 80)

if gateway_role_config and gateway_role_config.get('role_arn'):
    role_arn = gateway_role_config['role_arn']
    role_name = role_arn.split('/')[-1]
    policy_arn = gateway_role_config.get('policy_arn')
    
    print(f"Role Name: {role_name}")
    
    # Detach policy
    if policy_arn:
        try:
            iam_client.detach_role_policy(
                RoleName=role_name,
                PolicyArn=policy_arn
            )
            print(f"✓ Detached policy from {role_name}")
        except Exception as e:
            if "not found" not in str(e).lower():
                print(f"⚠️  Could not detach policy: {e}")
        
        # Delete policy
        policy_name = policy_arn.split('/')[-1]
        safe_delete(
            f"Policy '{policy_name}'",
            iam_client.delete_policy,
            PolicyArn=policy_arn
        )
    
    # Delete role
    safe_delete(
        f"Role '{role_name}'",
        iam_client.delete_role,
        RoleName=role_name
    )
else:
    print("⚠️  No gateway role config found - skipping")

# ============================================================================
# STEP 7: Delete Runtime Execution IAM Role
# ============================================================================
print("\n" + "=" * 80)
print("STEP 7: Deleting Runtime Execution IAM Role")
print("=" * 80)

if runtime_role_config and runtime_role_config.get('role_arn'):
    role_arn = runtime_role_config['role_arn']
    role_name = role_arn.split('/')[-1]
    policy_arn = runtime_role_config.get('policy_arn')
    
    print(f"Role Name: {role_name}")
    
    # Detach policy
    if policy_arn:
        try:
            iam_client.detach_role_policy(
                RoleName=role_name,
                PolicyArn=policy_arn
            )
            print(f"✓ Detached policy from {role_name}")
        except Exception as e:
            if "not found" not in str(e).lower():
                print(f"⚠️  Could not detach policy: {e}")
        
        # Delete policy
        policy_name = policy_arn.split('/')[-1]
        safe_delete(
            f"Policy '{policy_name}'",
            iam_client.delete_policy,
            PolicyArn=policy_arn
        )
    
    # Delete role
    safe_delete(
        f"Role '{role_name}'",
        iam_client.delete_role,
        RoleName=role_name
    )
else:
    print("⚠️  No runtime role config found - skipping")

# ============================================================================
# STEP 8: Delete ECR Repository
# ============================================================================
print("\n" + "=" * 80)
print("STEP 8: Deleting ECR Repository")
print("=" * 80)

if runtime_config and runtime_config.get('agent_name'):
    agent_name = runtime_config['agent_name']
    repo_name = f"bedrock-agentcore-{agent_name}"
    
    print(f"Repository Name: {repo_name}")
    
    safe_delete(
        f"ECR repository '{repo_name}'",
        ecr_client.delete_repository,
        repositoryName=repo_name,
        force=True  # Delete even if contains images
    )
else:
    print("⚠️  No runtime config found - skipping")

# ============================================================================
# CLEANUP COMPLETE
# ============================================================================
print("\n" + "=" * 80)
print("✓ CLEANUP COMPLETE")
print("=" * 80)
print("\nAll AWS resources have been deleted (or were already deleted).")
print("\nConfiguration files remain for reference:")
print("  - *.json files (contain resource IDs)")
print("  - Python scripts (reusable for future deployments)")
print("\nTo remove configuration files:")
print("  rm *_config.json")
print("\n" + "=" * 80)
