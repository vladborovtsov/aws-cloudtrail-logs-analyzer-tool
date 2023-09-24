from decouple import config


def config_aws_region() -> str:
    return config("AWS_REGION")


def config_aws_access_key() -> str:
    return config("AWS_ACCESS_KEY")


def config_aws_secret_key() -> str:
    return config("AWS_SECRET_KEY")


def config_logs_bucket() -> str:
    return config("LOGS_BUCKET")


def config_logs_path() -> str:
    return config("LOGS_PATH")


def config_logs_delete_imported_files_from_s3() -> bool:
    return config("DELETE_FROM_S3", default=False)


def config_mongo_host() -> str:
    return config("MONGO_HOST")


def config_mongo_user() -> str:
    return config("MONGO_USER")


def config_mongo_password() -> str:
    return config("MONGO_PASSWORD")


def config_mongo_db() -> str:
    return config("MONGO_DB")


def config_mongo_collection_logs() -> str:
    return config("MONGO_COLLECTION_LOGS", default="cloudtrail")


def config_mongo_collection_metadata() -> str:
    return config("MONGO_COLLECTION_METADATA", default="metadata")
