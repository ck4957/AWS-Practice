import json
import boto3

def lambda_handler(event, context):
    # TODO implement
    
    file_name = event["Records"][0]['s3']['object']['key']
    
    bucket_name = event["Records"][0]['s3']['bucket']['name']
    
    print("Event Details:", event)
    print("File Name: ", file_name)
    print("Bucket Name", bucket_name)
    
    subject = 'Event from ' + bucket_name
    
    client = boto3.client('ses')
    
    body = """
                <br>
                Lambda has been triggered. This is a notification mail to inform you regarding s3 event.
                
                The file {} is inserted in the {} bucket.
                
            """.format(file_name, bucket_name)
    
    message = {"Subject": {"Data": subject}, "Body": {"Html": {"Data": body}}}
    
    response = client.send_email(Source = "kular.chirag.it@gmail.com", 
                                 Destination = {"ToAddresses": ["kular.chirag.it@gmail.com"]},
                                 Message = message
                                 )
    print("the mail is sent successfully")                                 
                                
    
