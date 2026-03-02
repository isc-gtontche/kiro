"""
Complete Returns Agent with Memory and Gateway Integration
Loads configurations from JSON files and sets up environment
"""

import os
import json
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

# Load configurations
with open('memory_config.json') as f:
    memory_config = json.load(f)
with open('gateway_config.json') as f:
    gateway_config = json.load(f)
with open('cognito_config.json') as f:
    cognito_config = json.load(f)
with open('kb_config.json') as f:
    kb_config = json.load(f)

# Constants
MODEL_ID = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"
REGION = "us-west-2"
SESSION_ID = "default-session"
ACTOR_ID = "default-actor"

# Model configuration
bedrock_model = BedrockModel(model_id=MODEL_ID, temperature=0.3)

# ============================================================================
# KNOWLEDGE BASE CONFIGURATION
# ============================================================================

kb_id = kb_config["knowledge_base_id"]
print(f"✓ Knowledge Base ID: {kb_id}")

# ============================================================================
# GATEWAY HELPER FUNCTIONS
# ============================================================================

def get_cognito_token_with_scope(client_id, client_secret, discovery_url, scope):
    """Get Cognito bearer token with a specific OAuth scope"""
    # Extract token endpoint from discovery URL
    discovery_response = requests.get(discovery_url)
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
        headers={'Content-Type': 'application/x-www-form-urlencoded'}
    )
    
    response.raise_for_status()
    return response.json()["access_token"]

def create_mcp_client():
    """Create MCP client for gateway access"""
    gateway_url = gateway_config["gateway_url"]
    cognito_client_id = cognito_config["client_id"]
    cognito_client_secret = cognito_config["client_secret"]
    cognito_discovery_url = cognito_config["discovery_url"]
    oauth_scopes = "agentcore-gateway-api/read agentcore-gateway-api/write agentcore-gateway-api/invoke"
    
    try:
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
        print(f"⚠️  Failed to create MCP client: {e}")
        return None

# ============================================================================
# MEMORY CONFIGURATION
# ============================================================================

def create_memory_session_manager(memory_id: str, session_id: str = SESSION_ID, actor_id: str = ACTOR_ID):
    """Create AgentCore Memory session manager"""
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
    
    return AgentCoreMemorySessionManager(
        agentcore_memory_config=agentcore_memory_config,
        region_name=REGION
    )

# System prompt
system_prompt = f"""You are a returns assistant with memory and order lookup capabilities. Remember customer preferences, look up order details, and use the retrieve tool to access Amazon return policy documents for accurate information.

When using the retrieve tool, always pass these parameters:
- knowledgeBaseId: {kb_id}
- region: {REGION}
- text: the search query
- Gateway tools for external operations
- Customer conversation history and preferences through memory"""

# Custom tool definitions
@tool
def check_return_eligibility(purchase_date: str, category: str) -> dict:
    """Check if an item is eligible for return based on purchase date and category"""
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

@tool
def calculate_refund_amount(price: float, condition: str, reason: str) -> dict:
    """Calculate refund amount based on item price, condition, and return reason"""
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

@tool
def format_policy_response(policy_text: str) -> str:
    """Format policy information in a customer-friendly way"""
    formatted = policy_text.replace('\n\n', '\n')
    formatted = '📋 Return Policy:\n\n' + formatted
    return formatted


def run_agent(user_input: str, session_id: str = SESSION_ID, actor_id: str = ACTOR_ID):
    """Run the agent with user input"""
    
    # Build tools list
    custom_tools = [retrieve, current_time, check_return_eligibility, calculate_refund_amount, format_policy_response]
    
    # Configure memory
    memory_id = memory_config["memory_id"]
    session_manager = create_memory_session_manager(memory_id, session_id, actor_id)
    print(f"✓ Memory configured: {memory_id}")
    
    # Try to add gateway tools
    mcp_client = create_mcp_client()
    
    if mcp_client:
        try:
            # Keep MCP client active during agent execution
            with mcp_client:
                # Get gateway tools from MCP client
                gateway_tools = list(mcp_client.list_tools_sync())
                print(f"✓ Loaded {len(gateway_tools)} gateway tools")
                
                # Create agent with gateway tools
                agent = Agent(
                    model=bedrock_model,
                    tools=custom_tools + gateway_tools,
                    system_prompt=system_prompt,
                    session_manager=session_manager
                )
                
                response = agent(user_input)
                return response.message["content"][0]["text"]
        except Exception as e:
            print(f"⚠️  Failed to use gateway tools: {e}")
            # Fall back to agent without gateway tools
    
    # Create agent without gateway tools (fallback or no gateway)
    agent = Agent(
        model=bedrock_model,
        tools=custom_tools,
        system_prompt=system_prompt,
        session_manager=session_manager
    )
    
    response = agent(user_input)
    return response.message["content"][0]["text"]

if __name__ == "__main__":
    # Example usage
    user_query = "Hello, how can you help me?"
    result = run_agent(user_query)
    print("\n" + "="*80)
    print("AGENT RESPONSE:")
    print("="*80)
    print(result)
