#!/usr/bin/env python3
"""
Script to create Lambda function for order lookup.

This script creates:
- Lambda execution role (if needed)
- Lambda function with order lookup logic
- Tool schema for AgentCore Gateway
- Configuration file with Lambda ARN and tool schema
"""

import boto3
import json
import time
import zipfile
import io
from botocore.exceptions import ClientError

# Configuration
REGION = 'us-west-2'
FUNCTION_NAME = 'OrderLookupFunction'
ROLE_NAME = 'OrderLookupLambdaRole'

print("=" * 80)
print("LAMBDA FUNCTION SETUP FOR ORDER LOOKUP")
print("=" * 80)
print()
print(f"Region: {REGION}")
print(f"Function Name: {FUNCTION_NAME}")
print()

# Create clients
lambda_client = boto3.client('lambda', region_name=REGION)
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
# STEP 1: CREATE LAMBDA EXECUTION ROLE
# ============================================================================
print("=" * 80)
print("STEP 1: Creating Lambda Execution Role")
print("=" * 80)
print()

# Trust policy for Lambda service
lambda_trust_policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "lambda.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}

try:
    role_response = iam_client.create_role(
        RoleName=ROLE_NAME,
        AssumeRolePolicyDocument=json.dumps(lambda_trust_policy),
        Description='Execution role for OrderLookupFunction Lambda'
    )
    
    role_arn = role_response['Role']['Arn']
    print(f"✓ Lambda execution role created")
    print(f"  Role ARN: {role_arn}")
    print()
    
    # Attach basic Lambda execution policy
    iam_client.attach_role_policy(
        RoleName=ROLE_NAME,
        PolicyArn='arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole'
    )
    print("✓ Attached AWSLambdaBasicExecutionRole policy")
    print()
    
    # Wait for IAM propagation
    print("Waiting for IAM propagation (10 seconds)...")
    time.sleep(10)
    print("✓ IAM propagation complete")
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
# STEP 2: CREATE LAMBDA FUNCTION CODE
# ============================================================================
print("=" * 80)
print("STEP 2: Creating Lambda Function Code")
print("=" * 80)
print()

# Lambda function code with mock order data
lambda_code = '''
import json
from datetime import datetime, timedelta

# Mock order database
ORDERS = {
    "ORD-001": {
        "order_id": "ORD-001",
        "product_name": "Dell XPS 15 Laptop",
        "purchase_date": (datetime.now() - timedelta(days=15)).strftime("%Y-%m-%d"),
        "amount": 1299.99,
        "status": "delivered",
        "category": "electronics"
    },
    "ORD-002": {
        "order_id": "ORD-002",
        "product_name": "iPhone 12",
        "purchase_date": (datetime.now() - timedelta(days=45)).strftime("%Y-%m-%d"),
        "amount": 799.99,
        "status": "delivered",
        "category": "electronics"
    },
    "ORD-003": {
        "order_id": "ORD-003",
        "product_name": "Samsung Galaxy Tab S7",
        "purchase_date": (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d"),
        "amount": 649.99,
        "status": "delivered",
        "category": "electronics",
        "defective": True
    }
}

def check_return_eligibility(purchase_date_str, category="electronics"):
    """Check if order is eligible for return based on purchase date"""
    try:
        purchase_date = datetime.strptime(purchase_date_str, "%Y-%m-%d")
        days_since_purchase = (datetime.now() - purchase_date).days
        
        # 30-day return window for electronics
        return_window = 30
        
        if days_since_purchase <= return_window:
            return {
                "eligible": True,
                "days_remaining": return_window - days_since_purchase,
                "reason": f"Within {return_window}-day return window"
            }
        else:
            return {
                "eligible": False,
                "days_remaining": 0,
                "reason": f"Exceeds {return_window}-day return window"
            }
    except Exception as e:
        return {
            "eligible": False,
            "days_remaining": 0,
            "reason": f"Error checking eligibility: {str(e)}"
        }

def lambda_handler(event, context):
    """
    Lambda handler for order lookup
    
    Expected input:
    {
        "order_id": "ORD-001"
    }
    
    Returns:
    {
        "order_id": "ORD-001",
        "product_name": "Dell XPS 15 Laptop",
        "purchase_date": "2026-02-15",
        "amount": 1299.99,
        "status": "delivered",
        "category": "electronics",
        "return_eligibility": {
            "eligible": true,
            "days_remaining": 15,
            "reason": "Within 30-day return window"
        }
    }
    """
    try:
        # Parse input
        if isinstance(event, str):
            event = json.loads(event)
        
        order_id = event.get('order_id', '').upper()
        
        if not order_id:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Missing required parameter: order_id'
                })
            }
        
        # Look up order
        order = ORDERS.get(order_id)
        
        if not order:
            return {
                'statusCode': 404,
                'body': json.dumps({
                    'error': f'Order {order_id} not found',
                    'available_orders': list(ORDERS.keys())
                })
            }
        
        # Check return eligibility
        eligibility = check_return_eligibility(
            order['purchase_date'],
            order.get('category', 'electronics')
        )
        
        # Build response
        response_data = {
            **order,
            'return_eligibility': eligibility
        }
        
        # Add defective flag if present
        if order.get('defective'):
            response_data['defective'] = True
            response_data['return_eligibility']['eligible'] = True
            response_data['return_eligibility']['reason'] = 'Defective product - eligible for full refund'
        
        return {
            'statusCode': 200,
            'body': json.dumps(response_data)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': f'Internal error: {str(e)}'
            })
        }
'''

# Create deployment package
print("Creating deployment package...")
zip_buffer = io.BytesIO()
with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
    zip_file.writestr('lambda_function.py', lambda_code)

zip_buffer.seek(0)
deployment_package = zip_buffer.read()

print(f"✓ Deployment package created ({len(deployment_package)} bytes)")
print()

# ============================================================================
# STEP 3: CREATE LAMBDA FUNCTION
# ============================================================================
print("=" * 80)
print("STEP 3: Creating Lambda Function")
print("=" * 80)
print()

try:
    function_response = lambda_client.create_function(
        FunctionName=FUNCTION_NAME,
        Runtime='python3.12',
        Role=role_arn,
        Handler='lambda_function.lambda_handler',
        Code={'ZipFile': deployment_package},
        Description='Order lookup function for AgentCore Gateway',
        Timeout=30,
        MemorySize=128,
        Environment={
            'Variables': {
                'REGION': REGION
            }
        }
    )
    
    function_arn = function_response['FunctionArn']
    print(f"✓ Lambda function created successfully")
    print(f"  Function Name: {FUNCTION_NAME}")
    print(f"  Function ARN: {function_arn}")
    print(f"  Runtime: python3.12")
    print(f"  Handler: lambda_function.lambda_handler")
    print()
    
except ClientError as e:
    if e.response['Error']['Code'] == 'ResourceConflictException':
        print(f"⚠️  Function {FUNCTION_NAME} already exists, updating code...")
        
        # Update existing function
        update_response = lambda_client.update_function_code(
            FunctionName=FUNCTION_NAME,
            ZipFile=deployment_package
        )
        
        function_arn = update_response['FunctionArn']
        print(f"✓ Lambda function code updated")
        print(f"  Function ARN: {function_arn}")
        print()
    else:
        print(f"❌ Error creating function: {e}")
        exit(1)

# Wait for function to be ready
print("Waiting for function to be active...")
time.sleep(5)
print("✓ Function is active")
print()

# ============================================================================
# STEP 4: TEST LAMBDA FUNCTION
# ============================================================================
print("=" * 80)
print("STEP 4: Testing Lambda Function")
print("=" * 80)
print()

test_payload = {"order_id": "ORD-001"}
print(f"Test payload: {json.dumps(test_payload)}")
print()

try:
    test_response = lambda_client.invoke(
        FunctionName=FUNCTION_NAME,
        InvocationType='RequestResponse',
        Payload=json.dumps(test_payload)
    )
    
    response_payload = json.loads(test_response['Payload'].read())
    print("✓ Lambda function test successful")
    print()
    print("Response:")
    print(json.dumps(response_payload, indent=2))
    print()
    
except ClientError as e:
    print(f"⚠️  Lambda test failed: {e}")
    print()

# ============================================================================
# STEP 5: CREATE TOOL SCHEMA
# ============================================================================
print("=" * 80)
print("STEP 5: Creating Tool Schema")
print("=" * 80)
print()

tool_schema = {
    "name": "lookup_order",
    "description": "Look up order details by order ID. Returns order information including product name, purchase date, amount, and return eligibility status.",
    "inputSchema": {
        "type": "object",
        "properties": {
            "order_id": {
                "type": "string",
                "description": "The order ID to look up (e.g., ORD-001, ORD-002, ORD-003)"
            }
        },
        "required": ["order_id"]
    }
}

print("Tool Schema:")
print(json.dumps(tool_schema, indent=2))
print()

# ============================================================================
# STEP 6: SAVE CONFIGURATION
# ============================================================================
print("=" * 80)
print("STEP 6: Saving Configuration")
print("=" * 80)
print()

config = {
    "function_name": FUNCTION_NAME,
    "function_arn": function_arn,
    "role_arn": role_arn,
    "region": REGION,
    "tool_schema": tool_schema,
    "sample_orders": [
        "ORD-001: Dell XPS 15 Laptop (recent, eligible)",
        "ORD-002: iPhone 12 (old, not eligible)",
        "ORD-003: Samsung Galaxy Tab S7 (recent, defective, eligible)"
    ]
}

with open('lambda_config.json', 'w') as f:
    json.dump(config, f, indent=2)

print("✓ Configuration saved to lambda_config.json")
print()

# ============================================================================
# SUMMARY
# ============================================================================
print("=" * 80)
print("SETUP COMPLETE")
print("=" * 80)
print()
print("Lambda Function Created:")
print(f"  ✓ Name: {FUNCTION_NAME}")
print(f"  ✓ ARN: {function_arn}")
print(f"  ✓ Runtime: Python 3.12")
print()
print("Mock Orders Available:")
print("  ✓ ORD-001: Dell XPS 15 Laptop (purchased 15 days ago, eligible)")
print("  ✓ ORD-002: iPhone 12 (purchased 45 days ago, not eligible)")
print("  ✓ ORD-003: Samsung Galaxy Tab S7 (purchased 10 days ago, defective, eligible)")
print()
print("Tool Schema:")
print(f"  ✓ Tool Name: lookup_order")
print(f"  ✓ Input: order_id (string)")
print(f"  ✓ Output: order details + return eligibility")
print()
print("Configuration File:")
print("  ✓ lambda_config.json")
print()
print("Next Steps:")
print("  1. Create AgentCore Gateway")
print("  2. Add this Lambda as a gateway target")
print("  3. Test order lookup through gateway")
print()
print("=" * 80)
