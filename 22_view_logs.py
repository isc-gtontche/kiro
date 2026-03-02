#!/usr/bin/env python3
"""
Script to view recent logs from the deployed agent.
"""

import json
import boto3
from datetime import datetime, timedelta

# Load runtime config
with open('runtime_config.json') as f:
    runtime_config = json.load(f)

agent_arn = runtime_config['agent_arn']
agent_name = runtime_config['agent_name']

# Extract agent ID from ARN
agent_id = agent_arn.split('/')[-1]

# CloudWatch Logs client
logs_client = boto3.client('logs', region_name='us-west-2')

# Log group name
log_group = f"/aws/bedrock-agentcore/runtimes/{agent_id}-DEFAULT"

print("=" * 80)
print("AGENTCORE RUNTIME LOGS")
print("=" * 80)
print(f"\nAgent: {agent_name}")
print(f"Log Group: {log_group}")
print("\n" + "=" * 80)

try:
    # Get logs from the last hour
    start_time = int((datetime.now() - timedelta(hours=1)).timestamp() * 1000)
    end_time = int(datetime.now().timestamp() * 1000)
    
    # Filter log events
    response = logs_client.filter_log_events(
        logGroupName=log_group,
        startTime=start_time,
        endTime=end_time,
        limit=50  # Get last 50 log entries
    )
    
    events = response.get('events', [])
    
    if not events:
        print("\nNo logs found in the last hour.")
        print("\nTips:")
        print("  - Make sure you've invoked the agent recently")
        print("  - Check the log group exists in CloudWatch Console")
    else:
        print(f"\nShowing {len(events)} most recent log entries:\n")
        
        for event in events:
            timestamp = datetime.fromtimestamp(event['timestamp'] / 1000)
            message = event['message'].strip()
            
            # Color code based on log level
            if 'ERROR' in message or 'Error' in message or '✗' in message:
                prefix = "❌"
            elif 'WARNING' in message or 'Warning' in message or '⚠' in message:
                prefix = "⚠️ "
            elif '✓' in message or 'SUCCESS' in message:
                prefix = "✓"
            else:
                prefix = "ℹ️ "
            
            print(f"{prefix} [{timestamp.strftime('%H:%M:%S')}] {message}")
        
        print("\n" + "=" * 80)
        print("LOG ANALYSIS")
        print("=" * 80)
        
        # Count log types
        errors = sum(1 for e in events if 'ERROR' in e['message'] or 'Error' in e['message'])
        warnings = sum(1 for e in events if 'WARNING' in e['message'] or 'Warning' in e['message'])
        
        print(f"\nTotal Entries: {len(events)}")
        print(f"Errors: {errors}")
        print(f"Warnings: {warnings}")
        
        if errors > 0:
            print("\n⚠️  Errors detected! Review the logs above for details.")
        elif warnings > 0:
            print("\n⚠️  Warnings detected. Agent is working but check for issues.")
        else:
            print("\n✓ No errors or warnings detected.")
    
    print("\n" + "=" * 80)
    print("MONITORING OPTIONS")
    print("=" * 80)
    print("\n1. GenAI Observability Dashboard:")
    print("   https://console.aws.amazon.com/cloudwatch/home?region=us-west-2#gen-ai-observability/agent-core")
    print("\n2. CloudWatch Logs Console:")
    print(f"   https://console.aws.amazon.com/cloudwatch/home?region=us-west-2#logsV2:log-groups/log-group/{log_group.replace('/', '$252F')}")
    print("\n3. Tail logs in real-time (AWS CLI):")
    print(f"   aws logs tail {log_group} --follow")
    print("\n" + "=" * 80)

except logs_client.exceptions.ResourceNotFoundException:
    print(f"\n❌ Log group not found: {log_group}")
    print("\nThis could mean:")
    print("  - Agent hasn't been invoked yet (logs created on first invocation)")
    print("  - Agent deployment is still in progress")
    print("  - Log group name has changed")
    print("\nTry invoking the agent first: python 21_invoke_agent.py")

except Exception as e:
    print(f"\n❌ Error retrieving logs: {e}")
    import traceback
    traceback.print_exc()
