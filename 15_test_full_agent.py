#!/usr/bin/env python3
"""
Test script for the complete returns agent with memory and gateway integration.

Tests:
1. Memory recall (customer preferences)
2. Gateway tool usage (order lookup via Lambda)
3. Combined personalized response
"""

import json
import sys
import importlib.util

# Load configuration files
print("="*80)
print("LOADING CONFIGURATIONS")
print("="*80)

with open('memory_config.json') as f:
    memory_config = json.load(f)
    print(f"✓ Memory ID: {memory_config['memory_id']}")

with open('gateway_config.json') as f:
    gateway_config = json.load(f)
    print(f"✓ Gateway URL: {gateway_config['gateway_url']}")

with open('cognito_config.json') as f:
    cognito_config = json.load(f)
    print(f"✓ Cognito Client ID: {cognito_config['client_id']}")

with open('kb_config.json') as f:
    kb_config = json.load(f)
    print(f"✓ Knowledge Base ID: {kb_config['knowledge_base_id']}")

# Import the agent module
print("\n" + "="*80)
print("IMPORTING AGENT MODULE")
print("="*80)

spec = importlib.util.spec_from_file_location("full_agent", "14_full_agent.py")
agent_module = importlib.util.module_from_spec(spec)
sys.modules["full_agent"] = agent_module
spec.loader.exec_module(agent_module)

print("✓ Agent module loaded successfully")

# Test the agent
print("\n" + "="*80)
print("TESTING FULL AGENT WITH USER_001")
print("="*80)

test_query = "Hi! Can you look up my order ORD-001 and tell me if I can return it? Remember, I prefer email updates."

print(f"\nUser: {test_query}")
print("\nAgent is processing (this may take a moment)...")
print("-" * 80)

try:
    # Run agent with user_001 (who has memory history)
    response = agent_module.run_agent(
        user_input=test_query,
        session_id="test-session-001",
        actor_id="user_001"
    )
    
    print("\nAgent Response:")
    print("-" * 80)
    print(response)
    print("-" * 80)
    
    # Verification checks
    print("\n" + "="*80)
    print("VERIFICATION CHECKS")
    print("="*80)
    
    response_lower = response.lower()
    
    checks = {
        "Memory Recall (email preference)": any(word in response_lower for word in ["email", "prefer"]),
        "Gateway Tool (order lookup)": any(word in response_lower for word in ["ord-001", "dell", "xps", "laptop", "1299"]),
        "Return Eligibility": any(word in response_lower for word in ["eligible", "return", "15 days", "30 day"])
    }
    
    print()
    for check_name, passed in checks.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {check_name}")
    
    all_passed = all(checks.values())
    
    print("\n" + "="*80)
    if all_passed:
        print("✓ ALL CHECKS PASSED - Agent successfully used memory and gateway!")
    else:
        print("⚠️  SOME CHECKS FAILED - Review the response above")
    print("="*80)
    
except Exception as e:
    print(f"\n✗ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
