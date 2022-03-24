import boto3
import json
import logging
import os
from boto3.dynamodb.types import TypeDeserializer
from redis import Redis

logger = logging.getLogger()
logger.setLevel(logging.INFO)

## LAMBDA ENVIRONMENT VARIABLES ##
# The current AWS region for boto3 configuration
current_region = os.environ['AWS_REGION']

# ARN of the Elasticache Redis cluster 
ec_cluster_endpoint = os.environ['EC_CLUSTER_ENDPOINT']

# ARN of the Secrets Manager secret containing Elasticache user credentials 
ec_secret_arn = os.environ['EC_SECRET_ARN']

# Name of the Redis key used for the geospatial index
geo_index_key = os.environ['GEO_INDEX_KEY']


logger.info(f"Retrieving secret {ec_secret_arn}")
# Retrieve Redis user credentials from Secrets Manager
session = boto3.session.Session(region_name=current_region)
secrets_manager_client = session.client(service_name='secretsmanager')
secret_response = secrets_manager_client.get_secret_value(SecretId=ec_secret_arn)

# Deserialize the Secrets Manager secret string to a Python dict
secret = json.loads(secret_response['SecretString'])
redis_user = secret['username']
redis_password = secret['password']
logger.info(f"Successfully retrieved secret {ec_secret_arn}")


logger.info(f"Connecting to Redis cluster {ec_cluster_endpoint}")
# Connect to the Elasticache cluster
redis_client = Redis(host=ec_cluster_endpoint, 
                     port=6379, decode_responses=True, ssl=True, 
                     username=redis_user, password=redis_password)
logger.info(f"Successfully connected to Redis cluster {ec_cluster_endpoint}")

# This boto3 deserializer converts DynamoDB types to Python types
dynamodb_deserializer = TypeDeserializer()


# The main lambda handler function
def lambda_handler(event, context):
    logger.info("Received event: {}".format(event))
    
    # DynamoDB Streams events contain one or more change records
    for record in event['Records']:
        operation = record['eventName']
        item_details = {}

        # If this is a PutItem or UpdateItem operation, we want the new data 
        if operation == 'INSERT' or operation == 'MODIFY':
            item_details = record['dynamodb']['NewImage']

        # If this is a DeleteItem operation, the current data has the key to delete
        elif operation == 'REMOVE':
            item_details = record['dynamodb']['OldImage']

        # Convert event data from DynamoDB types to Python types
        property_details = {k: dynamodb_deserializer.deserialize(v) for k, v in item_details.items()}

        # Convert booleans to strings for Redis compatibility
        for attribute in property_details:
            if type(property_details[attribute] is bool):
                property_details[attribute]= str(property_details[attribute])

        # We need a unique key to store the property details in Redis. 
        # Since DynamoDB requires the combination of pk and sk to be unique, combining them
        # is an easy way to create a unique key
        property_detail_key = "#".join([property_details['pk'], property_details['sk']])

        if operation == 'INSERT' or operation == 'MODIFY':
            # Add the complete property information to the cache
            redis_client.hmset(property_detail_key, mapping=property_details)

            # Add the property to the geospatial index
            property_geo_data = (property_details["longitude"], property_details["latitude"], property_detail_key)
            redis_client.geoadd(geo_index_key, property_geo_data)
            
            logger.info(f"Populated cache key {property_detail_key} with {property_details}")

        elif operation == 'REMOVE':
            # Remove the full property information from the cache
            redis_client.delete(property_detail_key)

            # Remove the property from the geospatial index
            redis_client.zrem(geo_index_key, property_detail_key)
            logger.info(f"Removed cache key {property_detail_key}")

    return 'Successfully processed {} records.'.format(len(event['Records']))