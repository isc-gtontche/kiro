#!/usr/bin/env python3
"""
Script to create AgentCore Memory for returns_refunds_agent.

This script creates an AgentCore Memory resource with memory strategies:
- Summary: Conversation summaries per session
- Preferences: User preferences across sessions
- Semantic: Factual information about returns and customer history
"""

import json
from bedrock_agentcore_starter_toolkit.operations.memory.manager import MemoryManager

# Define memory strategies in boto3 tagged union format
strategies = [
    {
        "summaryMemoryStrategy": {
            "name": "summary",
            "namespaces": [
                "app/{actorId}/{sessionId}/summary"
            ]
        }
    },
    {
        "userPreferenceMemoryStrategy": {
            "name": "preferences",
            "namespaces": [
                "app/{actorId}/preferences"
            ]
        }
    },
    {
        "semanticMemoryStrategy": {
            "name": "semantic",
            "namespaces": [
                "app/{actorId}/semantic"
            ]
        }
    }
]

# Create memory manager
memory_manager = MemoryManager(region_name='us-west-2')

# Create memory
print("Creating AgentCore Memory...")
print("  Name: returns_refunds_memory")
print("  Description: Stores customer interactions, preferences, and return history")
print("  Strategies: summary, preferences, semantic")
print()

memory = memory_manager.get_or_create_memory(
    name="returns_refunds_memory",
    description="Stores customer interactions, preferences, and return history",
    strategies=strategies
)

# Extract memory_id
memory_id = memory["id"]

# Save memory_id to config file
config = {
    "memory_id": memory_id,
    "name": "returns_refunds_memory",
    "region": "us-west-2",
    "strategies": ["summary", "preferences", "semantic"]
}

with open('memory_config.json', 'w') as f:
    json.dump(config, f, indent=2)

print(f"✓ Memory created successfully!")
print(f"  Memory ID: {memory_id}")
print(f"  Status: {memory.get('status', 'ACTIVE')}")
print()
print(f"✓ Configuration saved to memory_config.json")
print()
print("Memory Strategies:")
print("  - Summary: Stores conversation summaries per session")
print("  - Preferences: Stores user preferences across sessions")
print("  - Semantic: Stores factual information about returns")
print()
print("Note: Memory strategies process asynchronously (20-30 seconds after events)")
