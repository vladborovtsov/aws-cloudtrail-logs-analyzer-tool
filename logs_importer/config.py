from decouple import config


def aws_region() -> str:
    return config("AWS_REGION")


def logs_bucket() -> str:
    return config("LOGS_BUCKET")


def logs_path() -> str:
    return config("LOGS_PATH")


def remove_imported_s3_files() -> bool:
    return config("DELETE_FROM_S3", default=False)


def mongo_host() -> str:
    return config("MONGO_HOST")


def mongo_user() -> str:
    return config("MONGO_USER")


def mongo_password() -> str:
    return config("MONGO_PASSWORD")


def mongo_db() -> str:
    return config("MONGO_DB")


def mongo_collection_logs() -> str:
    return config("MONGO_COLLECTION_LOGS", default="cloudtrail")


def mongo_collection_metadata() -> str:
    return config("MONGO_COLLECTION_METADATA", default="metadata")
