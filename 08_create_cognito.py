#!/usr/bin/env python3
"""
Script to create Cognito User Pool for AgentCore Gateway authentication.

This script sets up:
- Cognito User Pool (secure login system)
- User Pool Domain (for OAuth endpoints)
- Resource Server (defines API scopes)
- App Client (for machine-to-machine authentication)
"""

import boto3
import json
import time
import uuid
from botocore.exceptions import ClientError

# Configuration
REGION = 'us-west-2'
POOL_NAME = f'agentcore-gateway-pool-{uuid.uuid4().hex[:8]}'
DOMAIN_PREFIX = f'agentcore-gateway-{uuid.uuid4().hex[:8]}'
RESOURCE_SERVER_IDENTIFIER = 'agentcore-gateway-api'
RESOURCE_SERVER_NAME = 'AgentCore Gateway API'

print("=" * 80)
print("COGNITO USER POOL SETUP FOR AGENTCORE GATEWAY")
print("=" * 80)
print()
print(f"Region: {REGION}")
print(f"User Pool Name: {POOL_NAME}")
print(f"Domain Prefix: {DOMAIN_PREFIX}")
print()

# Create Cognito client
client = boto3.client('cognito-idp', region_name=REGION)

# ============================================================================
# STEP 1: CREATE USER POOL
# ============================================================================
print("=" * 80)
print("STEP 1: Creating Cognito User Pool")
print("=" * 80)
print()

try:
    user_pool_response = client.create_user_pool(
        PoolName=POOL_NAME,
        Policies={
            'PasswordPolicy': {
                'MinimumLength': 8,
                'RequireUppercase': False,
                'RequireLowercase': False,
                'RequireNumbers': False,
                'RequireSymbols': False
            }
        },
        AutoVerifiedAttributes=[],
        Schema=[
            {
                'Name': 'email',
                'AttributeDataType': 'String',
                'Required': False,
                'Mutable': True
            }
        ]
    )
    
    user_pool_id = user_pool_response['UserPool']['Id']
    print(f"✓ User Pool created successfully")
    print(f"  User Pool ID: {user_pool_id}")
    print()
    
except ClientError as e:
    print(f"❌ Error creating User Pool: {e}")
    exit(1)

# ============================================================================
# STEP 2: CREATE USER POOL DOMAIN
# ============================================================================
print("=" * 80)
print("STEP 2: Creating User Pool Domain")
print("=" * 80)
print()

try:
    domain_response = client.create_user_pool_domain(
        Domain=DOMAIN_PREFIX,
        UserPoolId=user_pool_id
    )
    
    print(f"✓ User Pool Domain created successfully")
    print(f"  Domain Prefix: {DOMAIN_PREFIX}")
    print(f"  Hosted UI URL: https://{DOMAIN_PREFIX}.auth.{REGION}.amazoncognito.com")
    print()
    
except ClientError as e:
    print(f"❌ Error creating User Pool Domain: {e}")
    # Clean up user pool
    client.delete_user_pool(UserPoolId=user_pool_id)
    exit(1)

# Wait for domain to be ready
print("Waiting for domain to be ready...")
time.sleep(5)
print("✓ Domain ready")
print()

# ============================================================================
# STEP 3: CREATE RESOURCE SERVER (API Scopes)
# ============================================================================
print("=" * 80)
print("STEP 3: Creating Resource Server")
print("=" * 80)
print()

try:
    resource_server_response = client.create_resource_server(
        UserPoolId=user_pool_id,
        Identifier=RESOURCE_SERVER_IDENTIFIER,
        Name=RESOURCE_SERVER_NAME,
        Scopes=[
            {
                'ScopeName': 'read',
                'ScopeDescription': 'Read access to gateway tools'
            },
            {
                'ScopeName': 'write',
                'ScopeDescription': 'Write access to gateway tools'
            },
            {
                'ScopeName': 'invoke',
                'ScopeDescription': 'Invoke gateway tools'
            }
        ]
    )
    
    print(f"✓ Resource Server created successfully")
    print(f"  Identifier: {RESOURCE_SERVER_IDENTIFIER}")
    print(f"  Scopes: read, write, invoke")
    print()
    
except ClientError as e:
    print(f"❌ Error creating Resource Server: {e}")
    # Clean up
    client.delete_user_pool_domain(Domain=DOMAIN_PREFIX, UserPoolId=user_pool_id)
    client.delete_user_pool(UserPoolId=user_pool_id)
    exit(1)

# ============================================================================
# STEP 4: CREATE APP CLIENT (Machine-to-Machine)
# ============================================================================
print("=" * 80)
print("STEP 4: Creating App Client")
print("=" * 80)
print()

try:
    app_client_response = client.create_user_pool_client(
        UserPoolId=user_pool_id,
        ClientName=f'{POOL_NAME}-client',
        GenerateSecret=True,  # Required for client credentials flow
        AllowedOAuthFlows=['client_credentials'],
        AllowedOAuthFlowsUserPoolClient=True,
        AllowedOAuthScopes=[
            f'{RESOURCE_SERVER_IDENTIFIER}/read',
            f'{RESOURCE_SERVER_IDENTIFIER}/write',
            f'{RESOURCE_SERVER_IDENTIFIER}/invoke'
        ],
        ExplicitAuthFlows=[],  # Not needed for client credentials
        PreventUserExistenceErrors='ENABLED'
    )
    
    client_id = app_client_response['UserPoolClient']['ClientId']
    client_secret = app_client_response['UserPoolClient']['ClientSecret']
    
    print(f"✓ App Client created successfully")
    print(f"  Client ID: {client_id}")
    print(f"  Client Secret: {client_secret[:10]}...{client_secret[-10:]}")
    print()
    
except ClientError as e:
    print(f"❌ Error creating App Client: {e}")
    # Clean up
    client.delete_resource_server(
        UserPoolId=user_pool_id,
        Identifier=RESOURCE_SERVER_IDENTIFIER
    )
    client.delete_user_pool_domain(Domain=DOMAIN_PREFIX, UserPoolId=user_pool_id)
    client.delete_user_pool(UserPoolId=user_pool_id)
    exit(1)

# ============================================================================
# STEP 5: GENERATE CONFIGURATION
# ============================================================================
print("=" * 80)
print("STEP 5: Generating Configuration")
print("=" * 80)
print()

# Build OAuth endpoints
token_endpoint = f"https://{DOMAIN_PREFIX}.auth.{REGION}.amazoncognito.com/oauth2/token"

# CRITICAL: Use IDP-based discovery URL (NOT hosted UI domain)
discovery_url = f"https://cognito-idp.{REGION}.amazonaws.com/{user_pool_id}/.well-known/openid-configuration"

# Create configuration
config = {
    "user_pool_id": user_pool_id,
    "domain_prefix": DOMAIN_PREFIX,
    "client_id": client_id,
    "client_secret": client_secret,
    "token_endpoint": token_endpoint,
    "discovery_url": discovery_url,
    "region": REGION,
    "resource_server_identifier": RESOURCE_SERVER_IDENTIFIER,
    "scopes": [
        f"{RESOURCE_SERVER_IDENTIFIER}/read",
        f"{RESOURCE_SERVER_IDENTIFIER}/write",
        f"{RESOURCE_SERVER_IDENTIFIER}/invoke"
    ]
}

# Save to file
with open('cognito_config.json', 'w') as f:
    json.dump(config, f, indent=2)

print("✓ Configuration saved to cognito_config.json")
print()

# ============================================================================
# STEP 6: TEST TOKEN GENERATION
# ============================================================================
print("=" * 80)
print("STEP 6: Testing Token Generation")
print("=" * 80)
print()

try:
    import requests
    from requests.auth import HTTPBasicAuth
    
    print("Requesting OAuth token...")
    
    response = requests.post(
        token_endpoint,
        auth=HTTPBasicAuth(client_id, client_secret),
        data={
            'grant_type': 'client_credentials',
            'scope': ' '.join(config['scopes'])
        },
        headers={'Content-Type': 'application/x-www-form-urlencoded'}
    )
    
    if response.status_code == 200:
        token_data = response.json()
        access_token = token_data.get('access_token')
        expires_in = token_data.get('expires_in')
        
        print(f"✓ Token generated successfully!")
        print(f"  Token: {access_token[:20]}...{access_token[-20:]}")
        print(f"  Expires in: {expires_in} seconds ({expires_in // 60} minutes)")
        print()
    else:
        print(f"⚠️  Token generation failed: {response.status_code}")
        print(f"  Response: {response.text}")
        print()
        
except ImportError:
    print("⚠️  'requests' library not installed - skipping token test")
    print("  Install with: pip install requests")
    print()
except Exception as e:
    print(f"⚠️  Token test failed: {e}")
    print()

# ============================================================================
# SUMMARY
# ============================================================================
print("=" * 80)
print("SETUP COMPLETE")
print("=" * 80)
print()
print("Cognito Resources Created:")
print(f"  ✓ User Pool: {user_pool_id}")
print(f"  ✓ Domain: {DOMAIN_PREFIX}")
print(f"  ✓ Resource Server: {RESOURCE_SERVER_IDENTIFIER}")
print(f"  ✓ App Client: {client_id}")
print()
print("Configuration File:")
print(f"  ✓ cognito_config.json")
print()
print("OAuth Endpoints:")
print(f"  Token Endpoint: {token_endpoint}")
print(f"  Discovery URL: {discovery_url}")
print()
print("Scopes:")
for scope in config['scopes']:
    print(f"  - {scope}")
print()
print("Next Steps:")
print("  1. Use this configuration to create an AgentCore Gateway")
print("  2. Configure your agent to use the OAuth token")
print("  3. Test gateway authentication")
print()
print("=" * 80)
