AWS Bedrock Knowledge Base Query Tool

Overview
This Python application enables users to interact with AWS Bedrock Knowledge Bases. It provides functionality to list available knowledge bases and query them using natural language, leveraging the Bedrock Agent Runtime service.

Features
List all available knowledge bases in your AWS account
Interactive selection of knowledge bases
Natural language querying of selected knowledge base
Display of responses with citations and sources

Prerequisites
Python 3.x
AWS credentials configured

Required Python packages:
boto3
botocore

Installation
Ensure you have Python installed
Install required dependencies:

pip install boto3


Project Structure
The project consists of three main functions:

list_knowledge_bases()
Lists all available knowledge bases in the specified AWS region

Allows user selection of a knowledge base

Returns the selected knowledge base ID

query_knowledge_base(knowledge_base_id, query_text)
Queries the selected knowledge base using the provided text

Uses Claude 3 Haiku model for processing

Displays the response and relevant citations

Handles error cases through exception handling

main()
Orchestrates the program flow

Provides an interactive query loop

Handles program exit

Usage
Run the script:

python kb1.py


Select a knowledge base from the displayed list

Enter your queries when prompted

Type 'quit' to exit the program

Configuration
Region: Currently set to us-west-2

Model: Uses anthropic.claude-3-haiku-20240307-v1:0

Vector search configuration: Set to retrieve up to 100 results

Error Handling
The application includes error handling for:

AWS client errors

Invalid knowledge base selection

Query execution failures

Best Practices
Uses boto3 for AWS service interaction

Implements proper error handling

Provides user feedback for all operations

Maintains clean separation of concerns between functions

Limitations
Region is hardcoded to us-west-2
Single model support
Maximum of 100 vector search results

Security Considerations

Requires appropriate AWS IAM permissions
Should be run in a secure environment with proper AWS credentials
Credentials should be managed through AWS best practices