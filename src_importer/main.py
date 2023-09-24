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
    config_mongo_collection_logs,
    config_mongo_collection_metadata,
    config_logs_delete_imported_files_from_s3,
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
        self.logs_collection = self.mongo_db[config_mongo_collection_logs()]
        self.metadata_collection = self.mongo_db[config_mongo_collection_metadata()]

    def fetch_logs_list(self) -> list[str]:
        response = self.s3_client.list_objects_v2(
            Bucket=config_logs_bucket(), Prefix=config_logs_path()
        )
        return [
            content["Key"]
            for content in response.get("Contents", [])
            if "Key" in content and content["Key"] != config_logs_path()
        ]

    def s3_needs_import(self, s3_obj, key) -> bool:
        name = key
        content_length = s3_obj["ContentLength"]
        # last_modified = s3_obj["LastModified"] # TODO: i have some doubts its really needed: logs are always growing.

        q = {"name": name}
        item = {"name": name, "content_length": content_length}

        mongo_result = self.metadata_collection.update_one(
            q, {"$set": item}, upsert=True
        )

        if mongo_result.upserted_id is not None:
            logging.debug("File %s was never processed before. Record created", key)
            return True
        elif mongo_result.modified_count == 1:
            logging.debug(
                "File in S3 (%s) has different content length. Record updated", key
            )
            return True
        elif mongo_result.modified_count == 0:
            logging.debug("File has been already processed: %s", key)
            return False
        else:
            # This else block will handle unexpected scenarios.
            logging.error(
                "Unexpected behavior while updating MongoDB record for %s", key
            )
            raise ValueError("Unexpected behavior while updating MongoDB record.")

    def import_logs(self):
        for s3_file_name in self.fetch_logs_list():
            s3_obj = self.s3_client.get_object(
                Bucket=config_logs_bucket(), Key=s3_file_name
            )

            if not self.s3_needs_import(s3_obj, s3_file_name):
                logging.info("Skipping %s by metadata conditions.", s3_file_name)
                continue
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
                    # I never caught it yet.
                    print("OOPS!")
                    exit(1)
                    # col.replace_one(query, document, upsert=True)
                    # col.insert_one(records) # this is performannt by doesnt work in my case.

            if config_logs_delete_imported_files_from_s3():
                self.s3_client.delete_object(
                    Bucket=config_logs_bucket(), Key=s3_file_name
                )

        logging.info(
            "Total records: %s", self.logs_collection.estimated_document_count()
        )
        logging.info("Finished.")


if __name__ == "__main__":
    LogsImporter().import_logs()
