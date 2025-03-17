import boto3
from botocore.exceptions import ClientError

def list_knowledge_bases():
    """List all available knowledge bases"""
    try:
        # Create a Bedrock Agent client with explicit region
        bedrock_client = boto3.client('bedrock-agent', region_name='us-west-2')
        
        # List knowledge bases
        response = bedrock_client.list_knowledge_bases()
        
        if not response['knowledgeBaseSummaries']:
            print("No knowledge bases found")
            return None
        
        # Print available knowledge bases
        print("\nAvailable Knowledge Bases:")
        for idx, kb in enumerate(response['knowledgeBaseSummaries'], 1):
            print(f"{idx}. {kb['name']} (ID: {kb['knowledgeBaseId']}")
        
        # Let user select a knowledge base
        selection = int(input("\nSelect a knowledge base (enter number): ")) - 1
        if 0 <= selection < len(response['knowledgeBaseSummaries']):
            return response['knowledgeBaseSummaries'][selection]['knowledgeBaseId']
        else:
            print("Invalid selection")
            return None
            
    except ClientError as e:
        print(f"Error listing knowledge bases: {e}")
        return None

def query_knowledge_base(knowledge_base_id, query_text):
    """Query the selected knowledge base"""
    try:
        # Create a Bedrock Agent Runtime client with explicit region
        agent_client = boto3.client('bedrock-agent-runtime', region_name='us-west-2')
        
        # Define the model ARN for us-west-2
        model_id = "arn:aws:bedrock:us-west-2::foundation-model/anthropic.claude-3-haiku-20240307-v1:0"
        
        # Create the request
        request = {
            'input': {
                'text': query_text
            },
            'retrieveAndGenerateConfiguration': {
                'type': 'KNOWLEDGE_BASE',
                'knowledgeBaseConfiguration': {
                    'knowledgeBaseId': knowledge_base_id,
                    'modelArn': model_id,
                    'retrievalConfiguration': {
                        'vectorSearchConfiguration': {
                            #'overrideSearchType': 'HYBRID',
                            'numberOfResults': 100  # Maximum number for vector search results
                        }
                    }
                }
            }
        }
        
        # Make the retrieve and generate request
        response = agent_client.retrieve_and_generate(**request)
        
        # Extract and print the generated response
        if 'output' in response and 'text' in response['output']:
            print("\nResponse:")
            print(response['output']['text'])
            
            # Print citations if available
            if 'citations' in response['output']:
                print("\nCitations:")
                for citation in response['output']['citations']:
                    print(f"- {citation['generatedResponsePart']}")
                    if 'retrievedReferences' in citation:
                        print(f"  Source: {citation['retrievedReferences'][0]['location']['s3Location']['uri']}")
        
    except ClientError as e:
        print(f"Error querying knowledge base: {e}")

def main():
    # List and select knowledge base
    knowledge_base_id = list_knowledge_bases()
    if not knowledge_base_id:
        return
    
    # Interactive query loop
    while True:
        query = input("\nEnter your query (or 'quit' to exit): ")
        if query.lower() == 'quit':
            break
            
        print("\nQuerying knowledge base...")
        query_knowledge_base(knowledge_base_id, query)

if __name__ == "__main__":
    main()
