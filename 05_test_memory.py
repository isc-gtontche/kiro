#!/usr/bin/env python3
"""
Script to test memory retrieval for user_001.

This script demonstrates:
- Loading memory configuration
- Retrieving user preferences
- Searching semantic facts
- Displaying what the agent remembers about the customer
"""

import json

try:
    from bedrock_agentcore.memory import MemoryClient
except ImportError:
    print("✗ Error: bedrock_agentcore package not found")
    print("  Install with: pip install bedrock-agentcore")
    exit(1)

# Load memory_id from config
print("=" * 80)
print("AGENTCORE MEMORY RETRIEVAL TEST")
print("=" * 80)
print()

with open('memory_config.json') as f:
    config = json.load(f)
    memory_id = config['memory_id']
    memory_name = config.get('name', 'N/A')

print(f"Memory Name: {memory_name}")
print(f"Memory ID: {memory_id}")
print(f"Region: us-west-2")
print(f"Customer ID: user_001")
print()

# Create memory client
memory_client = MemoryClient(region_name='us-west-2')

# ============================================================================
# 1. RETRIEVE USER PREFERENCES
# ============================================================================
print("=" * 80)
print("1. USER PREFERENCES")
print("=" * 80)
print(f"Namespace: app/user_001/preferences")
print(f"Query: 'customer preferences and communication'")
print()

try:
    preferences = memory_client.retrieve_memories(
        memory_id=memory_id,
        namespace="app/user_001/preferences",
        query="customer preferences and communication",
        top_k=5
    )
    
    if preferences:
        print(f"✓ Found {len(preferences)} preference memory/memories")
        print()
        
        for i, memory in enumerate(preferences, 1):
            print(f"Preference {i}:")
            print("─" * 80)
            
            content = memory.get('content', {})
            if isinstance(content, dict):
                text = content.get('text', 'N/A')
            else:
                text = str(content)
            
            # Try to parse JSON if it looks like JSON
            if text.startswith('{'):
                try:
                    parsed = json.loads(text)
                    print(f"Preference: {parsed.get('preference', 'N/A')}")
                    print(f"Context: {parsed.get('context', 'N/A')}")
                    print(f"Categories: {', '.join(parsed.get('categories', []))}")
                except:
                    print(f"Content: {text}")
            else:
                print(f"Content: {text}")
            
            print()
    else:
        print("⚠️  No preferences found")
        print("Memory extraction may still be processing (takes 20-30 seconds)")
        
except Exception as e:
    print(f"❌ Error retrieving preferences: {e}")

print()

# ============================================================================
# 2. RETRIEVE SEMANTIC FACTS
# ============================================================================
print("=" * 80)
print("2. SEMANTIC FACTS (Return History)")
print("=" * 80)
print(f"Namespace: app/user_001/semantic")
print(f"Query: 'return history laptop defective'")
print()

try:
    facts = memory_client.retrieve_memories(
        memory_id=memory_id,
        namespace="app/user_001/semantic",
        query="return history laptop defective",
        top_k=5
    )
    
    if facts:
        print(f"✓ Found {len(facts)} semantic memory/memories")
        print()
        
        for i, memory in enumerate(facts, 1):
            print(f"Fact {i}:")
            print("─" * 80)
            
            content = memory.get('content', {})
            if isinstance(content, dict):
                text = content.get('text', 'N/A')
            else:
                text = str(content)
            
            print(f"Content: {text}")
            print()
    else:
        print("⚠️  No semantic facts found")
        
except Exception as e:
    print(f"❌ Error retrieving facts: {e}")

print()

# ============================================================================
# 3. RETRIEVE RECENT CONVERSATION TURNS
# ============================================================================
print("=" * 80)
print("3. RECENT CONVERSATION HISTORY")
print("=" * 80)
print(f"Session: session_001")
print(f"Last K turns: 3")
print()

try:
    turns = memory_client.get_last_k_turns(
        memory_id=memory_id,
        actor_id="user_001",
        session_id="session_001",
        k=3
    )
    
    if turns:
        print(f"✓ Retrieved {len(turns)} conversation turn(s)")
        print()
        
        for i, turn in enumerate(turns, 1):
            print(f"Turn {i}:")
            print("─" * 80)
            for msg in turn:
                role = msg.get('role', 'UNKNOWN')
                content = msg.get('content', {})
                if isinstance(content, dict):
                    text = content.get('text', str(content))
                else:
                    text = str(content)
                
                # Truncate long messages
                if len(text) > 150:
                    text = text[:150] + "..."
                
                print(f"[{role}]: {text}")
            print()
    else:
        print("⚠️  No conversation turns found")
        
except Exception as e:
    print(f"❌ Error retrieving turns: {e}")

print()

# ============================================================================
# 4. SUMMARY - WHAT THE AGENT REMEMBERS
# ============================================================================
print("=" * 80)
print("SUMMARY: WHAT THE AGENT REMEMBERS ABOUT user_001")
print("=" * 80)
print()

print("Communication Preferences:")
if preferences:
    for pref in preferences:
        content = pref.get('content', {})
        if isinstance(content, dict):
            text = content.get('text', '')
        else:
            text = str(content)
        
        if text.startswith('{'):
            try:
                parsed = json.loads(text)
                print(f"  ✓ {parsed.get('preference', 'N/A')}")
            except:
                print(f"  ✓ {text}")
        else:
            print(f"  ✓ {text}")
else:
    print("  (No preferences recorded)")

print()
print("Return History:")
if facts:
    for fact in facts:
        content = fact.get('content', {})
        if isinstance(content, dict):
            text = content.get('text', 'N/A')
        else:
            text = str(content)
        print(f"  ✓ {text}")
else:
    print("  (No return history recorded)")

print()
print("Recent Interactions:")
if turns:
    print(f"  ✓ {len(turns)} recent conversation turn(s) available")
    print(f"  ✓ Last session: session_001")
else:
    print("  (No recent interactions)")

print()
print("=" * 80)
print("TEST COMPLETE")
print("=" * 80)
print()
print("Next Steps:")
print("  - Integrate memory retrieval into returns_refunds_agent")
print("  - Test agent responses with memory context")
print("  - Add more customer conversations to build richer memory")
print()
