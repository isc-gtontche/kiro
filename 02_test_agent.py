#!/usr/bin/env python3
"""
Test script for returns_refunds_agent
Tests various customer service scenarios
"""

import importlib.util
import sys
from pathlib import Path

# Import run_agent from 01_returns_refunds_agent.py using importlib
def load_agent_module():
    """Load the agent module dynamically using importlib"""
    agent_path = Path("01_returns_refunds_agent.py")
    
    if not agent_path.exists():
        print(f"Error: {agent_path} not found")
        sys.exit(1)
    
    spec = importlib.util.spec_from_file_location("returns_agent", agent_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["returns_agent"] = module
    spec.loader.exec_module(module)
    
    return module

# Load the agent
print("Loading returns_refunds_agent...")
agent_module = load_agent_module()
run_agent = agent_module.run_agent

# Test questions
test_questions = [
    {
        "id": 1,
        "question": "What time is it?",
        "description": "Test current_time tool"
    },
    {
        "id": 2,
        "question": "Can I return a laptop I purchased 25 days ago?",
        "description": "Test check_return_eligibility tool"
    },
    {
        "id": 3,
        "question": "Calculate my refund for a $500 item returned due to defect in like-new condition",
        "description": "Test calculate_refund_amount tool"
    },
    {
        "id": 4,
        "question": "Explain the return policy for electronics in a simple way",
        "description": "Test format_policy_response tool"
    },
    {
        "id": 5,
        "question": "Use the retrieve tool to search the knowledge base for 'Amazon return policy for electronics'",
        "description": "Test retrieve tool with knowledge base"
    }
]

# Run tests
print("\n" + "="*80)
print("TESTING RETURNS & REFUNDS AGENT")
print("="*80)

for test in test_questions:
    print(f"\n{'='*80}")
    print(f"TEST {test['id']}: {test['description']}")
    print(f"{'='*80}")
    print(f"\nQuestion: {test['question']}\n")
    print("-" * 80)
    
    try:
        result = run_agent(test['question'])
        print(f"\nAgent Response:\n{result}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "-" * 80)
    input("\nPress Enter to continue to next test...")

print("\n" + "="*80)
print("ALL TESTS COMPLETED")
print("="*80)
