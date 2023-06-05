import json
import math
import boto3
from time import gmtime, strftime

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('PowerOfMathDatabase')

now = strftime("%a, %d %b %Y %H:%M:%S +0000", gmtime())

def lambda_handler(event, context):
    # TODO implement
    mathResult = math.pow(int(event['base']), int(event['exponent']))
    
    response = table.put_item(
        Item= {
            'ID': str(mathResult),
            'LatestGreetingTime': now
        })
    return {
        'statusCode': 200,
        'body': json.dumps('Your result!' + str(mathResult))
    }
