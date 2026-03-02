"""
AgentCore Runtime Agent: returns_agent_runtime
Production-ready returns assistant with full memory and gateway capabilities

This agent is ready to deploy to AgentCore Runtime with:
1. BedrockAgentCoreApp entrypoint
2. Memory integration for customer preferences
3. Gateway tools for order lookup
4. Knowledge Base access for policy documents
5. Custom tools for return processing
6. Comprehensive error handling
"""

import os
import json
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands import Agent, tool
from strands.models import BedrockModel
from strands_tools import retrieve
from strands_tools import current_time
from strands.tools.mcp import MCPClient
from mcp.client.streamable_http import streamablehttp_client
import requests
from bedrock_agentcore.memory.integrations.strands.config import AgentCoreMemoryConfig, RetrievalConfig
from bedrock_agentcore.memory.integrations.strands.session_manager import AgentCoreMemorySessionManager
from datetime import datetime

# Constants
MODEL_ID = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"
REGION = "us-west-2"
SESSION_ID = "default-session"
ACTOR_ID = "default-actor"

# Initialize app
app = BedrockAgentCoreApp()

# Environment variables - loaded at runtime
kb_id = os.environ.get("KNOWLEDGE_BASE_ID", "YOUR_KB_ID_HERE")
print(f"✓ Knowledge Base ID: {kb_id}")

# ============================================================================
# CUSTOM TOOLS
# ============================================================================

@tool
def check_return_eligibility(purchase_date: str, category: str) -> dict:
    """Check if an item is eligible for return based on purchase date and category"""
    try:
        purchase = datetime.strptime(purchase_date, '%Y-%m-%d')
        today = datetime.now()
        days_since_purchase = (today - purchase).days
        
        return_windows = {'electronics': 30, 'clothing': 60, 'books': 30, 'default': 30}
        window = return_windows.get(category.lower(), return_windows['default'])
        
        eligible = days_since_purchase <= window
        days_remaining = max(0, window - days_since_purchase)
        
        return {
            'eligible': eligible,
            'days_since_purchase': days_since_purchase,
            'return_window': window,
            'days_remaining': days_remaining,
            'category': category
        }
    except Exception as e:
        return {'error': f'Failed to check eligibility: {str(e)}'}

@tool
def calculate_refund_amount(price: float, condition: str, reason: str) -> dict:
    """Calculate refund amount based on item price, condition, and return reason"""
    try:
        condition_multipliers = {'new': 1.0, 'like-new': 0.95, 'used': 0.80}
        reason_adjustments = {'defect': 0.0, 'changed-mind': 0.15, 'wrong-item': 0.0}
        
        condition_mult = condition_multipliers.get(condition.lower(), 0.80)
        restocking_fee = reason_adjustments.get(reason.lower(), 0.15)
        
        refund = price * condition_mult * (1 - restocking_fee)
        
        return {
            'original_price': price,
            'condition': condition,
            'reason': reason,
            'refund_amount': round(refund, 2),
            'restocking_fee': round(price * restocking_fee, 2)
        }
    except Exception as e:
        return {'error': f'Failed to calculate refund: {str(e)}'}

@tool
def format_policy_response(policy_text: str) -> str:
    """Format policy information in a customer-friendly way"""
    try:
        formatted = policy_text.replace('\n\n', '\n')
        formatted = '📋 Return Policy:\n\n' + formatted
        return formatted
    except Exception as e:
        return f'Error formatting policy: {str(e)}'

# ============================================================================
# GATEWAY HELPER FUNCTIONS
# ============================================================================

def get_cognito_token_with_scope(client_id, client_secret, discovery_url, scope):
    """Get Cognito bearer token with a specific OAuth scope"""
    try:
        # Extract token endpoint from discovery URL
        discovery_response = requests.get(discovery_url, timeout=10)
        discovery_response.raise_for_status()
        token_endpoint = discovery_response.json()['token_endpoint']
        
        # Get token using client credentials flow
        response = requests.post(
            token_endpoint,
            data={
                'grant_type': 'client_credentials',
                'client_id': client_id,
                'client_secret': client_secret,
                'scope': scope
            },
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            timeout=10
        )
        
        response.raise_for_status()
        return response.json()["access_token"]
    except Exception as e:
        print(f"Error getting Cognito token: {e}")
        raise

def create_mcp_client():
    """Create MCP client for gateway access"""
    try:
        # Get environment variables
        gateway_url = os.environ.get("GATEWAY_URL")
        cognito_client_id = os.environ.get("COGNITO_CLIENT_ID")
        cognito_client_secret = os.environ.get("COGNITO_CLIENT_SECRET")
        cognito_discovery_url = os.environ.get("COGNITO_DISCOVERY_URL")
        oauth_scopes = os.environ.get("OAUTH_SCOPES", "agentcore-gateway-api/read agentcore-gateway-api/write agentcore-gateway-api/invoke")
        
        if not all([gateway_url, cognito_client_id, cognito_client_secret, cognito_discovery_url]):
            print("Warning: Gateway environment variables not set - gateway tools will not be available")
            return None
        
        token = get_cognito_token_with_scope(
            cognito_client_id,
            cognito_client_secret,
            cognito_discovery_url,
            oauth_scopes
        )
        
        print(f"✓ Gateway configured: {gateway_url}")
        return MCPClient(
            lambda: streamablehttp_client(
                gateway_url,
                headers={"Authorization": f"Bearer {token}"},
            )
        )
    except Exception as e:
        print(f"Warning: Failed to create MCP client: {e}")
        return None

# System prompt
system_prompt = f"""Production returns assistant with full memory and gateway capabilities. Use the retrieve tool to access Amazon return policy documents for accurate information.

When using the retrieve tool, always pass these parameters:
- knowledgeBaseId: {kb_id}
- region: {REGION}
- text: the search query
- Gateway tools for external operations
- Customer conversation history and preferences through memory"""

@app.entrypoint
def invoke(payload, context=None):
    """AgentCore Runtime entrypoint with comprehensive error handling"""
    try:
        print("=" * 80)
        print("AGENT INVOCATION STARTED")
        print("=" * 80)
        
        # Initialize model inside the function (not at module level)
        bedrock_model = BedrockModel(model_id=MODEL_ID, temperature=0.3)
        print(f"✓ Model initialized: {MODEL_ID}")
        
        # Get environment variables
        memory_id = os.environ.get("MEMORY_ID")
        if not memory_id:
            error_msg = "Error: MEMORY_ID environment variable is required"
            print(error_msg)
            return error_msg
        
        session_id = context.session_id if context else SESSION_ID
        actor_id = payload.get("actor_id", ACTOR_ID)
        
        print(f"✓ Memory ID: {memory_id}")
        print(f"✓ Session ID: {session_id}")
        print(f"✓ Actor ID: {actor_id}")
        
        # Configure memory with retrieval settings
        try:
            agentcore_memory_config = AgentCoreMemoryConfig(
                memory_id=memory_id,
                session_id=session_id,
                actor_id=actor_id,
                retrieval_config={
                f"app/{actor_id}/semantic": RetrievalConfig(top_k=3),
                f"app/{actor_id}/preferences": RetrievalConfig(top_k=3),
                f"app/{actor_id}/{session_id}/summary": RetrievalConfig(top_k=2),
                }
            )
            
            session_manager = AgentCoreMemorySessionManager(
                agentcore_memory_config=agentcore_memory_config,
                region_name=REGION
            )
            print("✓ Memory session manager configured")
        except Exception as e:
            print(f"Warning: Failed to configure memory: {e}")
            session_manager = None
        
        # Build custom tools list
        custom_tools = [
            retrieve, 
            current_time, 
            check_return_eligibility, 
            calculate_refund_amount, 
            format_policy_response
        ]
        print(f"✓ Loaded {len(custom_tools)} custom tools")
        
        # Try to create MCP client for gateway tools
        mcp_client = create_mcp_client()
        
        if mcp_client:
            try:
                # Keep MCP client active during agent execution
                with mcp_client:
                    # Get gateway tools from MCP client
                    gateway_tools = list(mcp_client.list_tools_sync())
                    print(f"✓ Loaded {len(gateway_tools)} gateway tools")
                    
                    # Create agent with all tools
                    agent = Agent(
                        model=bedrock_model,
                        tools=custom_tools + gateway_tools,
                        system_prompt=system_prompt,
                        session_manager=session_manager
                    )
                    
                    user_input = payload.get("prompt", "")
                    print(f"\nUser Input: {user_input}")
                    print("-" * 80)
                    
                    response = agent(user_input)
                    result = response.message["content"][0]["text"]
                    
                    print("-" * 80)
                    print("✓ Agent response generated successfully")
                    return result
            except Exception as e:
                print(f"Warning: Failed to use gateway tools: {e}")
                # Fall back to agent without gateway tools
        
        # Create agent without gateway tools (fallback)
        print("Creating agent without gateway tools (fallback mode)")
        agent = Agent(
            model=bedrock_model,
            tools=custom_tools,
            system_prompt=system_prompt,
            session_manager=session_manager
        )
        
        user_input = payload.get("prompt", "")
        print(f"\nUser Input: {user_input}")
        print("-" * 80)
        
        response = agent(user_input)
        result = response.message["content"][0]["text"]
        
        print("-" * 80)
        print("✓ Agent response generated successfully")
        return result
    
    except Exception as e:
        error_msg = f"Agent invocation failed: {str(e)}"
        print("=" * 80)
        print("ERROR OCCURRED")
        print("=" * 80)
        print(error_msg)
        import traceback
        traceback.print_exc()
        return error_msg

if __name__ == "__main__":
    app.run()
