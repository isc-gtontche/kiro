#!/usr/bin/env python3
"""
Test script for memory-enabled returns agent.

This script tests if the agent correctly recalls:
- Customer communication preferences
- Past return history
- Provides personalized responses
"""

import json
import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 80)
print("MEMORY-ENABLED AGENT TEST")
print("=" * 80)
print()

# ============================================================================
# LOAD CONFIGURATION
# ============================================================================
print("Loading configuration...")

try:
    with open('memory_config.json', 'r') as f:
        memory_config = json.load(f)
        memory_id = memory_config.get('memory_id')
        print(f"✓ Memory ID: {memory_id}")
except FileNotFoundError:
    print("❌ Error: memory_config.json not found")
    sys.exit(1)

try:
    with open('kb_config.json', 'r') as f:
        kb_config = json.load(f)
        kb_id = kb_config.get('knowledge_base_id')
        print(f"✓ Knowledge Base ID: {kb_id}")
except FileNotFoundError:
    print("⚠️  Warning: kb_config.json not found")
    kb_id = None

print()

# ============================================================================
# IMPORT MEMORY-ENABLED AGENT
# ============================================================================
print("Importing memory-enabled agent...")

try:
    # Import the agent module
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "memory_agent", 
        "06_memory_enabled_agent.py"
    )
    memory_agent = importlib.util.module_from_spec(spec)
    sys.modules["memory_agent"] = memory_agent
    spec.loader.exec_module(memory_agent)
    
    run_agent = memory_agent.run_agent
    print("✓ Agent imported successfully")
except Exception as e:
    print(f"❌ Error importing agent: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# ============================================================================
# TEST CONFIGURATION
# ============================================================================
print("=" * 80)
print("TEST CONFIGURATION")
print("=" * 80)
print()

test_config = {
    "actor_id": "user_001",
    "session_id": "test_memory_session",
    "query": "Hi! I'm thinking about returning something. What do you remember about my preferences?"
}

print(f"Customer ID: {test_config['actor_id']}")
print(f"Session ID: {test_config['session_id']}")
print(f"Query: {test_config['query']}")
print()

# ============================================================================
# EXPECTED MEMORY
# ============================================================================
print("=" * 80)
print("EXPECTED MEMORY FOR user_001")
print("=" * 80)
print()
print("Communication Preferences:")
print("  ✓ Prefers email notifications over SMS")
print()
print("Return History:")
print("  ✓ Returned a defective laptop last month (dead pixels)")
print()
print("Conversation History:")
print("  ✓ Asked about return windows for electronics")
print("  ✓ Inquired about laptop, tablet, smartphone policies")
print()

# ============================================================================
# RUN TEST
# ============================================================================
print("=" * 80)
print("RUNNING TEST")
print("=" * 80)
print()

try:
    print("Sending query to agent...")
    print()
    
    response = run_agent(
        user_input=test_config['query'],
        session_id=test_config['session_id'],
        actor_id=test_config['actor_id']
    )
    
    print("=" * 80)
    print("AGENT RESPONSE")
    print("=" * 80)
    print()
    print(response)
    print()
    
except Exception as e:
    print(f"❌ Error running agent: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ============================================================================
# ANALYZE RESPONSE
# ============================================================================
print("=" * 80)
print("RESPONSE ANALYSIS")
print("=" * 80)
print()

# Check if agent mentioned key information
checks = {
    "email_preference": ["email", "notification", "SMS"],
    "laptop_return": ["laptop", "defective", "dead pixel", "returned"],
    "personalization": ["you", "your", "remember", "preference"]
}

results = {}
response_lower = response.lower()

for check_name, keywords in checks.items():
    found = any(keyword.lower() in response_lower for keyword in keywords)
    results[check_name] = found

print("Memory Recall Verification:")
print()

if results["email_preference"]:
    print("✓ Agent recalled email notification preference")
else:
    print("✗ Agent did NOT mention email preference")

if results["laptop_return"]:
    print("✓ Agent recalled previous laptop return")
else:
    print("✗ Agent did NOT mention laptop return")

if results["personalization"]:
    print("✓ Agent provided personalized response")
else:
    print("✗ Agent response was not personalized")

print()

# ============================================================================
# TEST SUMMARY
# ============================================================================
print("=" * 80)
print("TEST SUMMARY")
print("=" * 80)
print()

total_checks = len(results)
passed_checks = sum(results.values())

print(f"Checks Passed: {passed_checks}/{total_checks}")
print()

if passed_checks == total_checks:
    print("✓ TEST PASSED - Agent successfully recalled all memory!")
    exit_code = 0
elif passed_checks >= total_checks * 0.6:
    print("⚠️  TEST PARTIAL - Agent recalled some memory")
    exit_code = 0
else:
    print("✗ TEST FAILED - Agent did not recall memory correctly")
    exit_code = 1

print()
print("Details:")
for check_name, passed in results.items():
    status = "✓" if passed else "✗"
    print(f"  {status} {check_name.replace('_', ' ').title()}")

print()
print("=" * 80)

sys.exit(exit_code)
