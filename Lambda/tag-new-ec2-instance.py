import json
import boto3

ec2 = boto3.client('ec2')

def lambda_handler(event, context):
    # print(event)
    # Instance ID
    instanceId = event['detail']['responseElements']['instancesSet']['items'][0]['instanceId']
    
    # Username
    user = event['detail']['userIdentity']['userName']
    
    print(instanceId, user)
    
    # tag an ec2 instance with owner's name
    ec2.create_tags(
    Resources=[
        instanceId,
    ],
    Tags=[
        {
            'Key': 'Owner',
            'Value': user,
        },
    ]
    
)
