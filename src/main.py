import json
from urllib.parse import quote_plus

import boto3
import pymongo
from config import (
    config_logs_path,
    config_logs_bucket,
    config_aws_region,
    config_mongo_host,
    config_mongo_user,
    config_mongo_password,
    config_mongo_db,
    config_mongo_collection,
)
import gzip
import logging

logging.basicConfig(level=logging.INFO)


class LogsImporter:
    def __init__(self):
        self.s3_client = boto3.client("s3", region_name=config_aws_region())
        self.mongo_uri = "mongodb://%s:%s@%s" % (
            quote_plus(config_mongo_user()),
            quote_plus(config_mongo_password()),
            config_mongo_host(),
        )
        self.mongo_client = pymongo.MongoClient(self.mongo_uri)
        self.mongo_db = self.mongo_client[config_mongo_db()]
        self.logs_collection = self.mongo_db[config_mongo_collection()]

    def fetch_logs_list(self) -> list[str]:
        response = self.s3_client.list_objects_v2(
            Bucket=config_logs_bucket(), Prefix=config_logs_path()
        )
        return [
            content["Key"]
            for content in response.get("Contents", [])
            if "Key" in content and content["Key"] != config_logs_path()
        ]

    def import_logs(self):
        for s3_file_name in self.fetch_logs_list():
            s3_obj = self.s3_client.get_object(
                Bucket=config_logs_bucket(), Key=s3_file_name
            )
            logging.info("Processing %s", s3_file_name)
            s3_file_content = s3_obj["Body"].read()

            decompressed_content = gzip.decompress(s3_file_content).decode("utf-8")

            # CloudTrail logs are often stored in a single line, separated by newline characters
            logs = decompressed_content.strip().split("\n")

            for log in logs:
                log_json = json.loads(log)
                records: list = log_json["Records"]

                if type(records) == list:
                    for item in records:
                        q = {"eventID": item["eventID"]}
                        self.logs_collection.replace_one(q, item, upsert=True)
                        # col.insert_one(item)
                else:
                    print("OOPS!")
                    exit(1)
                    # col.replace_one(query, document, upsert=True)
                    # col.insert_one(records) # this is performannt by doesnt work in my case.

        print("Total records: ")
        print(self.logs_collection.estimated_document_count())
        print("Data loaded into MongoDB successfully.")


if __name__ == "__main__":
    LogsImporter().import_logs()
