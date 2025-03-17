import boto3
import time
from botocore.exceptions import ClientError
from datetime import datetime, timedelta
import uuid


class Timer:
    def __init__(self):
        self.start_time = None
        self.end_time = None

    def start(self):
        self.start_time = datetime.now()
        print(f"Timer started at: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")

    def stop(self):
        self.end_time = datetime.now()
        print(f"Timer stopped at: {self.end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        duration = self.end_time - self.start_time
        hours, remainder = divmod(duration.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)
        print(f"Total duration: {int(hours)}h {int(minutes)}m {int(seconds)}s")
        return duration

def generate_client_token():
    """Generate a unique client token with sufficient length"""
    # Combine timestamp and UUID to ensure uniqueness and proper length
    timestamp = str(int(time.time()))
    unique_id = str(uuid.uuid4())
    return f"{timestamp}-{unique_id}"  # This will be well over 33 characters

def upload_and_ingest_document(file_path, bucket_name, s3_key, knowledge_base_id, data_source_id):
    """
    Upload a document to S3 and ingest it into a knowledge base
    
    Parameters:
    file_path (str): Local path to the file to upload
    bucket_name (str): S3 bucket name
    s3_key (str): S3 key (path) for the uploaded file
    knowledge_base_id (str): ID of the knowledge base
    data_source_id (str): ID of the data source
    """
    timer = Timer()
    
    try:
        # Create S3 and Bedrock Agent clients
        s3_client = boto3.client('s3', region_name='us-west-2')
        bedrock_client = boto3.client('bedrock-agent', region_name='us-west-2')
        
        # Start timer
        timer.start()
        
        # Upload file to S3
        print(f"Uploading file to S3: {s3_key}")
        with open(file_path, 'rb') as file:
            s3_client.upload_fileobj(file, bucket_name, s3_key)
        print("Upload complete")
        
        # Start ingestion job with proper client token
        print("Starting ingestion job...")
        response = bedrock_client.start_ingestion_job(
            knowledgeBaseId=knowledge_base_id,
            dataSourceId=data_source_id,
            clientToken=generate_client_token()  # Use the new token generator
        )
        
        job_id = response['ingestionJob']['ingestionJobId']
        print(f"Ingestion job started. Job ID: {job_id}")
        
        # Monitor job status
        print("Monitoring ingestion job status...")
        status_check_count = 0
        while True:
            status_response = bedrock_client.get_ingestion_job(
                knowledgeBaseId=knowledge_base_id,
                dataSourceId=data_source_id,
                ingestionJobId=job_id
            )
            
            status = status_response['ingestionJob']['status']
            status_check_count += 1
            print(f"Status check #{status_check_count} - Current status: {status}")
            
            if status == 'COMPLETE':
                print("Ingestion job completed successfully")
                break
            elif status in ['FAILED', 'STOPPED']:
                error_message = status_response['ingestionJob'].get('errorMessage', 'No error message provided')
                print(f"Ingestion job {status.lower()}. Error: {error_message}")
                break
            
            # Wait for 30 seconds before checking again
            time.sleep(30)
        
        # Stop timer and show duration
        duration = timer.stop()
        
        return status == 'COMPLETE', duration
        
    except ClientError as e:
        print(f"Error occurred: {e}")
        timer.stop()  # Stop timer even if there's an error
        return False, None
    
def list_ingestion_jobs(knowledge_base_id, data_source_id):
    """List all ingestion jobs for a knowledge base data source"""
    try:
        bedrock_client = boto3.client('bedrock-agent', region_name='us-west-2')
        
        response = bedrock_client.list_ingestion_jobs(
            knowledgeBaseId=knowledge_base_id,
            dataSourceId=data_source_id
        )
        
        print("\nIngestion Jobs:")
        for job in response['ingestionJobSummaries']:
            print(f"\nJob ID: {job['ingestionJobId']}")
            print(f"Status: {job['status']}")
            
            # Safely print timestamps if they exist
            if 'startTime' in job:
                print(f"Start Time: {job['startTime']}")
            
            if 'endTime' in job:
                print(f"End Time: {job['endTime']}")
                if 'startTime' in job:  # Only calculate duration if we have both times
                    duration = job['endTime'] - job['startTime']
                    hours, remainder = divmod(duration.total_seconds(), 3600)
                    minutes, seconds = divmod(remainder, 60)
                    print(f"Duration: {int(hours)}h {int(minutes)}m {int(seconds)}s")
            
            if 'errorMessage' in job:
                print(f"Error: {job['errorMessage']}")
            
    except ClientError as e:
        print(f"Error listing ingestion jobs: {e}")

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
                            'overrideSearchType': 'HYBRID',
                            'numberOfResults': 100
                        }
                    }
                }
            }
        }
        
        print("\nQuerying knowledge base...")
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
    # Configuration
        # Configuration
    file_path = "document.pdf"  # Replace with your file path
    bucket_name = "kb-bench-us-west-2"         # Replace with your S3 bucket
    s3_key = "documents/document.pdf"        # Replace with desired S3 path
    knowledge_base_id = "GMWJ9YXU6U"         # Replace with your knowledge base ID
    data_source_id = "KFD2PZZ7HC"           # Replace with your data source ID
    
    # Upload and ingest document
    success, duration = upload_and_ingest_document(
        file_path,
        bucket_name,
        s3_key,
        knowledge_base_id,
        data_source_id
    )
    
    if success:
        print("\nDocument processed successfully")
        if duration:
            print(f"Total processing time: {duration}")
            
        # Wait a few seconds to ensure the knowledge base is updated
        print("\nWaiting for knowledge base to be fully updated...")
        time.sleep(10)
        
        # Create a summary prompt
        summary_prompt = """Please provide a comprehensive summary of the document, including:
1. Main topics and key points
2. Important findings or conclusions
3. Any significant data or statistics
4. Key recommendations (if any)

Please structure the summary in a clear, organized way."""

        # Query the knowledge base for a summary
        query_knowledge_base(knowledge_base_id, summary_prompt)
        
    else:
        print("\nDocument processing failed")
        
    # List all ingestion jobs
    list_ingestion_jobs(knowledge_base_id, data_source_id)
    

if __name__ == "__main__":
    main()
