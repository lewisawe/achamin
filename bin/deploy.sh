#!/bin/bash

echo "===== Deploying Achamin - Cultural Understanding Through AI ====="
echo ""

# Check for AWS CLI
if ! command -v aws &> /dev/null; then
    echo "AWS CLI is not installed. Please install it first."
    exit 1
fi

# Check for AWS credentials
aws sts get-caller-identity &> /dev/null
if [ $? -ne 0 ]; then
    echo "AWS credentials not configured. Please run 'aws configure' first."
    exit 1
fi

echo "Creating S3 buckets..."
aws s3 mb s3://achamin-uploads --region us-east-1
aws s3 mb s3://achamin-generated-content --region us-east-1

echo "Setting bucket CORS policies..."
aws s3api put-bucket-cors --bucket achamin-uploads --cors-configuration file://../policies/cors-policy.json
aws s3api put-bucket-cors --bucket achamin-generated-content --cors-configuration file://../policies/cors-policy.json

echo "Deploying Lambda function..."
cd ../lambdas
./deployLambdaFunction

echo "Deploying API Gateway..."
cd ../apiGateway
./deployAPIGateway

echo "Deployment complete!"
echo ""
echo "Next steps:"
echo "1. Update the API endpoint URL in index.html"
echo "2. Open index.html in your browser to start using Achamin"
echo ""
