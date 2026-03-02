#!/usr/bin/env python3
"""
Script to seed AgentCore Memory with sample customer conversations.

This script adds two sample conversations for user_001:
1. Customer mentions email preference and defective laptop return
2. Customer asks about return windows for electronics
"""

import json
import time

try:
    from bedrock_agentcore.memory import MemoryClient
except ImportError:
    print("✗ Error: bedrock_agentcore package not found")
    print("  Install with: pip install bedrock-agentcore")
    exit(1)

# Load memory_id from config
print("Loading memory configuration...")
with open('memory_config.json') as f:
    config = json.load(f)
    memory_id = config['memory_id']

print(f"✓ Using Memory ID: {memory_id}")
print(f"✓ Region: us-west-2")
print(f"✓ Customer ID: user_001")
print()

# Create memory client
memory_client = MemoryClient(region_name='us-west-2')

# ============================================================================
# CONVERSATION 1: Email preference and defective laptop return
# ============================================================================
print("=" * 80)
print("CONVERSATION 1: Email Preferences & Defective Laptop Return")
print("=" * 80)

conversation_1 = [
    (
        "Hi, I wanted to update my notification preferences. I prefer to receive updates via email rather than SMS.",
        "USER"
    ),
    (
        "Thank you for letting me know! I've noted that you prefer email notifications. Is there anything else I can help you with today?",
        "ASSISTANT"
    ),
    (
        "Yes, I actually returned a laptop last month because it was defective. The screen had dead pixels. Just wanted to make sure that was processed correctly.",
        "USER"
    ),
    (
        "I understand. Let me check on that return for you. A defective laptop with screen issues would qualify for a full refund under our return policy. The return should have been processed, and you should receive your refund within 5-7 business days from when we received the item. Is there anything specific about the return you'd like me to verify?",
        "ASSISTANT"
    )
]

print("\nStoring conversation 1...")
memory_client.create_event(
    memory_id=memory_id,
    actor_id="user_001",
    session_id="session_001",
    messages=conversation_1
)
print(f"✓ Stored {len(conversation_1)} messages (session_001)")

# ============================================================================
# CONVERSATION 2: Return windows for electronics
# ============================================================================
print()
print("=" * 80)
print("CONVERSATION 2: Return Windows for Electronics")
print("=" * 80)

conversation_2 = [
    (
        "Hi, I have a question about return policies. What's the return window for electronics like laptops and tablets?",
        "USER"
    ),
    (
        "Great question! For most electronics including laptops and tablets, we offer a 30-day return window from the date of delivery. The item must be in its original condition with all accessories, packaging, and documentation. Would you like to know about any specific product category?",
        "ASSISTANT"
    ),
    (
        "That's helpful, thank you! And does the same apply to smartphones?",
        "USER"
    ),
    (
        "Yes, smartphones also have a 30-day return window. However, please note that for electronics, we do require that all personal data be erased before returning the device. Also, if the item is defective, you're eligible for a full refund regardless of the condition. Is there a specific return you're planning?",
        "ASSISTANT"
    )
]

print("\nStoring conversation 2...")
memory_client.create_event(
    memory_id=memory_id,
    actor_id="user_001",
    session_id="session_002",
    messages=conversation_2
)
print(f"✓ Stored {len(conversation_2)} messages (session_002)")

# ============================================================================
# WAIT FOR MEMORY PROCESSING
# ============================================================================
print()
print("=" * 80)
print("WAITING FOR MEMORY PROCESSING")
print("=" * 80)
print()
print("Memory strategies process asynchronously to extract:")
print("  - User preferences (e.g., 'prefers email notifications')")
print("  - Semantic facts (e.g., 'returned defective laptop')")
print("  - Conversation summaries")
print()
print("Waiting 30 seconds for processing...")

for i in range(30, 0, -5):
    print(f"  {i} seconds remaining...")
    time.sleep(5)

print()
print("✓ Memory processing complete!")
print()

# ============================================================================
# SUMMARY
# ============================================================================
print("=" * 80)
print("MEMORY SEEDING COMPLETE")
print("=" * 80)
print()
print("Summary:")
print(f"  Customer ID: user_001")
print(f"  Conversations stored: 2")
print(f"  Total messages: {len(conversation_1) + len(conversation_2)}")
print()
print("Expected Memory Extractions:")
print("  Preferences:")
print("    - Prefers email notifications over SMS")
print()
print("  Semantic Facts:")
print("    - Previously returned a defective laptop (dead pixels)")
print("    - Asked about return windows for electronics")
print("    - Interested in laptop, tablet, and smartphone return policies")
print()
print("  Summaries:")
print("    - Session 001: Customer updated preferences and inquired about laptop return")
print("    - Session 002: Customer asked about electronics return windows")
print()
print("Next Steps:")
print("  - Test memory retrieval with the agent")
print("  - Verify preferences were extracted correctly")
print("  - Check semantic search for return-related facts")
print()
print("=" * 80)
