import json
from urllib.parse import quote_plus

import boto3
import pymongo
from config import config_logs_path, config_logs_bucket, config_aws_region, config_mongo_host, config_mongo_user, config_mongo_password, config_mongo_db, config_mongo_collection
import gzip


# Initialize a session using Amazon DynamoDB
s3 = boto3.client('s3', region_name=config_aws_region())

# Initialize a session using pymongo
uri = "mongodb://%s:%s@%s" % (
    quote_plus(config_mongo_user()), quote_plus(config_mongo_password()), config_mongo_host())
client = pymongo.MongoClient(uri)

db = client[config_mongo_db()]
col = db[config_mongo_collection()]

# Fetch the list of CloudTrail logs
response = s3.list_objects_v2(
    Bucket=config_logs_bucket(),
    Prefix=config_logs_path()
)

# Loop through each file in the S3 bucket
for content in response.get('Contents', []):
    s3_file_name = content.get('Key')
    if s3_file_name == config_logs_path():
        continue # We don't need the dir itself

    s3_obj = s3.get_object(Bucket=config_logs_bucket(), Key=s3_file_name)

    print(s3_file_name)
    s3_file_content = s3_obj['Body'].read()
    decompressed_content = gzip.decompress(s3_file_content).decode('utf-8')

    # CloudTrail logs are often stored in a single line, separated by newline characters
    logs = decompressed_content.strip().split("\n")

    for log in logs:
        log_json = json.loads(log)
        records: list = log_json["Records"]

        if type(records) == list:
            for item in records:
                q = {"eventID" : item["eventID"]}
                col.replace_one(q, item, upsert=True)
                #col.insert_one(item)
        else:
            print("OOPS!")
            exit(1)
            #col.replace_one(query, document, upsert=True)
            #col.insert_one(records) # this is performannt by doesnt work in my case.



print("Total records: ")
print(col.estimated_document_count())
print('Data loaded into MongoDB successfully.')
