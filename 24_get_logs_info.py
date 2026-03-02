#!/usr/bin/env python3
"""
Script to get CloudWatch log group information for agent logs.
"""

import json
import os
from datetime import datetime

# Check if runtime config exists
if not os.path.exists('runtime_config.json'):
    print("❌ Error: runtime_config.json not found")
    print("Please deploy the agent first: python3 19_deploy_agent.py")
    exit(1)

# Load configuration
with open('runtime_config.json') as f:
    runtime_config = json.load(f)

agent_arn = runtime_config["agent_arn"]
agent_name = runtime_config.get("agent_name", "N/A")

# Extract agent ID from ARN
agent_id = agent_arn.split('/')[-1]

# Build log group name
log_group = f"/aws/bedrock-agentcore/runtimes/{agent_id}-DEFAULT"

# Get current date for log stream prefix
current_date = datetime.now().strftime("%Y/%m/%d")

print("=" * 80)
print("CLOUDWATCH LOGS INFORMATION")
print("=" * 80)

print(f"\nAgent Name: {agent_name}")
print(f"Agent ARN: {agent_arn}")
print(f"Agent ID: {agent_id}")
print(f"Region: us-west-2")

print("\n" + "=" * 80)
print("LOG GROUP")
print("=" * 80)
print(f"\n{log_group}")

print("\n" + "=" * 80)
print("AWS CLI COMMANDS")
print("=" * 80)

print("\n1. Tail logs in real-time:")
print(f'   aws logs tail {log_group} \\')
print(f'     --log-stream-name-prefix "{current_date}/[runtime-logs]" \\')
print(f'     --follow')

print("\n2. View recent logs (last hour):")
print(f'   aws logs tail {log_group} \\')
print(f'     --log-stream-name-prefix "{current_date}/[runtime-logs]" \\')
print(f'     --since 1h')

print("\n3. View recent logs (last 30 minutes):")
print(f'   aws logs tail {log_group} \\')
print(f'     --log-stream-name-prefix "{current_date}/[runtime-logs]" \\')
print(f'     --since 30m')

print("\n4. View OpenTelemetry logs:")
print(f'   aws logs tail {log_group} \\')
print(f'     --log-stream-names "otel-rt-logs" \\')
print(f'     --follow')

print("\n5. Filter logs by pattern:")
print(f'   aws logs tail {log_group} \\')
print(f'     --log-stream-name-prefix "{current_date}/[runtime-logs]" \\')
print(f'     --filter-pattern "ERROR"')

print("\n" + "=" * 80)
print("CLOUDWATCH CONSOLE")
print("=" * 80)

# Build console URL
log_group_encoded = log_group.replace('/', '$252F')
console_url = f"https://console.aws.amazon.com/cloudwatch/home?region=us-west-2#logsV2:log-groups/log-group/{log_group_encoded}"

print(f"\n{console_url}")

print("\n" + "=" * 80)
print("PROGRAMMATIC ACCESS")
print("=" * 80)

print("\nView logs using Python script:")
print("   python3 22_view_logs.py")

print("\n" + "=" * 80)
print("LOG TYPES")
print("=" * 80)

print("\n1. Runtime Logs:")
print("   - Agent invocations")
print("   - Tool calls (Memory, Gateway, KB)")
print("   - Custom tool executions")
print("   - Response generation")

print("\n2. Error Logs:")
print("   - Exceptions and stack traces")
print("   - Failed tool calls")
print("   - Authentication errors")
print("   - Timeout errors")

print("\n3. Performance Logs:")
print("   - Request latency")
print("   - Token usage")
print("   - Memory retrieval times")
print("   - Gateway call durations")

print("\n4. OpenTelemetry Logs:")
print("   - Distributed traces")
print("   - Span information")
print("   - Service metrics")

print("\n" + "=" * 80)
print("TIPS")
print("=" * 80)

print("\n- Use --follow to stream logs in real-time")
print("- Use --since to limit time range (e.g., 1h, 30m, 5m)")
print("- Use --filter-pattern to search for specific text")
print("- Logs are retained for 30 days by default")
print("- Use CloudWatch Insights for advanced queries")

print("\n" + "=" * 80)
