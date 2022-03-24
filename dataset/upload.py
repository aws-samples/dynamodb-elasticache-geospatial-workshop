from decimal import Decimal
import boto3, json, time, argparse

# Get Args
parser = argparse.ArgumentParser()
parser.add_argument("-t", "--tablename", help="Table Name")
parser.add_argument("-f", "--file", help="File Location")
parser.add_argument("-r", "--region", help="Region")
args = parser.parse_args()

start_time = time.time()
#  Create DynamoDB Client
dynamodb = boto3.resource('dynamodb', region_name=args.region)
# Create Table Resource to Provide DynamoDB JSON Abstraction
table = dynamodb.Table(args.tablename)

# Get Dataset
try:
    with open(args.file) as fp:
        data = json.load(fp, parse_float=Decimal)

    # Upload Data to DynamoDB Using BatchWriter
    # BatchWriter is a Wrapper for BatchWriteItems and Handles Retry Logic of Unprocessed Items
    try:
        with table.batch_writer() as batch:
            for property in data:
                batch.put_item(
                    Item=property
                )
        print("Uploaded {} items to {}".format(len(data), args.tablename))
        print("--- %s seconds ---" % (time.time() - start_time))
    
    except Exception as e:
        print("Failed to upload data: {}".format(e))

except Exception as e:
    print("Cannot open json file: {}".format(e))


