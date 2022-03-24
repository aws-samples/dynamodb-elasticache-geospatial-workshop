import json
import boto3
import os

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['TABLE_NAME'])

def lambda_handler(event, context):
    
    # Prepare the response for API Gateway
    response = {
        'isBase64Encoded': False,
        'statusCode': 0,
        'body': ''
        }

    # Begin update expression, append updates 
    stmt = "SET "

    # Initiate ExpressionAttributeValues
    expr_name = {}
    expr_value = {}
    
    # Declare keys for item to be updated
    pk = event['keys']['pk']
    sk = event['keys']['sk']

    # Loop through attibutes to be updated, adding key/values to ExpressionAttributeValues map
    # {
    #    ':agent':'Lee Hannigan',
    # }
    # 
    # Loop through attibutes to be updated, adding key/values to ExpressionAttributeNames map
    # DynamoDB has a list of reserved key words https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/ReservedWords.html
    # We add our attribute names to a variable to avoid unexpected clashses witht he list of reserved words
    # {
    #    '#agent':'agent',
    # }
    # 
    # Add UpdateExpression using expression map
    #  'SET agent = :agent'
    #
    for key, value in event['data'].items():
        expr_value[':{}'.format(key)] = value
        expr_name['#{}'.format(key)] = key
        stmt += '#{} = :{},'.format(key, key)

    try:
        table.update_item(
                Key = {
                        'pk': pk,
                        'sk': sk
                },
                UpdateExpression = stmt[:-1], # strip the trailing comma from UpdateExpression string
                ExpressionAttributeValues =  expr_value,
                ExpressionAttributeNames = expr_name
        )
                
        #  Create Response and Log
        response['statusCode'] = 200
        response['body'] = json.dumps({'message':'Success'})
        print("Successfully persisted item: {}".format(json.dumps(event)))

    except Exception as e:
        #  Create Response and Log
        print("Could not persist item: {}".format(e))
        response['statusCode'] = 400
        response['body'] = json.dumps({'message':'Something Went Wrong'})
    
    response['headers']= {
              'Access-Control-Allow-Headers':'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Requested-With',
              'Access-Control-Allow-Methods':'POST,OPTIONS',
              'Access-Control-Allow-Origin':'*'
         }
            
    return response