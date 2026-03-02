#!/usr/bin/env python3
"""
Script to get CloudWatch GenAI Observability dashboard URL.
"""

import json
import os

# Build dashboard URL
region = "us-west-2"
dashboard_url = f"https://console.aws.amazon.com/cloudwatch/home?region={region}#gen-ai-observability/agent-core"

print("=" * 80)
print("CLOUDWATCH GENAI OBSERVABILITY DASHBOARD")
print("=" * 80)

# Load runtime config if available
if os.path.exists('runtime_config.json'):
    with open('runtime_config.json') as f:
        runtime_config = json.load(f)
    
    agent_name = runtime_config.get('agent_name', 'N/A')
    agent_arn = runtime_config.get('agent_arn', 'N/A')
    
    print(f"\nAgent Name: {agent_name}")
    print(f"Agent ARN: {agent_arn}")
    print(f"Region: {region}")
else:
    print(f"\nRegion: {region}")
    print("\nNote: No runtime_config.json found. Deploy agent first to see specific metrics.")

print("\n" + "=" * 80)
print("DASHBOARD URL")
print("=" * 80)
print(f"\n{dashboard_url}")

print("\n" + "=" * 80)
print("DASHBOARD FEATURES")
print("=" * 80)
print("\n1. Agent Performance Metrics:")
print("   - Invocation count and success rate")
print("   - Response time (p50, p90, p99)")
print("   - Token usage and costs")
print("   - Error rates and patterns")

print("\n2. Request Traces:")
print("   - End-to-end conversation flow")
print("   - Tool invocations (Memory, Gateway, KB)")
print("   - Time spent in each component")
print("   - Detailed span information")

print("\n3. Session History:")
print("   - All agent interactions")
print("   - User queries and responses")
print("   - Session duration and patterns")

print("\n4. Tool Usage Analytics:")
print("   - Which tools are called most")
print("   - Tool success/failure rates")
print("   - Tool latency metrics")

print("\n5. Error Analysis:")
print("   - Error types and frequencies")
print("   - Stack traces and context")
print("   - Error trends over time")

print("\n" + "=" * 80)
print("OTHER MONITORING OPTIONS")
print("=" * 80)

print("\n1. View Recent Logs:")
print("   python3 22_view_logs.py")

print("\n2. X-Ray Traces:")
print(f"   https://console.aws.amazon.com/xray/home?region={region}#/traces")

print("\n3. CloudWatch Logs Console:")
if os.path.exists('runtime_config.json'):
    agent_arn = runtime_config.get('agent_arn', '')
    if agent_arn:
        agent_id = agent_arn.split('/')[-1]
        log_group = f"/aws/bedrock-agentcore/runtimes/{agent_id}-DEFAULT"
        log_group_encoded = log_group.replace('/', '$252F')
        print(f"   https://console.aws.amazon.com/cloudwatch/home?region={region}#logsV2:log-groups/log-group/{log_group_encoded}")
else:
    print("   Deploy agent first to get log group URL")

print("\n4. Tail Logs in Real-Time (AWS CLI):")
if os.path.exists('runtime_config.json') and agent_arn:
    agent_id = agent_arn.split('/')[-1]
    log_group = f"/aws/bedrock-agentcore/runtimes/{agent_id}-DEFAULT"
    print(f"   aws logs tail {log_group} --follow")
else:
    print("   Deploy agent first to get log group name")

print("\n" + "=" * 80)
print("QUICK TIPS")
print("=" * 80)
print("\n- Dashboard updates in real-time")
print("- Filter by time range to focus on specific periods")
print("- Click on traces to see detailed execution flow")
print("- Use the search to find specific sessions or errors")
print("- Export data for custom analysis")

print("\n" + "=" * 80)
print("\nOpen the dashboard URL above in your browser to start monitoring!")
print("=" * 80)
