# DynamoDB and ElastiCache Geospatial Workshop

This repository contains resources for the DynamoDB / ElastiCache Geospatial Workshop. This workshop shows you how to build a simple application architecture using DynamoDB as a database of record, and Elasticache for Redis as a geospatial query engine and cache.

While we make efforts to test and verify the functionality of these workshop components, you are encouraged to read and understand the code, and use it at your own risk. 


**Note: Launching the CloudFormation templates contained in this workshop will incur costs for the AWS resources used.**

---

### Workshop Overview

 The use case for this workshop is a rental property search application. Through a simple web-based UI, agents can update a rental property's information, and customers can search for rental properties near them.

---

### Repository Structure

This repository contains the following directories:

* **architecture**: Contains diagrams for the application and network architectures for this solution.

* **cloudformation**: Contains an [AWS CloudFormation](https://aws.amazon.com/cloudformation/) template that will create the resources required for the application architecture. This template  requires modification before it will successfully launch. 

* **dataset**: Contains Python scripts to generate and load data to DynamoDB, and a file containing data for 2500 test properties.

* **lambda**: Contains [AWS Lambda](https://aws.amazon.com/lambda/) function definitions written in Python.

* **website**: Contains HTML, CSS and image files for the application.

---

### Application Architecture

The property search application architecture includes the following AWS services:

* **[Amazon DynamoDB](https://aws.amazon.com/dynamodb/)**: A fully-managed NoSQL database used as the system of record for rental property information.
* **[Amazon Elasticache for Redis](https://aws.amazon.com/elasticache/redis/)**: An in-memory data store that provides geospatial indexing of rental property locations and caching of rental property information.
* **[AWS Lambda](https://aws.amazon.com/lambda/)**: An event-driven compute service, used here to:
    * Add and update rental property information to an Amazon DynamoDB table.
    * Populate the geospatial index and cache when changes are made to the Amazon DynamoDB table.
    * Search the geospatial index and retrieve property details from the cache.
* **[Amazon API Gateway](https://aws.amazon.com/api-gateway/)**: A fully-managed service that makes the AWS Lambda functions for updating and searching rental property information available as REST APIs. 
* **[AWS Secrets Manager](https://aws.amazon.com/secrets-manager/)**: A fully-managed service that helps you securely store, manage, and retrieve credentials. 
---

### Prerequisites
- [Install](https://docs.aws.amazon.com/cli/v1/userguide/cli-chap-install.html) the AWS CLI.
- [Configure](https://docs.aws.amazon.com/cli/v1/userguide/cli-chap-configure.html) the AWS CLI to access your account.
- [Create](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_create_for-user.html) An IAM role with permissions to create and access all of the required resources (ElastiCache for Redis cluster, DynamoDB table and stream, Lambda functions, API Gateway REST API, VPC, Subnets, Secrets Manager secret, S3 bucket).

---

### Clone the workshop repository
Clone the repo:
```
git clone https://github.com/aws-samples/dynamodb-elasticache-geospatial-workshop.git .
```
---

### Create an S3 bucket to host the Lambda functions
[Create an S3 bucket](https://docs.aws.amazon.com/AmazonS3/latest/userguide/create-bucket-overview.html) to store the Lambda function zip files:
```
aws s3 mb s3://my-s3-bucket-name
```

---
### Create the Lambda function zip files
While the provided Cloudformation template creates the necessary resources, you must make some changes in order to successfully launch the stack.

**Zip and Upload Lambda Functions to S3**

The Cloudformation template downloads Lambda function code packaged in a zip file from an S3 bucket:
```
Code: 
    S3Bucket: my-s3-bucket-name
    S3Key: lambda/property-cache-populate.zip
```
This deployment method is used because two of the Lambda functions in this workshop (`property-cache-populate` and `property-cache-query`) depend on the [redis-py](https://pypi.org/project/redis/) library. This dependency must be packaged with the Lambda function code into a zip file and stored in an S3 bucket so CloudFormation can access it. Instructions for packaging the lambda function code and dependencies in a zip file can be found [here](https://docs.aws.amazon.com/lambda/latest/dg/python-package.html#python-package-create-package-with-dependency). 

Below are example commands for packaging the `property-cache-populate` function. The same process must be followed for the other two Lambda functions (the `property-table-update` function does not require the external dependency, but for simplicity this workshop expects it to be packaged in the same way). 

After cloning the repo, perform the following from the repo's root directory:

1. Change to the lambda function directory:
```
cd lambda/property-cache-populate
```
2. Install py-redis into a directory named `package`:
```
pip3 install --target ./package redis
```
3. Change to the package directory and zip it (dont forget the period at the end of the command)
```
cd package &&  zip -r ../property-cache-populate.zip .
```
4. Add the lambda_function.py file to the root of the zip file:
```
cd .. && zip -g property-cache-populate.zip lambda_function.py
```
5. Upload the zip file to an S3 bucket (this example uses the AWS CLI, but you can also use the AWS console):
```
aws s3 cp property-cache-populate.zip s3://my-s3-bucket-name/lambda/
```
---

### Update the Cloudformation template

Once the three Lambda functions are zipped and uploaded to S3, update the S3 bucket names in the Cloudformation template to the S3 bucket containing your Lambda function zip files. Ensure the below template snippet for each of the three Lambda declarations refers to the correct path for your zip files, replacing  `my-s3-bucket-name` with the name of your  S3 bucket:
```
LambdaFunctionTableUpdate:
    Type: AWS::Lambda::Function
    DependsOn: LambdaIAMRole
    ...
    ...
    Code: 
        S3Bucket: my-s3-bucket-name
        S3Key: lambda/property-table-update.zip
```
---

### Launch the CloudFormation Stack

Once your Lambda function zip files are uploaded to S3 and the template modified to reflect their locations, you can [launch the CloudFormation stack](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/cfn-console-create-stack.html) in the same region as your S3 bucket. From the root of the repo, execute the following command:
```
aws cloudformation create-stack \
--stack-name dynamodb-workshop \
--template-body file://cloudformation/initial.yaml \
--capabilities CAPABILITY_IAM \
--region <your region>
```

---

### Update the website configuration

The website requires the following configuration to work: 

1. Add an API Key to the website.
    - Sign up to Mapbox and retrieve an API key.
    - Edit the file `website/js/index.js` and set the value of `mapboxgl.accessToken` to your API key.

2. Add the API endpoint for API Gateway to the website. 
    - Obtain the API Endpoint from the Outputs section of your CloudFormation stack. 
    - Edit the file `website/js/index.js` and set the value of `API_URL` to your API endpoint.

3. Add the API secret key to the website.
    - Obtain the API Gateway secret key from your [API Gateway Console](https://eu-west-1.console.aws.amazon.com/apigateway/home?region=eu-west-1#/api-keys) (using the correct region). The key is named `WorkshopApiKey`.
    - Edit the file `website/js/index.js` and set the value of `API_KEY` to the API Gateway secret key.

Example website/js/index.js:
```
const API_URL = 'https://yourid.execute-api.eu-west-1.amazonaws.com/workshop'
const API_KEY = 'youruniqueAPIkey'
mapboxgl.accessToken = 'pk.yourmapboxAPItoken';
```
---
### Load the sample data set
To have properties for the website to search, sample data must be loaded into the DynamoDB table. This will generate events in the DynamoDB Stream that trigger the Lambda function to populate the Redis Cache. We have provided data for 2500 sample properties and a python script to upload property data to the table. 

1. Retrieve the DynamoDB table name from the Output of your Cloudformation Stack.
2. Run the following command from the root of the repository:
```
python3 dataset/upload.py \
-t <dynamodb table name> \
-f dataset/properties.json \
-r <region> (e.g eu-west-1)
```
---

### Run the sample application!
Open the file `website/js/index.html` in your web browser to use the workshop application.

---


## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

---


## License

This library is licensed under the MIT-0 License. See the LICENSE file for more information.
