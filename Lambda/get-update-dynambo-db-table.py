import json
import boto3
dyn_resource = boto3.resource('dynamodb')
myTable = 'cloudresume-test'
table = dyn_resource.Table(myTable)


def lambda_handler(event, context):
    response = table.get_item(Key={'id': '1'})
    
    views = response['Item']['views']
    views = views + 1
    
    data = table.put_item(
        TableName=myTable,
        Item={
        'id': '1',
        'views': views
        }
    )
    response = table.get_item(Key={
        'id': '0'
    })
    return views
