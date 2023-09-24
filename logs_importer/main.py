import gzip
import json
import logging
from urllib.parse import quote_plus

import boto3
import pymongo

import logs_importer.config as Configuration

logging.basicConfig(level=logging.INFO)


class LogsImporter:
    def __init__(self, config: dict[str, str] | bool):
        self.s3_client = boto3.client("s3", region_name=config["aws_region"])
        self.mongo_uri = "mongodb://%s:%s@%s" % (
            quote_plus(config["mongo_user"]),
            quote_plus(config["mongo_password"]),
            config["mongo_host"],
        )
        self.mongo_client = pymongo.MongoClient(self.mongo_uri)
        self.mongo_db = self.mongo_client[config["mongo_db"]]

        self.logs_collection = self.mongo_db[config["mongo_collection_logs"]]
        self.metadata_collection = self.mongo_db[config["mongo_collection_metadata"]]

        self.logs_bucket = config["logs_bucket"]
        self.logs_path = config["logs_path"]
        self.remove_imported_s3_files = config["remove_imported_s3_files"]

    def fetch_logs_list(self) -> list[str]:
        response = self.s3_client.list_objects_v2(
            Bucket=self.logs_bucket, Prefix=self.logs_path
        )
        return [
            content["Key"]
            for content in response.get("Contents", [])
            if "Key" in content and content["Key"] != self.logs_path
        ]

    def s3_needs_import(self, s3_obj: dict[str, str], key: str) -> bool:
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
                Bucket=self.logs_bucket, Key=s3_file_name
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

                if records is None:
                    raise ValueError("Records field is missing in the log.")

                if isinstance(records, list):
                    for item in records:
                        query = {"eventID": item["eventID"]}
                        # Replace existing record with new data or insert if it doesn't exist
                        self.logs_collection.replace_one(query, item, upsert=True)
                        # col.insert_one(item)

                else:
                    # Raise an exception if records are not in the expected list format
                    raise TypeError("The Records field is not a list.")
                    # col.replace_one(query, document, upsert=True)
                    # col.insert_one(records) # this is performannt by doesnt work in my case.

            if self.remove_imported_s3_files:
                self.s3_client.delete_object(Bucket=self.logs_bucket, Key=s3_file_name)

        logging.info(
            "Total records: %s", self.logs_collection.estimated_document_count()
        )
        logging.info("Finished.")


if __name__ == "__main__":
    default_config = {
        "aws_region": Configuration.aws_region(),
        "logs_bucket": Configuration.logs_bucket(),
        "logs_path": Configuration.logs_path(),
        "remove_imported_s3_files": Configuration.remove_imported_s3_files(),
        "mongo_db": Configuration.mongo_db(),
        "mongo_host": Configuration.mongo_host(),
        "mongo_password": Configuration.mongo_password(),
        "mongo_user": Configuration.mongo_user(),
        "mongo_collection_logs": Configuration.mongo_collection_logs(),
        "mongo_collection_metadata": Configuration.mongo_collection_metadata(),
    }

    LogsImporter(config=default_config).import_logs()
