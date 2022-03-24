import boto3
import json
import logging
import os
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

# Search in a 25 mile radius by default
DEFAULT_SEARCH_RADIUS=25


# The main lambda handler function
def lambda_handler(event, context):

     # As this is a POST request, the body will contain the invocation parameters
     request_body = json.loads(event['body'])
     # The request path tells us if this is a geospatial search 
     # or retrieving a particular property's details
     request_path = event['path']
     results = None
     
     # Perform a geospatial radius search
     if request_path.endswith('search'):
          # Retrieve the geospatial search parameters from the request body
          search_latitude = request_body['lat']
          search_longitude = request_body['lon']

          # Use the default search radius if none is provided
          search_radius = request_body.get('radius', DEFAULT_SEARCH_RADIUS)

          # Search the Redis geospatial index 
          results = redis_client.geosearch(geo_index_key, 
                                        longitude=search_longitude,       
                                        latitude=search_latitude,               
                                        unit='mi', 
                                        radius=search_radius, 
                                        sort='ASC', 
                                        withcoord=True, 
                                        withdist=True)

     # Retrieve a property's details from the cache
     elif request_path.endswith('detail'):
          # Get the property key from the request body
          search_latitude = request_body['property_key']

          # Retrieve the details for this property key
          results = redis_client.hgetall(search_latitude)

     # Create the response to return to API Gateway
     response = {}
     response['isBase64Encoded'] = False
     response['statusCode'] = 200
     response['body'] = json.dumps(results)
     response['headers']= {
          'Access-Control-Allow-Headers':'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Requested-With',
          'Access-Control-Allow-Methods':'POST,OPTIONS',
          'Access-Control-Allow-Origin':'*'
     }
     

     return response