from decouple import config


def config_aws_region() -> str:
    return config("AWS_REGION")


def config_aws_access_key() -> str:
    return config("AWS_ACCESS_KEY")


def config_aws_secret_key() -> str:
    return config("AWS_SECRET_KEY")


def config_aws_account_id() -> str:
    return config("AWS_ACCOUNT_ID")

def config_logs_bucket() -> str:
    return config("LOGS_BUCKET")


def config_logs_path() -> str:
    return config("LOGS_PATH")

