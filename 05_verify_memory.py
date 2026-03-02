#!/usr/bin/env python3
"""
Script to verify memory extraction and retrieval.
"""

import json
from bedrock_agentcore.memory import MemoryClient

# Load memory_id from config
with open('memory_config.json') as f:
    config = json.load(f)
    memory_id = config['memory_id']

print("=" * 80)
print("MEMORY VERIFICATION")
print("=" * 80)
print(f"Memory ID: {memory_id}")
print(f"Customer ID: user_001")
print()

# Create memory client
memory_client = MemoryClient(region_name='us-west-2')

# ============================================================================
# 1. Retrieve recent conversation turns (Short-Term Memory)
# ============================================================================
print("1. SHORT-TERM MEMORY (Recent Conversation Turns)")
print("-" * 80)

try:
    turns = memory_client.get_last_k_turns(
        memory_id=memory_id,
        actor_id="user_001",
        session_id="session_001",
        k=3
    )
    
    print(f"Retrieved {len(turns)} recent turns from session_001:")
    for i, turn in enumerate(turns, 1):
        print(f"\nTurn {i}:")
        for msg in turn:
            role = msg.get('role', 'UNKNOWN')
            content = msg.get('content', {})
            if isinstance(content, dict):
                text = content.get('text', str(content))
            else:
                text = str(content)
            print(f"  [{role}]: {text[:100]}...")
except Exception as e:
    print(f"Error retrieving turns: {e}")

print()

# ============================================================================
# 2. Search for preferences (Long-Term Memory)
# ============================================================================
print("2. LONG-TERM MEMORY - USER PREFERENCES")
print("-" * 80)

try:
    preferences = memory_client.retrieve_memories(
        memory_id=memory_id,
        actor_id="user_001",
        namespace="app/user_001/preferences",
        query="notification preferences email",
        top_k=5
    )
    
    print(f"Found {len(preferences)} preference memories:")
    for i, pref in enumerate(preferences, 1):
        print(f"\n{i}. {pref.get('content', 'N/A')}")
        if 'relevanceScore' in pref:
            print(f"   Relevance: {pref.get('relevanceScore', 0):.2f}")
except Exception as e:
    print(f"Error retrieving preferences: {e}")

print()

# ============================================================================
# 3. Search for semantic facts (Long-Term Memory)
# ============================================================================
print("3. LONG-TERM MEMORY - SEMANTIC FACTS")
print("-" * 80)

try:
    facts = memory_client.retrieve_memories(
        memory_id=memory_id,
        actor_id="user_001",
        namespace="app/user_001/semantic",
        query="laptop return defective electronics",
        top_k=5
    )
    
    print(f"Found {len(facts)} semantic memories:")
    for i, fact in enumerate(facts, 1):
        print(f"\n{i}. {fact.get('content', 'N/A')}")
        if 'relevanceScore' in fact:
            print(f"   Relevance: {fact.get('relevanceScore', 0):.2f}")
except Exception as e:
    print(f"Error retrieving facts: {e}")

print()

# ============================================================================
# 4. Search for summaries (Long-Term Memory)
# ============================================================================
print("4. LONG-TERM MEMORY - CONVERSATION SUMMARIES")
print("-" * 80)

try:
    summaries = memory_client.retrieve_memories(
        memory_id=memory_id,
        actor_id="user_001",
        namespace="app/user_001/session_001/summary",
        query="conversation summary",
        top_k=3
    )
    
    print(f"Found {len(summaries)} summary memories:")
    for i, summary in enumerate(summaries, 1):
        print(f"\n{i}. {summary.get('content', 'N/A')}")
        if 'relevanceScore' in summary:
            print(f"   Relevance: {summary.get('relevanceScore', 0):.2f}")
except Exception as e:
    print(f"Error retrieving summaries: {e}")

print()
print("=" * 80)
print("VERIFICATION COMPLETE")
print("=" * 80)
