import json
import boto3
import uuid
import base64
import os

# Initialize AWS clients
s3 = boto3.client('s3')
rekognition = boto3.client('rekognition')
bedrock = boto3.client('bedrock-runtime')
polly = boto3.client('polly')

def lambda_handler(event, context):
    try:
        # Get the image data from the request
        content_type = event['headers'].get('content-type', '')
        if 'image' in content_type:
            # Handle direct image upload
            image_data = base64.b64decode(event['body'])
        else:
            # Handle JSON with base64 encoded image
            body = json.loads(event['body'])
            image_data = base64.b64decode(body['image'])
        
        # Generate unique identifier for this request
        request_id = str(uuid.uuid4())
        
        # Upload the image to S3
        image_path = f'uploads/{request_id}.jpg'
        s3.put_object(
            Bucket='achamin-uploads',
            Key=image_path,
            Body=image_data
        )
        
        # Step 1: Use Rekognition to analyze the image
        rekognition_response = rekognition.detect_labels(
            Image={
                'Bytes': image_data
            },
            MaxLabels=10
        )
        
        # Extract relevant labels
        labels = [label['Name'] for label in rekognition_response['Labels']]
        
        # Step 2: Use AWS Bedrock to generate cultural context
        cultural_prompt = f"""
        Analyze this image containing the following elements: {', '.join(labels)}.
        Provide cultural context including:
        1. Historical significance and origins
        2. Cultural meaning and symbolism
        3. Social and spiritual importance
        4. Modern relevance and evolution
        5. Respectful appreciation guidelines
        
        Format your response in a conversational, engaging style that's educational but not academic.
        """
        
        # Call Bedrock (using Claude model as an example)
        bedrock_response = bedrock.invoke_model(
            modelId='anthropic.claude-v3.7',
            body=json.dumps({
                "prompt": f"\n\nHuman: {cultural_prompt}\n\nAssistant:",
                "max_tokens_to_sample": 1000,
                "temperature": 0.7
            })
        )
        
        cultural_explanation = json.loads(bedrock_response['body'].read())['completion']
        
        # Step 3: Generate narration using Amazon Polly
        polly_response = polly.synthesize_speech(
            Text=cultural_explanation,
            OutputFormat='mp3',
            VoiceId='Joanna'
        )
        
        # Upload the generated audio to S3
        audio_path = f'audio/{request_id}.mp3'
        s3.put_object(
            Bucket='achamin-generated-content',
            Key=audio_path,
            Body=polly_response['AudioStream'].read()
        )
        
        # Generate a pre-signed URL for accessing the audio
        audio_url = s3.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': 'achamin-generated-content',
                'Key': audio_path
            },
            ExpiresIn=3600
        )
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'culturalContext': cultural_explanation,
                'audioUrl': audio_url,
                'detectedElements': labels
            })
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }