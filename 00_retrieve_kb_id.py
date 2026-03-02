#!/usr/bin/env python3
"""
Retrieve Knowledge Base ID from CloudFormation stack.
"""
import boto3
import json
from botocore.exceptions import ClientError

def retrieve_kb_id(stack_name='knowledgebase', region='us-west-2'):
    """Retrieve Knowledge Base ID from CloudFormation stack."""
    try:
        client = boto3.client('cloudformation', region_name=region)
        response = client.describe_stacks(StackName=stack_name)
        
        if not response['Stacks']:
            print(f"Stack '{stack_name}' not found")
            return None
        
        stack = response['Stacks'][0]
        outputs = stack.get('Outputs', [])
        
        for output in outputs:
            if output['OutputKey'] == 'KnowledgeBaseId':
                kb_id = output['OutputValue']
                print(f"Found Knowledge Base ID: {kb_id}")
                
                # Save to config file
                config = {'knowledge_base_id': kb_id}
                with open('kb_config.json', 'w') as f:
                    json.dump(config, f, indent=2)
                print("Saved to kb_config.json")
                
                return kb_id
        
        print(f"OutputKey 'KnowledgeBaseId' not found in stack '{stack_name}'")
        return None
        
    except ClientError as e:
        print(f"Error retrieving stack: {e}")
        return None

if __name__ == '__main__':
    kb_id = retrieve_kb_id()
    
    if not kb_id:
        print("\nUsing placeholder KB ID")
        kb_id = '<PLACE-YOUR-KB-ID>'
        config = {'knowledge_base_id': kb_id}
        with open('kb_config.json', 'w') as f:
            json.dump(config, f, indent=2)
        print("Saved placeholder to kb_config.json")
